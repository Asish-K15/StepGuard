"""
Tests for Phase 1.7 Deterministic Execution, Fingerprinting, and Stable Ordering.
"""

from pathlib import Path
import json
import pytest

from partner_b.evidence.phase_1_7 import run_phase_1_7_pipeline
from partner_b.evidence.phase_1_7_schema import (
    compute_candidate_lineage_fingerprint,
    compute_contract_relationship_fingerprint,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_repeated_pipeline_runs_produce_byte_identical_outputs(repo_root: Path, tmp_path: Path):
    """Verify executing pipeline twice on the same inputs produces byte-identical outputs."""
    # Run 1 in tmp_path / run1
    run1_dir = tmp_path / "run1"
    # Copy data/evidence into run1_dir
    import shutil
    shutil.copytree(repo_root / "data" / "evidence", run1_dir / "data" / "evidence")

    res1 = run_phase_1_7_pipeline(run1_dir, overwrite=True)

    # Run 2 in tmp_path / run2
    run2_dir = tmp_path / "run2"
    shutil.copytree(repo_root / "data" / "evidence", run2_dir / "data" / "evidence")

    res2 = run_phase_1_7_pipeline(run2_dir, overwrite=True)

    for artifact in ("analysis", "summary", "manifest"):
        sha1 = res1["output_artifacts"][artifact]["sha256"]
        sha2 = res2["output_artifacts"][artifact]["sha256"]
        assert sha1 == sha2, f"Hash mismatch for {artifact}: {sha1} != {sha2}"

        path1 = Path(res1["output_artifacts"][artifact]["path"])
        path2 = Path(res2["output_artifacts"][artifact]["path"])
        assert path1.read_bytes() == path2.read_bytes(), f"Byte mismatch for {artifact}"


def test_lineage_fingerprint_sensitivity():
    """Verify lineage fingerprint changes when any relationship or telemetry field changes."""
    base_kwargs = {
        "problem_id": "prob_1",
        "candidate_id": "cand_1",
        "test_suite_id": "suite_1",
        "phase_1_5_fingerprint": "fp15",
        "phase_1_6_fingerprint": "fp16",
        "relationships": {
            "p1": {"status": "DIRECTLY_LINKED", "target_role": "evidence", "evidence_type": "jsonl"}
        },
        "telemetry_provenance": {"baseline_outcome": "PASS", "total_steps": 5},
        "legacy_solution_id": "sol_1",
        "identity_mapped": True,
    }

    fp_base = compute_candidate_lineage_fingerprint(**base_kwargs)

    # Change relationship status
    modified_kwargs = dict(base_kwargs)
    modified_kwargs["relationships"] = {
        "p1": {"status": "AMBIGUOUS", "target_role": "evidence", "evidence_type": "jsonl"}
    }
    fp_mod = compute_candidate_lineage_fingerprint(**modified_kwargs)
    assert fp_base != fp_mod

    # Change telemetry
    modified_kwargs2 = dict(base_kwargs)
    modified_kwargs2["telemetry_provenance"] = {"baseline_outcome": "FAIL", "total_steps": 5}
    fp_mod2 = compute_candidate_lineage_fingerprint(**modified_kwargs2)
    assert fp_base != fp_mod2


def test_stable_key_ordering_in_records(repo_root: Path, tmp_path: Path):
    """Verify serialized JSON lines have stably sorted keys."""
    import shutil
    run_dir = tmp_path / "run"
    shutil.copytree(repo_root / "data" / "evidence", run_dir / "data" / "evidence")

    res = run_phase_1_7_pipeline(run_dir, overwrite=True)
    analysis_path = Path(res["output_artifacts"]["analysis"]["path"])

    with open(analysis_path, "r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            keys = list(rec.keys())
            assert keys == sorted(keys), f"Keys not sorted: {keys}"
