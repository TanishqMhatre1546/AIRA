"""Unit tests for multilingual Devanagari and Roman script text processing,
normalization, and negation.
"""

from app.core.text import (
    find_phrase,
    is_negated,
    normalize,
    tokens,
)


def test_devanagari_normalization_digits_and_danda() -> None:
    """Devanagari digits are mapped to ASCII and dandas become clause sentinels."""
    text = "३ दिवस से तेज बुखार है। सीने में दर्द नहीं है॥"
    norm = normalize(text)
    # Digits converted: ३ -> 3
    assert "3 दिवस से तेज बुखार है" in norm
    # Danda । converted to pipe |
    assert " | " in norm
    assert "सीने में दर्द नहीं है" in norm


def test_devanagari_nuktas_and_nasals_normalization() -> None:
    """Nuktas and nasal variants are mapped to canonical forms."""
    text = "साँस लेने में तकलीफ़ है और ख़ाँसी आ रही है"
    norm = normalize(text)
    # साँस -> सांस
    assert "सांस" in norm
    # तकलीफ़ -> तकलीफ
    assert "तकलीफ" in norm
    # ख़ाँसी -> खांसी
    assert "खांसी" in norm


def test_devanagari_succeeding_negation_hindi() -> None:
    """Hindi succeeding negation ('सीने में दर्द नहीं है') is detected."""
    toks = tokens(normalize("सीने में तेज दर्द नहीं है"))
    phrase = ["सीने", "में", "तेज", "दर्द"]
    matches = find_phrase(toks, phrase)
    assert len(matches) == 1
    # Phrase starts at index 0, length is 4. 'नहीं है' immediately follows.
    assert is_negated(toks, matches[0], len(phrase)) is True


def test_devanagari_succeeding_negation_marathi() -> None:
    """Marathi succeeding negation ('छातीत दुखत नाही') is detected."""
    toks = tokens(normalize("मला छातीत दुखत नाही"))
    phrase = ["छातीत", "दुखत"]
    matches = find_phrase(toks, phrase)
    assert len(matches) == 1
    # 'नाही' follows 'छातीत दुखत'
    assert is_negated(toks, matches[0], len(phrase)) is True


def test_devanagari_negation_broken_by_adversative_conjunction() -> None:
    """Adversative conjunctions (लेकिन, पण, परंतु) prevent cross-clause negation."""
    # "सीने में दर्द नहीं है लेकिन सांस फूल रही है"
    toks = tokens(normalize("सीने में दर्द नहीं है लेकिन सांस फूल रही है"))
    chest_phrase = ["सीने", "में", "दर्द"]
    breath_phrase = ["सांस", "फूल", "रही", "है"]

    m_chest = find_phrase(toks, chest_phrase)
    m_breath = find_phrase(toks, breath_phrase)

    assert len(m_chest) == 1
    assert len(m_breath) == 1

    # Chest pain is negated by "नहीं है"
    assert is_negated(toks, m_chest[0], len(chest_phrase)) is True
    # Breathlessness after "लेकिन" is NOT negated!
    assert is_negated(toks, m_breath[0], len(breath_phrase)) is False


def test_marathi_negation_broken_by_adversative_pan() -> None:
    """Marathi adversative 'पण' prevents negation bleed."""
    toks = tokens(normalize("छातीत दुखत नाही पण चक्कर येत आहे"))
    chest_phrase = ["छातीत", "दुखत"]
    dizzy_phrase = ["चक्कर", "येत", "आहे"]

    m_chest = find_phrase(toks, chest_phrase)
    m_dizzy = find_phrase(toks, dizzy_phrase)

    assert is_negated(toks, m_chest[0], len(chest_phrase)) is True
    assert is_negated(toks, m_dizzy[0], len(dizzy_phrase)) is False


def test_roman_script_succeeding_negation() -> None:
    """Roman Hindi/Marathi succeeding negation
    ('seene mein dard nahi hai', 'chhatit dukhava nahi') is detected.
    """
    toks = tokens(normalize("seene mein dard nahi hai, halki khansi hai"))
    chest_phrase = ["seene", "mein", "dard"]
    cough_phrase = ["halki", "khansi"]

    m_chest = find_phrase(toks, chest_phrase)
    m_cough = find_phrase(toks, cough_phrase)

    assert is_negated(toks, m_chest[0], len(chest_phrase)) is True
    assert is_negated(toks, m_cough[0], len(cough_phrase)) is False
