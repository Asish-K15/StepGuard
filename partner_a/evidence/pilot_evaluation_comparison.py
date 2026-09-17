import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PILOT_INPUT = (
    ROOT / "data" / "evidence" / "pilot_summary.json"
)

EVALUATION_INPUT = (
    ROOT / "data" / "evaluation" / "evaluation_summary.json"
)

OUTPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "pilot_evaluation_comparison.json"
)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def rate_change(
    pilot_value: float,
    evaluation_value: float,
) -> float:
    return evaluation_value - pilot_value


def build_comparison(
    pilot: dict,
    evaluation: dict,
) -> dict:
    pilot_scope = pilot["scope"]
    evaluation_scope = evaluation["scope"]

    pilot_mutations = pilot["mutation_results"]
    evaluation_mutations = evaluation["mutations"]

    pilot_detection = pilot_mutations["detection_rate"]
    evaluation_detection = evaluation_mutations["detection_rate"]

    comparison = {
        "scope": {
            "pilot": {
                "problem_count": pilot_scope["problem_count"],
                "candidate_count": pilot_scope["candidate_count"],
                "baseline_pass_count": pilot_scope[
                    "baseline_pass_count"
                ],
                "baseline_pass_rate": pilot_scope[
                    "baseline_pass_rate"
                ],
            },
            "evaluation": {
                "problem_count": evaluation_scope[
                    "problem_count"
                ],
                "candidate_count": evaluation_scope[
                    "candidate_count"
                ],
                "baseline_pass_count": evaluation_scope[
                    "baseline_pass_count"
                ],
                "baseline_pass_rate": evaluation_scope[
                    "baseline_pass_rate"
                ],
            },
            "change": {
                "problem_count": (
                    evaluation_scope["problem_count"]
                    - pilot_scope["problem_count"]
                ),
                "candidate_count": (
                    evaluation_scope["candidate_count"]
                    - pilot_scope["candidate_count"]
                ),
                "baseline_pass_count": (
                    evaluation_scope["baseline_pass_count"]
                    - pilot_scope["baseline_pass_count"]
                ),
                "baseline_pass_rate": rate_change(
                    pilot_scope["baseline_pass_rate"],
                    evaluation_scope["baseline_pass_rate"],
                ),
            },
        },
        "mutation_results": {
            "pilot": {
                "mutation_count": pilot_mutations[
                    "mutation_count"
                ],
                "detected_count": pilot_mutations[
                    "detected_count"
                ],
                "undetected_count": pilot_mutations[
                    "undetected_count"
                ],
                "detection_rate": pilot_detection,
            },
            "evaluation": {
                "mutation_count": evaluation_mutations[
                    "execution_count"
                ],
                "detected_count": evaluation_mutations[
                    "detected_count"
                ],
                "undetected_count": evaluation_mutations[
                    "undetected_count"
                ],
                "detection_rate": evaluation_detection,
            },
            "change": {
                "mutation_count": (
                    evaluation_mutations["execution_count"]
                    - pilot_mutations["mutation_count"]
                ),
                "detected_count": (
                    evaluation_mutations["detected_count"]
                    - pilot_mutations["detected_count"]
                ),
                "undetected_count": (
                    evaluation_mutations["undetected_count"]
                    - pilot_mutations["undetected_count"]
                ),
                "detection_rate": rate_change(
                    pilot_detection,
                    evaluation_detection,
                ),
            },
        },
        "evaluation_specific": {
            "mutation_generation_coverage": evaluation[
                "mutation_coverage"
            ],
            "mutation_results_by_type": evaluation_mutations[
                "by_mutation_type"
            ],
            "mutation_results_by_problem": evaluation_mutations[
                "by_problem"
            ],
        },
        "interpretation": {
            "baseline_pass_rate_generalized": (
                evaluation_scope["baseline_pass_rate"]
                < pilot_scope["baseline_pass_rate"]
            ),
            "generated_mutations_fully_detected": (
                evaluation_mutations["undetected_count"] == 0
            ),
            "mutation_generation_is_complete": (
                evaluation["mutation_coverage"][
                    "coverage_rate"
                ] == 1.0
            ),
        },
    }

    return comparison


def main() -> None:
    pilot = load_json(PILOT_INPUT)
    evaluation = load_json(EVALUATION_INPUT)

    comparison = build_comparison(
        pilot,
        evaluation,
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            comparison,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")

    print(
        "Pilot baseline pass rate:",
        f"{comparison['scope']['pilot']['baseline_pass_rate']:.4f}",
    )

    print(
        "Evaluation baseline pass rate:",
        f"{comparison['scope']['evaluation']['baseline_pass_rate']:.4f}",
    )

    print(
        "Baseline pass-rate change:",
        f"{comparison['scope']['change']['baseline_pass_rate']:+.4f}",
    )

    print(
        "Pilot mutation detection rate:",
        f"{comparison['mutation_results']['pilot']['detection_rate']:.4f}",
    )

    print(
        "Evaluation mutation detection rate:",
        f"{comparison['mutation_results']['evaluation']['detection_rate']:.4f}",
    )

    print(
        "Detection-rate change:",
        f"{comparison['mutation_results']['change']['detection_rate']:+.4f}",
    )

    print(
        "Evaluation mutation-generation coverage:",
        f"{comparison['evaluation_specific']['mutation_generation_coverage']['coverage_rate']:.4f}",
    )


if __name__ == "__main__":
    main()