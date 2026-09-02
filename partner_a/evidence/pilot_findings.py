import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STEP_EVIDENCE = ROOT / "data" / "evidence" / "step_evidence.jsonl"
STEP_ANALYSIS = ROOT / "data" / "evidence" / "step_analysis.jsonl"
OUTPUT = ROOT / "data" / "evidence" / "pilot_findings.json"


def load_jsonl(path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    evidence = load_jsonl(STEP_EVIDENCE)
    steps = load_jsonl(STEP_ANALYSIS)

    problem_ids = sorted({r["problem_id"] for r in evidence})

    by_problem = {}
    for problem_id in problem_ids:
        records = [r for r in evidence if r["problem_id"] == problem_id]
        results = Counter(r["mutation_result"] for r in records)
        mutation_types = Counter(r["mutation_type"] for r in records)
        detected = results["FAIL"] + results["RUNTIME_ERROR"]

        by_problem[problem_id] = {
            "mutation_count": len(records),
            "results": dict(sorted(results.items())),
            "mutation_types": dict(sorted(mutation_types.items())),
            "detected_count": detected,
            "undetected_count": results["PASS"],
            "detection_rate": detected / len(records),
        }

    total_mutations = len(evidence)
    total_detected = sum(
        r["mutation_result"] in ("FAIL", "RUNTIME_ERROR") for r in evidence
    )
    total_undetected = sum(r["mutation_result"] == "PASS" for r in evidence)

    step_status = Counter()
    for step in steps:
        rate = step["detection_rate"]
        if rate == 1.0:
            step_status["fully_detected"] += 1
        elif rate == 0.0:
            step_status["undetected"] += 1
        else:
            step_status["partially_detected"] += 1

    undetected_steps = [
        {
            "problem_id": r["problem_id"],
            "solution_id": r["solution_id"],
            "step_id": r["step_id"],
            "mutation_count": r["mutation_count"],
            "detection_rate": r["detection_rate"],
        }
        for r in steps
        if r["detection_rate"] == 0.0
    ]

    partial_steps = [
        {
            "problem_id": r["problem_id"],
            "solution_id": r["solution_id"],
            "step_id": r["step_id"],
            "mutation_count": r["mutation_count"],
            "detection_rate": r["detection_rate"],
        }
        for r in steps
        if 0.0 < r["detection_rate"] < 1.0
    ]

    result = {
        "pilot": {
            "problem_count": len(problem_ids),
            "candidate_count": 25,
            "baseline_pass_count": 25,
            "baseline_pass_rate": 1.0,
            "mutation_count": total_mutations,
            "detected_count": total_detected,
            "undetected_count": total_undetected,
            "detection_rate": total_detected / total_mutations,
        },
        "mutation_types": dict(
            sorted(Counter(r["mutation_type"] for r in evidence).items())
        ),
        "by_problem": by_problem,
        "step_analysis": {
            "step_count": len(steps),
            "fully_detected": step_status["fully_detected"],
            "partially_detected": step_status["partially_detected"],
            "undetected": step_status["undetected"],
            "undetected_steps": undetected_steps,
            "partial_steps": partial_steps,
        },
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print(f"Problems: {len(problem_ids)}")
    print(f"Mutations: {total_mutations}")
    print(f"Detected: {total_detected}")
    print(f"Undetected: {total_undetected}")
    print(f"Detection rate: {total_detected / total_mutations:.4f}")
    print(f"Steps: {len(steps)}")
    print(f"Fully detected steps: {step_status['fully_detected']}")
    print(f"Partially detected steps: {step_status['partially_detected']}")
    print(f"Undetected steps: {step_status['undetected']}")


if __name__ == "__main__":
    main()
