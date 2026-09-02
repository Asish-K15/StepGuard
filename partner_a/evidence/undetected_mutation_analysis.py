import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "evidence" / "step_evidence.jsonl"
OUTPUT = ROOT / "data" / "evidence" / "undetected_mutation_analysis.json"


def main():
    with INPUT.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    undetected = [
        r for r in records
        if r["mutation_result"] == "PASS"
    ]

    by_problem = {}
    for problem_id in sorted({r["problem_id"] for r in undetected}):
        rows = [r for r in undetected if r["problem_id"] == problem_id]

        by_problem[problem_id] = {
            "mutation_count": len(rows),
            "mutation_types": dict(
                sorted(Counter(r["mutation_type"] for r in rows).items())
            ),
            "steps": sorted({
                r["step_id"] for r in rows
            }),
            "operator_changes": sorted({
                f"{r['original_operator']}->{r['mutated_operator']}"
                for r in rows
            }),
            "locations": sorted({
                f"line_{r['line']}"
                for r in rows
            }),
            "solution_count": len({
                r["solution_id"] for r in rows
            }),
        }

    result = {
        "undetected_count": len(undetected),
        "problems_with_undetected_mutations": len(by_problem),
        "by_problem": by_problem,
        "records": [
            {
                "problem_id": r["problem_id"],
                "solution_id": r["solution_id"],
                "step_id": r["step_id"],
                "mutation_type": r["mutation_type"],
                "line": r["line"],
                "original_operator": r["original_operator"],
                "mutated_operator": r["mutated_operator"],
            }
            for r in undetected
        ],
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"Undetected mutations: {len(undetected)}")

    for problem_id, data in by_problem.items():
        print(
            problem_id,
            "mutations=", data["mutation_count"],
            "types=", data["mutation_types"],
            "steps=", data["steps"],
            "operators=", data["operator_changes"],
            "locations=", data["locations"],
            "solutions=", data["solution_count"],
        )


if __name__ == "__main__":
    main()
