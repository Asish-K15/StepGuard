"""Neural Process Reward Model (PRM) architecture and high-level verifier for StepGuard.

Implements StepGuardPRMNet (a lightweight deep neural classifier) and StepGuardPRM
(the end-to-end verifier wrapping feature extraction, training, checkpointing, and inference).
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from partner_a.verifier.features import StepFeatureExtractor

LABEL_MAP = {"uncertain": 0, "correct": 1}
INV_LABEL_MAP = {0: "uncertain", 1: "correct"}


class StepGuardPRMNet(nn.Module):
    """Lightweight 3-layer neural Process Reward Model network.

    Maps composite step semantic & execution evidence feature vectors to
    unnormalized step verification logits [uncertain_logit, correct_logit].
    """

    def __init__(
        self,
        in_features: int,
        hidden_dim: int = 32,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        mid_dim = max(16, hidden_dim // 2)
        self.net = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, mid_dim),
            nn.LayerNorm(mid_dim),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(mid_dim, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class StepGuardPRM:
    """End-to-end StepGuard Process Reward Model verifier."""

    def __init__(
        self,
        hidden_dim: int = 32,
        dropout: float = 0.2,
        max_tfidf_features: int = 48,
        include_prompt: bool = True,
        device: str = "cpu",
    ) -> None:
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.max_tfidf_features = max_tfidf_features
        self.include_prompt = include_prompt
        self.device = torch.device(device if torch.cuda.is_available() and device.startswith("cuda") else "cpu")

        self.extractor = StepFeatureExtractor(
            max_tfidf_features=max_tfidf_features,
            include_prompt=include_prompt,
        )
        self.model: Optional[StepGuardPRMNet] = None
        self.training_history: List[Dict[str, float]] = []

    def fit(
        self,
        records: List[Dict[str, Any]],
        epochs: int = 80,
        lr: float = 0.005,
        batch_size: int = 32,
        weight_decay: float = 1e-4,
        seed: int = 42,
    ) -> "StepGuardPRM":
        """Train the PRM neural network deterministically on step records."""
        # Set seeds for complete determinism
        torch.manual_seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        # 1. Feature extraction
        X = self.extractor.fit_transform(records)
        y = np.array([LABEL_MAP[r["label"]] for r in records], dtype=np.int64)

        in_features = X.shape[1]
        self.model = StepGuardPRMNet(
            in_features=in_features,
            hidden_dim=self.hidden_dim,
            dropout=self.dropout,
        ).to(self.device)

        # 2. Dataset & DataLoader
        dataset = TensorDataset(
            torch.tensor(X, dtype=torch.float32),
            torch.tensor(y, dtype=torch.long),
        )
        # Using a deterministic generator for DataLoader shuffling
        gen = torch.Generator()
        gen.manual_seed(seed)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=gen)

        # 3. Optimizer & Criterion
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=weight_decay)
        criterion = nn.CrossEntropyLoss()

        self.training_history = []
        for epoch in range(1, epochs + 1):
            self.model.train()
            epoch_loss = 0.0
            correct_count = 0
            total_count = 0

            for batch_x, batch_y in loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                optimizer.zero_grad()
                logits = self.model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()

                epoch_loss += loss.item() * batch_x.size(0)
                preds = logits.argmax(dim=1)
                correct_count += (preds == batch_y).sum().item()
                total_count += batch_x.size(0)

            avg_loss = epoch_loss / max(1, total_count)
            train_acc = correct_count / max(1, total_count)
            self.training_history.append({
                "epoch": epoch,
                "loss": round(avg_loss, 5),
                "accuracy": round(train_acc, 4),
            })

        return self

    def predict_proba(self, records: List[Dict[str, Any]]) -> np.ndarray:
        """Compute softmax probability distribution [p(uncertain), p(correct)]."""
        if self.model is None or not self.extractor.is_fitted:
            raise RuntimeError("Model and extractor must be fitted before predict_proba.")

        X = self.extractor.transform(records)
        self.model.eval()
        with torch.no_grad():
            t_x = torch.tensor(X, dtype=torch.float32).to(self.device)
            logits = self.model(t_x)
            probs = torch.softmax(logits, dim=1).cpu().numpy()
        return probs

    def predict(self, records: List[Dict[str, Any]]) -> List[str]:
        """Predict discrete class string labels ('correct' or 'uncertain')."""
        probs = self.predict_proba(records)
        preds = np.argmax(probs, axis=1)
        return [INV_LABEL_MAP[int(p)] for p in preds]

    def score_step(self, record: Dict[str, Any]) -> float:
        """Score a single step with P(correct) Process Reward confidence."""
        probs = self.predict_proba([record])
        return float(probs[0, 1])

    def save_checkpoint(self, checkpoint_dir: Union[str, Path]) -> Path:
        """Save model weights, extractor, and config to directory."""
        ckpt_path = Path(checkpoint_dir)
        ckpt_path.mkdir(parents=True, exist_ok=True)

        if self.model is None or not self.extractor.is_fitted:
            raise RuntimeError("Cannot save unfitted StepGuardPRM.")

        # Save model weights
        weights_path = ckpt_path / "model_weights.pt"
        torch.save(self.model.state_dict(), weights_path)

        # Save feature extractor
        extractor_path = ckpt_path / "extractor.joblib"
        self.extractor.save(extractor_path)

        # Save config & metadata
        config = {
            "model_type": "StepGuardPRMNet",
            "in_features": self.extractor.get_feature_dimension(),
            "hidden_dim": self.hidden_dim,
            "dropout": self.dropout,
            "max_tfidf_features": self.max_tfidf_features,
            "include_prompt": self.include_prompt,
            "training_epochs": len(self.training_history),
            "final_train_loss": self.training_history[-1]["loss"] if self.training_history else None,
            "final_train_acc": self.training_history[-1]["accuracy"] if self.training_history else None,
        }
        with open(ckpt_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return ckpt_path

    @classmethod
    def load_checkpoint(cls, checkpoint_dir: Union[str, Path], device: str = "cpu") -> "StepGuardPRM":
        """Load fitted StepGuardPRM from checkpoint directory."""
        ckpt_path = Path(checkpoint_dir)
        config_path = ckpt_path / "config.json"
        weights_path = ckpt_path / "model_weights.pt"
        extractor_path = ckpt_path / "extractor.joblib"

        if not (config_path.exists() and weights_path.exists() and extractor_path.exists()):
            raise FileNotFoundError(f"Incomplete checkpoint in {ckpt_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        prm = cls(
            hidden_dim=config["hidden_dim"],
            dropout=config["dropout"],
            max_tfidf_features=config["max_tfidf_features"],
            include_prompt=config["include_prompt"],
            device=device,
        )
        prm.extractor = StepFeatureExtractor.load(extractor_path)

        in_features = config["in_features"]
        prm.model = StepGuardPRMNet(
            in_features=in_features,
            hidden_dim=config["hidden_dim"],
            dropout=config["dropout"],
        ).to(prm.device)
        state_dict = torch.load(weights_path, map_location=prm.device, weights_only=True)
        prm.model.load_state_dict(state_dict)
        prm.model.eval()

        return prm
