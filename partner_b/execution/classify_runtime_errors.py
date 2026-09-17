import json
from pathlib import Path

path = Path("data/evaluation/mutations/mutation_execution_results_passing.jsonl")
output = Path("data/evaluation/mutations/runtime_error_classification.jsonl")

results = []

for line in path.read_text(encoding="utf-8").splitlines():
    record = json.loads(line)

    if record["mutation_result"] != "RUNTIME_ERROR":
        continue

    error = record.get("stderr", "")

    if "IndexError" in error:
        classification = "valid_mutation_consequence"
    else:
        classification = "requires_manual_review"

    results.append({
        "solution_id": record["solution_id"],
        "problem_id": record["problem_id"],
        "mutation_type": record["mutation_type"],
        "line": record.get("line"),
        "column": record.get("column"),
        "error_type": "IndexError" if "IndexError" in error else "unknown",
        "classification": classification,
        "reason": "Off-by-one mutation causes invalid array indexing."
        if classification == "valid_mutation_consequence"
        else "Error requires manual review.",
    })

output.write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n",
    encoding="utf-8",
)

print(f"Classified runtime errors: {len(results)}")
print(f"Valid mutation consequences: {sum(r['classification'] == 'valid_mutation_consequence' for r in results)}")
print(f"Manual review required: {sum(r['classification'] == 'requires_manual_review' for r in results)}")
print(f"Output: {output}")
