from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "run_pilot_validation.py"


def test_runner_exists():
    assert RUNNER.exists()


def test_runner_passes():
    result = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Manifest consistency: PASS" in result.stdout
    assert "Evidence paths: PASS" in result.stdout
    assert "Reproducibility: PASS" in result.stdout
    assert "StepGuard pilot validation: PASS" in result.stdout
