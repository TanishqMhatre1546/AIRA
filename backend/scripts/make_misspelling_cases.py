"""Deterministic seeded generation of misspelling evaluation test cases.

Takes every emergency, refusal, and triage case from existing evaluation suites
and generates variants with single typos:
- delete a letter
- insert a letter
- swap adjacent letters
- replace a letter
- phonetic spelling
- missing space
- doubled letter
"""

from __future__ import annotations

import random
import re
from pathlib import Path
from typing import Any

import yaml

TYPO_TYPES: list[str] = [
    "delete",
    "insert",
    "swap",
    "replace",
    "phonetic",
    "missing_space",
    "doubled_letter",
]

PHONETIC_REPLACEMENTS: list[tuple[str, str]] = [
    ("ph", "f"),
    ("ea", "ee"),
    ("oo", "u"),
    ("c", "k"),
    ("tion", "shun"),
    ("gh", "f"),
]


def apply_delete(word: str, rng: random.Random) -> str:
    """Delete a single character from word (word length must be >= 5)."""
    if len(word) < 5:
        return word
    # Choose index from 1 to len(word)-1 to preserve first letter
    idx = rng.randint(1, len(word) - 1)
    return word[:idx] + word[idx + 1 :]


def apply_insert(word: str, rng: random.Random) -> str:
    """Insert an extra letter into word."""
    if len(word) < 4:
        return word
    idx = rng.randint(1, len(word) - 1)
    char = rng.choice("aeiousntrd")
    return word[:idx] + char + word[idx:]


def apply_swap(word: str, rng: random.Random) -> str:
    """Swap two adjacent letters in word."""
    if len(word) < 4:
        return word
    idx = rng.randint(1, len(word) - 2)
    chars = list(word)
    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    return "".join(chars)


def apply_replace(word: str, rng: random.Random) -> str:
    """Replace a single letter in word with another letter."""
    if len(word) < 5:
        return word
    idx = rng.randint(1, len(word) - 1)
    orig_char = word[idx]
    # Pick different character
    options = [c for c in "aeioustrndpmkb" if c != orig_char]
    char = rng.choice(options)
    return word[:idx] + char + word[idx + 1 :]


def apply_phonetic(word: str, _rng: random.Random) -> str:
    """Apply a phonetic spelling transformation to word."""
    w_lower = word.lower()
    for src, tgt in PHONETIC_REPLACEMENTS:
        if src in w_lower:
            return re.sub(src, tgt, word, count=1, flags=re.IGNORECASE)
    # Fallback to swapping vowels or c->k
    if "c" in w_lower:
        return re.sub("c", "k", word, count=1, flags=re.IGNORECASE)
    return word


def apply_doubled_letter(word: str, rng: random.Random) -> str:
    """Double a consonant or vowel in word."""
    if len(word) < 4:
        return word
    idx = rng.randint(1, len(word) - 1)
    char = word[idx]
    return word[:idx] + char + word[idx:]


def apply_missing_space(text: str, rng: random.Random) -> str:
    """Join two adjacent words by removing the space between them."""
    words = text.split()
    if len(words) < 2:
        return text

    # Find candidates where both words are >= 3 chars
    valid_indices = [
        i
        for i in range(len(words) - 1)
        if len(words[i].strip(",.!?")) >= 3 and len(words[i + 1].strip(",.!?")) >= 3
    ]
    if not valid_indices:
        return text

    idx = rng.choice(valid_indices)
    w1 = words[idx].rstrip(",.!?")
    w2 = words[idx + 1].lstrip(",.!?")
    joined = w1 + w2
    new_words = words[:idx] + [joined] + words[idx + 2 :]
    return " ".join(new_words)


def mutate_text(text: str, typo_type: str, rng: random.Random) -> str:
    """Mutate text by introducing exactly one typo according to typo_type."""
    if typo_type == "missing_space":
        return apply_missing_space(text, rng)

    words = text.split()
    # Find candidate words with length >= 4 that are purely alphabetic
    candidates = [
        (idx, w) for idx, w in enumerate(words) if re.search(r"[a-zA-Z]{4,}", w) and not w.isupper()
    ]
    if not candidates:
        candidates = [(idx, w) for idx, w in enumerate(words) if len(w) >= 4]
    if not candidates:
        return text

    idx, target_token = rng.choice(candidates)
    # Strip trailing punctuation if present
    punct = ""
    clean_word = target_token
    m = re.search(r"([,\.!\?:;]+)$", target_token)
    if m:
        punct = m.group(1)
        clean_word = target_token[: -len(punct)]

    if typo_type == "delete":
        mutated = apply_delete(clean_word, rng)
    elif typo_type == "insert":
        mutated = apply_insert(clean_word, rng)
    elif typo_type == "swap":
        mutated = apply_swap(clean_word, rng)
    elif typo_type == "replace":
        mutated = apply_replace(clean_word, rng)
    elif typo_type == "phonetic":
        mutated = apply_phonetic(clean_word, rng)
    elif typo_type == "doubled_letter":
        mutated = apply_doubled_letter(clean_word, rng)
    else:
        mutated = clean_word

    if mutated == clean_word:
        # Fallback to swap if mutation didn't change word
        mutated = apply_swap(clean_word, rng)

    words[idx] = mutated + punct
    return " ".join(words)


def generate_misspelling_cases() -> None:
    """Generate eval/misspelling_cases.yaml with seed 42."""
    rng = random.Random(42)  # noqa: S311
    base_dir = Path(__file__).resolve().parent.parent / "eval"

    with open(base_dir / "emergency_cases.yaml", encoding="utf-8") as f:
        emergency_cases = yaml.safe_load(f).get("cases", [])
    with open(base_dir / "refusal_cases.yaml", encoding="utf-8") as f:
        refusal_cases = yaml.safe_load(f).get("cases", [])
    with open(base_dir / "triage_cases.yaml", encoding="utf-8") as f:
        triage_cases = yaml.safe_load(f).get("cases", [])

    generated_cases: list[dict[str, Any]] = []

    # 1. Emergency cases (2 variants per case)
    for c in emergency_cases:
        orig_id = c.get("id", "EM")
        text = c.get("text", "")
        should_fire = c.get("should_fire", True)
        exp_outcome = c.get("expected_outcome", "EMERGENCY" if should_fire else "PASS")

        # Pick 2 different typo types
        selected_types = rng.sample(TYPO_TYPES, 2)
        for t_type in selected_types:
            mut_text = mutate_text(text, t_type, rng)
            if mut_text != text:
                generated_cases.append(
                    {
                        "id": f"{orig_id}-TYPO-{t_type.upper()}",
                        "original_id": orig_id,
                        "suite": "emergency",
                        "typo_type": t_type,
                        "text": mut_text,
                        "should_fire": should_fire,
                        "expected_outcome": exp_outcome,
                    }
                )

    # 2. Refusal cases (2 variants per case)
    for c in refusal_cases:
        orig_id = c.get("id", "REF")
        text = c.get("text", "")
        exp_outcome = c.get("expected_outcome", "REFUSAL")

        selected_types = rng.sample(TYPO_TYPES, 2)
        for t_type in selected_types:
            mut_text = mutate_text(text, t_type, rng)
            if mut_text != text:
                generated_cases.append(
                    {
                        "id": f"{orig_id}-TYPO-{t_type.upper()}",
                        "original_id": orig_id,
                        "suite": "refusal",
                        "typo_type": t_type,
                        "text": mut_text,
                        "expected_outcome": exp_outcome,
                    }
                )

    # 3. Triage cases (2 variants per case)
    for c in triage_cases:
        orig_id = c.get("id", "TR")
        text = c.get("text", "")
        exp_level = c.get("expected_level", "SELF_CARE")
        condition = c.get("condition")

        selected_types = rng.sample(TYPO_TYPES, 2)
        for t_type in selected_types:
            mut_text = mutate_text(text, t_type, rng)
            if mut_text != text:
                entry: dict[str, Any] = {
                    "id": f"{orig_id}-TYPO-{t_type.upper()}",
                    "original_id": orig_id,
                    "suite": "triage",
                    "typo_type": t_type,
                    "text": mut_text,
                    "expected_level": exp_level,
                }
                if condition:
                    entry["condition"] = condition
                generated_cases.append(entry)

    out_file = base_dir / "misspelling_cases.yaml"
    out_data = {
        "version": "1.0.0",
        "description": "Deterministic typo and misspelling evaluation test suite.",
        "seed": 42,
        "total_cases": len(generated_cases),
        "cases": generated_cases,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(out_data, f, sort_keys=False, width=120)

    print(f"Generated {len(generated_cases)} misspelling cases to {out_file}")


if __name__ == "__main__":
    generate_misspelling_cases()
