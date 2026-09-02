import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_FILE = ROOT / "data" / "evidence" / "step_evidence.jsonl"


def load_records():
    with EVIDENCE_FILE.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_evidence_record_count():
    records = load_records()

    assert len(records) == 99


def test_all_execution_outcomes_are_valid():
    records = load_records()

    allowed = {
        "PASS",
        "FAIL",
        "RUNTIME_ERROR",
    }

    for record in records:
        assert record["mutation_result"] in allowed


def test_expected_outcome_counts():
    records = load_records()

    counts = {
        "PASS": 0,
        "FAIL": 0,
        "RUNTIME_ERROR": 0,
    }

    for record in records:
        counts[record["mutation_result"]] += 1

    assert counts["FAIL"] == 67
    assert counts["RUNTIME_ERROR"] == 19
    assert counts["PASS"] == 13


def test_required_fields_exist():
    records = load_records()

    required = {
        "problem_id",
        "solution_id",
        "step_id",
        "mutation_type",
        "original_code",
        "mutated_code",
        "changed",
        "mutation_result",
        "stdout",
        "stderr",
        "returncode",
    }

    for record in records:
        assert required.issubset(record.keys())


def test_traceability_fields_are_not_empty():
    records = load_records()

    for record in records:
        assert record["problem_id"]
        assert record["solution_id"]
        assert record["step_id"]
        assert record["mutation_type"]


def test_mutated_records_are_changed():
    records = load_records()

    for record in records:
        assert record["changed"] is True
        assert record["original_code"] != record["mutated_code"]