"""
Tests for Phase 1.7 Process Isolation and Frozen Artifact Protection.
"""

from pathlib import Path
import pytest

from partner_b.evidence.phase_1_7 import run_phase_1_7_pipeline, compute_sha256


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_frozen_source_files_remain_byte_identical(repo_root: Path, tmp_path: Path):
    """Verify all prior-phase evidence and code remain completely untouched."""
    frozen_files = [
        repo_root / "data" / "evidence" / "stage_1_4_phase_1_5" / "evidence.jsonl",
        repo_root / "data" / "evidence" / "stage_1_4_phase_1_5" / "summary.json",
        repo_root / "data" / "evidence" / "stage_1_4_phase_1_6" / "analysis.jsonl",
        repo_root / "data" / "evidence" / "stage_1_4_phase_1_6" / "summary.json",
        repo_root / "data" / "evidence" / "stage_1_4_phase_1_6" / "manifest.json",
        repo_root / "shared" / "schema.py",
        repo_root / "partner_b" / "execution" / "tracer.py",
        repo_root / "partner_b" / "evidence" / "coverage.py",
        repo_root / "partner_b" / "evidence" / "phase_1_5.py",
        repo_root / "partner_b" / "evidence" / "phase_1_6.py",
    ]

    before_hashes = {p: compute_sha256(p) for p in frozen_files}

    # Run pipeline in a subfolder
    import shutil
    run_dir = tmp_path / "worktree"
    shutil.copytree(repo_root / "data" / "evidence", run_dir / "data" / "evidence")
    run_phase_1_7_pipeline(run_dir, overwrite=True)

    after_hashes = {p: compute_sha256(p) for p in frozen_files}

    for p in frozen_files:
        assert before_hashes[p] == after_hashes[p], f"Frozen file was modified: {p}"


def test_zero_subprocesses_spawned(monkeypatch, repo_root: Path, tmp_path: Path):
    """Verify zero subprocess calls occur during Phase 1.7 execution."""
    import subprocess

    def forbidden_call(*args, **kwargs):
        raise AssertionError("Subprocess execution is strictly forbidden in Phase 1.7!")

    monkeypatch.setattr(subprocess, "run", forbidden_call)
    monkeypatch.setattr(subprocess, "Popen", forbidden_call)
    monkeypatch.setattr(subprocess, "call", forbidden_call)
    monkeypatch.setattr(subprocess, "check_call", forbidden_call)
    monkeypatch.setattr(subprocess, "check_output", forbidden_call)

    import shutil
    run_dir = tmp_path / "worktree"
    shutil.copytree(repo_root / "data" / "evidence", run_dir / "data" / "evidence")

    # Should run with 0 errors without triggering subprocess
    res = run_phase_1_7_pipeline(run_dir, overwrite=True)
    assert res["status"] == "SUCCESS"


def test_overwrite_safety_fails_fast_when_overwrite_false(repo_root: Path, tmp_path: Path):
    """Verify pipeline fails fast if output artifacts already exist and overwrite=False."""
    import shutil
    run_dir = tmp_path / "worktree"
    shutil.copytree(repo_root / "data" / "evidence", run_dir / "data" / "evidence")

    # First run succeeds
    run_phase_1_7_pipeline(run_dir, overwrite=True)

    # Second run without overwrite=True must raise FileExistsError
    with pytest.raises(FileExistsError):
        run_phase_1_7_pipeline(run_dir, overwrite=False)


def test_output_confined_strictly_to_designated_directory(repo_root: Path, tmp_path: Path):
    """Verify pipeline writes strictly into data/evidence/stage_1_4_phase_1_7/."""
    import shutil
    run_dir = tmp_path / "worktree"
    shutil.copytree(repo_root / "data" / "evidence", run_dir / "data" / "evidence")

    res = run_phase_1_7_pipeline(run_dir, overwrite=True)

    output_dir = run_dir / "data" / "evidence" / "stage_1_4_phase_1_7"
    assert output_dir.exists()

    generated_files = {p.name for p in output_dir.iterdir()}
    assert generated_files == {"analysis.jsonl", "summary.json", "manifest.json"}
