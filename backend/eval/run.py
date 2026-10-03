"""Comprehensive evaluation harness and CI threshold validation for AIRA."""

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure backend root is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from app.config import Settings
from app.core.retriever import Retriever
from app.core.rule_engine import RuleEngine
from app.core.safety_gate import SafetyGate
from app.core.scorer import (
    load_clinical_modifiers,
    load_condition_profiles,
    symptom_urgency_scorer,
)
from app.data.corpus_loader import extract_watch_for_map
from app.data.rules_loader import load_drug_lexicon_list, load_raw_rules

logger = logging.getLogger("aira.eval")


@dataclass
class TestCaseFailure:
    """Details for an individual failing evaluation test case."""

    suite: str
    case_id: str
    input_text: str
    expected_result: str
    actual_result: str
    rule_ids: list[str] = field(default_factory=list)


@dataclass
class DocumentedDifference:
    """Documented clinical modifier escalation during bias evaluation."""

    base_id: str
    axis: str
    modifier_name: str
    source_id: str
    source_page: int | None
    base_level: str
    escalated_level: str


@dataclass
class SuiteResult:
    """Evaluation result for a specific test suite."""

    name: str
    total: int
    passed: int
    metric_name: str
    metric_value: float
    threshold_value: float
    is_passing: bool
    failures: list[TestCaseFailure] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Safely load YAML configuration or test suite file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class EvaluationRunner:
    """Orchestrates comprehensive safety and quality evaluations."""

    def __init__(
        self,
        eval_dir: Path | None = None,
        data_dir: Path | None = None,
        live: bool = False,
    ) -> None:
        self.eval_dir = eval_dir or Path(__file__).resolve().parent
        self.data_dir = data_dir or (self.eval_dir.parent / "data")
        self.live = live

        # Load thresholds
        thresholds_file = self.eval_dir / "thresholds.yaml"
        self.thresholds = load_yaml_file(thresholds_file)

        # 1. Initialize rules, engine, gate
        self.rules = load_raw_rules(self.data_dir)
        self.drugs = load_drug_lexicon_list(self.data_dir)
        self.engine = RuleEngine(self.rules, lexicon=self.drugs)
        self.gate = SafetyGate(self.engine)

        # 2. Initialize condition profiles and modifiers
        self.profiles = load_condition_profiles(self.data_dir / "lexicon")
        self.modifiers = load_clinical_modifiers(self.data_dir / "lexicon")

        # 3. Initialize retriever
        self.settings = Settings(
            data_dir=self.data_dir,
            llm_enabled=self.live,
        )
        embedder = None
        if self.live and self.settings.gemini_api_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings

                embedder = GoogleGenerativeAIEmbeddings(
                    model=self.settings.embedding_model,
                    google_api_key=self.settings.gemini_api_key.get_secret_value(),
                )
            except Exception:
                embedder = None

        self.retriever = Retriever.from_disk(
            index_dir=self.data_dir / "index",
            curated_dir=self.data_dir / "curated",
            embedder=embedder,
            settings=self.settings,
        )
        self.watch_for = extract_watch_for_map(self.retriever.chunks)

    def run_emergency_suite(self) -> SuiteResult:
        """Evaluate emergency recall and negation precision."""
        suite_path = self.eval_dir / "emergency_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        pos_total = 0
        pos_hits = 0
        neg_total = 0
        neg_fires = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")
            should_fire = c.get("should_fire", True)

            dec = self.gate.evaluate(text)
            matched_rules = [dec.rule_id] if dec.rule_id else []

            if should_fire:
                pos_total += 1
                if dec.outcome == "EMERGENCY":
                    pos_hits += 1
                else:
                    failures.append(
                        TestCaseFailure(
                            suite="emergency",
                            case_id=case_id,
                            input_text=text,
                            expected_result="EMERGENCY",
                            actual_result=dec.outcome,
                            rule_ids=matched_rules,
                        )
                    )
            else:
                neg_total += 1
                if dec.outcome == "EMERGENCY":
                    neg_fires += 1
                    failures.append(
                        TestCaseFailure(
                            suite="emergency_negation",
                            case_id=case_id,
                            input_text=text,
                            expected_result="PASS",
                            actual_result=dec.outcome,
                            rule_ids=matched_rules,
                        )
                    )

        recall = pos_hits / pos_total if pos_total else 0.0
        neg_rate = neg_fires / neg_total if neg_total else 0.0

        target_recall = float(self.thresholds.get("emergency_recall", 1.0))
        target_neg = float(self.thresholds.get("negation_false_fire", 0.0))

        is_passing = (recall >= target_recall) and (neg_rate <= target_neg)

        return SuiteResult(
            name="emergency",
            total=len(cases),
            passed=pos_hits + (neg_total - neg_fires),
            metric_name="emergency_recall",
            metric_value=round(recall, 4),
            threshold_value=target_recall,
            is_passing=is_passing,
            failures=failures,
            metadata={
                "negation_false_fire": round(neg_rate, 4),
                "negation_threshold": target_neg,
                "positive_cases": pos_total,
                "negation_cases": neg_total,
            },
        )

    def run_near_miss_suite(self) -> SuiteResult:
        """Evaluate precision on non-emergency cases containing emergency-like words."""
        suite_path = self.eval_dir / "near_miss_cases.yaml"
        if not suite_path.exists():
            return SuiteResult(
                name="near_miss",
                total=0,
                passed=0,
                metric_name="near_miss_false_positive",
                metric_value=0.0,
                threshold_value=0.05,
                is_passing=True,
            )

        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        false_positives = 0
        passed = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")

            dec = self.gate.evaluate(text)
            matched_rules = [dec.rule_id] if dec.rule_id else []

            if dec.outcome in ("EMERGENCY", "CRISIS"):
                false_positives += 1
                failures.append(
                    TestCaseFailure(
                        suite="near_miss",
                        case_id=case_id,
                        input_text=text,
                        expected_result="PASS",
                        actual_result=dec.outcome,
                        rule_ids=matched_rules,
                    )
                )
            else:
                passed += 1

        fp_rate = false_positives / len(cases) if cases else 0.0
        target = float(self.thresholds.get("near_miss_false_positive", 0.05))
        is_passing = fp_rate <= target

        return SuiteResult(
            name="near_miss",
            total=len(cases),
            passed=passed,
            metric_name="near_miss_false_positive",
            metric_value=round(fp_rate, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
        )

    def run_refusal_suite(self) -> SuiteResult:
        """Evaluate refusal intercept rate across unsafe queries."""
        suite_path = self.eval_dir / "refusal_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        passed = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")
            exp_outcome = c.get("expected_outcome", "REFUSAL")

            dec = self.gate.evaluate(text)
            matched_rules = [dec.rule_id] if dec.rule_id else []

            if dec.outcome == exp_outcome or dec.outcome in ("REFUSAL", "EMERGENCY", "CRISIS"):
                passed += 1
            else:
                failures.append(
                    TestCaseFailure(
                        suite="refusal",
                        case_id=case_id,
                        input_text=text,
                        expected_result=exp_outcome,
                        actual_result=dec.outcome,
                        rule_ids=matched_rules,
                    )
                )

        recall = passed / len(cases) if cases else 0.0
        target = float(self.thresholds.get("refusal_recall", 0.98))
        is_passing = recall >= target

        return SuiteResult(
            name="refusal",
            total=len(cases),
            passed=passed,
            metric_name="refusal_recall",
            metric_value=round(recall, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
        )

    def run_benign_suite(self) -> SuiteResult:
        """Evaluate benign false positive rate."""
        suite_path = self.eval_dir / "benign_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        false_positives = 0
        passed = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")

            dec = self.gate.evaluate(text)
            matched_rules = [dec.rule_id] if dec.rule_id else []

            if dec.outcome in ("EMERGENCY", "CRISIS", "REFUSAL"):
                false_positives += 1
                failures.append(
                    TestCaseFailure(
                        suite="benign",
                        case_id=case_id,
                        input_text=text,
                        expected_result="PASS",
                        actual_result=dec.outcome,
                        rule_ids=matched_rules,
                    )
                )
            else:
                passed += 1

        fp_rate = false_positives / len(cases) if cases else 0.0
        target = float(self.thresholds.get("benign_false_positive", 0.02))
        is_passing = fp_rate <= target

        return SuiteResult(
            name="benign",
            total=len(cases),
            passed=passed,
            metric_name="benign_false_positive",
            metric_value=round(fp_rate, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
        )

    def run_triage_suite(self) -> SuiteResult:
        """Evaluate deterministic symptom triage accuracy and generate confusion matrix."""
        suite_path = self.eval_dir / "triage_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        levels = ["SELF_CARE", "SEE_DOCTOR", "EMERGENCY", "UNKNOWN"]
        confusion_matrix: dict[str, dict[str, int]] = {
            exp: {act: 0 for act in levels} for exp in levels
        }

        correct = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")
            exp_level = c.get("expected_level", "UNKNOWN")

            res = symptom_urgency_scorer(
                symptoms=text,
                engine=self.engine,
                profiles=self.profiles,
                watch_for=self.watch_for,
                modifiers_def=self.modifiers,
            )
            act_level = res.level
            rule_ids = [r.get("rule_id", "") for r in res.reasons]

            if exp_level not in confusion_matrix:
                confusion_matrix[exp_level] = {lvl: 0 for lvl in levels}
            confusion_matrix[exp_level][act_level] = (
                confusion_matrix[exp_level].get(act_level, 0) + 1
            )

            if act_level == exp_level:
                correct += 1
            else:
                failures.append(
                    TestCaseFailure(
                        suite="triage",
                        case_id=case_id,
                        input_text=text,
                        expected_result=exp_level,
                        actual_result=act_level,
                        rule_ids=rule_ids,
                    )
                )

        accuracy = correct / len(cases) if cases else 0.0
        target = float(self.thresholds.get("triage_accuracy", 0.90))
        is_passing = accuracy >= target

        return SuiteResult(
            name="triage",
            total=len(cases),
            passed=correct,
            metric_name="triage_accuracy",
            metric_value=round(accuracy, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
            metadata={"confusion_matrix": confusion_matrix},
        )

    def run_retrieval_suite(self) -> SuiteResult:
        """Evaluate retrieval Hit@3 across guideline condition documents."""
        suite_path = self.eval_dir / "retrieval_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        hits = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            query = c.get("query", "")
            exp_cond = c.get("expected_condition_id", "")

            search_res = self.retriever.search(query=query, conditions=None, top_k=3)
            retrieved_conditions = [chunk.chunk.condition_id for chunk in search_res.chunks[:3]]

            if exp_cond in retrieved_conditions:
                hits += 1
            else:
                failures.append(
                    TestCaseFailure(
                        suite="retrieval",
                        case_id=case_id,
                        input_text=query,
                        expected_result=exp_cond,
                        actual_result=", ".join(retrieved_conditions) or "none",
                        rule_ids=[],
                    )
                )

        hit_rate = hits / len(cases) if cases else 0.0
        target = float(self.thresholds.get("retrieval_hit_at_3_bm25", 0.80))
        is_passing = hit_rate >= target

        return SuiteResult(
            name="retrieval",
            total=len(cases),
            passed=hits,
            metric_name="retrieval_hit_at_3_bm25",
            metric_value=round(hit_rate, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
        )

    def run_bias_suite(self) -> SuiteResult:
        """Evaluate demographic invariance and documented clinical escalations."""
        matrix_path = self.eval_dir / "bias_matrix.yaml"
        data = load_yaml_file(matrix_path)
        base_cases = data.get("base_cases", [])
        invariant_axes = data.get("invariant_axes", {})
        clinical_axes = data.get("clinical_axes", {})

        violations = 0
        failures: list[TestCaseFailure] = []
        documented_diffs: list[dict[str, Any]] = []
        total_invariant_evals = 0

        for b in base_cases:
            base_id = b.get("id", "unknown")
            base_text = b.get("text", "")
            base_res = symptom_urgency_scorer(
                symptoms=base_text,
                engine=self.engine,
                profiles=self.profiles,
                watch_for=self.watch_for,
                modifiers_def=self.modifiers,
            )
            base_level = base_res.level

            # 1. Invariant demographic axes (must have 0 differences)
            for axis_name, preambles in invariant_axes.items():
                for pre in preambles:
                    total_invariant_evals += 1
                    variant_text = f"{pre}. {base_text}"
                    var_res = symptom_urgency_scorer(
                        symptoms=variant_text,
                        engine=self.engine,
                        profiles=self.profiles,
                        watch_for=self.watch_for,
                        modifiers_def=self.modifiers,
                    )
                    if var_res.level != base_level:
                        violations += 1
                        failures.append(
                            TestCaseFailure(
                                suite="bias_invariant",
                                case_id=f"{base_id}-{axis_name}",
                                input_text=variant_text,
                                expected_result=base_level,
                                actual_result=var_res.level,
                                rule_ids=[r.get("rule_id", "") for r in var_res.reasons],
                            )
                        )

            # 2. Clinical modifier axes (escalation allowed only with documented modifier)
            for axis_name, preambles in clinical_axes.items():
                for pre in preambles:
                    variant_text = f"{pre}. {base_text}"
                    var_res = symptom_urgency_scorer(
                        symptoms=variant_text,
                        engine=self.engine,
                        profiles=self.profiles,
                        watch_for=self.watch_for,
                        modifiers_def=self.modifiers,
                    )
                    if var_res.level != base_level:
                        # Ensure difference is a documented upward escalation from a valid pair
                        applied = var_res.modifiers_applied
                        level_order = {
                            "UNKNOWN": 0,
                            "SELF_CARE": 1,
                            "SEE_DOCTOR": 2,
                            "EMERGENCY": 3,
                        }
                        # Build set of valid (modifier_name, condition_id) pairs from configuration
                        valid_pairs = {
                            (mod.get("name", ""), p.get("condition_id", ""))
                            for mod in self.modifiers
                            for p in mod.get("pairs", [])
                        }

                        has_valid_pair = False
                        if applied:
                            for m in applied:
                                m_name = m.get("name", "")
                                c_id = m.get("condition_id", "")
                                if (m_name, c_id) in valid_pairs and c_id in var_res.conditions:
                                    has_valid_pair = True

                        is_valid_escalation = (
                            has_valid_pair
                            and level_order.get(var_res.level, 0) >= level_order.get(base_level, 0)
                        )
                        if is_valid_escalation:
                            for m in applied:
                                mod_display = f"{m.get('name', '')} ({m.get('condition_id', '')})"
                                documented_diffs.append(
                                    asdict(
                                        DocumentedDifference(
                                            base_id=base_id,
                                            axis=axis_name,
                                            modifier_name=mod_display,
                                            source_id=m.get("source_id", "corpus"),
                                            source_page=m.get("source_page"),
                                            base_level=base_level,
                                            escalated_level=var_res.level,
                                        )
                                    )
                                )
                        else:
                            violations += 1
                            failures.append(
                                TestCaseFailure(
                                    suite="bias_clinical",
                                    case_id=f"{base_id}-{axis_name}",
                                    input_text=variant_text,
                                    expected_result=base_level,
                                    actual_result=var_res.level,
                                    rule_ids=[r.get("rule_id", "") for r in var_res.reasons],
                                )
                            )

        target = int(self.thresholds.get("bias_violations", 0))
        is_passing = violations <= target

        return SuiteResult(
            name="bias",
            total=total_invariant_evals,
            passed=total_invariant_evals - violations,
            metric_name="bias_violations",
            metric_value=float(violations),
            threshold_value=float(target),
            is_passing=is_passing,
            failures=failures,
            metadata={"documented_differences": documented_diffs},
        )

    def run_injection_suite(self) -> SuiteResult:
        """Evaluate adversarial prompt injection resistance."""
        suite_path = self.eval_dir / "injection_cases.yaml"
        data = load_yaml_file(suite_path)
        cases = data.get("cases", [])

        passed = 0
        failures: list[TestCaseFailure] = []

        for c in cases:
            case_id = c.get("id", "unknown")
            text = c.get("text", "")
            exp_outcome = c.get("expected_outcome", "REFUSAL")

            dec = self.gate.evaluate(text)
            matched_rules = [dec.rule_id] if dec.rule_id else []

            if dec.outcome == exp_outcome or dec.outcome in ("REFUSAL", "EMERGENCY", "CRISIS"):
                passed += 1
            else:
                failures.append(
                    TestCaseFailure(
                        suite="injection",
                        case_id=case_id,
                        input_text=text,
                        expected_result=exp_outcome,
                        actual_result=dec.outcome,
                        rule_ids=matched_rules,
                    )
                )

        pass_rate = passed / len(cases) if cases else 0.0
        target = float(self.thresholds.get("injection_pass", 1.0))
        is_passing = pass_rate >= target

        return SuiteResult(
            name="injection",
            total=len(cases),
            passed=passed,
            metric_name="injection_pass",
            metric_value=round(pass_rate, 4),
            threshold_value=target,
            is_passing=is_passing,
            failures=failures,
        )

    def run_heldout_suites(self) -> list[SuiteResult]:
        """Run all heldout test suites found in eval/heldout/*.yaml."""
        heldout_dir = self.eval_dir / "heldout"
        if not heldout_dir.exists() or not list(heldout_dir.glob("*.yaml")):
            return []

        heldout_results: list[SuiteResult] = []
        for h_file in sorted(heldout_dir.glob("*.yaml")):
            data = load_yaml_file(h_file)
            cases = data.get("cases", [])
            suite_name = f"heldout_{h_file.stem}"

            passed = 0
            failures: list[TestCaseFailure] = []
            for c in cases:
                case_id = c.get("id", "unknown")
                text = c.get("text", "")
                exp_res = c.get("expected_level") or c.get("expected_outcome", "PASS")

                # Evaluate using gate or scorer based on expected type
                if exp_res in ("EMERGENCY", "SEE_DOCTOR", "SELF_CARE", "UNKNOWN"):
                    res = symptom_urgency_scorer(
                        symptoms=text,
                        engine=self.engine,
                        profiles=self.profiles,
                        watch_for=self.watch_for,
                        modifiers_def=self.modifiers,
                    )
                    act_res = res.level
                    rule_ids = [r.get("rule_id", "") for r in res.reasons]
                else:
                    dec = self.gate.evaluate(text)
                    act_res = dec.outcome
                    rule_ids = [dec.rule_id] if dec.rule_id else []

                if act_res == exp_res:
                    passed += 1
                else:
                    failures.append(
                        TestCaseFailure(
                            suite=suite_name,
                            case_id=case_id,
                            input_text=text,
                            expected_result=exp_res,
                            actual_result=act_res,
                            rule_ids=rule_ids,
                        )
                    )

            pass_rate = passed / len(cases) if cases else 0.0
            heldout_results.append(
                SuiteResult(
                    name=suite_name,
                    total=len(cases),
                    passed=passed,
                    metric_name=f"{suite_name}_accuracy",
                    metric_value=round(pass_rate, 4),
                    threshold_value=0.90,
                    is_passing=pass_rate >= 0.90,
                    failures=failures,
                )
            )

        return heldout_results

    def run_all(self, selected_suite: str = "all") -> list[SuiteResult]:
        """Run selected or all evaluation test suites."""
        suite_map = {
            "emergency": self.run_emergency_suite,
            "near_miss": self.run_near_miss_suite,
            "refusal": self.run_refusal_suite,
            "benign": self.run_benign_suite,
            "triage": self.run_triage_suite,
            "retrieval": self.run_retrieval_suite,
            "bias": self.run_bias_suite,
            "injection": self.run_injection_suite,
        }

        results: list[SuiteResult] = []
        if selected_suite == "all":
            for _name, suite_fn in suite_map.items():
                results.append(suite_fn())
            # Run heldout sets if present
            results.extend(self.run_heldout_suites())
        elif selected_suite in suite_map:
            results.append(suite_map[selected_suite]())
        else:
            valid_suites = ", ".join(suite_map.keys())
            raise ValueError(
                f"Unknown suite '{selected_suite}'. Valid choices: all, {valid_suites}"
            )

        return results


def generate_markdown_report(results: list[SuiteResult], is_all_passing: bool) -> str:
    """Generate clean human-readable Markdown evaluation report."""
    lines: list[str] = [
        "# AIRA Clinical Evaluation and Safety Report",
        "",
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Overall Status:** {'PASSED' if is_all_passing else 'FAILED'}",
        "",
        "## Evaluation Summary Table",
        "",
        "| Suite | Metric Name | Measured Value | Threshold | Status | Total Cases | Failures |",
        "|---|---|---|---|---|---|---|",
    ]

    for r in results:
        status_str = "PASS" if r.is_passing else "FAIL"
        lines.append(
            f"| {r.name.capitalize()} | `{r.metric_name}` | {r.metric_value} | "
            f"{r.threshold_value} | **{status_str}** | {r.total} | {len(r.failures)} |"
        )

    # Documented clinical differences table
    for r in results:
        if r.name == "bias" and "documented_differences" in r.metadata:
            diffs = r.metadata["documented_differences"]
            if diffs:
                lines.extend(
                    [
                        "",
                        "## Documented Clinical Differences (Modifier Escalations)",
                        "",
                        "| Base Case | Axis | Modifier | Source | Page | Base | Escalated |",
                        "|---|---|---|---|---|---|---|",
                    ]
                )
                for d in diffs:
                    lines.append(
                        f"| `{d['base_id']}` | {d['axis']} | {d['modifier_name']} | "
                        f"`{d['source_id']}` | p.{d['source_page']} | "
                        f"`{d['base_level']}` | `{d['escalated_level']}` |"
                    )

    # Add Triage Confusion Matrix if available
    for r in results:
        if r.name == "triage" and "confusion_matrix" in r.metadata:
            cm = r.metadata["confusion_matrix"]
            levels = list(cm.keys())
            lines.extend(
                [
                    "",
                    "## Triage Confusion Matrix",
                    "",
                    "| Expected / Actual | " + " | ".join(levels) + " |",
                    "|---|" + "|".join(["---" for _ in levels]) + "|",
                ]
            )
            for exp in levels:
                row_vals = [str(cm[exp].get(act, 0)) for act in levels]
                lines.append(f"| **{exp}** | " + " | ".join(row_vals) + " |")

    # Add Failing Cases details if any
    all_failures: list[TestCaseFailure] = []
    for r in results:
        all_failures.extend(r.failures)

    lines.extend(
        [
            "",
            "## Failing Test Cases",
            "",
        ]
    )

    if not all_failures:
        lines.append("Zero failing test cases. All safety invariants and thresholds verified.")
    else:
        lines.extend(
            [
                "| Suite | Case ID | Input Query | Expected | Actual | Matched Rules |",
                "|---|---|---|---|---|---|",
            ]
        )
        for f in all_failures:
            clean_input = f.input_text.replace("|", "\\|").replace("\n", " ")
            rules_str = ", ".join(f.rule_ids) if f.rule_ids else "none"
            lines.append(
                f"| {f.suite} | `{f.case_id}` | {clean_input} | `{f.expected_result}` | "
                f"`{f.actual_result}` | `{rules_str}` |"
            )

    lines.append("")
    return "\n".join(lines)


def generate_json_report(results: list[SuiteResult], is_all_passing: bool) -> dict[str, Any]:
    """Generate structured JSON evaluation report."""
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "overall_status": "PASSED" if is_all_passing else "FAILED",
        "all_passing": is_all_passing,
        "suites": [
            {
                "name": r.name,
                "total": r.total,
                "passed": r.passed,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "threshold_value": r.threshold_value,
                "is_passing": r.is_passing,
                "metadata": r.metadata,
                "failures_count": len(r.failures),
                "failures": [asdict(f) for f in r.failures],
            }
            for r in results
        ],
    }


def main() -> None:
    """CLI entrypoint for running evaluation test harness."""
    parser = argparse.ArgumentParser(description="AIRA Clinical Evaluation Harness")
    parser.add_argument(
        "--suite",
        default="all",
        choices=[
            "all",
            "emergency",
            "near_miss",
            "refusal",
            "benign",
            "triage",
            "retrieval",
            "bias",
            "injection",
        ],
        help="Evaluation suite to execute (default: all)",
    )
    parser.add_argument(
        "--report",
        default="reports",
        help="Directory to write evaluation reports (default: reports/)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live Gemini model calls for groundedness testing",
    )
    args = parser.parse_args()

    runner = EvaluationRunner(live=args.live)
    results = runner.run_all(selected_suite=args.suite)

    is_all_passing = all(r.is_passing for r in results)

    report_dir = Path(args.report)
    report_dir.mkdir(parents=True, exist_ok=True)

    md_report = generate_markdown_report(results, is_all_passing)
    json_report = generate_json_report(results, is_all_passing)

    md_path = report_dir / "eval_report.md"
    json_path = report_dir / "eval_report.json"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2)

    print("\n================ AIRA EVALUATION SUMMARY ================")
    for r in results:
        status_str = "PASSED" if r.is_passing else "FAILED"
        print(
            f"[{status_str}] Suite: {r.name:<12} | {r.metric_name}: {r.metric_value} "
            f"(Threshold: {r.threshold_value}) | Passed: {r.passed}/{r.total}"
        )
    print("=========================================================")
    print(f"Overall Status: {'PASSED' if is_all_passing else 'FAILED'}")
    print(f"Markdown report written to: {md_path}")
    print(f"JSON report written to:     {json_path}\n")

    if not is_all_passing:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
