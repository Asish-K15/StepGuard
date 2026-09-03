import json
from pathlib import Path

from partner_a.execution.harness import run_candidate


ROOT = Path(__file__).resolve().parents[2]

PROBLEMS_DIR = ROOT / "data" / "evaluation" / "problems"
CANDIDATES_PATH = ROOT / "data" / "evaluation" / "solutions" / "candidates.jsonl"
OUTPUT_PATH = ROOT / "data" / "evaluation" / "solutions" / "baseline_results.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(
    problems_dir: Path = PROBLEMS_DIR,
    candidates_path: Path = CANDIDATES_PATH,
    output_path: Path = OUTPUT_PATH,
):
    problems = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in problems_dir.glob("*.json")
    }

    candidates = load_jsonl(candidates_path)

    results = []

    for candidate in candidates:
        problem_id = candidate["problem_id"]

        if problem_id not in problems:
            result = {
                "status": "HARNESS_ERROR",
                "stdout": "",
                "stderr": f"unknown problem: {problem_id}",
                "returncode": None,
            }
        else:
            result = run_candidate(
                candidate["code"],
                problems[problem_id]["test_list"],
            )

        record = {
            "problem_id": problem_id,
            "solution_id": candidate["solution_id"],
            "solution_code": candidate["code"],
            "baseline_result": result["status"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "returncode": result["returncode"],
        }

        results.append(record)

        print(
            candidate["solution_id"],
            "->",
            result["status"],
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in results
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"Wrote {len(results)} baseline results to {output_path}"
    )


if __name__ == "__main__":
    main()