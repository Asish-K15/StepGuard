from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from partner_a.execution.harness import run_candidate
import json
from collections import Counter

problems_dir = PROJECT_ROOT / "data/evaluation/problems"
mutations_path = PROJECT_ROOT / "data/evaluation/mutations/mutation_records_passing.jsonl"
results_path = PROJECT_ROOT / "data/evaluation/mutations/mutation_execution_results_passing.jsonl"

problems = {
    path.stem: json.loads(path.read_text(encoding="utf-8"))
    for path in problems_dir.glob("eval_*.json")
}

mutations = [
    json.loads(line)
    for line in mutations_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

execution_results = []

for index, mutation in enumerate(mutations, start=1):
    problem_id = mutation["problem_id"]
    problem = problems.get(problem_id)

    if problem is None:
        result = {
            "status": "HARNESS_ERROR",
            "stdout": "",
            "stderr": f"Unknown problem: {problem_id}",
            "returncode": None,
        }
    else:
        result = run_candidate(
            mutation["mutated_code"],
            problem["test_list"],
        )

    execution_record = {
        **mutation,
        "mutation_result": result["status"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "returncode": result["returncode"],
    }

    execution_results.append(execution_record)

    print(
        f"[{index}/{len(mutations)}] "
        f"{mutation['solution_id']} "
        f"{mutation['mutation_type']} -> "
        f"{result['status']}"
    )

results_path.write_text(
    "\n".join(
        json.dumps(record, ensure_ascii=False)
        for record in execution_results
    ) + "\n",
    encoding="utf-8",
)

counts = Counter(record["mutation_result"] for record in execution_results)

print("\n" + "=" * 50)
print("Evaluation Mutation Execution Summary")
print("=" * 50)

for status, count in sorted(counts.items()):
    print(f"{status}: {count}")

print(f"Total executed: {len(execution_results)}")
print(f"Output: {results_path}")
