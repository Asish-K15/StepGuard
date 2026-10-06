"""Unit tests for StepGuard Verifier Demo.

Validates:
- Checkpoint loading in demo runner
- Valid inference on real evaluation records
- Output schema verification
- Confidence range bounds [0, 1]
- Deterministic inference reproducibility
- Error handling for missing required fields and invalid indices
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from partner_a.verifier.demo_verifier import load_eval_record, run_demo


CHECKPOINT_DIR = Path("data/evaluation/stage_2/checkpoint")
EVAL_PATH = Path("data/evaluation/stage_2/verifier_eval.jsonl")


def test_checkpoint_exists_and_loads() -> None:
    """Verify that checkpoint directory exists with all required serialized assets."""
    assert CHECKPOINT_DIR.exists()
    assert (CHECKPOINT_DIR / "model_weights.pt").exists()
    assert (CHECKPOINT_DIR / "extractor.joblib").exists()
    assert (CHECKPOINT_DIR / "config.json").exists()


def test_load_eval_record_valid_and_bounds() -> None:
    """Verify loading real evaluation records by index and index boundary checks."""
    assert EVAL_PATH.exists()
    rec0 = load_eval_record(EVAL_PATH, index=0)
    assert rec0["problem_id"] == "eval_001"
    assert rec0["step_id"] == "block_01"

    rec36 = load_eval_record(EVAL_PATH, index=36)
    assert rec36["problem_id"] == "mbpp_005"

    with pytest.raises(IndexError):
        load_eval_record(EVAL_PATH, index=999)

    with pytest.raises(IndexError):
        load_eval_record(EVAL_PATH, index=-1)


def test_demo_inference_output_schema() -> None:
    """Verify that run_demo returns complete, type-safe schema."""
    result = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=0)

    expected_keys = {
        "problem_id",
        "solution_id",
        "step_id",
        "step_type",
        "code",
        "gold_label",
        "predicted_label",
        "p_correct",
        "p_uncertain",
        "mutation_families",
        "num_mutations",
        "num_pass",
        "num_fail",
        "num_runtime_error",
        "exception_types",
        "checkpoint_path",
    }
    assert set(result.keys()) == expected_keys
    assert isinstance(result["p_correct"], float)
    assert isinstance(result["p_uncertain"], float)
    assert result["predicted_label"] in {"correct", "uncertain"}


def test_demo_confidence_range_and_probabilities() -> None:
    """Verify that P(correct) and P(uncertain) are valid probabilities summing to 1.0."""
    result = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=0)

    assert 0.0 <= result["p_correct"] <= 1.0
    assert 0.0 <= result["p_uncertain"] <= 1.0
    assert abs((result["p_correct"] + result["p_uncertain"]) - 1.0) < 1e-4


def test_demo_deterministic_result() -> None:
    """Verify that repeated calls on the same record produce identical predictions and scores."""
    res1 = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=3)
    res2 = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=3)

    assert res1["predicted_label"] == res2["predicted_label"]
    assert res1["p_correct"] == res2["p_correct"]
    assert res1["predicted_label"] == "uncertain"


def test_demo_custom_record_inference() -> None:
    """Verify demo inference on an explicitly passed dictionary record."""
    custom_record = {
        "problem_id": "eval_001",
        "solution_id": "eval_001_custom",
        "step_id": "block_01",
        "step_type": "unified_func_block",
        "code": "def max_product_tuple(lst):\n    return max(abs(a * b) for a, b in lst)",
        "num_mutations": 1,
        "num_pass": 0,
        "num_fail": 1,
        "num_runtime_error": 0,
        "applicable_mutation_types": ["multiplication_swap"],
        "exception_types": ["AssertionError"],
    }

    result = run_demo(checkpoint_dir=CHECKPOINT_DIR, step_record=custom_record)
    assert result["problem_id"] == "eval_001"
    assert result["predicted_label"] == "correct"
    assert result["p_correct"] > 0.99


def test_demo_missing_required_keys_raises() -> None:
    """Verify that passing an invalid record missing core keys raises ValueError."""
    bad_record = {"problem_id": "eval_001"}
    with pytest.raises(ValueError, match="missing required keys"):
        run_demo(checkpoint_dir=CHECKPOINT_DIR, step_record=bad_record)
