"""Guided clinical intake planning, validation, and answer parsing."""

from collections.abc import Mapping
from typing import Any

from app.core.scorer import ScoreResult, extract_duration_days


def get_all_questions_by_id(intake_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a mapping of question id to question data dictionary."""
    questions: dict[str, dict[str, Any]] = {}
    if "duration_question" in intake_data:
        questions[intake_data["duration_question"]["id"]] = intake_data["duration_question"]
    if "risk_question" in intake_data:
        questions[intake_data["risk_question"]["id"]] = intake_data["risk_question"]
    if "area_question" in intake_data:
        questions[intake_data["area_question"]["id"]] = intake_data["area_question"]
    if "general_signs_question" in intake_data:
        gq = intake_data["general_signs_question"]
        questions[gq["id"]] = gq
    for cond_q in intake_data.get("condition_questions", {}).values():
        questions[cond_q["id"]] = cond_q
    return questions


def validate_intake_payload(
    intake: dict[str, Any],
    intake_data: dict[str, Any],
) -> None:
    """Validate intake answers and extra text against clinical questions table.

    Raises ValueError on any invalid question ID, option ID, exclusivity violation,
    or length exceedance.
    """
    extra_text = intake.get("extra_text")
    if extra_text is not None:
        if not isinstance(extra_text, str):
            raise ValueError("Extra text must be a string.")
        if len(extra_text) > 300:
            raise ValueError("Extra text cannot exceed 300 characters.")

    answers = intake.get("answers", [])
    if not isinstance(answers, list):
        raise ValueError("Answers must be a list.")

    all_q_map = get_all_questions_by_id(intake_data)

    seen_questions: set[str] = set()
    for ans in answers:
        if not isinstance(ans, dict):
            raise ValueError("Each answer must be an object.")
        qid = ans.get("question_id")
        if not qid or not isinstance(qid, str):
            raise ValueError("Answer missing valid question_id.")
        if qid not in all_q_map:
            raise ValueError(f"Unknown question ID: {qid}")
        if qid in seen_questions:
            raise ValueError(f"Duplicate answer for question ID: {qid}")
        seen_questions.add(qid)

        q_def = all_q_map[qid]
        q_type = q_def.get("type", "multi_select")
        valid_options = {opt["id"]: opt for opt in q_def.get("options", [])}

        sel_ids = ans.get("selected_option_ids", [])
        if not isinstance(sel_ids, list):
            raise ValueError(f"Selected option IDs for {qid} must be a list.")

        for opt_id in sel_ids:
            if not isinstance(opt_id, str):
                raise ValueError(f"Invalid option ID type in question {qid}.")
            if opt_id not in valid_options:
                raise ValueError(f"Unknown option ID: {opt_id} for question {qid}")

        if q_type == "single_select" and len(sel_ids) > 1:
            raise ValueError(
                f"Question {qid} is single-select but received {len(sel_ids)} options."
            )

        # Check exclusive options (e.g. 'None of these')
        for opt_id in sel_ids:
            opt = valid_options[opt_id]
            if opt.get("exclusive", False) and len(sel_ids) > 1:
                raise ValueError(
                    f"Exclusive option '{opt.get('label')}' cannot be combined with other options."
                )


def parse_intake_answers(
    intake: dict[str, Any],
    intake_data: dict[str, Any],
) -> dict[str, Any]:
    """Extract clinical signals, phrases, and summaries from validated intake payload."""
    all_q_map = get_all_questions_by_id(intake_data)

    structured_duration: int | None = None
    structured_modifiers: list[str] = []
    forced_conditions: list[str] = []
    selected_option_ids: list[str] = []
    canonical_phrases: list[str] = []
    answers_summary: list[str] = []

    for ans in intake.get("answers", []):
        qid = ans.get("question_id")
        if not qid or qid not in all_q_map:
            continue
        q_def = all_q_map[qid]
        options_by_id = {opt["id"]: opt for opt in q_def.get("options", [])}

        for opt_id in ans.get("selected_option_ids", []):
            if opt_id not in options_by_id:
                continue
            selected_option_ids.append(opt_id)
            opt = options_by_id[opt_id]

            if opt.get("exclusive", False):
                # None of these: record summary if relevant, but no clinical escalation
                answers_summary.append(f"{q_def.get('text', '')}: {opt.get('label', '')}")
                continue

            label = opt.get("label", "")
            if "duration_days" in opt:
                structured_duration = opt["duration_days"]
                answers_summary.append(f"Duration: {label}")

            if "modifier" in opt:
                structured_modifiers.append(opt["modifier"])
                answers_summary.append(f"Condition factor: {label}")

            if "condition_ids" in opt:
                forced_conditions.extend(opt["condition_ids"])
                answers_summary.append(f"Main problem: {label}")

            if "canonical_phrase" in opt:
                canonical_phrases.append(opt["canonical_phrase"])
                answers_summary.append(f"Sign: {label}")

    extra_text = (intake.get("extra_text") or "").strip()
    return {
        "structured_duration": structured_duration,
        "structured_modifiers": structured_modifiers,
        "forced_conditions": forced_conditions,
        "selected_option_ids": selected_option_ids,
        "canonical_phrases": canonical_phrases,
        "answers_summary": answers_summary,
        "extra_text": extra_text if extra_text else None,
    }


def select_intake_questions(
    score: ScoreResult | None,
    raw_text: str,
    intake_data: dict[str, Any],
    allow_unverified: bool,
    verified_item_ids: set[str],
    profiles: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Deterministically select up to 3 intake questions based on clinical findings.

    Never chooses, creates, or rewords questions using an LLM.
    Selection is invariant to demographic identifiers (age, gender, occupation).
    """
    detected_conditions = score.conditions if score is not None else []

    if detected_conditions:
        # Case A: Scorer detected condition(s).
        # Pick the one with the highest floor level.
        def get_floor_rank(cid: str) -> int:
            prof = profiles.get(cid)
            floor = "SELF_CARE"
            if prof:
                floor = getattr(prof, "floor_level", None) or (
                    prof.get("floor_level", "SELF_CARE") if isinstance(prof, dict) else "SELF_CARE"
                )
            ranks = {"EMERGENCY": 3, "SEE_DOCTOR": 2, "SELF_CARE": 1, "UNKNOWN": 0}
            return ranks.get(floor, 1)

        best_cond = max(detected_conditions, key=get_floor_rank)
        cond_q = intake_data.get("condition_questions", {}).get(best_cond)

        usable_options = []
        if cond_q:
            for opt in cond_q.get("options", []):
                if opt.get("exclusive", False):
                    usable_options.append(opt)
                else:
                    item_id = opt.get("item_id")
                    if allow_unverified or (item_id and item_id in verified_item_ids):
                        usable_options.append(opt)

        non_exclusive = [o for o in usable_options if not o.get("exclusive", False)]
        if non_exclusive:
            q1 = {**cond_q, "options": usable_options}
        else:
            q1 = intake_data["general_signs_question"]

        questions = [q1]

        # Q2: Duration question, unless the message already states a duration parsed by the scorer
        parsed_duration = extract_duration_days(raw_text)
        if parsed_duration is None:
            questions.append(intake_data["duration_question"])

        # Q3: Risk question (always asked in Case A)
        questions.append(intake_data["risk_question"])

    else:
        # Case B: No condition detected (UNKNOWN)
        questions = [
            intake_data["area_question"],
            intake_data["general_signs_question"],
            intake_data["duration_question"],
        ]

    return questions[:3]


def strip_question_for_client(question: dict[str, Any]) -> dict[str, Any]:
    """Strip internal clinical metadata, retaining only id, type, text, and option id/label."""
    options = [
        {"id": opt["id"], "label": opt["label"]}
        for opt in question.get("options", [])
    ]
    return {
        "id": question["id"],
        "type": question.get("type", "multi_select"),
        "text": question["text"],
        "options": options,
    }
