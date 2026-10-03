import json
from pathlib import Path

import yaml


def test_rule_phrases_length_and_no_eval_copy() -> None:
    """Rules must be <=4 tokens or must not appear as 5+ token verbatim substrings of eval."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    eval_dir = Path(__file__).resolve().parent.parent / "eval"

    urgency_file = data_dir / "curated" / "urgency_rules.json"
    with open(urgency_file, encoding="utf-8") as f:
        rules_data = json.load(f)

    # Collect all eval case input texts
    eval_texts: list[str] = []
    for yaml_path in eval_dir.glob("*.yaml"):
        if yaml_path.name in ("thresholds.yaml", "bias_matrix.yaml"):
            continue
        with open(yaml_path, encoding="utf-8") as f:
            suite_data = yaml.safe_load(f) or {}
            for case in suite_data.get("cases", []):
                txt = case.get("text") or case.get("query")
                if txt:
                    eval_texts.append(txt.lower())

    # Check all rule phrases
    for rule in rules_data.get("rules", []):
        rule_id = rule.get("id", "unknown")
        match_block = rule.get("match", {})
        phrases = match_block.get("phrases", [])
        requires_all = match_block.get("requires_all", [])

        all_phrases = list(phrases)
        for group in requires_all:
            all_phrases.extend(group)

        for p in all_phrases:
            if not p or p.startswith("@"):
                continue
            toks = p.strip().split()
            # Rule phrases of 5 or more tokens must never appear as verbatim substrings
            if len(toks) >= 5:
                p_lower = p.lower()
                for eval_txt in eval_texts:
                    assert p_lower not in eval_txt, (
                        f"Rule {rule_id} phrase '{p}' (length {len(toks)} >= 5 tokens) "
                        f"appears as verbatim substring in eval text: '{eval_txt}'"
                    )
