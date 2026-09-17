import json
from pathlib import Path

input_path = Path(
    "data/evaluation/mutations/mutation_execution_results_passing.jsonl"
)

output_path = Path(
    "data/evaluation/mutations/runtime_error_cases_full.jsonl"
)

records = []

for line in input_path.read_text(encoding="utf-8").splitlines():
    record = json.loads(line)

    if record["mutation_result"] != "RUNTIME_ERROR":
        continue

    stderr = record.get("stderr", "")

    if "IndexError" in stderr:
        classification = "valid_mutation_induced_failure"
    else:
        classification = "requires_manual_review"

    records.append({
        "problem_id": record["problem_id"],
        "solution_id": record["solution_id"],
        "step_id": record["step_id"],
        "mutation_type": record["mutation_type"],
        "original_code": record["original_code"],
        "mutated_code": record["mutated_code"],
        "stderr": stderr,
        "returncode": record["returncode"],
        "classification": classification,
    })

output_path.write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n",
    encoding="utf-8",
)

print(f"Exported runtime-error cases: {len(records)}")
print(f"Output: {output_path}")
