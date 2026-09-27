"""Unit tests for StepGuard Verifier (PRM) pipeline.

Validates:
- Dataset loading and split disjointness
- Feature extraction and strict leakage prevention
- Label encoding
- Baseline implementations (Majority & Execution Heuristic)
- PyTorch neural network forward pass and gradients
- Model checkpoint saving and loading
- Evaluation metrics and confusion matrix accuracy
- End-to-end training script execution
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
import torch

from partner_a.verifier.baselines import ExecutionHeuristicBaseline, MajorityClassBaseline
from partner_a.verifier.features import StepFeatureExtractor, FORBIDDEN_LEAKAGE_FIELDS
from partner_a.verifier.metrics import evaluate_predictions, LABEL_MAP, INV_LABEL_MAP
from partner_a.verifier.model import StepGuardPRM, StepGuardPRMNet
from partner_a.verifier.train_verifier import load_jsonl, verify_disjoint_splits, train_and_evaluate


TRAIN_PATH = Path("data/evaluation/stage_1/verifier_train.jsonl")
EVAL_PATH = Path("data/evaluation/stage_1/verifier_eval.jsonl")


def test_dataset_loading_and_split_disjointness() -> None:
    """Verify that train and eval datasets exist, have expected counts, and zero solution leakage."""
    assert TRAIN_PATH.exists(), f"Missing train file: {TRAIN_PATH}"
    assert EVAL_PATH.exists(), f"Missing eval file: {EVAL_PATH}"

    train_records = load_jsonl(TRAIN_PATH)
    eval_records = load_jsonl(EVAL_PATH)

    assert len(train_records) == 119
    assert len(eval_records) == 37
    assert len(train_records) + len(eval_records) == 156

    # Verify solution disjointness
    train_sols = {r["solution_id"] for r in train_records}
    eval_sols = {r["solution_id"] for r in eval_records}
    assert len(train_sols) == 59
    assert len(eval_sols) == 15
    assert len(train_sols.intersection(eval_sols)) == 0

    # Ensure verify_disjoint_splits helper passes
    verify_disjoint_splits(train_records, eval_records)


def test_split_disjointness_catches_leakage() -> None:
    """Verify verify_disjoint_splits raises ValueError when solutions overlap."""
    train_records = [{"solution_id": "sol_1"}]
    eval_records = [{"solution_id": "sol_1"}]
    with pytest.raises(ValueError, match="Solution leakage detected"):
        verify_disjoint_splits(train_records, eval_records)


def test_feature_extractor_strict_leakage_exclusion() -> None:
    """Verify that changing ground-truth label and derived outcome fields does not alter features."""
    train_records = load_jsonl(TRAIN_PATH)
    extractor = StepFeatureExtractor(max_tfidf_features=24)
    extractor.fit(train_records[:20])

    base_record: Dict[str, Any] = {
        "problem_id": "eval_001",
        "solution_id": "eval_001_sol_001",
        "step_id": "block_01",
        "step_type": "unified_func_block",
        "code": "def solve(x):\n    return x * 2",
        "line": 1,
        "column": 0,
        "applicable_mutation_types": ["multiplication_swap"],
        "num_mutations": 1,
        "num_pass": 0,
        "num_fail": 1,
        "num_runtime_error": 0,
        "exception_types": ["AssertionError"],
        # Forbidden fields:
        "flips_by_type": ["multiplication_swap"],
        "outcome_flip": True,
        "label": "correct",
        "label_rationale": "100% genuine outcome flip",
        "split": "train",
    }

    # Extract baseline feature vector
    feat_base = extractor.transform([base_record])

    # Mutate all forbidden fields
    tampered_record = copy.deepcopy(base_record)
    tampered_record["label"] = "uncertain"
    tampered_record["label_rationale"] = "tampered rationale text that should not affect features"
    tampered_record["split"] = "eval"
    tampered_record["outcome_flip"] = False
    tampered_record["flips_by_type"] = []

    feat_tampered = extractor.transform([tampered_record])

    # Both feature vectors MUST be bitwise identical
    assert np.allclose(feat_base, feat_tampered, atol=1e-7), (
        "Feature vector changed when tampering with forbidden fields! Potential data leakage."
    )


def test_feature_extractor_dimension_and_serialization(tmp_path: Path) -> None:
    """Test extractor fit, transform shapes, dimension getter, and save/load."""
    train_records = load_jsonl(TRAIN_PATH)[:30]
    extractor = StepFeatureExtractor(max_tfidf_features=32)
    X = extractor.fit_transform(train_records)

    assert X.shape[0] == 30
    assert X.shape[1] == extractor.get_feature_dimension()
    assert X.dtype == np.float32

    # Test serialization
    save_path = tmp_path / "extractor.joblib"
    extractor.save(save_path)
    loaded_extractor = StepFeatureExtractor.load(save_path)

    X_loaded = loaded_extractor.transform(train_records)
    assert np.allclose(X, X_loaded)


def test_label_encoding() -> None:
    """Verify label encoding consistency."""
    assert LABEL_MAP["correct"] == 1
    assert LABEL_MAP["uncertain"] == 0
    assert INV_LABEL_MAP[1] == "correct"
    assert INV_LABEL_MAP[0] == "uncertain"


def test_majority_baseline() -> None:
    """Verify majority class baseline behavior."""
    train_records = [
        {"label": "correct"},
        {"label": "correct"},
        {"label": "uncertain"},
    ]
    test_records = [{"label": "uncertain"}, {"label": "correct"}]

    baseline = MajorityClassBaseline().fit(train_records)
    preds = baseline.predict(test_records)
    probs = baseline.predict_proba(test_records)

    assert preds == ["correct", "correct"]
    assert probs.shape == (2, 2)
    assert np.isclose(probs[0, 1], 2 / 3)


def test_execution_heuristic_baseline() -> None:
    """Verify execution heuristic baseline rules."""
    records = [
        {"num_fail": 2, "num_pass": 0},  # all killed -> correct
        {"num_fail": 1, "num_pass": 1},  # survivor present -> uncertain
        {"num_fail": 0, "num_pass": 0},  # no mutations failed -> uncertain
    ]
    baseline = ExecutionHeuristicBaseline()
    preds = baseline.predict(records)
    assert preds == ["correct", "uncertain", "uncertain"]


def test_model_forward_pass_and_backward() -> None:
    """Verify PyTorch neural network forward pass, output shape, and gradient updates."""
    in_features = 50
    batch_size = 8
    model = StepGuardPRMNet(in_features=in_features, hidden_dim=32, dropout=0.1)

    dummy_x = torch.randn(batch_size, in_features)
    out = model(dummy_x)

    assert out.shape == (batch_size, 2)
    criterion = torch.nn.CrossEntropyLoss()
    target = torch.randint(0, 2, (batch_size,))
    loss = criterion(out, target)
    loss.backward()

    # Verify gradients exist
    for p in model.parameters():
        if p.requires_grad:
            assert p.grad is not None


def test_checkpoint_save_and_load(tmp_path: Path) -> None:
    """Verify end-to-end model checkpointing and standalone inference reload."""
    train_records = load_jsonl(TRAIN_PATH)[:25]
    eval_records = load_jsonl(EVAL_PATH)[:10]

    prm = StepGuardPRM(hidden_dim=16, max_tfidf_features=16)
    prm.fit(train_records, epochs=5, lr=0.01, seed=42)

    orig_preds = prm.predict(eval_records)
    orig_probs = prm.predict_proba(eval_records)

    ckpt_dir = tmp_path / "checkpoint"
    prm.save_checkpoint(ckpt_dir)

    assert (ckpt_dir / "model_weights.pt").exists()
    assert (ckpt_dir / "extractor.joblib").exists()
    assert (ckpt_dir / "config.json").exists()

    # Load from checkpoint
    loaded_prm = StepGuardPRM.load_checkpoint(ckpt_dir)
    loaded_preds = loaded_prm.predict(eval_records)
    loaded_probs = loaded_prm.predict_proba(eval_records)

    assert orig_preds == loaded_preds
    assert np.allclose(orig_probs, loaded_probs, atol=1e-5)

    # Test single step scoring
    score = loaded_prm.score_step(eval_records[0])
    assert 0.0 <= score <= 1.0


def test_evaluate_predictions_metrics() -> None:
    """Verify evaluate_predictions computes exact precision, recall, F1, and confusion matrix."""
    y_true = ["correct", "correct", "uncertain", "uncertain"]
    y_pred = ["correct", "uncertain", "uncertain", "uncertain"]
    # True correct=2, True uncertain=2
    # Pred: TP (correct->correct) = 1, FN (correct->uncertain) = 1, TN (unc->unc) = 2, FP = 0

    metrics = evaluate_predictions(y_true, y_pred)

    assert metrics["total_samples"] == 4
    assert metrics["accuracy"] == 0.75
    assert metrics["confusion_matrix"]["true_correct_pred_correct (TP)"] == 1
    assert metrics["confusion_matrix"]["true_correct_pred_uncertain (FN)"] == 1
    assert metrics["confusion_matrix"]["true_uncertain_pred_uncertain (TN)"] == 2
    assert metrics["confusion_matrix"]["true_uncertain_pred_correct (FP)"] == 0

    assert metrics["per_class"]["correct"]["recall"] == 0.5
    assert metrics["per_class"]["correct"]["precision"] == 1.0
    assert metrics["per_class"]["uncertain"]["recall"] == 1.0


def test_end_to_end_train_verifier_execution(tmp_path: Path) -> None:
    """Verify train_verifier train_and_evaluate runs and writes all required artifacts."""
    output_dir = tmp_path / "stage_2_test"
    args = argparse.Namespace(
        train_path=str(TRAIN_PATH),
        eval_path=str(EVAL_PATH),
        output_dir=str(output_dir),
        epochs=10,
        lr=0.005,
        batch_size=32,
        hidden_dim=16,
        dropout=0.1,
        weight_decay=1e-4,
        max_tfidf_features=24,
        seed=42,
        device="cpu",
    )

    results = train_and_evaluate(args)

    assert (output_dir / "checkpoint" / "model_weights.pt").exists()
    assert (output_dir / "checkpoint" / "extractor.joblib").exists()
    assert (output_dir / "checkpoint" / "config.json").exists()
    assert (output_dir / "verifier_metrics.json").exists()
    assert (output_dir / "verifier_training_report.md").exists()

    assert "prm_evaluation" in results
    assert results["prm_evaluation"]["accuracy"] > 0.8
