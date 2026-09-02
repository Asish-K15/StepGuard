from pathlib import Path
import json
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
        "Schema version: 1",
        "Status: exploratory_pilot",
        "Generalization: not_supported_beyond_evaluated_dataset",
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


def test_status_json_output():
    result = subprocess.run(
        [sys.executable, str(STATUS), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    data = json.loads(result.stdout)

    assert data == {
        "baseline_pass_rate": 1.0,
        "candidates": 25,
        "detected": 86,
        "detection_rate": 0.8686868686868687,
        "generalization": "not_supported_beyond_evaluated_dataset",
        "mutations": 99,
        "problems": 5,
        "schema_version": 1,
        "status": "exploratory_pilot",
        "step_groups": 77,
        "survivor_patterns": 2,
        "undetected": 13,
    }


def test_status_validate_mode():
    result = subprocess.run(
        [sys.executable, str(STATUS), "--validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "StepGuard pilot validation: PASS" in result.stdout
    assert "Problems: 5" in result.stdout
    assert "Detection rate: 0.8687" in result.stdout


def test_status_validate_json_output():
    result = subprocess.run(
        [sys.executable, str(STATUS), "--validate", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""

    data = json.loads(result.stdout)

    assert data["schema_version"] == 1
    assert data["problems"] == 5
    assert data["candidates"] == 25
    assert data["mutations"] == 99
    assert data["detected"] == 86
    assert data["undetected"] == 13
    assert data["step_groups"] == 77
    assert data["survivor_patterns"] == 2
    assert data["status"] == "exploratory_pilot"
    assert data["generalization"] == "not_supported_beyond_evaluated_dataset"


def test_status_schema_version():
    result = subprocess.run(
        [sys.executable, str(STATUS), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    data = json.loads(result.stdout)

    assert data["schema_version"] == 1


def test_status_human_schema_version():
    result = subprocess.run(
        [sys.executable, str(STATUS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Schema version: 1" in result.stdout


def test_status_interpretation_metadata():
    result = subprocess.run(
        [sys.executable, str(STATUS)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Status: exploratory_pilot" in result.stdout
    assert "Generalization: not_supported_beyond_evaluated_dataset" in result.stdout


def test_status_json_interpretation_metadata():
    result = subprocess.run(
        [sys.executable, str(STATUS), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0

    data = json.loads(result.stdout)

    assert data["status"] == "exploratory_pilot"
    assert data["generalization"] == "not_supported_beyond_evaluated_dataset"
