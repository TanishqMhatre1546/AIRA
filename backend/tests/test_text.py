"""Unit tests for deterministic text normalization, tokenization, phrase matching, and negation."""

from app.core.text import (
    find_phrase,
    is_negated,
    normalize,
    strip_demographics,
    tokens,
)


def test_normalize_truncation_and_nfkc() -> None:
    """Normalization truncates to 1000 characters and applies Unicode NFKC."""
    long_text = "word " * 300
    norm = normalize(long_text)
    assert len(norm) <= 1000

    # Unicode compatibility characters
    unicode_sample = "ﬀ ﬁ ﬂ"
    assert normalize(unicode_sample) == "ff fi fl"


def test_normalize_quotes_and_apostrophes() -> None:
    """Curly quotes are normalized and all apostrophes are removed."""
    sample = "‘Can’t breathe’, “won’t stop”"
    assert normalize(sample) == "cannot breathe | wont stop"


def test_normalize_clause_punctuation_and_repeated_letters() -> None:
    """Punctuation is replaced with pipe sentinel, and runs of 3+ letters collapse to 2."""
    sample = "Chesttt   painnn!!! Very bad... please help?"
    assert normalize(sample) == "chestt painn | very bad | please help |"


def test_normalize_synonym_replacement() -> None:
    """Synonyms are canonicalized from data/lexicon/synonyms.json."""
    sample = "I have loose motions and breathless feeling with tummy ache"
    norm = normalize(sample)
    assert "diarrhoea" in norm
    assert "short of breath" in norm
    assert "abdominal pain" in norm


def test_find_phrase_exact_whole_token_matching() -> None:
    """Phrase finding matches whole tokens only, preventing substring matches."""
    toks = tokens("she has a beautiful dress and urinary tract infection")

    # "uti" or "tract"
    assert find_phrase(toks, ["urinary", "tract", "infection"]) == [6]
    # No false match for "uti" inside "beautiful"
    assert find_phrase(toks, ["uti"]) == []


def test_is_negated_cues_and_window() -> None:
    """Negation is detected within 4 tokens before the target match."""
    toks1 = tokens("patient has no chest pain")
    # "chest pain" starts at token index 3
    assert is_negated(toks1, 3) is True

    toks2 = tokens("denies severe headache")
    # "severe headache" starts at index 1
    assert is_negated(toks2, 1) is True

    toks3 = tokens("i do not have fever")
    # "fever" starts at index 4
    assert is_negated(toks3, 4) is True

    toks4 = tokens("free of palpitations")
    # "palpitations" starts at index 2
    assert is_negated(toks4, 2) is True


def test_is_negated_blocked_by_boundaries() -> None:
    """Negation does not cross boundary tokens like '|', 'and', 'but'."""
    # 'and' blocks negation: "no fever and chest pain" does not negate chest pain
    toks1 = tokens("no fever and chest pain")
    # "chest pain" starts at index 3
    assert is_negated(toks1, 3) is False

    # '|' blocks negation
    toks2 = tokens("no fever | chest pain")
    assert is_negated(toks2, 3) is False

    # 'but' blocks negation
    toks3 = tokens("no fever but chest pain")
    assert is_negated(toks3, 3) is False


def test_strip_demographics() -> None:
    """Demographic age and familial words are stripped from token list."""
    toks = tokens("my 45 years old father has high blood pressure")
    stripped = strip_demographics(toks)
    assert "father" not in stripped
    assert "years" not in stripped
    assert "old" not in stripped
    assert "high" in stripped
    assert "blood" in stripped
    assert "pressure" in stripped
