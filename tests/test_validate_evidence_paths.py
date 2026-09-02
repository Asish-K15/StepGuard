from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "partner_a" / "evidence" / "validate_evidence_paths.py"


def test_validator_exists():
    assert VALIDATOR.exists()


def test_evidence_paths_pass():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Evidence path validation: PASS" in result.stdout
    assert "Evidence artifacts checked: 10" in result.stdout

    expected_paths = [
        "mutation_execution_results",
        "step_evidence",
        "step_analysis",
        "pilot_findings",
        "mutation_type_analysis",
        "undetected_mutation_analysis",
        "survivor_classification",
        "pilot_summary",
        "pilot_report",
        "pilot_limitations",
    ]

    for name in expected_paths:
        assert f"Present: {name}" in result.stdout
