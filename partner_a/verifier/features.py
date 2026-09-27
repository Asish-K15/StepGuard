"""Feature extraction pipeline for StepGuard Process Reward Model (PRM).

Extracts non-leaking semantic, structural, and execution evidence features
from candidate step records while strictly excluding ground-truth labels
and label-derived outcome fields.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# Forbidden fields that must NEVER enter the feature pipeline
FORBIDDEN_LEAKAGE_FIELDS: Set[str] = {
    "label",
    "label_rationale",
    "split",
    "outcome_flip",
    "flips_by_type",
}

ALL_MUTATION_FAMILIES: List[str] = [
    "multiplication_swap",
    "boolean_flip",
    "comparison_swap",
    "off_by_one",
    "identity_swap",
]

ALL_EXCEPTION_TYPES: List[str] = [
    "AssertionError",
    "TypeError",
    "IndexError",
    "ZeroDivisionError",
    "KeyError",
    "ValueError",
]

ALL_STEP_TYPES: List[str] = [
    "unified_func_block",
    "func_block",
    "block",
]


class StepFeatureExtractor:
    """Extracts non-leaking composite feature vectors from step records."""

    def __init__(
        self,
        max_tfidf_features: int = 48,
        include_prompt: bool = True,
        problems_dirs: Optional[List[Path]] = None,
    ) -> None:
        self.max_tfidf_features = max_tfidf_features
        self.include_prompt = include_prompt
        self.problems_dirs = problems_dirs or [
            Path("data/evaluation/problems"),
            Path("data/problems"),
        ]
        self._prompt_cache: Dict[str, str] = {}
        self.tfidf = TfidfVectorizer(
            max_features=max_tfidf_features,
            token_pattern=r"(?u)\b\w+\b|[^\w\s]",
            ngram_range=(1, 2),
        )
        self.dense_mean: Optional[np.ndarray] = None
        self.dense_std: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def get_prompt(self, problem_id: str) -> str:
        """Retrieve problem prompt from cached problem files."""
        if not problem_id:
            return ""
        if problem_id in self._prompt_cache:
            return self._prompt_cache[problem_id]

        for p_dir in self.problems_dirs:
            p_file = p_dir / f"{problem_id}.json"
            if p_file.exists():
                try:
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        prompt = data.get("prompt", "")
                        self._prompt_cache[problem_id] = prompt
                        return prompt
                except Exception:
                    pass

        self._prompt_cache[problem_id] = ""
        return ""

    def _extract_text(self, record: Dict[str, Any]) -> str:
        code = str(record.get("code", ""))
        if self.include_prompt:
            prob_id = str(record.get("problem_id", ""))
            prompt = self.get_prompt(prob_id)
            if prompt:
                return f"Prompt: {prompt}\nCode:\n{code}"
        return code

    def _extract_dense_vector(self, record: Dict[str, Any]) -> np.ndarray:
        """Extract numerical and categorical features without leakage."""
        feats: List[float] = []

        # 1. Structural features
        feats.append(float(record.get("line", 1) or 1))
        feats.append(float(record.get("column", 1) or 1))
        code = str(record.get("code", ""))
        feats.append(float(len(code)))
        feats.append(float(len(code.splitlines())))

        # 2. Step type one-hot
        step_type = str(record.get("step_type", ""))
        for st in ALL_STEP_TYPES:
            feats.append(1.0 if step_type == st else 0.0)

        # 3. Mutation family affordances (one-hot multi-label)
        app_types = set(record.get("applicable_mutation_types", []) or [])
        for mt in ALL_MUTATION_FAMILIES:
            feats.append(1.0 if mt in app_types else 0.0)

        # 4. Raw execution observations
        n_mut = max(1, int(record.get("num_mutations", 1) or 1))
        n_pass = int(record.get("num_pass", 0) or 0)
        n_fail = int(record.get("num_fail", 0) or 0)
        n_rt = int(record.get("num_runtime_error", 0) or 0)

        feats.append(float(n_mut))
        feats.append(float(n_pass))
        feats.append(float(n_fail))
        feats.append(float(n_rt))
        feats.append(float(n_pass / n_mut))
        feats.append(float(n_fail / n_mut))
        feats.append(float(n_rt / n_mut))

        # 5. Exception types observed
        exc_set = set(record.get("exception_types", []) or [])
        for exc in ALL_EXCEPTION_TYPES:
            feats.append(1.0 if exc in exc_set else 0.0)

        return np.array(feats, dtype=np.float32)

    def fit(self, records: List[Dict[str, Any]]) -> "StepFeatureExtractor":
        """Fit TF-IDF vocabulary and dense normalizers on training records."""
        texts = [self._extract_text(r) for r in records]
        self.tfidf.fit(texts)

        dense_matrix = np.stack([self._extract_dense_vector(r) for r in records])
        self.dense_mean = dense_matrix.mean(axis=0)
        self.dense_std = dense_matrix.std(axis=0) + 1e-6
        self.is_fitted = True
        return self

    def transform(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """Transform records into composite feature matrix."""
        if not self.is_fitted or self.dense_mean is None or self.dense_std is None:
            raise RuntimeError("StepFeatureExtractor must be fitted before calling transform.")

        texts = [self._extract_text(r) for r in records]
        tfidf_features = self.tfidf.transform(texts).toarray().astype(np.float32)

        raw_dense = np.stack([self._extract_dense_vector(r) for r in records])
        norm_dense = (raw_dense - self.dense_mean) / self.dense_std

        return np.concatenate([tfidf_features, norm_dense], axis=1).astype(np.float32)

    def fit_transform(self, records: List[Dict[str, Any]]) -> np.ndarray:
        return self.fit(records).transform(records)

    def get_feature_dimension(self) -> int:
        if not self.is_fitted:
            raise RuntimeError("Extractor is not fitted.")
        dense_dim = 4 + len(ALL_STEP_TYPES) + len(ALL_MUTATION_FAMILIES) + 7 + len(ALL_EXCEPTION_TYPES)
        return len(self.tfidf.get_feature_names_out()) + dense_dim

    def save(self, filepath: Path) -> None:
        """Serialize extractor state to disk."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "max_tfidf_features": self.max_tfidf_features,
            "include_prompt": self.include_prompt,
            "tfidf": self.tfidf,
            "dense_mean": self.dense_mean,
            "dense_std": self.dense_std,
            "is_fitted": self.is_fitted,
        }
        joblib.dump(state, filepath)

    @classmethod
    def load(cls, filepath: Path) -> "StepFeatureExtractor":
        """Load serialized extractor from disk."""
        state = joblib.load(filepath)
        extractor = cls(
            max_tfidf_features=state["max_tfidf_features"],
            include_prompt=state["include_prompt"],
        )
        extractor.tfidf = state["tfidf"]
        extractor.dense_mean = state["dense_mean"]
        extractor.dense_std = state["dense_std"]
        extractor.is_fitted = state["is_fitted"]
        return extractor
