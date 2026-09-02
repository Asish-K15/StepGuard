import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EVIDENCE_FILE = ROOT / "data" / "evidence" / "step_evidence.jsonl"
ANALYSIS_FILE = ROOT / "data" / "evidence" / "step_analysis.jsonl"


def load_jsonl(path):
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def test_step_analysis_record_count():
    records = load_jsonl(ANALYSIS_FILE)
    assert len(records) == 77


def test_step_analysis_has_unique_step_keys():
    records = load_jsonl(ANALYSIS_FILE)

    keys = [
        (record["problem_id"], record["solution_id"], record["step_id"])
        for record in records
    ]

    assert len(keys) == len(set(keys))


def test_step_analysis_required_fields_exist():
    records = load_jsonl(ANALYSIS_FILE)

    required = {
        "problem_id",
        "solution_id",
        "step_id",
        "mutation_count",
        "mutation_types",
        "results",
        "detected_count",
        "undetected_count",
        "detection_rate",
    }

    for record in records:
        assert required.issubset(record.keys())


def test_step_analysis_counts_match_mutations():
    evidence = load_jsonl(EVIDENCE_FILE)
    analysis = load_jsonl(ANALYSIS_FILE)

    expected = {}

    for record in evidence:
        key = (
            record["problem_id"],
            record["solution_id"],
            record["step_id"],
        )

        expected.setdefault(
            key,
            {
                "mutation_count": 0,
                "PASS": 0,
                "FAIL": 0,
                "RUNTIME_ERROR": 0,
            },
        )

        expected[key]["mutation_count"] += 1
        expected[key][record["mutation_result"]] += 1

    for record in analysis:
        key = (
            record["problem_id"],
            record["solution_id"],
            record["step_id"],
        )

        actual = expected[key]

        assert record["mutation_count"] == actual["mutation_count"]

        for result in ("PASS", "FAIL", "RUNTIME_ERROR"):
            assert record["results"][result] == actual[result]


def test_detected_and_undetected_counts_are_consistent():
    records = load_jsonl(ANALYSIS_FILE)

    for record in records:
        results = record["results"]

        assert record["detected_count"] == (
            results["FAIL"] + results["RUNTIME_ERROR"]
        )

        assert record["undetected_count"] == results["PASS"]

        assert (
            record["detected_count"] + record["undetected_count"]
            == record["mutation_count"]
        )


def test_detection_rates_are_consistent():
    records = load_jsonl(ANALYSIS_FILE)

    for record in records:
        expected_rate = (
            record["detected_count"] / record["mutation_count"]
        )

        assert record["detection_rate"] == expected_rate
        assert 0.0 <= record["detection_rate"] <= 1.0
