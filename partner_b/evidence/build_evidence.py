"""
Build the StepGuard Stage 0A step-level evidence dataset.

Input:
    data/mutations/mutation_execution_results.jsonl

Output:
    data/evidence/step_evidence.jsonl

Each evidence record preserves:
    - problem/solution identity
    - decomposition step identity
    - mutation metadata
    - original and mutated program
    - execution-grounded mutation outcome
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "data"
    / "mutations"
    / "mutation_execution_results.jsonl"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "evidence"
    / "step_evidence.jsonl"
)


REQUIRED_FIELDS = {
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


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSON Lines file."""

    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {path}"
                ) from exc

    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write records as JSON Lines."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def validate_execution_record(record: dict) -> None:
    """Validate that an A-side execution record has the expected fields."""

    missing = REQUIRED_FIELDS - record.keys()

    if missing:
        raise ValueError(
            f"Missing fields for "
            f"{record.get('solution_id', '<unknown>')}: "
            f"{sorted(missing)}"
        )

    allowed_results = {
        "PASS",
        "FAIL",
        "RUNTIME_ERROR",
    }

    if record["mutation_result"] not in allowed_results:
        raise ValueError(
            f"Unexpected mutation_result "
            f"{record['mutation_result']!r} for "
            f"{record['solution_id']}"
        )


def build_evidence_record(record: dict) -> dict:
    """
    Convert an A-side mutation execution record into a
    step-level evidence record.

    The execution outcome is retained exactly as:
        PASS
        FAIL
        RUNTIME_ERROR
    """

    return {
        "problem_id": record["problem_id"],
        "solution_id": record["solution_id"],
        "step_id": record["step_id"],
        "mutation_type": record["mutation_type"],
        "original_code": record["original_code"],
        "mutated_code": record["mutated_code"],
        "changed": record["changed"],
        "original_operator": record.get("original_operator"),
        "mutated_operator": record.get("mutated_operator"),
        "line": record.get("line"),
        "column": record.get("column"),
        "mutation_result": record["mutation_result"],
        "stdout": record["stdout"],
        "stderr": record["stderr"],
        "returncode": record["returncode"],
    }


def main() -> None:
    execution_records = read_jsonl(INPUT_FILE)

    evidence_records = []

    for record in execution_records:
        validate_execution_record(record)
        evidence_records.append(
            build_evidence_record(record)
        )

    write_jsonl(
        OUTPUT_FILE,
        evidence_records,
    )

    result_counts = {
        "PASS": 0,
        "FAIL": 0,
        "RUNTIME_ERROR": 0,
    }

    for record in evidence_records:
        result_counts[record["mutation_result"]] += 1

    print("=" * 60)
    print("StepGuard Stage 0A - Step-Level Evidence")
    print("=" * 60)
    print(f"Execution records : {len(execution_records)}")
    print(f"Evidence records  : {len(evidence_records)}")
    print(f"FAIL              : {result_counts['FAIL']}")
    print(f"RUNTIME_ERROR     : {result_counts['RUNTIME_ERROR']}")
    print(f"PASS              : {result_counts['PASS']}")
    print(f"Output            : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()