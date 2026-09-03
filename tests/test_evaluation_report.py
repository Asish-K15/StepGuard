from partner_a.evidence.evaluation_report import build_report


def make_pilot():
    return {
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


def make_evaluation():
    return {
        "scope": {
            "problem_count": 20,
            "candidate_count": 100,
            "baseline_pass_count": 60,
            "baseline_pass_rate": 0.6,
        },
        "baseline_results": {
            "FAIL": 39,
            "PASS": 60,
            "RUNTIME_ERROR": 1,
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
            "execution_results": {
                "FAIL": 68,
                "RUNTIME_ERROR": 8,
            },
            "by_mutation_type": {
                "boolean_flip": {
                    "mutation_count": 10,
                    "detected_count": 10,
                    "undetected_count": 0,
                    "detection_rate": 1.0,
                },
                "comparison_swap": {
                    "mutation_count": 44,
                    "detected_count": 44,
                    "undetected_count": 0,
                    "detection_rate": 1.0,
                },
                "off_by_one": {
                    "mutation_count": 22,
                    "detected_count": 22,
                    "undetected_count": 0,
                    "detection_rate": 1.0,
                },
            },
        },
    }


def make_comparison():
    return {
        "scope": {
            "pilot": {
                "problem_count": 5,
                "candidate_count": 25,
                "baseline_pass_count": 25,
                "baseline_pass_rate": 1.0,
            },
            "evaluation": {
                "problem_count": 20,
                "candidate_count": 100,
                "baseline_pass_count": 60,
                "baseline_pass_rate": 0.6,
            },
            "change": {
                "problem_count": 15,
                "candidate_count": 75,
                "baseline_pass_count": 35,
                "baseline_pass_rate": -0.4,
            },
        },
        "mutation_results": {
            "pilot": {
                "mutation_count": 99,
                "detected_count": 86,
                "undetected_count": 13,
                "detection_rate": 86 / 99,
            },
            "evaluation": {
                "mutation_count": 76,
                "detected_count": 76,
                "undetected_count": 0,
                "detection_rate": 1.0,
            },
            "change": {
                "mutation_count": -23,
                "detected_count": -10,
                "undetected_count": -13,
                "detection_rate": 1 - (86 / 99),
            },
        },
    }


def test_build_report_contains_required_sections_and_results():
    report = build_report(
        make_pilot(),
        make_evaluation(),
        make_comparison(),
    )

    assert "# StepGuard Larger Evaluation Report" in report
    assert "## 1. Evaluation Scope" in report
    assert "## 2. Pilot vs. Larger Evaluation" in report
    assert "## 3. Baseline Candidate Results" in report
    assert "## 4. Mutation-Generation Coverage" in report
    assert "## 5. Mutation Detection Results" in report
    assert "## 6. Detection by Mutation Type" in report
    assert "## 7. Interpretation" in report
    assert "## 8. Limitations" in report
    assert "## 9. Conclusion" in report

    assert "60.0%" in report
    assert "33.3%" in report
    assert "100.0%" in report


def test_build_report_qualifies_detection_and_avoids_overclaim():
    report = build_report(
        make_pilot(),
        make_evaluation(),
        make_comparison(),
    )

    assert (
        "100.0% detection rate among generated mutations"
        not in report
    )

    assert (
        "every mutation generated in the larger evaluation "
        "was detected"
        in report
    )

    assert (
        "33.3% mutation-generation coverage"
        in report
    )

    assert (
        "They do not establish that all possible mutations, "
        "all program defects, or all candidate solutions would be detected."
        in report
    )

    assert "detects 100% of bugs" not in report.lower()