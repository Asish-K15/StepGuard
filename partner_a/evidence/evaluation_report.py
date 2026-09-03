import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PILOT_INPUT = ROOT / "data" / "evidence" / "pilot_summary.json"
EVALUATION_INPUT = (
    ROOT / "data" / "evaluation" / "evaluation_summary.json"
)
COMPARISON_INPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "pilot_evaluation_comparison.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "evaluation_report.md"
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_report(
    pilot: dict,
    evaluation: dict,
    comparison: dict,
) -> str:
    pilot_scope = pilot["scope"]
    pilot_mutations = pilot["mutation_results"]

    evaluation_scope = evaluation["scope"]
    evaluation_coverage = evaluation["mutation_coverage"]
    evaluation_mutations = evaluation["mutations"]

    pilot_detection = pilot_mutations["detection_rate"]
    evaluation_detection = evaluation_mutations["detection_rate"]

    lines = [
        "# StepGuard Larger Evaluation Report",
        "",
        "## 1. Evaluation Scope",
        "",
        (
            "The larger evaluation uses 20 MBPP problems and "
            "100 generated candidate solutions, with five candidates "
            "generated per problem."
        ),
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Problems | {evaluation_scope['problem_count']} |",
        f"| Candidates | {evaluation_scope['candidate_count']} |",
        (
            f"| Baseline-passing candidates | "
            f"{evaluation_scope['baseline_pass_count']} |"
        ),
        (
            f"| Baseline pass rate | "
            f"{percent(evaluation_scope['baseline_pass_rate'])} |"
        ),
        "",
        "## 2. Pilot vs. Larger Evaluation",
        "",
        "| Metric | Pilot | Larger evaluation | Change |",
        "|---|---:|---:|---:|",
        (
            f"| Problems | "
            f"{comparison['scope']['pilot']['problem_count']} | "
            f"{comparison['scope']['evaluation']['problem_count']} | "
            f"+{comparison['scope']['change']['problem_count']} |"
        ),
        (
            f"| Candidates | "
            f"{comparison['scope']['pilot']['candidate_count']} | "
            f"{comparison['scope']['evaluation']['candidate_count']} | "
            f"+{comparison['scope']['change']['candidate_count']} |"
        ),
        (
            f"| Baseline pass rate | "
            f"{percent(comparison['scope']['pilot']['baseline_pass_rate'])} | "
            f"{percent(comparison['scope']['evaluation']['baseline_pass_rate'])} | "
            f"{percent(comparison['scope']['change']['baseline_pass_rate'])} |"
        ),
        (
            f"| Mutations | "
            f"{comparison['mutation_results']['pilot']['mutation_count']} | "
            f"{comparison['mutation_results']['evaluation']['mutation_count']} | "
            f"{comparison['mutation_results']['change']['mutation_count']} |"
        ),
        (
            f"| Detected mutations | "
            f"{comparison['mutation_results']['pilot']['detected_count']} | "
            f"{comparison['mutation_results']['evaluation']['detected_count']} | "
            f"{comparison['mutation_results']['change']['detected_count']} |"
        ),
        (
            f"| Undetected mutations | "
            f"{comparison['mutation_results']['pilot']['undetected_count']} | "
            f"{comparison['mutation_results']['evaluation']['undetected_count']} | "
            f"{comparison['mutation_results']['change']['undetected_count']} |"
        ),
        (
            f"| Mutation detection rate | "
            f"{percent(pilot_detection)} | "
            f"{percent(evaluation_detection)} | "
            f"{percent(comparison['mutation_results']['change']['detection_rate'])} |"
        ),
        "",
        (
            "The pilot achieved a 100.0% baseline candidate pass rate, "
            "whereas the larger evaluation achieved 60.0%. Thus, the "
            "pilot's 100.0% candidate pass rate was not reproduced at "
            "the larger evaluation scale."
        ),
        "",
        "## 3. Baseline Candidate Results",
        "",
        (
            f"The larger evaluation produced "
            f"{evaluation_scope['candidate_count']} candidates. "
            f"{evaluation_scope['baseline_pass_count']} passed the "
            f"original MBPP tests, giving a baseline pass rate of "
            f"{percent(evaluation_scope['baseline_pass_rate'])}."
        ),
        "",
        (
            "The remaining candidates consisted of "
            f"{evaluation['baseline_results'].get('FAIL', 0)} FAIL results "
            f"and "
            f"{evaluation['baseline_results'].get('RUNTIME_ERROR', 0)} "
            "RUNTIME_ERROR result."
        ),
        "",
        "## 4. Mutation-Generation Coverage",
        "",
        (
            f"Mutation generation was applied to baseline-passing "
            f"candidates. Of the "
            f"{evaluation_coverage['passing_candidate_count']} "
            f"baseline-passing candidates, "
            f"{evaluation_coverage['passing_candidates_with_mutations']} "
            f"produced at least one mutation."
        ),
        "",
        (
            f"This corresponds to "
            f"{percent(evaluation_coverage['coverage_rate'])} "
            "mutation-generation coverage among baseline-passing "
            "candidates. "
            f"{evaluation_coverage['passing_candidates_without_mutations']} "
            "passing candidates produced no mutation under the current "
            "mutation-generation rules."
        ),
        "",
        (
            "Therefore, mutation-generation coverage is distinct from "
            "mutation detection: the 100.0% detection result applies only "
            "to mutations that were actually generated."
        ),
        "",
        "## 5. Mutation Detection Results",
        "",
        (
            f"The evaluation generated and executed "
            f"{evaluation_mutations['execution_count']} mutations. "
            f"{evaluation_mutations['detected_count']} were detected and "
            f"{evaluation_mutations['undetected_count']} were undetected."
        ),
        "",
        (
            f"The resulting detection rate was "
            f"{percent(evaluation_detection)} among generated mutations."
        ),
        "",
        (
            f"Mutation execution produced "
            f"{evaluation_mutations['execution_results'].get('FAIL', 0)} "
            "FAIL results and "
            f"{evaluation_mutations['execution_results'].get('RUNTIME_ERROR', 0)} "
            "RUNTIME_ERROR results."
        ),
        "",
        "## 6. Detection by Mutation Type",
        "",
        "| Mutation type | Mutations | Detected | Undetected | Detection rate |",
        "|---|---:|---:|---:|---:|",
    ]

    for mutation_type, data in evaluation_mutations[
        "by_mutation_type"
    ].items():
        lines.append(
            f"| {mutation_type} | "
            f"{data['mutation_count']} | "
            f"{data['detected_count']} | "
            f"{data['undetected_count']} | "
            f"{percent(data['detection_rate'])} |"
        )

    lines.extend(
        [
            "",
            "## 7. Interpretation",
            "",
            (
                "The larger evaluation changes the interpretation of the "
                "pilot in two important ways."
            ),
            "",
            (
                "First, the baseline result is less favorable at larger "
                "scale. Candidate solutions passed the original tests at "
                "60.0%, compared with 100.0% in the five-problem pilot."
            ),
            "",
            (
                "Second, every mutation generated in the larger evaluation "
                "was detected. This is stronger than the pilot's 86.9% "
                "detection rate, but it must be interpreted together with "
                "the 33.3% mutation-generation coverage among "
                "baseline-passing candidates."
            ),
            "",
            (
                "The results therefore support the narrower conclusion "
                "that the current pipeline successfully detected all "
                "mutations generated under its current rules in this "
                "20-problem evaluation. They do not establish that all "
                "possible mutations, all program defects, or all candidate "
                "solutions would be detected."
            ),
            "",
            "## 8. Limitations",
            "",
            (
                "- The evaluation contains 20 selected MBPP problems and "
                "100 generated candidates; it is not a representative "
                "sample of all programming problems or generated programs."
            ),
            (
                "- Only 60 of the 100 candidates passed the baseline tests."
            ),
            (
                "- Only 20 of those 60 passing candidates produced "
                "mutations under the current mutation-generation rules."
            ),
            (
                "- The evaluation uses the existing comparison-swap, "
                "boolean-flip, and off-by-one mutation operators."
            ),
            (
                "- Detection is measured against the supplied MBPP tests, "
                "so an undetected defect may reflect insufficient test "
                "coverage rather than correctness."
            ),
            (
                "- RUNTIME_ERROR is counted as detected because the mutated "
                "program did not pass the test execution."
            ),
            "",
            "## 9. Conclusion",
            "",
            (
                "The 20-problem evaluation provides a larger validation "
                "of the StepGuard pipeline than the initial five-problem "
                "pilot. The larger evaluation reduced the baseline "
                "candidate pass rate from 100.0% to 60.0%, demonstrating "
                "that the pilot baseline result did not persist at larger "
                "scale."
            ),
            "",
            (
                "For the mutations generated by the current pipeline, "
                "detection was 100.0%: all 76 generated mutations were "
                "detected. This result is conditional on the 33.3% "
                "mutation-generation coverage observed among the "
                "60 baseline-passing candidates."
            ),
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    pilot = load_json(PILOT_INPUT)
    evaluation = load_json(EVALUATION_INPUT)
    comparison = load_json(COMPARISON_INPUT)

    report = build_report(
        pilot,
        evaluation,
        comparison,
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        report,
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()