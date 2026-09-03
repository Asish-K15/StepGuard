import json
from pathlib import Path

from partner_b.integration.pipeline import process_candidate


ROOT = Path(__file__).resolve().parents[2]

PROBLEMS_DIR = ROOT / "data" / "evaluation" / "problems"
CANDIDATES_PATH = ROOT / "data" / "evaluation" / "solutions" / "candidates.jsonl"
BASELINE_PATH = ROOT / "data" / "evaluation" / "solutions" / "baseline_results.jsonl"
OUTPUT_PATH = ROOT / "data" / "evaluation" / "mutations" / "mutation_records.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as file:
        return [json.loads(line) for line in file if line.strip()]


def main(
    candidates_path: Path = CANDIDATES_PATH,
    baseline_path: Path = BASELINE_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    candidates = load_jsonl(candidates_path)
    baseline_results = load_jsonl(baseline_path)

    passing_solution_ids = {
        record["solution_id"]
        for record in baseline_results
        if record["baseline_result"] == "PASS"
    }

    candidates_by_id = {
        candidate["solution_id"]: candidate
        for candidate in candidates
    }

    passing_candidates = [
        candidates_by_id[solution_id]
        for solution_id in passing_solution_ids
        if solution_id in candidates_by_id
    ]

    all_records = []

    for candidate in sorted(
        passing_candidates,
        key=lambda item: (item["problem_id"], item["solution_id"]),
    ):
        records = process_candidate(candidate)
        all_records.extend(records)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("=" * 60)
    print("StepGuard Evaluation Mutation Generation")
    print("=" * 60)
    print(f"Candidates generated : {len(candidates)}")
    print(f"Baseline PASS        : {len(passing_candidates)}")
    print(f"Mutation records     : {len(all_records)}")
    print(f"Output               : {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()