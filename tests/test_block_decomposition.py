import json
from pathlib import Path

from shared.schema import DecompositionType
from partner_b.decomposition.block import decompose_blocks


PROBLEMS_DIR = Path("data/problems")


def load_problem(problem_id: str) -> dict:
    path = PROBLEMS_DIR / f"{problem_id}.json"

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_mbpp_001_blocks():
    problem = load_problem("mbpp_001")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_001_reference",
        source_code=problem["code"],
    )

    assert len(steps) > 0

    for step in steps:
        assert step.problem_id == "mbpp_001"
        assert step.solution_id == "mbpp_001_reference"
        assert step.decomposition_type == DecompositionType.BLOCK
        assert step.step_id.startswith("block_")
        assert step.step_text.strip()


def test_mbpp_002_helper_function_blocks():
    problem = load_problem("mbpp_002")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_002_reference",
        source_code=problem["code"],
    )

    assert len(steps) > 0

    combined = "\n".join(step.step_text for step in steps)

    assert "terms = (n + 1)//2" in combined
    assert "return sum_odd(r) - sum_odd(l - 1)" in combined


def test_mbpp_003_conditional_blocks():
    problem = load_problem("mbpp_003")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=problem["code"],
    )

    assert len(steps) > 0

    combined = "\n".join(step.step_text for step in steps)

    assert "if mx == mn" in combined
    assert "elif mx == r" in combined
    assert "elif mx == g" in combined
    assert "elif mx == b" in combined


def test_mbpp_004_nested_loop_blocks():
    problem = load_problem("mbpp_004")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_004_reference",
        source_code=problem["code"],
    )

    assert len(steps) > 0

    combined = "\n".join(step.step_text for step in steps)

    # The loop structure is intentionally treated as control-flow
    # context rather than as a mutation target.
    # The meaningful nested operations must still be preserved.
    assert "L[i][j][k] = 0" in combined
    assert "L[i][j][k] = L[i-1][j-1][k-1] + 1" in combined
    assert "L[i][j][k] = max" in combined
    assert "return L[m][n][o]" in combined

def test_mbpp_005_generator_blocks():
    problem = load_problem("mbpp_005")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_005_reference",
        source_code=problem["code"],
    )

    assert len(steps) > 0

    combined = "\n".join(step.step_text for step in steps)

    assert "first_odd" in combined
    assert "return first_odd" in combined


def test_block_ids_are_sequential():
    problem = load_problem("mbpp_004")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_004_reference",
        source_code=problem["code"],
    )

    expected_ids = [
        f"block_{index:02d}"
        for index in range(1, len(steps) + 1)
    ]

    actual_ids = [step.step_id for step in steps]

    assert actual_ids == expected_ids


def test_block_decomposer_rejects_invalid_python():
    invalid_code = """
def broken_function(
    return 10
"""

    try:
        decompose_blocks(
            problem_id="test_problem",
            solution_id="test_solution",
            source_code=invalid_code,
        )
        assert False, "Expected SyntaxError"
    except SyntaxError:
        pass
def test_blocks_do_not_overlap():
    for problem_id in [
        "mbpp_001",
        "mbpp_002",
        "mbpp_003",
        "mbpp_004",
        "mbpp_005",
    ]:
        problem = load_problem(problem_id)

        steps = decompose_blocks(
            problem_id=problem["pilot_id"],
            solution_id=f"{problem_id}_reference",
            source_code=problem["code"],
        )

        spans = sorted(
            (step.start_line, step.end_line)
            for step in steps
        )

        for (_, previous_end), (current_start, _) in zip(
            spans,
            spans[1:],
        ):
            assert current_start > previous_end, (
                f"Overlapping blocks detected in {problem_id}"
            )