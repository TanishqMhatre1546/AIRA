"""Deterministic spelling correction and candidate lattice generation for symptom matching.

Safety Invariants:
1. Pure Python only. No external ML, PyTorch, transformers, or network packages.
2. Common English words are never corrected, preserving valid user vocabulary.
3. Tokens under 4 letters are never corrected.
4. Escalate-only: candidates supplement original tokens, never overwrite user text.
5. Operates in sub-millisecond time to ensure gate latency stays well under 5-15 ms.
"""

from __future__ import annotations

import contextlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.text import apply_synonym_mappings

SEVERITY_WORDS_DEFAULT: frozenset[str] = frozenset(
    {
        "severe",
        "unbearable",
        "worst",
        "bad",
        "intense",
        "extreme",
        "excruciating",
    }
)

CLINICAL_ESCALATORS_DEFAULT: tuple[str, ...] = (
    "high fever",
    "fever",
    "pus",
    "blood",
    "bloody",
    "swollen glands",
    "swollen neck glands",
    "spreading",
    "persistent vomiting",
    "chest pain",
    "chest discomfort",
    "short of breath",
    "difficulty breathing",
    "confusion",
    "worsening",
    "not improving",
    "recurrent",
    "recurring",
    "repeated",
    "widespread",
    "entire",
    "all over",
    "covering",
    "sleep disturbance",
)


def damerau_levenshtein(s1: str, s2: str) -> int:
    """Compute Damerau-Levenshtein distance with adjacent transpositions cost 1."""
    len1, len2 = len(s1), len(s2)
    if s1 == s2:
        return 0
    if abs(len1 - len2) > 2:
        return 999

    dp: list[list[int]] = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,  # deletion
                dp[i][j - 1] + 1,  # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )
            # Transposition of adjacent characters
            if i > 1 and j > 1 and s1[i - 1] == s2[j - 2] and s1[i - 2] == s2[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

    return dp[len1][len2]


def _get_deletes(word: str, max_dist: int) -> set[str]:
    """Generate all deletion substrings of word up to max_dist."""
    results: set[str] = set()
    queue = {word}
    for _ in range(max_dist):
        next_queue: set[str] = set()
        for w in queue:
            for i in range(len(w)):
                del_str = w[:i] + w[i + 1 :]
                if del_str and del_str not in results:
                    results.add(del_str)
                    next_queue.add(del_str)
        queue = next_queue
    return results


def get_default_data_dir() -> Path:
    """Find data directory relative to this module."""
    return Path(__file__).resolve().parent.parent.parent / "data"


class SpellingCorrector:
    """In-memory symmetric-delete spelling corrector for clinical symptom phrases."""

    def __init__(
        self,
        vocab: set[str] | None = None,
        common_words: set[str] | None = None,
        misspellings: dict[str, str] | None = None,
        data_dir: Path | None = None,
    ) -> None:
        self.data_dir = data_dir or get_default_data_dir()

        self.misspellings: dict[str, str] = (
            misspellings if misspellings is not None else self._load_misspellings()
        )
        self.common_words: set[str] = (
            common_words if common_words is not None else self._load_common_words()
        )
        self.vocab: set[str] = vocab if vocab is not None else self._build_vocabulary()

        # Build SymSpell symmetric-delete index for vocabulary words
        self.deletes: dict[str, set[str]] = {}
        for word in self.vocab:
            if not word.isalpha():
                continue
            w_len = len(word)
            if w_len >= 4:
                dist1 = _get_deletes(word, 1)
                for d in dist1:
                    self.deletes.setdefault(d, set()).add(word)
            if w_len >= 7:
                dist2 = _get_deletes(word, 2)
                for d in dist2:
                    self.deletes.setdefault(d, set()).add(word)

    def _load_misspellings(self) -> dict[str, str]:
        path = self.data_dir / "lexicon" / "misspellings.json"
        if not path.exists():
            return {}
        with (
            contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError),
            open(path, encoding="utf-8") as f,
        ):
            data: dict[str, str] = json.load(f)
            return {k.lower(): v.lower() for k, v in data.items()}
        return {}

    def _load_common_words(self) -> set[str]:
        path = self.data_dir / "lexicon" / "common_words.txt"
        if not path.exists():
            return set()
        with (
            contextlib.suppress(OSError, UnicodeDecodeError),
            open(path, encoding="utf-8") as f,
        ):
            return {line.strip().lower() for line in f if line.strip()}
        return set()

    def _build_vocabulary(self) -> set[str]:
        vocab: set[str] = set()

        # 1. Rule phrases from urgency_rules.json
        rules_path = self.data_dir / "curated" / "urgency_rules.json"
        if rules_path.exists():
            with (
                contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError),
                open(rules_path, encoding="utf-8") as f,
            ):
                raw_data: dict[str, Any] = json.load(f)
                for rule in raw_data.get("rules", []):
                    match_blk = rule.get("match", {})
                    all_rule_phrases = (
                        list(match_blk.get("phrases", [])) + rule.get("trigger_keywords", [])
                    )
                    phrases_by_lang = match_blk.get("phrases_by_lang", {})
                    if isinstance(phrases_by_lang, dict):
                        for p_list in phrases_by_lang.values():
                            if isinstance(p_list, list):
                                all_rule_phrases.extend(p_list)

                    for p in all_rule_phrases:
                        for tok in p.lower().split():
                            if tok.isalpha():
                                vocab.add(tok)
                    for grp in match_blk.get("requires_all", []):
                        for item in grp:
                            if not item.startswith("@"):
                                for tok in item.lower().split():
                                    if tok.isalpha():
                                        vocab.add(tok)

        # 2. Condition aliases from condition_profiles.json
        profiles_path = self.data_dir / "lexicon" / "condition_profiles.json"
        if profiles_path.exists():
            with (
                contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError),
                open(profiles_path, encoding="utf-8") as f,
            ):
                profiles: dict[str, Any] = json.load(f)
                for prof in profiles.values():
                    for alias in prof.get("aliases", []):
                        for tok in alias.lower().split():
                            if tok.isalpha():
                                vocab.add(tok)

        # 3. Synonyms from synonyms.json
        synonyms_path = self.data_dir / "lexicon" / "synonyms.json"
        if synonyms_path.exists():
            with (
                contextlib.suppress(OSError, json.JSONDecodeError, UnicodeDecodeError),
                open(synonyms_path, encoding="utf-8") as f,
            ):
                syn_map: dict[str, str] = json.load(f)
                for k, v in syn_map.items():
                    for tok in k.lower().split():
                        if tok.isalpha():
                            vocab.add(tok)
                    for tok in v.lower().split():
                        if tok.isalpha():
                            vocab.add(tok)

        # 4. Severity words and clinical escalators
        for w in SEVERITY_WORDS_DEFAULT:
            if w.isalpha():
                vocab.add(w)

        for esc in CLINICAL_ESCALATORS_DEFAULT:
            for tok in esc.lower().split():
                if tok.isalpha():
                    vocab.add(tok)

        # 5. Canonical targets from misspellings
        for target in self.misspellings.values():
            for tok in target.lower().split():
                if tok.isalpha():
                    vocab.add(tok)

        # 6. Negation cues and boundaries
        for neg in (
            "without",
            "denies",
            "denied",
            "history",
            "never",
            "signs",
            "sign",
            "evidence",
        ):
            vocab.add(neg)

        return vocab

    def get_token_candidates(self, token: str) -> list[str]:
        """Return candidate corrections for a token, preserving original token first."""
        cand_list: list[str] = [token]
        tok_clean = token.lower().strip()

        # Check explicit reviewed misspelling map first
        if tok_clean in self.misspellings:
            canonical = self.misspellings[tok_clean]
            if canonical != tok_clean and canonical not in cand_list:
                cand_list.append(canonical)

        # Never correct numbers, non-alphabetic tokens, or short words <= 3 chars
        if not tok_clean.isalpha() or len(tok_clean) <= 3:
            return cand_list

        # If token is in vocabulary or common_words, never run fuzzy SymSpell correction
        if tok_clean in self.vocab or tok_clean in self.common_words:
            return cand_list

        # Edit distance limit based on length:
        # 4 to 6 chars: max_dist = 1
        # 7 or more chars: max_dist = 2
        max_dist = 1 if len(tok_clean) <= 6 else 2

        # Generate deletions for query token
        q_deletes = {tok_clean}
        q_deletes.update(_get_deletes(tok_clean, max_dist))

        # Find potential matching vocabulary words
        matches: set[str] = set()
        for d in q_deletes:
            if d in self.deletes:
                matches.update(self.deletes[d])
            if d in self.vocab:
                matches.add(d)

        # Score candidates with exact Damerau-Levenshtein distance
        scored_candidates: list[tuple[int, str]] = []
        for cand in matches:
            if abs(len(cand) - len(tok_clean)) > max_dist:
                continue
            dist = damerau_levenshtein(tok_clean, cand)
            if dist <= max_dist:
                scored_candidates.append((dist, cand))

        if scored_candidates:
            # Keep minimum edit distance candidates
            min_dist = min(dist for dist, _ in scored_candidates)
            best_cands = sorted({cand for dist, cand in scored_candidates if dist == min_dist})
            for c in best_cands:
                if c not in cand_list:
                    cand_list.append(c)

        return cand_list

    def split_concatenated_token(self, token: str) -> tuple[str, str] | None:
        """Detect missing space in compound words (e.g., 'chestpain' -> ('chest', 'pain'))."""
        tok_clean = token.lower().strip()
        if not tok_clean.isalpha() or len(tok_clean) < 7:
            return None
        if tok_clean in self.vocab or tok_clean in self.common_words:
            return None

        for k in range(3, len(tok_clean) - 2):
            w1 = tok_clean[:k]
            w2 = tok_clean[k:]
            if w1 in self.vocab and (w2 in self.vocab or w2 in self.common_words):
                return (w1, w2)
        return None

    def get_candidate_sequences(
        self,
        norm_tokens: list[str],
        max_sequences: int = 16,
    ) -> list[tuple[list[str], bool, str | None]]:
        """Generate candidate token sequences for escalate-only matching.

        Returns tuples of: (candidate_tokens, was_corrected, corrected_phrase_description)
        Original sequence is always returned first with was_corrected=False.
        """
        if not norm_tokens:
            return [(norm_tokens, False, None)]

        # Sequence 0 is always the original uncorrected sequence
        sequences: list[tuple[list[str], bool, str | None]] = [(list(norm_tokens), False, None)]

        # Collect corrections for each position
        corrections_by_pos: dict[int, list[str]] = {}
        splits_by_pos: dict[int, tuple[str, str]] = {}

        for idx, tok in enumerate(norm_tokens):
            cands = self.get_token_candidates(tok)
            # Alternate candidates beyond original token
            alts = [c for c in cands if c != tok]
            if alts:
                corrections_by_pos[idx] = alts

            split_res = self.split_concatenated_token(tok)
            if split_res:
                splits_by_pos[idx] = split_res

        if not corrections_by_pos and not splits_by_pos:
            return sequences

        # 1. Full combination sequence with all primary corrections applied
        full_corrected = list(norm_tokens)
        changes: list[str] = []
        for idx, alts in corrections_by_pos.items():
            full_corrected[idx] = alts[0]
            changes.append(alts[0])

        if full_corrected != norm_tokens:
            phrase_desc = " ".join(full_corrected)
            mapped_full = apply_synonym_mappings(full_corrected)
            sequences.append((mapped_full, True, phrase_desc))

        # 2. Individual single-word correction sequences
        for idx, alts in corrections_by_pos.items():
            for alt in alts:
                single_var = list(norm_tokens)
                single_var[idx] = alt
                mapped_single = apply_synonym_mappings(single_var)
                if (mapped_single, True, alt) not in sequences and len(sequences) < max_sequences:
                    sequences.append((mapped_single, True, alt))

        # 3. Concatenated token split sequences
        for idx, (w1, w2) in splits_by_pos.items():
            split_seq = norm_tokens[:idx] + [w1, w2] + norm_tokens[idx + 1 :]
            desc = f"{w1} {w2}"
            mapped_split = apply_synonym_mappings(split_seq)
            if (mapped_split, True, desc) not in sequences and len(sequences) < max_sequences:
                sequences.append((mapped_split, True, desc))

        return sequences


@lru_cache(maxsize=1)
def get_spelling_corrector() -> SpellingCorrector:
    """Cached singleton instance of SpellingCorrector."""
    return SpellingCorrector()
