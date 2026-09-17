from partner_a.evidence.evaluation_summary import build_summary


def test_build_summary_aggregates_baseline_and_mutation_results():
    baseline = [
        {"problem_id": "eval_001", "solution_id": "eval_001_sol_001", "baseline_result": "PASS"},
        {"problem_id": "eval_001", "solution_id": "eval_001_sol_002", "baseline_result": "FAIL"},
        {"problem_id": "eval_002", "solution_id": "eval_002_sol_001", "baseline_result": "PASS"},
    ]

    mutations = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "mutation_type": "comparison_swap",
        },
        {
            "problem_id": "eval_002",
            "solution_id": "eval_002_sol_001",
            "mutation_type": "boolean_flip",
        },
    ]

    executions = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "mutation_type": "comparison_swap",
            "mutation_result": "FAIL",
            "detected": True,
        },
        {
            "problem_id": "eval_002",
            "solution_id": "eval_002_sol_001",
            "mutation_type": "boolean_flip",
            "mutation_result": "PASS",
            "detected": False,
        },
    ]

    summary = build_summary(baseline, mutations, executions)

    assert summary["scope"]["problem_count"] == 2
    assert summary["scope"]["candidate_count"] == 3
    assert summary["scope"]["baseline_pass_count"] == 2
    assert summary["scope"]["baseline_pass_rate"] == 2 / 3

    assert summary["mutation_coverage"]["passing_candidate_count"] == 2
    assert summary["mutation_coverage"]["passing_candidates_with_mutations"] == 2
    assert summary["mutation_coverage"]["passing_candidates_without_mutations"] == 0
    assert summary["mutation_coverage"]["coverage_rate"] == 1.0

    assert summary["mutations"]["mutation_record_count"] == 2
    assert summary["mutations"]["execution_count"] == 2
    assert summary["mutations"]["detected_count"] == 1
    assert summary["mutations"]["undetected_count"] == 1
    assert summary["mutations"]["detection_rate"] == 0.5


def test_build_summary_separates_mutation_types():
    baseline = [
        {"problem_id": "eval_001", "solution_id": "sol_001", "baseline_result": "PASS"},
    ]

    mutations = [
        {
            "problem_id": "eval_001",
            "solution_id": "sol_001",
            "mutation_type": "boolean_flip",
        },
        {
            "problem_id": "eval_001",
            "solution_id": "sol_001",
            "mutation_type": "off_by_one",
        },
    ]

    executions = [
        {
            "problem_id": "eval_001",
            "solution_id": "sol_001",
            "mutation_type": "boolean_flip",
            "mutation_result": "RUNTIME_ERROR",
            "detected": True,
        },
        {
            "problem_id": "eval_001",
            "solution_id": "sol_001",
            "mutation_type": "off_by_one",
            "mutation_result": "PASS",
            "detected": False,
        },
    ]

    summary = build_summary(baseline, mutations, executions)

    by_type = summary["mutations"]["by_mutation_type"]

    assert by_type["boolean_flip"]["mutation_count"] == 1
    assert by_type["boolean_flip"]["detected_count"] == 1
    assert by_type["boolean_flip"]["detection_rate"] == 1.0

    assert by_type["off_by_one"]["mutation_count"] == 1
    assert by_type["off_by_one"]["undetected_count"] == 1
    assert by_type["off_by_one"]["detection_rate"] == 0.0