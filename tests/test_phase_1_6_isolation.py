"""
Isolation and immutability tests for StepGuard Stage 1.4 Phase 1.6.

Verifies:
- Frozen Phase 1.5 inputs and historical baseline artifacts are not modified.
- Pipeline executes in-process with zero subprocesses spawned.
- Output files are strictly confined to the designated directory.
- Overwrite protection fails fast when overwrite=False.
"""

import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
import pytest

from partner_b.evidence.phase_1_6 import compute_file_sha256, run_phase_1_6_pipeline


ROOT = Path(__file__).resolve().parents[1]
PHASE_1_5_EVIDENCE = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "evidence.jsonl"
PHASE_1_5_SUMMARY = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "summary.json"

FROZEN_BASELINE_PATHS = [
    ROOT / "data" / "evidence" / "step_evidence.jsonl",
    ROOT / "data" / "evidence" / "step_analysis.jsonl",
    ROOT / "data" / "mutations" / "mutation_execution_results.jsonl",
    ROOT / "data" / "solutions" / "baseline_results.jsonl",
    ROOT / "data" / "solutions" / "candidates.jsonl",
]


def test_frozen_source_files_remain_byte_identical_after_pipeline(tmp_path: Path):
    """Verify that source Phase 1.5 and historical baseline files are strictly unmodified."""
    pre_hashes = {
        PHASE_1_5_EVIDENCE: compute_file_sha256(PHASE_1_5_EVIDENCE),
        PHASE_1_5_SUMMARY: compute_file_sha256(PHASE_1_5_SUMMARY),
    }
    for p in FROZEN_BASELINE_PATHS:
        pre_hashes[p] = compute_file_sha256(p)

    # Run Phase 1.6 pipeline
    run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
    )

    # Verify post-run hashes
    for path, expected_hash in pre_hashes.items():
        actual_hash = compute_file_sha256(path)
        assert actual_hash == expected_hash, (
            f"File {path.name} was modified! Expected {expected_hash}, got {actual_hash}"
        )


def test_zero_subprocesses_spawned_during_phase_1_6(tmp_path: Path):
    """Verify that Phase 1.6 runs completely in-process with zero subprocess execution."""
    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        run_phase_1_6_pipeline(
            evidence_path=PHASE_1_5_EVIDENCE,
            phase_1_5_summary_path=PHASE_1_5_SUMMARY,
            output_dir=tmp_path,
        )
        assert mock_run.call_count == 0, f"Expected 0 subprocess.run calls, got {mock_run.call_count}"
        assert mock_popen.call_count == 0, f"Expected 0 subprocess.Popen calls, got {mock_popen.call_count}"


def test_overwrite_safety_fails_fast_when_overwrite_false(tmp_path: Path):
    """Verify that existing outputs are not silently overwritten when overwrite=False."""
    # First write succeeds
    run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
        overwrite=True,
    )

    # Second write with overwrite=False must fail
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        run_phase_1_6_pipeline(
            evidence_path=PHASE_1_5_EVIDENCE,
            phase_1_5_summary_path=PHASE_1_5_SUMMARY,
            output_dir=tmp_path,
            overwrite=False,
        )


def test_output_confined_strictly_to_designated_directory(tmp_path: Path):
    """Verify that all created files are strictly inside the target output directory."""
    target_dir = tmp_path / "custom_output"
    target_dir.mkdir(parents=True, exist_ok=True)

    a, s, m = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=target_dir,
    )

    assert a.parent.resolve() == target_dir.resolve()
    assert s.parent.resolve() == target_dir.resolve()
    assert m.parent.resolve() == target_dir.resolve()

    # Sibling directory check
    sibling_files = list(tmp_path.glob("*"))
    assert set(sibling_files) == {target_dir}
