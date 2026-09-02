import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "data" / "evidence" / "pilot_summary.json"
OUTPUT = ROOT / "data" / "evidence" / "pilot_report.md"


def load_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main():
    summary = load_json(SUMMARY)

    scope = summary["scope"]
    results = summary["mutation_results"]
    step = summary["step_analysis"]
    mutation_types = summary["mutation_types"]
    survivors = summary["survivor_patterns"]

    lines = [
        "# StepGuard Pilot Report",
        "",
        "## Pilot scope",
        "",
        f"- Problems: {scope['problem_count']}",
        f"- Generated candidates: {scope['candidate_count']}",
        f"- Baseline-passing candidates: {scope['baseline_pass_count']}",
        f"- Baseline pass rate: {scope['baseline_pass_rate']:.2%}",
        "",
        "## Mutation results",
        "",
        f"- Mutations evaluated: {results['mutation_count']}",
        f"- Detected mutations: {results['detected_count']}",
        f"- Undetected mutations: {results['undetected_count']}",
        f"- Overall mutation detection rate: {results['detection_rate']:.2%}",
        "",
        "## Mutation-type results",
        "",
        "| Mutation type | Count | Detected | Undetected | Detection rate |",
        "|---|---:|---:|---:|---:|",
    ]

    for mutation_type, values in mutation_types.items():
        lines.append(
            f"| {mutation_type} | {values['mutation_count']} | "
            f"{values['detected_count']} | {values['undetected_count']} | "
            f"{values['detection_rate']:.2%} |"
        )

    lines.extend([
        "",
        "## Step-level analysis",
        "",
        f"- Step groups analyzed: {step['step_count']}",
        f"- Fully detected: {step['fully_detected']}",
        f"- Partially detected: {step['partially_detected']}",
        f"- Undetected: {step['undetected']}",
        "",
        "## Undetected survivor patterns",
        "",
    ])

    for survivor in survivors:
        location = survivor.get("location")
        if location is None:
            location = ", ".join(survivor.get("locations", []))

        line = survivor.get("line")
        if line is None:
            line = ", ".join(str(value) for value in survivor.get("lines", []))

        lines.append(
            f"- **{survivor['problem_id']}**: "
            f"{survivor['mutation_type']} `{survivor['operator_change']}`; "
            f"location(s): {location}; line(s): {line}; "
            f"{survivor['solution_count']} solution(s). "
            f"{survivor['observation']}"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "The pilot establishes a baseline mutation-detection result for the "
        "current five-problem, 25-candidate dataset. The results show that "
        "most generated mutations were detected, while a smaller set of "
        "survivors remained behaviorally equivalent under the current test "
        "suite. The survivor patterns identify concrete areas where stronger "
        "tests could provide additional discrimination.",
        "",
        "This pilot is exploratory and should not be treated as a general "
        "estimate of StepGuard performance beyond the evaluated dataset.",
        "",
    ])

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

