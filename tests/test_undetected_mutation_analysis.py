import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "undetected_mutation_analysis.json"


def load_report():
    with REPORT.open(encoding="utf-8") as f:
        return json.load(f)


def test_report_exists():
    assert REPORT.exists()


def test_undetected_total():
    report = load_report()
    assert report["undetected_count"] == 13
    assert report["problems_with_undetected_mutations"] == 2


def test_mbpp_003_pattern():
    report = load_report()
    data = report["by_problem"]["mbpp_003"]

    assert data["mutation_count"] == 5
    assert data["mutation_types"] == {"comparison_swap": 5}
    assert data["steps"] == ["block_08"]
    assert data["operator_changes"] == ["==->!="]
    assert data["locations"] == ["line_12"]
    assert data["solution_count"] == 5


def test_mbpp_004_pattern():
    report = load_report()
    data = report["by_problem"]["mbpp_004"]

    assert data["mutation_count"] == 8
    assert data["mutation_types"] == {"boolean_flip": 8}
    assert data["steps"] == ["block_05", "func_01"]
    assert data["operator_changes"] == ["or->and"]
    assert data["locations"] == [
        "line_10",
        "line_11",
        "line_9",
    ]
    assert data["solution_count"] == 4


def test_record_count_matches_summary():
    report = load_report()

    assert len(report["records"]) == report["undetected_count"]


def test_records_are_all_undetected_patterns():
    report = load_report()

    for record in report["records"]:
        assert record["problem_id"] in {"mbpp_003", "mbpp_004"}
        assert record["mutation_type"] in {
            "comparison_swap",
            "boolean_flip",
        }
        assert record["original_operator"] != record["mutated_operator"]


def test_problem_counts_reconcile():
    report = load_report()

    assert sum(
        data["mutation_count"]
        for data in report["by_problem"].values()
    ) == report["undetected_count"]

    assert sum(
        data["solution_count"]
        for data in report["by_problem"].values()
    ) == 9
