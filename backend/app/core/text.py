"""Deterministic text normalization, tokenization, phrase matching, and negation detection."""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

# Boundary words that break negation propagation
NEGATION_BOUNDARIES = frozenset(
    {
        "|",
        "but",
        "however",
        "although",
        "except",
        "and",
        "लेकिन",
        "मगर",
        "परंतु",
        "किंतु",
        "पण",
        "पर",
        "par",
        "pan",
        "lekin",
        "magar",
        "parantu",
    }
)

# Conjunctions that continue negation scope
NEGATION_CONTINUATIONS = frozenset({"or", "nor", "या", "वा", "किंवा", "ya", "kinva"})

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
        "is",
        "are",
        "was",
        "were",
        "hai",
        "hain",
        "tha",
        "thi",
        "aa",
        "raha",
        "rahi",
        "rahe",
        "aahe",
        "aahet",
        "hota",
        "hoti",
        "hote",
        "ahe",
        "ahet",
        "ka",
        "ki",
        "ke",
        "mein",
        "me",
        "ko",
        "se",
        "cha",
        "chi",
        "che",
        "madhe",
        "t",
        "la",
        "हून",
        "त",
        "मध्ये",
        "का",
        "की",
        "के",
        "में",
        "को",
        "से",
        "है",
        "हैं",
        "था",
        "थी",
        "थे",
        "रहा",
        "रही",
        "रहे",
        "आहे",
        "आहेत",
        "होता",
        "होती",
        "होते",
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
    ("nahi", "hai"),
    ("nahi", "aa", "raha"),
    ("nahi", "aa", "rahi"),
    ("nahi", "aa", "rahe"),
    ("nahin", "hai"),
    ("nahin", "aa", "raha"),
    ("nahin", "aa", "rahi"),
    ("nahin", "aa", "rahe"),
    ("nahi", "ahe"),
    ("nahi", "aahe"),
    ("nahi", "hot"),
    ("nahi", "zala"),
    ("nahi", "jhala"),
    ("नहीं", "है"),
    ("नहीं", "आ", "रहा"),
    ("नहीं", "आ", "रही"),
    ("नहीं", "आ", "रहे"),
    ("नही", "है"),
    ("नही", "आ", "रहा"),
    ("नही", "आ", "रही"),
    ("नही", "आ", "रहे"),
    ("नाही", "आहे"),
    ("नाही", "होत"),
    ("नाही", "झाला"),
    ("नाही", "झाली"),
)

SINGLE_TOKEN_NEGATION_CUES = frozenset(
    {
        "no",
        "not",
        "never",
        "without",
        "denies",
        "denied",
        "नहीं",
        "नही",
        "बिना",
        "नाही",
        "नाहीत",
        "शिवाय",
        "नको",
        "नव्हते",
        "nahi",
        "nahin",
        "bina",
        "shivaay",
        "shivay",
        "nahit",
    }
)

# Single-token negation cues that can occur after a symptom phrase (Indic SOV languages)
INDIC_SUCCEEDING_NEGATION_CUES = frozenset(
    {
        "नहीं",
        "नही",
        "बिना",
        "नाही",
        "नाहीत",
        "शिवाय",
        "नको",
        "नव्हते",
        "nahi",
        "nahin",
        "bina",
        "shivaay",
        "shivay",
        "nahit",
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

# Devanagari digits to ASCII mapping table
DEVANAGARI_DIGITS = str.maketrans(
    {
        "०": "0",
        "१": "1",
        "२": "2",
        "३": "3",
        "४": "4",
        "५": "5",
        "६": "6",
        "७": "7",
        "८": "8",
        "९": "9",
    }
)

# Regex for glued units (e.g., 250mg -> 250 mg, 5ml -> 5 ml)
GLUED_UNITS_PATTERN = re.compile(
    r"\b(\d+(?:\.\d+)?)(mg|mcg|g|iu|ml|puff|puffs|tablet|tablets|capsule|capsules)\b",
    re.IGNORECASE,
)

# Regex for blood pressure (e.g., 148/94, 120/80 mmHg)
BP_PATTERN = re.compile(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b")

# Regex for clause punctuation (including Danda \u0964 and Double Danda \u0965)
CLAUSE_PUNCT_PATTERN = re.compile(r"[\.,;:?!\n\r\u0964\u0965]+")

# Regex for non-alphanumeric (except pipe and Devanagari range \u0900-\u097F)
NON_ALPHANUM_PATTERN = re.compile(r"[^a-z0-9|\u0900-\u097F]+")

# Regex for 3+ repeated letters
REPEATED_LETTERS_PATTERN = re.compile(r"([a-z\u0900-\u097F])\1{2,}")


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
def load_synonyms_by_first_token(
    synonyms_path: Path | None = None,
) -> dict[str, list[tuple[list[str], list[str]]]]:
    """Group synonym phrase replacements by their first token for O(1) prefix lookup."""
    rules = load_synonyms_map(synonyms_path)
    by_first: dict[str, list[tuple[list[str], list[str]]]] = {}
    for src, tgt in rules:
        by_first.setdefault(src[0], []).append((src, tgt))
    return by_first


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
    synonyms_by_first = load_synonyms_by_first_token(synonyms_path)
    if not synonyms_by_first:
        return toks

    res: list[str] = list(toks)
    idx = 0
    while idx < len(res):
        first = res[idx]
        candidate_rules = synonyms_by_first.get(first)
        if not candidate_rules:
            idx += 1
            continue

        matched = False
        for src_phrase, tgt_phrase in candidate_rules:
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


@lru_cache(maxsize=1)
def load_devanagari_variants_map(
    variants_path: Path | None = None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Load Devanagari character and word canonical variants."""
    path = variants_path or (get_default_data_dir() / "lexicon" / "devanagari_variants.json")
    if not path.exists():
        return ([], [])

    with open(path, encoding="utf-8") as f:
        raw_data: dict[str, dict[str, str]] = json.load(f)

    nuktas: list[tuple[str, str]] = []
    for src, tgt in raw_data.get("nuktas", {}).items():
        if src and tgt and src != tgt:
            nuktas.append((unicodedata.normalize("NFC", src), unicodedata.normalize("NFC", tgt)))

    words: list[tuple[str, str]] = []
    for cat in ("nasals", "vowel_variants"):
        for src, tgt in raw_data.get(cat, {}).items():
            if src and tgt and src != tgt:
                words.append((unicodedata.normalize("NFC", src), unicodedata.normalize("NFC", tgt)))

    words.sort(key=lambda x: len(x[0]), reverse=True)
    return (nuktas, words)


def apply_devanagari_variants(text: str, variants_path: Path | None = None) -> str:
    """Apply Devanagari nukta, chandrabindu/anusvara, and vowel canonicalizations."""
    nuktas, words = load_devanagari_variants_map(variants_path)

    res = text
    # 1. Apply single-character nukta replacements first
    for src, tgt in nuktas:
        if src in res:
            res = res.replace(src, tgt)

    # 2. General chandrabindu (\u0901) to anusvara (\u0902) mapping
    # In Devanagari typography, chandrabindu and anusvara are phonetic variants for nasalization
    res = res.replace("\u0901", "\u0902")

    # 3. Apply word-level canonical variants
    for src, tgt in words:
        if src in res:
            res = res.replace(src, tgt)

    return res


def normalize(text: str, synonyms_path: Path | None = None) -> str:
    """Normalize input text into standard token string format across all languages."""
    # 1. Truncate to 1000 characters
    s = text[:1000]

    # 2. Unicode NFKD compatibility decomposition followed by NFC composition
    # This decomposes ligatures (e.g. ﬀ -> ff) while maintaining clean Devanagari NFC characters
    s = unicodedata.normalize("NFKD", s)
    s = unicodedata.normalize("NFC", s)

    # 3. Remove zero-width joiners and non-joiners (\u200D, \u200C)
    s = s.replace("\u200c", "").replace("\u200d", "")

    # 4. Convert Devanagari digits to ASCII digits
    s = s.translate(DEVANAGARI_DIGITS)

    # 5. Lowercase Roman characters
    s = s.lower()

    # 6. Apply Devanagari canonical variant mappings (nuktas, nasals, vowel pairs)
    s = apply_devanagari_variants(s)

    # 7. Separate glued dosage units (e.g., 250mg -> 250 mg)
    s = GLUED_UNITS_PATTERN.sub(r"\1 \2", s)

    # 8. Replace curly quotes and remove apostrophes
    s = s.translate(CURLY_QUOTES)
    s = s.replace("'", "")

    # 9. Replace clause punctuation (including Danda । and ॥) with sentinel token '|'
    s = CLAUSE_PUNCT_PATTERN.sub(" | ", s)

    # 10. Replace every other non-alphanumeric character with a space
    s = NON_ALPHANUM_PATTERN.sub(" ", s)

    # 11. Collapse runs of 3+ repeated letters to 2, collapse whitespace
    s = REPEATED_LETTERS_PATTERN.sub(r"\1\1", s)
    s = re.sub(r"\s+", " ", s).strip()

    # 12. Apply synonym map at token level
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


def is_negated(tok_list: list[str], start: int, phrase_len: int = 1) -> bool:
    """Check if token sequence at start index is negated (preceding or succeeding cue)."""
    if not tok_list or start < 0 or start >= len(tok_list):
        return False

    end_pos = start + phrase_len

    # --- 1. Check preceding negation: [cue] ... [target at start] ---
    if start > 0:
        # Find the nearest boundary before start (breaks negation propagation)
        left_bound = 0
        for i in range(start - 1, -1, -1):
            if tok_list[i] in NEGATION_BOUNDARIES:
                left_bound = i + 1
                break

        if left_bound < start:
            # Check single token cue
            for cue_pos in range(max(left_bound, start - 4), start):
                if tok_list[cue_pos] in SINGLE_TOKEN_NEGATION_CUES:
                    fillers = tok_list[cue_pos + 1 : start]
                    if len(fillers) <= 3 and all(f in NEGATION_FILLERS for f in fillers):
                        return True

            # Check multi token cue
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

    # --- 2. Check succeeding negation (Hindi/Marathi): [target] ... [cue] ---
    # Many Indic expressions place negation after the symptom:
    # e.g. "सीने में दर्द नहीं है", "छातीत दुखत नाही".
    # English does not place negation after nouns ("nosebleed not stopping" is not negated).
    t_len = len(tok_list)
    if end_pos < t_len:
        # Find the nearest boundary after end_pos in the same clause
        right_bound = t_len
        for i in range(end_pos, t_len):
            if tok_list[i] in NEGATION_BOUNDARIES:
                right_bound = i
                break

        if right_bound > end_pos:
            # Check single token Indic negation cue within 4 tokens after the target phrase
            scan_end = min(right_bound, end_pos + 5)
            for cue_pos in range(end_pos, scan_end):
                if tok_list[cue_pos] in INDIC_SUCCEEDING_NEGATION_CUES:
                    fillers = tok_list[end_pos:cue_pos]
                    if len(fillers) <= 3 and all(f in NEGATION_FILLERS for f in fillers):
                        return True

            # Check multi token Indic negation cue
            for cue in MULTI_TOKEN_NEGATION_CUES:
                # Only check Indic cues for succeeding negation
                if not any(tok in INDIC_SUCCEEDING_NEGATION_CUES for tok in cue):
                    continue
                c_len = len(cue)
                for cue_pos in range(end_pos, min(right_bound - c_len + 1, end_pos + 5)):
                    if tuple(tok_list[cue_pos : cue_pos + c_len]) == cue:
                        fillers = tok_list[end_pos:cue_pos]
                        if len(fillers) <= 3 and all(f in NEGATION_FILLERS for f in fillers):
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
