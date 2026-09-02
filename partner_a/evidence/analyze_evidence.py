import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    ROOT
    / "data"
    / "evidence"
    / "step_evidence.jsonl"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "evidence"
    / "step_analysis.jsonl"
)


ALLOWED_RESULTS = {
    "PASS",
    "FAIL",
    "RUNTIME_ERROR",
}


def read_jsonl(path: Path) -> list[dict]:
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


def analyze(records: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for record in records:
        if record["mutation_result"] not in ALLOWED_RESULTS:
            raise ValueError(
                f"Unexpected mutation result: "
                f"{record['mutation_result']!r}"
            )

        key = (
            record["problem_id"],
            record["solution_id"],
            record["step_id"],
        )

        grouped[key].append(record)

    analysis = []

    for key in sorted(grouped):
        problem_id, solution_id, step_id = key
        mutations = grouped[key]

        counts = Counter(
            mutation["mutation_result"]
            for mutation in mutations
        )

        mutation_types = sorted(
            {
                mutation["mutation_type"]
                for mutation in mutations
            }
        )

        mutation_count = len(mutations)
        detected_count = (
            counts["FAIL"] + counts["RUNTIME_ERROR"]
        )
        undetected_count = counts["PASS"]

        detection_rate = (
            detected_count / mutation_count
            if mutation_count
            else 0.0
        )

        analysis.append(
            {
                "problem_id": problem_id,
                "solution_id": solution_id,
                "step_id": step_id,
                "mutation_count": mutation_count,
                "mutation_types": mutation_types,
                "results": {
                    "PASS": counts["PASS"],
                    "FAIL": counts["FAIL"],
                    "RUNTIME_ERROR": counts["RUNTIME_ERROR"],
                },
                "detected_count": detected_count,
                "undetected_count": undetected_count,
                "detection_rate": detection_rate,
            }
        )

    return analysis


def main() -> None:
    records = read_jsonl(INPUT_FILE)
    analysis = analyze(records)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        for record in analysis:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Input records : {len(records)}")
    print(f"Step records  : {len(analysis)}")
    print(f"Output        : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
