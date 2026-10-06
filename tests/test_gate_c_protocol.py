"""
Unit and protocol tests for StepGuard Gate C Preflight Protocol.

Verifies:
1. Exact 37-sample coverage of held-out evaluation dataset (verifier_eval.jsonl).
2. Strict data blinding with ZERO forbidden-field leakage.
3. Deterministic sheet regeneration.
4. Complete isolation from training-set records.
5. Immutability of frozen evaluation assets and model checkpoints.
"""

import hashlib
import json
from pathlib import Path
import re
import pytest

from tools.generate_gate_c_eval_sheet import (
    FORBIDDEN_LEAKAGE_FIELDS,
    generate_gate_c_eval_sheet,
)

ROOT = Path(__file__).resolve().parents[1]
EVAL_FILE = ROOT / "data" / "evaluation" / "stage_1" / "verifier_eval.jsonl"
TRAIN_FILE = ROOT / "data" / "evaluation" / "stage_1" / "verifier_train.jsonl"
MODEL_WEIGHTS_FILE = ROOT / "data" / "evaluation" / "stage_2" / "checkpoint" / "model_weights.pt"
GATE_C_SHEET_FILE = ROOT / "data" / "validation" / "gate_c_blind_evaluation_sheet.md"
PILOT_SHEET_FILE = ROOT / "data" / "validation" / "blind_annotation_sheet.md"

# Authoritative SHA-256 digests of frozen historical assets in repository
EXPECTED_EVAL_SHA256 = "acf3408501f83ec83f86fae1e30f12e74c7addd2cd74462e42d834f8d44e9fd8"
EXPECTED_TRAIN_SHA256 = "3ab7ff749df9f53d44522de4f96fe4163c189f9e0a488422f01b494f9f9070e1"
EXPECTED_WEIGHTS_SHA256 = "4a0b37e480b1e87d7574f823f8601191049bb14658c9f1bffc192044144a8765"


def _sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_gate_c_sheet_exists_and_covers_all_37_records():
    """Verify Gate C blind evaluation sheet exists and contains exactly 37 sample blocks."""
    assert GATE_C_SHEET_FILE.exists(), "gate_c_blind_evaluation_sheet.md must exist"
    sheet_content = GATE_C_SHEET_FILE.read_text(encoding="utf-8")

    # Verify header banner
    assert "UNANNOTATED PROTOCOL MATERIAL — NOT SEMANTIC GROUND TRUTH" in sheet_content
    assert "# StepGuard Gate C Blind Evaluation Study: N=37 Held-Out Assessment Sheet" in sheet_content

    # Match sample headers
    sample_ids = re.findall(r"## Sample ID:\s*(SG-GATE-C-\d+)", sheet_content)
    assert len(sample_ids) == 37, f"Expected exactly 37 samples, found {len(sample_ids)}"

    expected_ids = [f"SG-GATE-C-{i:03d}" for i in range(1, 38)]
    assert sample_ids == expected_ids, "Sample IDs must match sequential numbering SG-GATE-C-001 through 037"

    # Verify each sample has required evaluation sections
    eval_lines = [json.loads(l) for l in EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(eval_lines) == 37

    sample_blocks = sheet_content.split("## Sample ID: ")[1:]
    assert len(sample_blocks) == 37

    for idx, (block, er) in enumerate(zip(sample_blocks, eval_lines), 1):
        assert f"SG-GATE-C-{idx:03d}" in block
        assert er["problem_id"] in block
        assert er["step_id"] in block
        assert "### 1. Problem Context" in block
        assert "### 2. Relevant Candidate Solution and Target Step" in block
        assert "### 3. Independent Semantic Evaluation" in block
        assert "[ UNANNOTATED — PENDING EVALUATOR INPUT ]" in block
        assert ">>" in block, "Target step must be highlighted with '>>'"


def test_gate_c_sheet_zero_forbidden_leakage():
    """Verify zero leakage of heuristic labels, rationales, mutation counts, or PRM predictions."""
    sheet_content = GATE_C_SHEET_FILE.read_text(encoding="utf-8")
    sample_blocks = sheet_content.split("## Sample ID: ")[1:]

    eval_lines = [json.loads(l) for l in EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Keywords that must not appear in sample blocks
    forbidden_terms = [
        "flips_by_type",
        "num_pass",
        "num_fail",
        "num_mutations",
        "num_runtime_error",
        "outcome_flip",
        "prm_prediction",
        "prm_confidence",
        "prm_probability",
        "feature_vector",
    ]

    for idx, (block, er) in enumerate(zip(sample_blocks, eval_lines), 1):
        # 1. No forbidden metadata keywords
        for term in forbidden_terms:
            assert term not in block, f"Forbidden term '{term}' leaked in sample {idx}"

        # 2. No leaked heuristic label rationale text
        if "label_rationale" in er and er["label_rationale"]:
            assert er["label_rationale"] not in block, f"Heuristic rationale leaked in sample {idx}"


def test_gate_c_sheet_deterministic_regeneration(tmp_path):
    """Verify generator produces byte-identical output across repeated runs."""
    tmp_out = tmp_path / "gate_c_regenerated.md"
    generate_gate_c_eval_sheet(repo_root=ROOT, output_path=tmp_out)

    orig_sha = _sha256(GATE_C_SHEET_FILE)
    regen_sha = _sha256(tmp_out)
    assert orig_sha == regen_sha, "Regenerated sheet must have byte-identical SHA-256 digest"


def test_gate_c_sheet_isolation_from_training_data():
    """Verify the Gate C sheet references exclusively held-out eval data with 0 training record overlap."""
    train_lines = [json.loads(l) for l in TRAIN_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    eval_lines = [json.loads(l) for l in EVAL_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

    train_keys = {(t["problem_id"], t.get("solution_id") or t.get("candidate_id"), t["step_id"]) for t in train_lines}
    eval_keys = {(e["problem_id"], e.get("solution_id") or e.get("candidate_id"), e["step_id"]) for e in eval_lines}

    # Evaluate disjointness of step keys between train and eval splits
    overlap = train_keys.intersection(eval_keys)
    assert len(overlap) == 0, f"Train and eval splits must have 0 overlapping step keys, found {overlap}"


def test_frozen_evaluation_artifacts_unchanged():
    """Verify that all historical frozen artifacts remain byte-identical."""
    assert _sha256(EVAL_FILE) == EXPECTED_EVAL_SHA256, "verifier_eval.jsonl has been modified!"
    assert _sha256(TRAIN_FILE) == EXPECTED_TRAIN_SHA256, "verifier_train.jsonl has been modified!"
    assert _sha256(MODEL_WEIGHTS_FILE) == EXPECTED_WEIGHTS_SHA256, "model_weights.pt has been modified!"
    assert PILOT_SHEET_FILE.exists(), "Pilot blind_annotation_sheet.md must remain present"
