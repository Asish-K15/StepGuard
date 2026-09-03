import json
from pathlib import Path

from partner_a.execution.harness import run_candidate


ROOT = Path(__file__).resolve().parents[2]

PROBLEMS_DIR = ROOT / "data" / "evaluation" / "problems"
MUTATIONS_PATH = ROOT / "data" / "evaluation" / "mutations" / "mutation_records.jsonl"
OUTPUT_PATH = (
    ROOT / "data" / "evaluation" / "mutations" / "mutation_execution_results.jsonl"
)


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as file:
        return [json.loads(line) for line in file if line.strip()]


def main(
    problems_dir: Path = PROBLEMS_DIR,
    mutations_path: Path = MUTATIONS_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    problems = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in problems_dir.glob("*.json")
    }

    mutations = load_jsonl(mutations_path)

    results = []

    for mutation in mutations:
        problem_id = mutation["problem_id"]

        if problem_id not in problems:
            execution = {
                "status": "HARNESS_ERROR",
                "stdout": "",
                "stderr": f"unknown problem: {problem_id}",
                "returncode": None,
            }
        else:
            execution = run_candidate(
                mutation["mutated_code"],
                problems[problem_id]["test_list"],
            )

        detected = execution["status"] != "PASS"

        record = {
            "problem_id": problem_id,
            "solution_id": mutation["solution_id"],
            "step_id": mutation["step_id"],
            "mutation_type": mutation["mutation_type"],
            "original_code": mutation["original_code"],
            "mutated_code": mutation["mutated_code"],
            "changed": mutation["changed"],
            "original_operator": mutation["original_operator"],
            "mutated_operator": mutation["mutated_operator"],
            "line": mutation["line"],
            "column": mutation["column"],
            "mutation_result": execution["status"],
            "detected": detected,
            "stdout": execution["stdout"],
            "stderr": execution["stderr"],
            "returncode": execution["returncode"],
        }

        results.append(record)

        print(
            mutation["solution_id"],
            mutation["step_id"],
            mutation["mutation_type"],
            "->",
            execution["status"],
            "detected=",
            detected,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in results:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("=" * 60)
    print("StepGuard Evaluation Mutation Execution")
    print("=" * 60)
    print(f"Mutations executed : {len(results)}")
    print(f"Output             : {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()