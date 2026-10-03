"""Deterministic text normalization, tokenization, phrase matching, and negation detection."""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

# Boundary words that break negation propagation
NEGATION_BOUNDARIES = frozenset({"|", "but", "however", "although", "except", "and"})

# Conjunctions that continue negation scope
NEGATION_CONTINUATIONS = frozenset({"or", "nor"})

# Allowable filler words between negation cue and symptom phrase (up to 3 tokens)
NEGATION_FILLERS = frozenset(
    {
        "history",
        "of",
        "any",
        "signs",
        "sign",
        "symptoms",
        "symptom",
        "evidence",
        "a",
        "the",
        "my",
        "current",
        "recent",
        "new",
        "known",
        "had",
        "have",
        "has",
        "experienced",
        "experience",
    }
)

# Multi-token and single-token negation cues
MULTI_TOKEN_NEGATION_CUES = (
    ("does", "not", "have"),
    ("do", "not", "have"),
    ("doesnt", "have"),
    ("dont", "have"),
    ("free", "of"),
    ("no", "history", "of"),
    ("no", "signs", "of"),
    ("no", "sign", "of"),
    ("no", "evidence", "of"),
    ("never", "had"),
    ("never", "have"),
)

SINGLE_TOKEN_NEGATION_CUES = frozenset(
    {
        "no",
        "not",
        "never",
        "without",
        "denies",
        "denied",
    }
)

# Curly quotes mapping table
CURLY_QUOTES = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "`": "'",
        "´": "'",
    }
)

# Regex for glued units (e.g., 250mg -> 250 mg, 5ml -> 5 ml)
GLUED_UNITS_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)(mg|mcg|g|iu|ml|puff|puffs|tablet|tablets|capsule|capsules)\b",
    re.IGNORECASE,
)

# Regex for blood pressure (e.g., 148/94, 120/80 mmHg)
BP_PATTERN = re.compile(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b")

# Regex for clause punctuation
CLAUSE_PUNCT_PATTERN = re.compile(r"[\.,;:?!\n\r]+")

# Regex for non-alphanumeric (except pipe)
NON_ALPHANUM_PATTERN = re.compile(r"[^a-z0-9|]+")

# Regex for 3+ repeated letters
REPEATED_LETTERS_PATTERN = re.compile(r"([a-z])\1{2,}")


def get_default_data_dir() -> Path:
    """Find data directory relative to this module."""
    return Path(__file__).resolve().parent.parent.parent / "data"


@lru_cache(maxsize=1)
def load_synonyms_map(synonyms_path: Path | None = None) -> list[tuple[list[str], list[str]]]:
    """Load and sort synonym phrase replacements from data/lexicon/synonyms.json."""
    path = synonyms_path or (get_default_data_dir() / "lexicon" / "synonyms.json")
    if not path.exists():
        return []

    with open(path, encoding="utf-8") as f:
        raw_map: dict[str, str] = json.load(f)

    # Pre-tokenize patterns and replacements, sort by length descending
    compiled: list[tuple[list[str], list[str]]] = []
    for k, v in raw_map.items():
        src_tokens = k.strip().lower().split()
        tgt_tokens = v.strip().lower().split()
        if src_tokens and tgt_tokens and src_tokens != tgt_tokens:
            compiled.append((src_tokens, tgt_tokens))

    compiled.sort(key=lambda x: len(x[0]), reverse=True)
    return compiled


@lru_cache(maxsize=1)
def load_demographics_tokens(demographics_path: Path | None = None) -> list[list[str]]:
    """Load demographic phrases from data/lexicon/demographics.json."""
    path = demographics_path or (get_default_data_dir() / "lexicon" / "demographics.json")
    if not path.exists():
        return []

    with open(path, encoding="utf-8") as f:
        data: dict[str, list[str]] = json.load(f)

    phrases: list[list[str]] = []
    for terms in data.values():
        for t in terms:
            toks = t.strip().lower().split()
            if toks:
                phrases.append(toks)

    phrases.sort(key=len, reverse=True)
    return phrases


def apply_synonym_mappings(toks: list[str], synonyms_path: Path | None = None) -> list[str]:
    """Replace token subsequences according to the synonym dictionary."""
    synonym_rules = load_synonyms_map(synonyms_path)
    if not synonym_rules:
        return toks

    res: list[str] = list(toks)
    idx = 0
    while idx < len(res):
        matched = False
        for src_phrase, tgt_phrase in synonym_rules:
            src_len = len(src_phrase)
            if res[idx : idx + src_len] == src_phrase:
                res[idx : idx + src_len] = tgt_phrase
                idx += len(tgt_phrase)
                matched = True
                break
        if not matched:
            idx += 1
    return res


NUMBER_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "ten": 10,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
}


def extract_blood_pressure(raw_text: str) -> tuple[int, int] | None:
    """Extract blood pressure readings like '148/94' from raw text."""
    m = BP_PATTERN.search(raw_text)
    if m:
        try:
            return int(m.group(1)), int(m.group(2))
        except ValueError:
            return None
    return None


def extract_minutes(tok_list: list[str]) -> int | None:
    """Extract duration in minutes from token list (e.g. '25 minutes', '2 hours')."""
    if not tok_list:
        return None

    # Check for half an hour
    for i in range(len(tok_list)):
        if tok_list[i : i + 3] == ["half", "an", "hour"] or tok_list[i : i + 2] == ["half", "hour"]:
            return 30
        if tok_list[i : i + 2] == ["an", "hour"] or tok_list[i : i + 2] == ["one", "hour"]:
            return 60

    # Scan for number + unit
    for i in range(len(tok_list) - 1):
        w1 = tok_list[i]
        w2 = tok_list[i + 1]

        val: int | None = None
        if w1.isdigit():
            val = int(w1)
        elif w1 in NUMBER_WORDS:
            val = NUMBER_WORDS[w1]

        if val is not None:
            if w2 in {"minute", "minutes", "min", "mins"}:
                return val
            if w2 in {"hour", "hours", "hr", "hrs"}:
                return val * 60

    return None


def normalize(text: str, synonyms_path: Path | None = None) -> str:
    """Normalize input text into standard token string format."""
    # 1. Truncate to 1000 characters
    s = text[:1000]

    # 2. Unicode NFKC
    s = unicodedata.normalize("NFKC", s)

    # 3. Lowercase
    s = s.lower()

    # 4. Separate glued dosage units (e.g., 250mg -> 250 mg)
    s = GLUED_UNITS_PATTERN.sub(r"\1 \2", s)

    # 5. Replace curly quotes and remove apostrophes
    s = s.translate(CURLY_QUOTES)
    s = s.replace("'", "")

    # 6. Replace clause punctuation with sentinel token '|'
    s = CLAUSE_PUNCT_PATTERN.sub(" | ", s)

    # 7. Replace every other non-alphanumeric character with a space
    s = NON_ALPHANUM_PATTERN.sub(" ", s)

    # 8. Collapse runs of 3+ repeated letters to 2, collapse whitespace
    s = REPEATED_LETTERS_PATTERN.sub(r"\1\1", s)
    s = re.sub(r"\s+", " ", s).strip()

    # 9. Apply synonym map at token level
    tok_list = s.split()
    mapped_toks = apply_synonym_mappings(tok_list, synonyms_path)
    return " ".join(mapped_toks)


def tokens(norm: str) -> list[str]:
    """Split normalized text into a list of tokens."""
    return norm.split()


def find_phrase(tok_list: list[str], phrase_tokens: list[str]) -> list[int]:
    """Find all start indexes of a phrase in tokens with exact whole-token matching."""
    if not tok_list or not phrase_tokens:
        return []

    p_len = len(phrase_tokens)
    t_len = len(tok_list)
    if p_len > t_len:
        return []

    matches: list[int] = []
    for i in range(t_len - p_len + 1):
        if tok_list[i : i + p_len] == phrase_tokens:
            matches.append(i)
    return matches


def is_negated(tok_list: list[str], start: int) -> bool:
    """Check if token sequence at start index is preceded by an unbroken negation cue."""
    if start <= 0 or not tok_list:
        return False

    # Find the nearest boundary before start (breaks negation propagation)
    left_bound = 0
    for i in range(start - 1, -1, -1):
        if tok_list[i] in NEGATION_BOUNDARIES:
            left_bound = i + 1
            break

    if left_bound >= start:
        return False

    # Check direct negation: [cue] + (0-3 fillers) + [target at start]
    for cue_pos in range(max(left_bound, start - 4), start):
        if tok_list[cue_pos] in SINGLE_TOKEN_NEGATION_CUES:
            fillers = tok_list[cue_pos + 1 : start]
            if len(fillers) <= 3 and all(f in NEGATION_FILLERS for f in fillers):
                return True

    for cue in MULTI_TOKEN_NEGATION_CUES:
        c_len = len(cue)
        for cue_pos in range(max(left_bound, start - 4 - c_len), start - c_len + 1):
            if cue_pos >= left_bound and tuple(tok_list[cue_pos : cue_pos + c_len]) == cue:
                fillers = tok_list[cue_pos + c_len : start]
                if len(fillers) <= 3 and all(f in NEGATION_FILLERS for f in fillers):
                    return True

    # Check chained negation via "or" / "nor"
    for conj_pos in range(start - 1, left_bound - 1, -1):
        if tok_list[conj_pos] in NEGATION_CONTINUATIONS:
            fillers_after_conj = tok_list[conj_pos + 1 : start]
            if not all(f in NEGATION_FILLERS for f in fillers_after_conj):
                continue

            # Look for any negation cue before conj_pos in the same clause
            has_cue = False
            for cue_pos in range(left_bound, conj_pos):
                if tok_list[cue_pos] in SINGLE_TOKEN_NEGATION_CUES:
                    has_cue = True
                    break
                for cue in MULTI_TOKEN_NEGATION_CUES:
                    c_len = len(cue)
                    if (
                        cue_pos + c_len <= conj_pos
                        and tuple(tok_list[cue_pos : cue_pos + c_len]) == cue
                    ):
                        has_cue = True
                        break
                if has_cue:
                    break
            if has_cue:
                return True

    return False


def strip_demographics(tok_list: list[str], demographics_path: Path | None = None) -> list[str]:
    """Strip age, gender, familial, and pronoun noise terms from token list."""
    phrases = load_demographics_tokens(demographics_path)
    if not phrases:
        return tok_list

    res = list(tok_list)
    idx = 0
    while idx < len(res):
        matched = False
        for p in phrases:
            p_len = len(p)
            if res[idx : idx + p_len] == p:
                del res[idx : idx + p_len]
                matched = True
                break
        if not matched:
            idx += 1
    return res
