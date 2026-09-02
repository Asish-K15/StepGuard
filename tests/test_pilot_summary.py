import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "data" / "evidence" / "pilot_summary.json"


def load_summary():
    with SUMMARY.open(encoding="utf-8") as f:
        return json.load(f)


def test_summary_exists():
    assert SUMMARY.exists()


def test_summary_scope():
    summary = load_summary()
    scope = summary["scope"]

    assert scope["problem_count"] == 5
    assert scope["candidate_count"] == 25
    assert scope["baseline_pass_count"] == 25
    assert scope["baseline_pass_rate"] == 1.0


def test_summary_mutation_results():
    summary = load_summary()
    results = summary["mutation_results"]

    assert results["mutation_count"] == 99
    assert results["detected_count"] == 86
    assert results["undetected_count"] == 13
    assert results["detection_rate"] == 86 / 99


def test_summary_mutation_types():
    summary = load_summary()

    assert set(summary["mutation_types"]) == {
        "boolean_flip",
        "comparison_swap",
        "off_by_one",
    }


def test_summary_step_analysis():
    summary = load_summary()
    steps = summary["step_analysis"]

    assert steps["step_count"] == 77
    assert steps["fully_detected"] == 64
    assert steps["partially_detected"] == 8
    assert steps["undetected"] == 5


def test_summary_survivor_patterns():
    summary = load_summary()

    assert len(summary["survivor_patterns"]) == 2
