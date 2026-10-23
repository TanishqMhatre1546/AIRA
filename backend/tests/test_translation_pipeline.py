"""Tests for offline translation pipeline, validation rules, and safety gates."""

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.core.validators import build_extractive_fallback
from app.data.models import GuidelineChunk
from app.data.translations import TranslationItem, TranslationRegistry, compute_source_hash
from scripts.translate_corpus import (
    check_dosing_and_diagnosis,
    check_number_and_unit_preservation,
    check_script_and_length,
)


class TestValidationRules:
    """Tests for automated safety checks on translated clinical guidelines."""

    def test_number_preservation_success(self) -> None:
        src = "Sit upright and pinch nose for 10 minutes, repeating for 20 minutes if needed."
        trans = "सीधे बैठें और 10 मिनट तक नाक दबाएं, आवश्यकता होने पर 20 मिनट तक दोहराएं।"
        flags = check_number_and_unit_preservation(src, trans)
        assert len(flags) == 0

    def test_number_preservation_with_devanagari_digits(self) -> None:
        src = "Wash for 3 days and wait 24 hours."
        trans = "३ दिनों तक धोएं और २४ घंटे प्रतीक्षा करें।"
        flags = check_number_and_unit_preservation(src, trans)
        assert len(flags) == 0

    def test_missing_number_flagged(self) -> None:
        src = "Sit upright and pinch nose for 10 minutes without releasing."
        trans = "सीधे बैठें और बिना छोड़े नाक दबाएं।"
        flags = check_number_and_unit_preservation(src, trans)
        assert any("missing_number:10" in f for f in flags)

    def test_altered_number_flagged(self) -> None:
        src = "Wait for 10 minutes."
        trans = "15 मिनट तक प्रतीक्षा करें।"
        flags = check_number_and_unit_preservation(src, trans)
        assert any("missing_number:10" in f for f in flags)

    def test_critical_acronym_112_preservation(self) -> None:
        src = "In an emergency call 112 immediately."
        trans_missing = "आपात स्थिति में तुरंत फोन करें।"
        flags = check_number_and_unit_preservation(src, trans_missing)
        assert "missing_emergency_number_112" in flags

        trans_ok = "आपात स्थिति में तुरंत 112 पर कॉल करें।"
        flags_ok = check_number_and_unit_preservation(src, trans_ok)
        assert len(flags_ok) == 0

    def test_script_ratio_check(self) -> None:
        src = "Rest in a quiet room and avoid stress."
        all_english = "Rest in a quiet room and avoid stress."
        flags = check_script_and_length(src, all_english)
        assert any("low_devanagari_ratio" in f for f in flags)

    def test_dosing_pattern_rejection(self) -> None:
        src = "Drink fluids and rest."
        trans_with_dose = "तरल पदार्थ पिएं और 500 मिलीग्राम दवा लें।"
        flags = check_dosing_and_diagnosis(src, trans_with_dose, "hi")
        assert "forbidden_dose_pattern" in flags

    def test_diagnosis_statement_rejection(self) -> None:
        src = "High blood sugar and excessive thirst."
        trans_diagnosis = "यदि आपको डायबिटीज है तो पानी पिएं।"
        flags = check_dosing_and_diagnosis(src, trans_diagnosis, "hi")
        assert "prohibited_diagnosis_statement" in flags

        trans_safe = "अधिक प्यास और हाई ब्लड शुगर डायबिटीज का संकेत हो सकता है।"
        flags_safe = check_dosing_and_diagnosis(src, trans_safe, "hi")
        assert "prohibited_diagnosis_statement" not in flags_safe


class TestProductionSettingsSafety:
    """Test safety rules preventing draft translations in production."""

    def test_allow_unreviewed_disallowed_in_production(self) -> None:
        with pytest.raises(
            ValidationError, match="allow_unreviewed_translations must be False in production"
        ):
            Settings(environment="production", allow_unreviewed_translations=True)

    def test_allow_unreviewed_allowed_in_development(self) -> None:
        cfg = Settings(environment="development", allow_unreviewed_translations=True)
        assert cfg.allow_unreviewed_translations is True


class TestTranslationRegistryAndFallback:
    """Test registry lookup, review status enforcement, and extractive fallback."""

    def test_source_hash_invalidation(self) -> None:
        original = "Drink plenty of water"
        h = compute_source_hash(original)

        reg = TranslationRegistry()
        reg._loaded = True
        reg._cache[("test_cond", "hi")] = {
            "item_1": TranslationItem(
                item_id="item_1",
                text="भरपूर पानी पिएं",
                status="reviewed",
                source_hash=h,
            )
        }

        # Same text -> returns reviewed translation
        trans, status = reg.get_translation(
            "test_cond", "hi", "item_1", current_source_text=original
        )
        assert trans == "भरपूर पानी पिएं"
        assert status == "reviewed"

        # Changed English text -> status resets to draft, rejected in production
        changed = "Drink plenty of warm water"
        trans_changed, status_changed = reg.get_translation(
            "test_cond", "hi", "item_1", allow_unreviewed=False, current_source_text=changed
        )
        assert trans_changed is None
        assert status_changed is None

    def test_draft_translation_hidden_when_unreviewed_not_allowed(self) -> None:
        reg = TranslationRegistry()
        reg._loaded = True
        reg._cache[("test_cond", "hi")] = {
            "item_draft": TranslationItem(
                item_id="item_draft",
                text="प्रारूप अनुवाद",
                status="draft",
            )
        }

        # In production (allow_unreviewed=False), draft is NOT returned
        trans, status = reg.get_translation(
            "test_cond", "hi", "item_draft", allow_unreviewed=False
        )
        assert trans is None
        assert status is None

        # In dev (allow_unreviewed=True), draft IS returned with status='draft'
        trans_dev, status_dev = reg.get_translation(
            "test_cond", "hi", "item_draft", allow_unreviewed=True
        )
        assert trans_dev == "प्रारूप अनुवाद"
        assert status_dev == "draft"

    def test_extractive_fallback_translates_for_indic_languages(self) -> None:
        chunk = GuidelineChunk(
            chunk_id="chunk_1",
            condition_id="icmr-stw-dermatophytosis",
            condition="Dermatophytosis",
            section_type="self_care",
            label="Self-Care at Home",
            text="Take a daily bath with regular soap and normal temperature water.",
            item_ids=["3b2b161b3fb9"],
            source_title="STW for Dermatophytoses",
            source_publisher="DHR ICMR",
            source_year="2022",
            source_url="https://stw.icmr.org.in",
            page=1,
        )

        # In Hindi, should translate to reviewed Hindi text
        answer = build_extractive_fallback(
            chunks=[chunk],
            triage_level="SELF_CARE",
            lang="hi",
            allow_unreviewed=False,
        )

        claims = answer.guidelines_say + answer.do_now
        assert len(claims) > 0
        assert answer.content_language == "hi"
        assert answer.translation_status == "reviewed"
        # Hindi text should be Devanagari
        assert any("स्नान करें" in c.text or "साबुन" in c.text for c in claims)
        # Citations must retain English metadata
        assert len(answer.citations) == 1
        assert answer.citations[0].title == "STW for Dermatophytoses"
        assert answer.citations[0].publisher == "DHR ICMR"

    def test_extractive_fallback_defaults_to_english_when_untranslated(self) -> None:
        chunk = GuidelineChunk(
            chunk_id="chunk_unknown",
            condition_id="unknown_condition",
            condition="Unknown",
            section_type="self_care",
            label="Self Care",
            text="Completely unknown English text not present in i18n sidecars.",
            item_ids=["unknown_item_id"],
            source_title="Unknown Guide",
            source_publisher="ICMR",
            source_year="2024",
            source_url="https://example.com",
            page=1,
        )

        answer = build_extractive_fallback(
            chunks=[chunk],
            triage_level="SELF_CARE",
            lang="mr",
            allow_unreviewed=False,
        )

        claims = answer.guidelines_say + answer.do_now
        assert len(claims) == 1
        assert claims[0].text == "Completely unknown English text not present in i18n sidecars."
        assert answer.content_language == "en"
        assert answer.translation_status == "none"

