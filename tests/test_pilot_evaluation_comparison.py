from partner_a.evidence.pilot_evaluation_comparison import build_comparison


def test_build_comparison_calculates_scope_and_detection_changes():
    pilot = {
        "scope": {
            "problem_count": 5,
            "candidate_count": 25,
            "baseline_pass_count": 25,
            "baseline_pass_rate": 1.0,
        },
        "mutation_results": {
            "mutation_count": 99,
            "detected_count": 86,
            "undetected_count": 13,
            "detection_rate": 86 / 99,
        },
    }

    evaluation = {
        "scope": {
            "problem_count": 20,
            "candidate_count": 100,
            "baseline_pass_count": 60,
            "baseline_pass_rate": 0.6,
        },
        "mutation_coverage": {
            "passing_candidate_count": 60,
            "passing_candidates_with_mutations": 20,
            "passing_candidates_without_mutations": 40,
            "coverage_rate": 20 / 60,
            "problems_with_mutations": 5,
            "passing_problems": 14,
        },
        "mutations": {
            "execution_count": 76,
            "detected_count": 76,
            "undetected_count": 0,
            "detection_rate": 1.0,
            "by_mutation_type": {},
            "by_problem": {},
        },
    }

    comparison = build_comparison(pilot, evaluation)

    assert comparison["scope"]["change"]["problem_count"] == 15
    assert comparison["scope"]["change"]["candidate_count"] == 75
    assert comparison["scope"]["change"]["baseline_pass_count"] == 35
    assert comparison["scope"]["change"]["baseline_pass_rate"] == -0.4

    assert comparison["mutation_results"]["change"]["mutation_count"] == -23
    assert comparison["mutation_results"]["change"]["detected_count"] == -10
    assert comparison["mutation_results"]["change"]["undetected_count"] == -13

    assert comparison["mutation_results"]["change"]["detection_rate"] == (
        1.0 - (86 / 99)
    )


def test_build_comparison_preserves_evaluation_coverage_and_interpretation():
    pilot = {
        "scope": {
            "problem_count": 5,
            "candidate_count": 25,
            "baseline_pass_count": 25,
            "baseline_pass_rate": 1.0,
        },
        "mutation_results": {
            "mutation_count": 99,
            "detected_count": 86,
            "undetected_count": 13,
            "detection_rate": 86 / 99,
        },
    }

    evaluation = {
        "scope": {
            "problem_count": 20,
            "candidate_count": 100,
            "baseline_pass_count": 60,
            "baseline_pass_rate": 0.6,
        },
        "mutation_coverage": {
            "passing_candidate_count": 60,
            "passing_candidates_with_mutations": 20,
            "passing_candidates_without_mutations": 40,
            "coverage_rate": 1 / 3,
            "problems_with_mutations": 5,
            "passing_problems": 14,
        },
        "mutations": {
            "execution_count": 76,
            "detected_count": 76,
            "undetected_count": 0,
            "detection_rate": 1.0,
            "by_mutation_type": {
                "boolean_flip": {
                    "mutation_count": 10,
                    "detected_count": 10,
                    "undetected_count": 0,
                    "detection_rate": 1.0,
                }
            },
            "by_problem": {
                "eval_004": {
                    "mutation_count": 41,
                    "detected_count": 41,
                    "undetected_count": 0,
                    "detection_rate": 1.0,
                }
            },
        },
    }

    comparison = build_comparison(pilot, evaluation)

    assert (
        comparison["evaluation_specific"][
            "mutation_generation_coverage"
        ]["coverage_rate"]
        == 1 / 3
    )

    assert comparison["interpretation"][
        "baseline_pass_rate_generalized"
    ] is True

    assert comparison["interpretation"][
        "generated_mutations_fully_detected"
    ] is True

    assert comparison["interpretation"][
        "mutation_generation_is_complete"
    ] is False

    assert (
        comparison["evaluation_specific"][
            "mutation_results_by_type"
        ]["boolean_flip"]["mutation_count"]
        == 10
    )

    assert (
        comparison["evaluation_specific"][
            "mutation_results_by_problem"
        ]["eval_004"]["mutation_count"]
        == 41
    )