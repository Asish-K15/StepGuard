import json
from pathlib import Path

from shared.schema import DecompositionType
from partner_b.decomposition.function import decompose_functions


PROBLEMS_DIR = Path("data/problems")


def load_problem(problem_id: str) -> dict:
    path = PROBLEMS_DIR / f"{problem_id}.json"

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_mbpp_001_single_function():
    problem = load_problem("mbpp_001")

    steps = decompose_functions(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_001_reference",
        source_code=problem["code"],
    )

    assert len(steps) == 1

    step = steps[0]

    assert step.problem_id == "mbpp_001"
    assert step.solution_id == "mbpp_001_reference"
    assert step.decomposition_type == DecompositionType.FUNCTION
    assert step.step_id == "func_01"
    assert "def even_position" in step.step_text


def test_mbpp_002_helper_functions():
    problem = load_problem("mbpp_002")

    steps = decompose_functions(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_002_reference",
        source_code=problem["code"],
    )

    assert len(steps) == 2

    assert steps[0].step_id == "func_01"
    assert "def sum_odd" in steps[0].step_text

    assert steps[1].step_id == "func_02"
    assert "def sum_in_range" in steps[1].step_text


def test_mbpp_003_conditional_function():
    problem = load_problem("mbpp_003")

    steps = decompose_functions(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=problem["code"],
    )

    assert len(steps) == 1
    assert "def rgb_to_hsv" in steps[0].step_text


def test_mbpp_004_nested_logic():
    problem = load_problem("mbpp_004")

    steps = decompose_functions(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_004_reference",
        source_code=problem["code"],
    )

    assert len(steps) == 1
    assert "def lcs_of_three" in steps[0].step_text


def test_mbpp_005_generator_expression():
    problem = load_problem("mbpp_005")

    steps = decompose_functions(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_005_reference",
        source_code=problem["code"],
    )

    assert len(steps) == 1
    assert "def first_odd" in steps[0].step_text


def test_function_decomposer_rejects_invalid_python():
    invalid_code = """
def broken_function(
    return 10
"""

    try:
        decompose_functions(
            problem_id="test_problem",
            solution_id="test_solution",
            source_code=invalid_code,
        )
        assert False, "Expected SyntaxError"
    except SyntaxError:
        pass