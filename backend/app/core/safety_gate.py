"""Pre-model safety validation and emergency symptom interception gate.

Safety Invariant:
All emergency detection, crisis interception, and refusal guardrails run
deterministically in Python before any generative model call.
Informational queries that mention an emergency symptom (such as 'what are
the signs of a heart attack') still trigger emergency routing by design.
This is a documented conservative choice to guarantee user safety.
"""

import logging
import time
from dataclasses import dataclass
from typing import Literal

from app.core.helplines import (
    Helpline,
    get_crisis_helplines,
    get_emergency_helplines,
)
from app.core.rule_engine import RuleEngine
from app.core.text import normalize, tokens

GateOutcome = Literal["EMERGENCY", "CRISIS", "REFUSAL", "OUT_OF_SCOPE", "PASS"]

logger = logging.getLogger("aira.safety_gate")


@dataclass(frozen=True)
class GateDecision:
    """Evaluation result produced by the pre-model safety gate."""

    outcome: GateOutcome
    rule_id: str | None
    message: str | None
    helplines: list[Helpline]
    matched_phrase: str | None
    elapsed_ms: float


class SafetyGate:
    """Deterministic safety gate evaluating user queries before model execution."""

    def __init__(self, engine: RuleEngine) -> None:
        self.engine = engine

    def evaluate(self, text: str) -> GateDecision:
        """Evaluate input text through strict precedence tiers."""
        start_time = time.perf_counter()

        if not text or not text.strip():
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="PASS",
                rule_id=None,
                message=None,
                helplines=[],
                matched_phrase=None,
                elapsed_ms=elapsed,
            )

        norm_text = normalize(text)
        norm_tokens = tokens(norm_text)

        if not norm_tokens:
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="PASS",
                rule_id=None,
                message=None,
                helplines=[],
                matched_phrase=None,
                elapsed_ms=elapsed,
            )

        # 1. Tier 1: Emergency Rules
        emergency_hits = self.engine.match(norm_tokens, kinds=["emergency"])
        active_emergency = [h for h in emergency_hits if not h.skipped_by_negation]
        if active_emergency:
            hit = active_emergency[0]
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="EMERGENCY",
                rule_id=hit.rule_id,
                message=hit.response,
                helplines=get_emergency_helplines(),
                matched_phrase=hit.matched_phrase,
                elapsed_ms=elapsed,
            )

        # 2. Tier 2: Mental Health Crisis Rules
        crisis_hits = self.engine.match(norm_tokens, kinds=["crisis"])
        active_crisis = [h for h in crisis_hits if not h.skipped_by_negation]
        if active_crisis:
            hit = active_crisis[0]
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="CRISIS",
                rule_id=hit.rule_id,
                message=hit.response,
                helplines=get_crisis_helplines(),
                matched_phrase=hit.matched_phrase,
                elapsed_ms=elapsed,
            )

        # 3. Tier 3: Out-of-Scope and Prohibited Advice Refusals
        refusal_hits = self.engine.match(norm_tokens, kinds=["refusal"])
        active_refusal = [h for h in refusal_hits if not h.skipped_by_negation]
        if active_refusal:
            hit = active_refusal[0]
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="REFUSAL",
                rule_id=hit.rule_id,
                message=hit.response,
                helplines=[],
                matched_phrase=hit.matched_phrase,
                elapsed_ms=elapsed,
            )

        # 4. Tier 4: Pediatric Scope Rules
        scope_hits = self.engine.match(norm_tokens, kinds=["scope"])
        active_scope = [h for h in scope_hits if not h.skipped_by_negation]
        if active_scope:
            hit = active_scope[0]
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="OUT_OF_SCOPE",
                rule_id=hit.rule_id,
                message=hit.response,
                helplines=get_emergency_helplines(),
                matched_phrase=hit.matched_phrase,
                elapsed_ms=elapsed,
            )

        # 5. Default: Pass to Guideline Retrieval
        elapsed = (time.perf_counter() - start_time) * 1000
        return GateDecision(
            outcome="PASS",
            rule_id=None,
            message=None,
            helplines=[],
            matched_phrase=None,
            elapsed_ms=elapsed,
        )

    def evaluate_safe(self, text: str) -> GateDecision:
        """Fail-closed wrapper returning emergency guidance on any internal failure."""
        start_time = time.perf_counter()
        try:
            return self.evaluate(text)
        except Exception as exc:
            # Log exception class name only - never log user query text
            logger.error("Safety gate evaluation error: %s", exc.__class__.__name__)
            elapsed = (time.perf_counter() - start_time) * 1000
            return GateDecision(
                outcome="EMERGENCY",
                rule_id="FAILSAFE_ERROR",
                message=(
                    "We could not check this message safely. If this is an emergency, call 112."
                ),
                helplines=get_emergency_helplines(),
                matched_phrase=None,
                elapsed_ms=elapsed,
            )
