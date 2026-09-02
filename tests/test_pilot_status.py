from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "pilot_status.py"


def test_status_script_exists():
    assert STATUS.exists()


def test_status_output():
    result = subprocess.run(
        [sys.executable, str(STATUS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    expected = [
        "Problems: 5",
        "Candidates: 25",
        "Baseline pass rate: 1.0000",
        "Mutations: 99",
        "Detected: 86",
        "Undetected: 13",
        "Detection rate: 0.8687",
        "Step groups: 77",
        "Survivor patterns: 2",
    ]

    for line in expected:
        assert line in result.stdout
