"""Baseline models for StepGuard verifier evaluation.

Provides non-neural baselines to benchmark trained PRM performance:
1. MajorityClassBaseline: Always predicts the training majority class.
2. ExecutionHeuristicBaseline: Deterministic rule based on raw test pass/fail counts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List
import numpy as np


class MajorityClassBaseline:
    """Predicts the most frequent class observed during training."""

    def __init__(self) -> None:
        self.majority_label: str = "correct"
        self.class_frequencies: Dict[str, float] = {"uncertain": 0.0, "correct": 1.0}

    def fit(self, records: List[Dict[str, Any]]) -> "MajorityClassBaseline":
        labels = [r.get("label", "correct") for r in records]
        counts = Counter(labels)
        total = len(labels) or 1
        self.majority_label = counts.most_common(1)[0][0]
        self.class_frequencies = {
            "uncertain": counts.get("uncertain", 0) / total,
            "correct": counts.get("correct", 0) / total,
        }
        return self

    def predict(self, records: List[Dict[str, Any]]) -> List[str]:
        return [self.majority_label] * len(records)

    def predict_proba(self, records: List[Dict[str, Any]]) -> np.ndarray:
        prob = np.array([
            self.class_frequencies.get("uncertain", 0.0),
            self.class_frequencies.get("correct", 1.0),
        ], dtype=np.float32)
        return np.tile(prob, (len(records), 1))


class ExecutionHeuristicBaseline:
    """Deterministic rule-based baseline using raw execution counts.

    Rule:
    - If num_fail > 0 and num_pass == 0 -> predict 'correct' (all mutations were killed)
    - Else (num_pass > 0 or num_fail == 0) -> predict 'uncertain' (survivors or no evidence)
    """

    def fit(self, records: List[Dict[str, Any]]) -> "ExecutionHeuristicBaseline":
        # Rule is purely heuristic, no fitting required
        return self

    def predict(self, records: List[Dict[str, Any]]) -> List[str]:
        preds: List[str] = []
        for r in records:
            n_fail = int(r.get("num_fail", 0) or 0)
            n_pass = int(r.get("num_pass", 0) or 0)
            if n_fail > 0 and n_pass == 0:
                preds.append("correct")
            else:
                preds.append("uncertain")
        return preds

    def predict_proba(self, records: List[Dict[str, Any]]) -> np.ndarray:
        preds = self.predict(records)
        probs = []
        for p in preds:
            if p == "correct":
                probs.append([0.05, 0.95])
            else:
                probs.append([0.95, 0.05])
        return np.array(probs, dtype=np.float32)
