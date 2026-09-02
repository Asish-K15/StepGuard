from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "partner_a"
    / "evidence"
    / "validate_pilot_reproducibility.py"
)


def test_validator_exists():
    assert VALIDATOR.exists()


def test_reproducibility_validation_passes():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Pilot reproducibility validation: PASS" in result.stdout
    assert "Manifest consistency: PASS" in result.stdout
    assert "Evidence paths: PASS" in result.stdout
