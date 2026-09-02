import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SUMMARY = ROOT / "data" / "evidence" / "pilot_summary.json"
VALIDATOR = ROOT / "partner_a" / "evidence" / "validate_pilot.py"


def load_summary():
    with SUMMARY.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def build_status(data):
    scope = data["scope"]
    results = data["mutation_results"]
    step_analysis = data["step_analysis"]
    survivors = data["survivor_patterns"]

    return {
        "schema_version": 1,
        "problems": scope["problem_count"],
        "candidates": scope["candidate_count"],
        "baseline_pass_rate": scope["baseline_pass_rate"],
        "mutations": results["mutation_count"],
        "detected": results["detected_count"],
        "undetected": results["undetected_count"],
        "detection_rate": results["detection_rate"],
        "step_groups": step_analysis["step_count"],
        "survivor_patterns": len(survivors),
    }


def print_human(status):
    print(f"Problems: {status['problems']}")
    print(f"Candidates: {status['candidates']}")
    print(f"Baseline pass rate: {status['baseline_pass_rate']:.4f}")
    print(f"Mutations: {status['mutations']}")
    print(f"Detected: {status['detected']}")
    print(f"Undetected: {status['undetected']}")
    print(f"Detection rate: {status['detection_rate']:.4f}")
    print(f"Step groups: {status['step_groups']}")
    print(f"Survivor patterns: {status['survivor_patterns']}")


def validate(quiet=False):
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        capture_output=quiet,
        text=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json",
        action="store_true",
        help="print pilot status as JSON",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate the pilot before reporting status",
    )
    args = parser.parse_args()

    if args.validate:
        result = validate(quiet=args.json)

        if not args.json:
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")

        if result.returncode != 0:
            raise SystemExit(result.returncode)

    status = build_status(load_summary())

    if args.json:
        print(json.dumps(status, sort_keys=True))
    else:
        print_human(status)


if __name__ == "__main__":
    main()

