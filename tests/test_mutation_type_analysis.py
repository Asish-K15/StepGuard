import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "mutation_type_analysis.json"


def load_report():
    with REPORT.open(encoding="utf-8") as f:
        return json.load(f)


def test_report_exists():
    assert REPORT.exists()


def test_total_mutation_count():
    report = load_report()

    assert report["mutation_count"] == 99


def test_mutation_type_counts():
    report = load_report()
    by_type = report["by_mutation_type"]

    assert set(by_type) == {
        "boolean_flip",
        "comparison_swap",
        "off_by_one",
    }

    assert by_type["boolean_flip"]["mutation_count"] == 11
    assert by_type["comparison_swap"]["mutation_count"] == 74
    assert by_type["off_by_one"]["mutation_count"] == 14


def test_mutation_type_outcomes():
    report = load_report()
    by_type = report["by_mutation_type"]

    assert by_type["boolean_flip"]["detected_count"] == 3
    assert by_type["boolean_flip"]["undetected_count"] == 8

    assert by_type["comparison_swap"]["detected_count"] == 69
    assert by_type["comparison_swap"]["undetected_count"] == 5

    assert by_type["off_by_one"]["detected_count"] == 14
    assert by_type["off_by_one"]["undetected_count"] == 0


def test_mutation_type_detection_rates():
    report = load_report()
    by_type = report["by_mutation_type"]

    assert by_type["boolean_flip"]["detection_rate"] == 3 / 11
    assert by_type["comparison_swap"]["detection_rate"] == 69 / 74
    assert by_type["off_by_one"]["detection_rate"] == 1.0


def test_type_counts_reconcile():
    report = load_report()
    by_type = report["by_mutation_type"]

    assert sum(
        item["mutation_count"] for item in by_type.values()
    ) == report["mutation_count"]

    assert sum(
        item["detected_count"] for item in by_type.values()
    ) == 86

    assert sum(
        item["undetected_count"] for item in by_type.values()
    ) == 13
