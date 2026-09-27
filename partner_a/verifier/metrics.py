"""Evaluation metrics for StepGuard Process Reward Model (PRM).

Computes comprehensive classification metrics including per-class precision,
recall, F1, accuracy, and confusion matrix breakdown with raw counts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    brier_score_loss,
)

LABEL_MAP = {"uncertain": 0, "correct": 1}
INV_LABEL_MAP = {0: "uncertain", 1: "correct"}


def evaluate_predictions(
    y_true: List[str],
    y_pred: List[str],
    y_prob: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Calculate comprehensive evaluation metrics on held-out predictions."""
    y_t = np.array([LABEL_MAP[y] for y in y_true], dtype=int)
    y_p = np.array([LABEL_MAP[y] for y in y_pred], dtype=int)

    acc = float(accuracy_score(y_t, y_p))

    # Binary metrics for 'correct' (class 1)
    p_corr, r_corr, f1_corr, _ = precision_recall_fscore_support(
        y_t, y_p, pos_label=1, average="binary", zero_division=0
    )

    # Binary metrics for 'uncertain' (class 0)
    p_unc, r_unc, f1_unc, _ = precision_recall_fscore_support(
        y_t, y_p, pos_label=0, average="binary", zero_division=0
    )

    # Macro averages
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_t, y_p, average="macro", zero_division=0
    )

    # Confusion matrix:
    # rows: true [uncertain, correct]
    # cols: pred [uncertain, correct]
    cm = confusion_matrix(y_t, y_p, labels=[0, 1])
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    true_correct = int(np.sum(y_t == 1))
    true_uncertain = int(np.sum(y_t == 0))
    pred_correct = int(np.sum(y_p == 1))
    pred_uncertain = int(np.sum(y_p == 0))

    metrics: Dict[str, Any] = {
        "total_samples": len(y_true),
        "accuracy": acc,
        "accuracy_pct": round(acc * 100.0, 2),
        "macro_metrics": {
            "precision": float(p_macro),
            "recall": float(r_macro),
            "f1": float(f1_macro),
        },
        "per_class": {
            "correct": {
                "support": true_correct,
                "precision": float(p_corr),
                "recall": float(r_corr),
                "f1": float(f1_corr),
            },
            "uncertain": {
                "support": true_uncertain,
                "precision": float(p_unc),
                "recall": float(r_unc),
                "f1": float(f1_unc),
            },
        },
        "confusion_matrix": {
            "matrix": [[tn, fp], [fn, tp]],
            "true_uncertain_pred_uncertain (TN)": tn,
            "true_uncertain_pred_correct (FP)": fp,
            "true_correct_pred_uncertain (FN)": fn,
            "true_correct_pred_correct (TP)": tp,
        },
        "counts": {
            "true_correct": true_correct,
            "true_uncertain": true_uncertain,
            "pred_correct": pred_correct,
            "pred_uncertain": pred_uncertain,
            "correct_ratio": round(true_correct / (len(y_true) or 1), 4),
            "uncertain_ratio": round(true_uncertain / (len(y_true) or 1), 4),
        },
    }

    if y_prob is not None:
        try:
            prob_corr = y_prob[:, 1]
            brier = float(brier_score_loss(y_t, prob_corr))
            metrics["brier_score"] = round(brier, 4)
        except Exception:
            pass

    return metrics
