"""Unit tests for StepGuard Gate C PRM-vs-Human Semantic Evaluation.

Validates:
- Exactly 37 frozen evaluation records are represented in the Gate C cohort
- Final human ground truth distribution is exactly 33 A, 0 B, 4 C
- Sole disagreement is SG-GATE-C-025 (E1=C, E2=A, Srilu Adjudication=C)
- SG-GATE-C-022 is concordant (E1=A, E2=A)
- Class C (uncertain) samples are strictly excluded from definitive A/B accuracy
- Accuracy denominator is exactly the number of definitive A/B labels (33)
- E1/E2 raw agreement is exactly 36/37 (97.30%) with Cohen's kappa >= 0.75 (approx 0.8426)
- Zero data leakage between verifier_train.jsonl and verifier_eval.jsonl
- Deterministic PRM predictions on the held-out N=37 cohort (20 correct, 17 uncertain)
- Definitive cohort confusion matrix (TP=20, FN=13, TN=0, FP=0) and accuracy (60.61%)
- Threshold rule determination follows authorized Gate C protocol
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from partner_a.verifier.demo_verifier import run_demo


EVAL_PATH = Path("data/evaluation/stage_1/verifier_eval.jsonl")
TRAIN_PATH = Path("data/evaluation/stage_1/verifier_train.jsonl")
CHECKPOINT_DIR = Path("data/evaluation/stage_2/checkpoint")
BLIND_SHEET_PATH = Path("data/validation/gate_c_blind_evaluation_sheet.md")
REPORT_PATH = Path("data/validation/gate_c_prm_semantic_evaluation.md")

# Ground truth human labels for the 37 held-out evaluation samples
# (SG-GATE-C-001 through SG-GATE-C-037)
# Evaluator 1 (Partner A: 33 A, 0 B, 4 C)
# Evaluator 2 (Chandu: 34 A, 0 B, 3 C)
# Adjudicator (Srilu: 1 resolved sample SG-GATE-C-025 to C)
HUMAN_ANNOTATIONS = [
    # idx, sample_id, e1, e2, adj, final
    (0, "SG-GATE-C-001", "A", "A", None, "A"),
    (1, "SG-GATE-C-002", "A", "A", None, "A"),
    (2, "SG-GATE-C-003", "A", "A", None, "A"),
    (3, "SG-GATE-C-004", "A", "A", None, "A"),
    (4, "SG-GATE-C-005", "A", "A", None, "A"),
    (5, "SG-GATE-C-006", "A", "A", None, "A"),
    (6, "SG-GATE-C-007", "A", "A", None, "A"),
    (7, "SG-GATE-C-008", "A", "A", None, "A"),
    (8, "SG-GATE-C-009", "A", "A", None, "A"),
    (9, "SG-GATE-C-010", "A", "A", None, "A"),
    (10, "SG-GATE-C-011", "A", "A", None, "A"),
    (11, "SG-GATE-C-012", "A", "A", None, "A"),
    (12, "SG-GATE-C-013", "A", "A", None, "A"),
    (13, "SG-GATE-C-014", "A", "A", None, "A"),
    (14, "SG-GATE-C-015", "A", "A", None, "A"),
    (15, "SG-GATE-C-016", "A", "A", None, "A"),
    (16, "SG-GATE-C-017", "A", "A", None, "A"),
    (17, "SG-GATE-C-018", "A", "A", None, "A"),
    (18, "SG-GATE-C-019", "A", "A", None, "A"),
    (19, "SG-GATE-C-020", "A", "A", None, "A"),
    (20, "SG-GATE-C-021", "A", "A", None, "A"),
    (21, "SG-GATE-C-022", "A", "A", None, "A"),  # Concordant sample (E1=A, E2=A)
    (22, "SG-GATE-C-023", "A", "A", None, "A"),
    (23, "SG-GATE-C-024", "A", "A", None, "A"),
    (24, "SG-GATE-C-025", "C", "A", "C", "C"),  # Sole disagreement, adjudicated by Srilu
    (25, "SG-GATE-C-026", "C", "C", None, "C"),  # Class C (uncertain/ambiguous boundary)
    (26, "SG-GATE-C-027", "A", "A", None, "A"),
    (27, "SG-GATE-C-028", "A", "A", None, "A"),
    (28, "SG-GATE-C-029", "A", "A", None, "A"),
    (29, "SG-GATE-C-030", "A", "A", None, "A"),
    (30, "SG-GATE-C-031", "C", "C", None, "C"),  # Class C (uncertain/ambiguous boundary)
    (31, "SG-GATE-C-032", "A", "A", None, "A"),
    (32, "SG-GATE-C-033", "A", "A", None, "A"),
    (33, "SG-GATE-C-034", "C", "C", None, "C"),  # Class C (uncertain/ambiguous boundary)
    (34, "SG-GATE-C-035", "A", "A", None, "A"),
    (35, "SG-GATE-C-036", "A", "A", None, "A"),
    (36, "SG-GATE-C-037", "A", "A", None, "A"),
]


def test_frozen_evaluation_cohort_represented_exactly_37() -> None:
    """Verify that verifier_eval.jsonl contains exactly 37 records matching the 37 human annotations."""
    assert EVAL_PATH.exists(), f"Missing {EVAL_PATH}"
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        recs = [json.loads(line) for line in f if line.strip()]

    assert len(recs) == 37
    assert len(HUMAN_ANNOTATIONS) == 37

    # Verify 1:1 index alignment with sample IDs
    for idx, sample_id, _, _, _, _ in HUMAN_ANNOTATIONS:
        assert sample_id == f"SG-GATE-C-{idx+1:03d}"


def test_final_human_label_distribution() -> None:
    """Verify final human distribution is exactly 33 A, 0 B, 4 C."""
    final_labels = [row[5] for row in HUMAN_ANNOTATIONS]

    a_count = final_labels.count("A")
    b_count = final_labels.count("B")
    c_count = final_labels.count("C")

    assert a_count == 33
    assert b_count == 0
    assert c_count == 4
    assert len(final_labels) == 37


def test_sole_disagreement_and_adjudication() -> None:
    """Verify that SG-GATE-C-025 is the sole disagreement and SG-GATE-C-022 is concordant."""
    disagreements = [
        row for row in HUMAN_ANNOTATIONS if row[2] != row[3]
    ]
    assert len(disagreements) == 1
    sole_disagreement = disagreements[0]
    assert sole_disagreement[1] == "SG-GATE-C-025"
    assert sole_disagreement[2] == "C"  # E1 / Partner A
    assert sole_disagreement[3] == "A"  # E2 / Chandu
    assert sole_disagreement[4] == "C"  # Srilu Adjudication
    assert sole_disagreement[5] == "C"  # Final label

    # Verify SG-GATE-C-022 is concordant
    sg_022 = next(row for row in HUMAN_ANNOTATIONS if row[1] == "SG-GATE-C-022")
    assert sg_022[2] == "A"
    assert sg_022[3] == "A"
    assert sg_022[4] is None
    assert sg_022[5] == "A"


def test_e1_e2_inter_rater_agreement_and_kappa() -> None:
    """Verify E1 and E2 agree on exactly 36 of 37 samples and calculate exact Cohen's kappa."""
    e1_labels = [row[2] for row in HUMAN_ANNOTATIONS]
    e2_labels = [row[3] for row in HUMAN_ANNOTATIONS]

    assert e1_labels.count("A") == 33
    assert e1_labels.count("B") == 0
    assert e1_labels.count("C") == 4

    assert e2_labels.count("A") == 34
    assert e2_labels.count("B") == 0
    assert e2_labels.count("C") == 3

    agreed = sum(1 for e1, e2 in zip(e1_labels, e2_labels) if e1 == e2)
    assert agreed == 36
    raw_agreement = agreed / len(HUMAN_ANNOTATIONS)
    assert pytest.approx(raw_agreement, rel=1e-3) == 36 / 37
    assert raw_agreement >= 0.80

    # Compute exact Cohen's kappa:
    # P_o = 36 / 37 = 1332 / 1369
    # P_e = (33 * 34 + 4 * 3) / (37 * 37) = (1122 + 12) / 1369 = 1134 / 1369
    # kappa = (1332 - 1134) / (1369 - 1134) = 198 / 235 ≈ 0.842553
    p_o = raw_agreement
    p_e1_a = 33 / 37
    p_e1_c = 4 / 37
    p_e2_a = 34 / 37
    p_e2_c = 3 / 37

    p_e = (p_e1_a * p_e2_a) + (p_e1_c * p_e2_c)
    kappa = (p_o - p_e) / (1.0 - p_e)

    assert kappa >= 0.75
    assert pytest.approx(kappa, abs=0.001) == 198 / 235
    assert pytest.approx(kappa, abs=0.001) == 0.8426


def test_class_c_exclusion_from_definitive_accuracy() -> None:
    """Verify that Class C samples are excluded from the definitive A/B accuracy denominator."""
    definitive = [row for row in HUMAN_ANNOTATIONS if row[5] in ("A", "B")]
    excluded = [row for row in HUMAN_ANNOTATIONS if row[5] == "C"]

    assert len(definitive) == 33
    assert len(excluded) == 4
    assert len(definitive) + len(excluded) == 37

    # Ensure no C sample has an A or B label
    for row in excluded:
        assert row[5] not in ("A", "B")


def test_zero_data_leakage_and_artifact_immutability() -> None:
    """Verify that train and eval splits have zero overlapping keys and check artifacts exist."""
    assert TRAIN_PATH.exists()
    assert EVAL_PATH.exists()
    assert CHECKPOINT_DIR.exists()
    assert (CHECKPOINT_DIR / "model_weights.pt").exists()
    assert (CHECKPOINT_DIR / "extractor.joblib").exists()

    with open(TRAIN_PATH, "r", encoding="utf-8") as f:
        train_keys = {
            (r["problem_id"], r["solution_id"], r["step_id"])
            for r in (json.loads(l) for l in f if l.strip())
        }

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        eval_keys = {
            (r["problem_id"], r["solution_id"], r["step_id"])
            for r in (json.loads(l) for l in f if l.strip())
        }

    assert len(train_keys) == 119
    assert len(eval_keys) == 37
    assert len(train_keys.intersection(eval_keys)) == 0


def test_prm_predictions_on_frozen_cohort() -> None:
    """Verify PRM inference on the frozen evaluation cohort produces deterministic predictions."""
    predictions = []
    for idx in range(37):
        res = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=idx)
        predictions.append(res["predicted_label"])

    correct_count = predictions.count("correct")
    uncertain_count = predictions.count("uncertain")

    assert correct_count == 20
    assert uncertain_count == 17
    assert len(predictions) == 37


def test_definitive_cohort_prm_accuracy_and_confusion_matrix() -> None:
    """Verify confusion matrix and accuracy on the definitive human evaluation cohort (N=33)."""
    tp = 0
    fn = 0
    tn = 0
    fp = 0

    for idx, _, _, _, _, final_human in HUMAN_ANNOTATIONS:
        if final_human not in ("A", "B"):
            continue  # Exclude C samples

        res = run_demo(checkpoint_dir=CHECKPOINT_DIR, eval_path=EVAL_PATH, record_index=idx)
        pred = res["predicted_label"]

        if final_human == "A":
            if pred == "correct":
                tp += 1
            else:
                fn += 1
        elif final_human == "B":
            if pred != "correct":
                tn += 1
            else:
                fp += 1

    assert tp == 20
    assert fn == 13
    assert tn == 0
    assert fp == 0
    assert tp + fn + tn + fp == 33

    acc = (tp + tn) / 33
    assert pytest.approx(acc, abs=0.001) == 20 / 33
    assert pytest.approx(acc, abs=0.001) == 0.6061

    # PRM accuracy fails the 85% requirement
    assert acc < 0.85


def test_gate_c_threshold_determination() -> None:
    """Verify the formal Gate C determination under authorized evaluation rules."""
    e1_labels = [row[2] for row in HUMAN_ANNOTATIONS]
    e2_labels = [row[3] for row in HUMAN_ANNOTATIONS]

    # Rule 1: Raw agreement >= 80%
    agreed = sum(1 for e1, e2 in zip(e1_labels, e2_labels) if e1 == e2)
    raw_agreement = agreed / 37
    assert raw_agreement >= 0.80

    # Rule 2: Cohen's kappa >= 0.75
    p_o = raw_agreement
    p_e1_a = 33 / 37
    p_e1_c = 4 / 37
    p_e2_a = 34 / 37
    p_e2_c = 3 / 37
    p_e = (p_e1_a * p_e2_a) + (p_e1_c * p_e2_c)
    kappa = (p_o - p_e) / (1.0 - p_e)
    assert kappa >= 0.75

    # Rule 3: PRM accuracy on definitive labels >= 85% -> FAILS (60.61%)
    tp = 20
    tn = 0
    def_acc = (tp + tn) / 33
    prm_acc_passed = def_acc >= 0.85
    assert not prm_acc_passed

    # Rule 4: Absence of negative class (B=0) -> Structural constraint
    b_count = sum(1 for row in HUMAN_ANNOTATIONS if row[5] == "B")
    assert b_count == 0

    # Overall verdict
    is_gate_c_passed = raw_agreement >= 0.80 and kappa >= 0.75 and prm_acc_passed
    assert not is_gate_c_passed  # Inconclusive / threshold deficient


def test_semantic_evaluation_report_exists_and_covers_requirements() -> None:
    """Verify that the written report exists and contains all required metrics and disclosures."""
    assert REPORT_PATH.exists(), f"Missing {REPORT_PATH}"
    report_text = REPORT_PATH.read_text(encoding="utf-8")

    # Verify key sections and metrics
    assert "97.30%" in report_text or "36/37" in report_text
    assert "0.8426" in report_text or "198/235" in report_text
    assert "SG-GATE-C-025" in report_text
    assert "33" in report_text and "89.19%" in report_text  # Class A
    assert "0" in report_text and "0.00%" in report_text    # Class B
    assert "4" in report_text and "10.81%" in report_text   # Class C
    assert "60.61%" in report_text or "20/33" in report_text
    assert "Confusion Matrix on Definitive Cohort" in report_text
    assert "ZERO NEGATIVE CLASS SAMPLES" in report_text or "B = 0" in report_text
    assert "Undefined (0/0)" in report_text
    assert "INCONCLUSIVE" in report_text
