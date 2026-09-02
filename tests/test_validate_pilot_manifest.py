from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "partner_a" / "evidence" / "validate_pilot_manifest.py"


def test_validator_exists():
    assert VALIDATOR.exists()


def test_validator_passes():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Pilot manifest validation: PASS" in result.stdout
    assert "Baseline candidates: 25" in result.stdout
    assert "Baseline PASS: 25" in result.stdout
    assert "Mutations: 99" in result.stdout
    assert "Detected: 86" in result.stdout
    assert "Undetected: 13" in result.stdout
    assert "Detection rate: 0.8687" in result.stdout
