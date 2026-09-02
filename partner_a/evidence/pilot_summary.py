import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PILOT = ROOT / "data" / "evidence" / "pilot_findings.json"
MUTATION_TYPES = ROOT / "data" / "evidence" / "mutation_type_analysis.json"
SURVIVORS = ROOT / "data" / "evidence" / "survivor_classification.json"

OUTPUT = ROOT / "data" / "evidence" / "pilot_summary.json"


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main():
    pilot = load_json(PILOT)
    mutation_types = load_json(MUTATION_TYPES)
    survivors = load_json(SURVIVORS)

    p = pilot["pilot"]

    summary = {
        "scope": {
            "problem_count": p["problem_count"],
            "candidate_count": p["candidate_count"],
            "baseline_pass_count": p["baseline_pass_count"],
            "baseline_pass_rate": p["baseline_pass_rate"],
        },
        "mutation_results": {
            "mutation_count": p["mutation_count"],
            "detected_count": p["detected_count"],
            "undetected_count": p["undetected_count"],
            "detection_rate": p["detection_rate"],
        },
        "mutation_types": mutation_types["by_mutation_type"],
        "step_analysis": {
            "step_count": pilot["step_analysis"]["step_count"],
            "fully_detected": pilot["step_analysis"]["fully_detected"],
            "partially_detected": pilot["step_analysis"]["partially_detected"],
            "undetected": pilot["step_analysis"]["undetected"],
        },
        "survivor_patterns": survivors["classifications"],
    }

    OUTPUT.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    print("Problems:", summary["scope"]["problem_count"])
    print("Candidates:", summary["scope"]["candidate_count"])
    print("Baseline pass rate:", summary["scope"]["baseline_pass_rate"])
    print("Mutations:", summary["mutation_results"]["mutation_count"])
    print("Detected:", summary["mutation_results"]["detected_count"])
    print("Undetected:", summary["mutation_results"]["undetected_count"])
    print("Detection rate:", f"{summary['mutation_results']['detection_rate']:.4f}")
    print("Mutation types:", len(summary["mutation_types"]))
    print("Step groups:", summary["step_analysis"]["step_count"])
    print("Survivor patterns:", len(summary["survivor_patterns"]))


if __name__ == "__main__":
    main()
