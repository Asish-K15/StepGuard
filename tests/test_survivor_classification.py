import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "survivor_classification.json"


def load_report():
    with REPORT.open(encoding="utf-8") as f:
        return json.load(f)


def test_report_exists():
    assert REPORT.exists()


def test_classification_count():
    report = load_report()
    assert len(report["classifications"]) == 2


def test_mbpp_003_classification():
    report = load_report()
    item = next(
        x for x in report["classifications"]
        if x["problem_id"] == "mbpp_003"
    )

    assert item["mutation_type"] == "comparison_swap"
    assert item["operator_change"] == "==->!="
    assert item["location"] == "block_08"
    assert item["line"] == 12
    assert item["solution_count"] == 5


def test_mbpp_004_classification():
    report = load_report()
    item = next(
        x for x in report["classifications"]
        if x["problem_id"] == "mbpp_004"
    )

    assert item["mutation_type"] == "boolean_flip"
    assert item["operator_change"] == "or->and"
    assert item["locations"] == ["block_05", "func_01"]
    assert item["lines"] == [9, 10, 11]
    assert item["solution_count"] == 4


def test_classifications_have_observations():
    report = load_report()

    for item in report["classifications"]:
        assert item["observation"]
        assert isinstance(item["observation"], str)


def test_classified_solution_counts():
    report = load_report()

    counts = {
        item["problem_id"]: item["solution_count"]
        for item in report["classifications"]
    }

    assert counts == {
        "mbpp_003": 5,
        "mbpp_004": 4,
    }
