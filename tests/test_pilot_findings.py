import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "pilot_findings.json"


def load_report():
    with REPORT.open(encoding="utf-8") as f:
        return json.load(f)


def test_report_exists():
    assert REPORT.exists()


def test_pilot_totals():
    report = load_report()
    pilot = report["pilot"]

    assert pilot["problem_count"] == 5
    assert pilot["candidate_count"] == 25
    assert pilot["baseline_pass_count"] == 25
    assert pilot["baseline_pass_rate"] == 1.0
    assert pilot["mutation_count"] == 99
    assert pilot["detected_count"] == 86
    assert pilot["undetected_count"] == 13
    assert pilot["detection_rate"] == 86 / 99


def test_mutation_type_totals():
    report = load_report()

    assert report["mutation_types"] == {
        "boolean_flip": 11,
        "comparison_swap": 74,
        "off_by_one": 14,
    }


def test_problem_totals():
    report = load_report()
    problems = report["by_problem"]

    assert set(problems) == {
        "mbpp_001",
        "mbpp_002",
        "mbpp_003",
        "mbpp_004",
        "mbpp_005",
    }

    assert problems["mbpp_001"]["mutation_count"] == 13
    assert problems["mbpp_002"]["mutation_count"] == 20
    assert problems["mbpp_003"]["mutation_count"] == 30
    assert problems["mbpp_004"]["mutation_count"] == 26
    assert problems["mbpp_005"]["mutation_count"] == 10

    assert problems["mbpp_001"]["detection_rate"] == 1.0
    assert problems["mbpp_002"]["detection_rate"] == 1.0
    assert problems["mbpp_003"]["detection_rate"] == 25 / 30
    assert problems["mbpp_004"]["detection_rate"] == 18 / 26
    assert problems["mbpp_005"]["detection_rate"] == 1.0


def test_step_summary():
    report = load_report()
    steps = report["step_analysis"]

    assert steps["step_count"] == 77
    assert steps["fully_detected"] == 64
    assert steps["partially_detected"] == 8
    assert steps["undetected"] == 5


def test_undetected_steps_are_mbpp_003_block_08():
    report = load_report()
    steps = report["step_analysis"]["undetected_steps"]

    assert len(steps) == 5

    assert {
        (step["problem_id"], step["step_id"])
        for step in steps
    } == {
        ("mbpp_003", "block_08"),
    }

    assert {step["solution_id"] for step in steps} == {
        "mbpp_003_sol_001",
        "mbpp_003_sol_002",
        "mbpp_003_sol_003",
        "mbpp_003_sol_004",
        "mbpp_003_sol_005",
    }

    assert all(step["detection_rate"] == 0.0 for step in steps)


def test_partial_steps_count():
    report = load_report()
    partial = report["step_analysis"]["partial_steps"]

    assert len(partial) == 8
    assert all(
        0.0 < step["detection_rate"] < 1.0
        for step in partial
    )
