"""Deterministic rule evaluation engine for symptom triage and safety boundaries."""

from dataclasses import dataclass
from typing import Any

from app.core.text import extract_minutes, find_phrase, is_negated

# Preset placeholder expansions
DOSE_UNITS = (
    "mg",
    "mcg",
    "g",
    "iu",
    "ml",
    "drop",
    "drops",
    "puff",
    "puffs",
    "tablet",
    "tablets",
    "capsule",
    "capsules",
    "spoon",
    "teaspoon",
    "syrup",
)

CHILD_TERMS = (
    "baby",
    "infant",
    "newborn",
    "toddler",
    "child",
    "son",
    "daughter",
    "kid",
    "kids",
    "months old",
    "month old",
    "year old",
    "years old",
)


@dataclass(frozen=True)
class RuleHit:
    """Individual rule activation result."""

    rule_id: str
    kind: str
    condition: str
    matched_phrase: str
    negated: bool
    skipped_by_negation: bool
    response: str


def _get_clause_tokens(norm_tokens: list[str], match_pos: int) -> list[str]:
    """Extract tokens of the clause containing match_pos bounded by pipe '|' sentinels."""
    start = 0
    for i in range(match_pos - 1, -1, -1):
        if norm_tokens[i] == "|":
            start = i + 1
            break
    end = len(norm_tokens)
    for i in range(match_pos, len(norm_tokens)):
        if norm_tokens[i] == "|":
            end = i
            break
    return norm_tokens[start:end]


class CompiledRule:
    """In-memory representation of an individual compiled triage/safety rule."""

    def __init__(self, rule_data: dict[str, Any], lexicon: list[str] | None = None) -> None:
        self.id: str = rule_data.get("id", "")
        self.kind: str = rule_data.get("kind", "")
        self.condition: str = rule_data.get("condition", "")
        self.negatable: bool = rule_data.get("negatable", True)
        self.min_minutes: int | None = rule_data.get("min_minutes")
        self.response: str = rule_data.get("response", "")

        match_block = rule_data.get("match", {})
        raw_phrases = match_block.get("phrases", [])
        raw_requires_all = match_block.get("requires_all", [])

        # Fallback to v1 trigger_keywords if match block is absent
        if not raw_phrases and "trigger_keywords" in rule_data:
            raw_phrases = rule_data.get("trigger_keywords", [])

        self.phrase_tokens: list[list[str]] = [
            p.strip().lower().split() for p in raw_phrases if p.strip()
        ]

        # Expand requires_all groups with placeholders
        self.requires_all_groups: list[list[list[str]]] = []
        for group in raw_requires_all:
            expanded_group: list[list[str]] = []
            for item in group:
                item_clean = item.strip().lower()
                if item_clean == "@drugs" and lexicon:
                    for d in lexicon:
                        expanded_group.append(d.strip().lower().split())
                elif item_clean == "@dose_units":
                    for u in DOSE_UNITS:
                        expanded_group.append(u.split())
                elif item_clean == "@child_terms":
                    for c in CHILD_TERMS:
                        expanded_group.append(c.split())
                else:
                    toks = item_clean.split()
                    if toks:
                        expanded_group.append(toks)
            if expanded_group:
                self.requires_all_groups.append(expanded_group)


class RuleEngine:
    """In-memory deterministic matching engine for triage and safety rules."""

    def __init__(
        self,
        rules: list[dict[str, Any]],
        lexicon: list[str] | None = None,
    ) -> None:
        self.rules: list[CompiledRule] = [CompiledRule(r, lexicon) for r in rules]

    def match(
        self,
        norm_tokens: list[str],
        kinds: list[str] | None = None,
    ) -> list[RuleHit]:
        """Evaluate normalized tokens against compiled rules."""
        if not norm_tokens:
            return []

        allowed_kinds = set(kinds) if kinds is not None else None
        hits: list[RuleHit] = []

        for rule in self.rules:
            if allowed_kinds and rule.kind not in allowed_kinds:
                continue

            matched_hit: RuleHit | None = None

            # 1. Evaluate single phrase matches
            if rule.phrase_tokens:
                for phrase in rule.phrase_tokens:
                    matches = find_phrase(norm_tokens, phrase)
                    if matches:
                        # If min_minutes is specified, ensure at least one match meets duration
                        valid_matches = matches
                        if rule.min_minutes is not None:
                            valid_matches = []
                            for m in matches:
                                clause_toks = _get_clause_tokens(norm_tokens, m)
                                mins = extract_minutes(clause_toks)
                                if mins is None:
                                    mins = extract_minutes(norm_tokens)
                                if mins is not None and mins >= rule.min_minutes:
                                    valid_matches.append(m)

                        if not valid_matches:
                            continue

                        phrase_str = " ".join(phrase)
                        # Check if every valid occurrence is negated
                        all_negated = all(is_negated(norm_tokens, m) for m in valid_matches)
                        skipped = rule.negatable and all_negated
                        matched_hit = RuleHit(
                            rule_id=rule.id,
                            kind=rule.kind,
                            condition=rule.condition,
                            matched_phrase=phrase_str,
                            negated=all_negated,
                            skipped_by_negation=skipped,
                            response=rule.response,
                        )
                        break

            # 2. Evaluate multi-group requires_all matches if not already matched
            if matched_hit is None and rule.requires_all_groups:
                matched_phrases: list[str] = []
                group_matches_found = True
                any_negated = False
                all_match_positions: list[int] = []

                for group in rule.requires_all_groups:
                    group_hit = False
                    for phrase in group:
                        matches = find_phrase(norm_tokens, phrase)
                        if matches:
                            group_hit = True
                            matched_phrases.append(" ".join(phrase))
                            all_match_positions.extend(matches)
                            if any(is_negated(norm_tokens, m) for m in matches):
                                any_negated = True
                            break
                    if not group_hit:
                        group_matches_found = False
                        break

                if group_matches_found and matched_phrases:
                    combined_matched_phrase = " + ".join(matched_phrases)
                    skipped = rule.negatable and any_negated
                    matched_hit = RuleHit(
                        rule_id=rule.id,
                        kind=rule.kind,
                        condition=rule.condition,
                        matched_phrase=combined_matched_phrase,
                        negated=any_negated,
                        skipped_by_negation=skipped,
                        response=rule.response,
                    )

            if matched_hit is not None:
                hits.append(matched_hit)

        return hits
