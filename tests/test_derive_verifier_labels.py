"""
Unit tests for StepGuard verifier label derivation engine.
"""

from collections import Counter
import json
from pathlib import Path
import pytest

from partner_a.evidence.derive_verifier_labels import (
    DEFAULT_EVAL_EVIDENCE,
    DEFAULT_PILOT_EVIDENCE,
    DEFAULT_OUTPUT_DIR,
    deduplicate_canonical_steps,
    derive_step_label,
    extract_exception_type,
    partition_train_eval,
    validate_and_load_evidence,
    CanonicalStepLabel,
)


ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Outcome flip & Decision Logic Tests
# ---------------------------------------------------------------------------

def test_outcome_flip_pass_to_fail():
    records = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "step_id": "block_01",
            "mutation_type": "multiplication_swap",
            "original_code": "def f(a, b): return a * b",
            "mutated_code": "def f(a, b): return a / b",
            "mutation_result": "FAIL",
            "stderr": "AssertionError",
            "line": 1,
            "column": 23,
        }
    ]
    step = derive_step_label(
        problem_id="eval_001",
        solution_id="eval_001_sol_001",
        step_id="block_01",
        step_type="block",
        dataset_source="evaluation",
        records=records,
    )

    assert step.outcome_flip is True
    assert step.label == "correct"
    assert step.num_fail == 1
    assert step.num_pass == 0


def test_outcome_flip_pass_to_pass_survival():
    records = [
        {
            "problem_id": "mbpp_003",
            "solution_id": "mbpp_003_sol_001",
            "step_id": "block_08",
            "mutation_type": "comparison_swap",
            "original_code": "if a == b: return True",
            "mutated_code": "if a != b: return True",
            "mutation_result": "PASS",
            "stderr": "",
            "line": 1,
            "column": 5,
        }
    ]
    step = derive_step_label(
        problem_id="mbpp_003",
        solution_id="mbpp_003_sol_001",
        step_id="block_08",
        step_type="block",
        dataset_source="pilot",
        records=records,
    )

    assert step.outcome_flip is False
    assert step.label == "uncertain"
    assert step.num_pass == 1
    assert "survived" in step.label_rationale.lower()


def test_single_operator_1_of_1_correct():
    records = [
        {
            "problem_id": "eval_013",
            "solution_id": "eval_013_sol_001",
            "step_id": "block_01",
            "mutation_type": "identity_swap",
            "original_code": "return x is None",
            "mutated_code": "return x is not None",
            "mutation_result": "FAIL",
            "stderr": "AssertionError",
            "line": 1,
            "column": 9,
        }
    ]
    step = derive_step_label(
        problem_id="eval_013",
        solution_id="eval_013_sol_001",
        step_id="block_01",
        step_type="unified_func_block",
        dataset_source="evaluation",
        records=records,
    )

    assert step.label == "correct"
    assert step.outcome_flip is True
    assert step.applicable_mutation_types == ["identity_swap"]
    assert "100%" in step.label_rationale


def test_multi_operator_at_least_2_flips_correct():
    records = [
        {
            "problem_id": "eval_004",
            "solution_id": "eval_004_sol_001",
            "step_id": "block_05",
            "mutation_type": "comparison_swap",
            "original_code": "if s[i] == s[j] and length == 2:",
            "mutated_code": "if s[i] != s[j] and length == 2:",
            "mutation_result": "FAIL",
            "stderr": "AssertionError",
        },
        {
            "problem_id": "eval_004",
            "solution_id": "eval_004_sol_001",
            "step_id": "block_05",
            "mutation_type": "boolean_flip",
            "original_code": "if s[i] == s[j] and length == 2:",
            "mutated_code": "if s[i] == s[j] or length == 2:",
            "mutation_result": "FAIL",
            "stderr": "AssertionError",
        },
    ]
    step = derive_step_label(
        problem_id="eval_004",
        solution_id="eval_004_sol_001",
        step_id="block_05",
        step_type="block",
        dataset_source="evaluation",
        records=records,
    )

    assert step.label == "correct"
    assert step.outcome_flip is True
    assert len(step.flips_by_type) == 2
    assert ">=2" in step.label_rationale


def test_multi_operator_insufficient_flips_uncertain():
    records = [
        {
            "problem_id": "mbpp_004",
            "solution_id": "mbpp_004_sol_004",
            "step_id": "func_01",
            "mutation_type": "comparison_swap",
            "original_code": "code",
            "mutated_code": "code",
            "mutation_result": "FAIL",
            "stderr": "AssertionError",
        },
        {
            "problem_id": "mbpp_004",
            "solution_id": "mbpp_004_sol_004",
            "step_id": "func_01",
            "mutation_type": "boolean_flip",
            "original_code": "code",
            "mutated_code": "code",
            "mutation_result": "PASS",  # Survived
            "stderr": "",
        },
    ]
    step = derive_step_label(
        problem_id="mbpp_004",
        solution_id="mbpp_004_sol_004",
        step_id="func_01",
        step_type="function",
        dataset_source="pilot",
        records=records,
    )

    assert step.label == "uncertain"
    assert step.outcome_flip is False


def test_runtime_error_dominance_uncertain():
    records = [
        {
            "problem_id": "eval_014",
            "solution_id": "eval_014_sol_001",
            "step_id": "block_01",
            "mutation_type": "multiplication_swap",
            "original_code": "return sum(2*i for i in range(n))",
            "mutated_code": "return sum(2/i for i in range(n))",
            "mutation_result": "RUNTIME_ERROR",
            "stderr": "ZeroDivisionError: division by zero",
        }
    ]
    step = derive_step_label(
        problem_id="eval_014",
        solution_id="eval_014_sol_001",
        step_id="block_01",
        step_type="unified_func_block",
        dataset_source="evaluation",
        records=records,
    )

    assert step.label == "uncertain"
    assert step.outcome_flip is False
    assert "Dominant RUNTIME_ERROR" in step.label_rationale
    assert "ZeroDivisionError" in step.exception_types


def test_type_error_ambiguity_uncertain():
    records = [
        {
            "problem_id": "eval_004",
            "solution_id": "eval_004_sol_001",
            "step_id": "block_02",
            "mutation_type": "multiplication_swap",
            "original_code": "dp = [[0] * n for _ in range(n)]",
            "mutated_code": "dp = [[0] / n for _ in range(n)]",
            "mutation_result": "RUNTIME_ERROR",
            "stderr": "TypeError: unsupported operand type(s) for /: 'list' and 'int'",
        }
    ]
    step = derive_step_label(
        problem_id="eval_004",
        solution_id="eval_004_sol_001",
        step_id="block_02",
        step_type="block",
        dataset_source="evaluation",
        records=records,
    )

    assert step.label == "uncertain"
    assert "TypeError" in step.exception_types


# ---------------------------------------------------------------------------
# Deduplication Tests
# ---------------------------------------------------------------------------

def test_func_block_duplicate_deduplication():
    records = [
        {
            "problem_id": "eval_013",
            "solution_id": "eval_013_sol_001",
            "step_id": "func_01",
            "mutation_type": "identity_swap",
            "original_operator": "is",
            "mutated_operator": "is not",
            "line": 2,
            "column": 20,
            "original_code": "def check_none(t):\n    return any(x is None for x in t)",
            "mutated_code": "def check_none(t):\n    return any(x is not None for x in t)",
            "mutation_result": "FAIL",
            "dataset_source": "evaluation",
        },
        {
            "problem_id": "eval_013",
            "solution_id": "eval_013_sol_001",
            "step_id": "block_01",
            "mutation_type": "identity_swap",
            "original_operator": "is",
            "mutated_operator": "is not",
            "line": 2,
            "column": 20,
            "original_code": "def check_none(t):\n    return any(x is None for x in t)",
            "mutated_code": "def check_none(t):\n    return any(x is not None for x in t)",
            "mutation_result": "FAIL",
            "dataset_source": "evaluation",
        },
    ]

    canonical_steps, collapsed_count = deduplicate_canonical_steps(records)

    assert collapsed_count == 1
    assert len(canonical_steps) == 1
    assert canonical_steps[0]["step_id"] == "block_01"
    assert canonical_steps[0]["step_type"] == "unified_func_block"


def test_genuinely_different_blocks_preserved():
    records = [
        {
            "problem_id": "eval_016",
            "solution_id": "eval_016_sol_001",
            "step_id": "block_04",
            "mutation_type": "comparison_swap",
            "original_operator": "==",
            "mutated_operator": "!=",
            "line": 6,
            "column": 20,
            "original_code": "code",
            "mutated_code": "mutated_code_1",
            "mutation_result": "FAIL",
            "dataset_source": "evaluation",
        },
        {
            "problem_id": "eval_016",
            "solution_id": "eval_016_sol_001",
            "step_id": "block_05",
            "mutation_type": "comparison_swap",
            "original_operator": "<",
            "mutated_operator": ">=",
            "line": 9,
            "column": 22,
            "original_code": "code",
            "mutated_code": "mutated_code_2",
            "mutation_result": "FAIL",
            "dataset_source": "evaluation",
        },
    ]

    canonical_steps, collapsed_count = deduplicate_canonical_steps(records)

    assert collapsed_count == 0
    assert len(canonical_steps) == 2
    step_ids = {s["step_id"] for s in canonical_steps}
    assert step_ids == {"block_04", "block_05"}


# ---------------------------------------------------------------------------
# Aggregation & Leakage Prevention Tests
# ---------------------------------------------------------------------------

def test_pilot_and_evaluation_aggregation():
    raw_records = validate_and_load_evidence(
        pilot_path=DEFAULT_PILOT_EVIDENCE,
        eval_path=DEFAULT_EVAL_EVIDENCE,
    )

    assert len(raw_records) == 257  # 99 pilot + 158 eval
    sources = Counter(r["dataset_source"] for r in raw_records)
    assert sources["pilot"] == 99
    assert sources["evaluation"] == 158


def test_solution_level_train_eval_leakage_prevention():
    raw_records = validate_and_load_evidence(
        pilot_path=DEFAULT_PILOT_EVIDENCE,
        eval_path=DEFAULT_EVAL_EVIDENCE,
    )
    canonical_groups, _ = deduplicate_canonical_steps(raw_records)

    labeled_steps = [
        derive_step_label(
            problem_id=grp["problem_id"],
            solution_id=grp["solution_id"],
            step_id=grp["step_id"],
            step_type=grp["step_type"],
            dataset_source=grp["dataset_source"],
            records=grp["records"],
        )
        for grp in canonical_groups
    ]

    train_steps, eval_steps = partition_train_eval(
        labeled_steps=labeled_steps,
        train_ratio=0.8,
        seed=42,
    )

    train_solutions = {s.solution_id for s in train_steps}
    eval_solutions = {s.solution_id for s in eval_steps}

    # Strict zero-leakage assertion
    assert train_solutions.isdisjoint(eval_solutions)
    assert len(train_solutions.intersection(eval_solutions)) == 0


def test_canonical_step_target_exceeds_150():
    raw_records = validate_and_load_evidence(
        pilot_path=DEFAULT_PILOT_EVIDENCE,
        eval_path=DEFAULT_EVAL_EVIDENCE,
    )
    canonical_groups, collapsed_count = deduplicate_canonical_steps(raw_records)

    assert len(canonical_groups) >= 150
    assert len(canonical_groups) == 156
    assert collapsed_count == 51


def test_generated_artifacts_integrity():
    summary_path = DEFAULT_OUTPUT_DIR / "verifier_label_summary.json"
    labels_path = DEFAULT_OUTPUT_DIR / "verifier_labels.jsonl"
    train_path = DEFAULT_OUTPUT_DIR / "verifier_train.jsonl"
    eval_path = DEFAULT_OUTPUT_DIR / "verifier_eval.jsonl"
    report_path = DEFAULT_OUTPUT_DIR / "verifier_label_derivation.md"

    for path in [summary_path, labels_path, train_path, eval_path, report_path]:
        assert path.exists(), f"Artifact {path} must exist"
        assert path.stat().st_size > 0, f"Artifact {path} must not be empty"

    with summary_path.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["target_met"] is True
    assert summary["total_canonical_steps"] == 156
    assert summary["split_summary"]["solution_leakage"] == 0
    assert summary["split_summary"]["train_steps"] + summary["split_summary"]["eval_steps"] == 156
