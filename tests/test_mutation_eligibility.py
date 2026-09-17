from partner_a.evidence.mutation_eligibility import (
    analyze_code,
    build_eligibility,
)


def test_analyze_code_detects_supported_mutation_targets():
    code = """
def solve(x, values):
    if x == 1 and True:
        return values[x + 1]
    return range(x + 1)
"""

    result = analyze_code(code)

    assert result["comparison_targets"] == 1
    assert result["boolean_targets"] == 2
    assert result["off_by_one_targets"] == 2
    assert result["eligible"] is True

    assert result["comparison_operators"] == {
        "Eq": 1,
    }

    assert result["boolean_operators"] == {
        "And": 1,
        "True": 1,
    }

    assert result["off_by_one_contexts"] == {
        "range": 1,
        "subscript": 1,
    }


def test_analyze_code_ignores_unsupported_operator_forms():
    code = """
def solve(x, values):
    if x in values:
        return values[x + 2]
    return range(x)
"""

    result = analyze_code(code)

    assert result["comparison_targets"] == 0
    assert result["boolean_targets"] == 0
    assert result["off_by_one_targets"] == 0
    assert result["eligible"] is False


def test_build_eligibility_uses_only_baseline_passing_candidates():
    baseline = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "baseline_result": "PASS",
            "solution_code": "def solve(x):\n    return x == 1\n",
        },
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_002",
            "baseline_result": "FAIL",
            "solution_code": "def solve(x):\n    return x == 1\n",
        },
        {
            "problem_id": "eval_002",
            "solution_id": "eval_002_sol_001",
            "baseline_result": "PASS",
            "solution_code": "def solve(x):\n    return x + 2\n",
        },
    ]

    result = build_eligibility(baseline)

    assert result["scope"]["baseline_passing_candidates"] == 2
    assert result["candidate_eligibility"]["eligible_candidates"] == 1
    assert result["candidate_eligibility"]["ineligible_candidates"] == 1
    assert result["candidate_eligibility"]["eligibility_rate"] == 0.5

    assert len(result["candidates"]) == 2