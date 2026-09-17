import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from partner_a.execution.harness import run_candidate

PROBLEMS_DIR = Path("data/evaluation/problems")
CANDIDATES_FILE = Path("data/evaluation/solutions/candidates.jsonl")
RESULTS_FILE = Path("data/evaluation/solutions/baseline_results.jsonl")


def main():
    problems = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in PROBLEMS_DIR.glob("eval_*.json")
    }

    candidates = [
        json.loads(line)
        for line in CANDIDATES_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    results = []

    for candidate in candidates:
        problem = problems[candidate["problem_id"]]

        execution = run_candidate(
            candidate["code"],
            problem["test_list"],
        )

        record = {
            "problem_id": candidate["problem_id"],
            "task_id": candidate["task_id"],
            "solution_id": candidate["solution_id"],
            "required_function": candidate["required_function"],
            "status": execution["status"],
            "stdout": execution["stdout"],
            "stderr": execution["stderr"],
            "returncode": execution["returncode"],
        }

        results.append(record)

        print(candidate["solution_id"], "->", execution["status"])

    RESULTS_FILE.write_text(
        "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in results
        )
        + "\n",
        encoding="utf-8",
    )

    counts = {}

    for result in results:
        status = result["status"]
        counts[status] = counts.get(status, 0) + 1

    print("\nBaseline summary:")

    for status, count in sorted(counts.items()):
        print(f"{status}: {count}")

    print(f"\nWrote {len(results)} results to {RESULTS_FILE}")


if __name__ == "__main__":
    main()