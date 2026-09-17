import json
import ast
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]

baseline_path = ROOT / "data/evaluation/solutions/baseline_results.jsonl"
passing_path = ROOT / "data/evaluation/solutions/passing_candidates.jsonl"
mutation_path = ROOT / "data/evaluation/mutations/mutation_records_passing.jsonl"


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


passing = load_jsonl(passing_path)
mutations = load_jsonl(mutation_path)

mutated_solutions = {
    record["solution_id"]
    for record in mutations
}

no_target_candidates = [
    candidate
    for candidate in passing
    if candidate["solution_id"] not in mutated_solutions
]

print(f"Total baseline-PASS candidates : {len(passing)}")
print(f"Candidates with mutations     : {len(mutated_solutions)}")
print(f"Candidates without targets    : {len(no_target_candidates)}")
print()

for candidate in no_target_candidates:
    code = candidate["code"]

    try:
        tree = ast.parse(code)
    except SyntaxError:
        print(f"{candidate['solution_id']} | SYNTAX_ERROR")
        continue

    comparisons = sum(
        isinstance(node, ast.Compare)
        for node in ast.walk(tree)
    )
    booleans = sum(
        isinstance(node, ast.BoolOp)
        for node in ast.walk(tree)
    )
    arithmetic = sum(
        isinstance(node, ast.BinOp)
        for node in ast.walk(tree)
    )
    loops = sum(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(tree)
    )

    print(
        f"{candidate['solution_id']} | "
        f"comparisons={comparisons} | "
        f"boolean_ops={booleans} | "
        f"arithmetic_ops={arithmetic} | "
        f"loops={loops}"
    )