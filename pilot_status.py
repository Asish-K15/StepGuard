import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "data" / "evidence" / "pilot_summary.json"


def main():
    with SUMMARY.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    scope = data["scope"]
    results = data["mutation_results"]
    step_analysis = data["step_analysis"]
    survivors = data["survivor_patterns"]

    print(f"Problems: {scope['problem_count']}")
    print(f"Candidates: {scope['candidate_count']}")
    print(f"Baseline pass rate: {scope['baseline_pass_rate']:.4f}")
    print(f"Mutations: {results['mutation_count']}")
    print(f"Detected: {results['detected_count']}")
    print(f"Undetected: {results['undetected_count']}")
    print(f"Detection rate: {results['detection_rate']:.4f}")
    print(f"Step groups: {step_analysis['step_count']}")
    print(f"Survivor patterns: {len(survivors)}")


if __name__ == "__main__":
    main()

