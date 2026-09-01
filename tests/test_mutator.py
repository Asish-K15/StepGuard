import json
from pathlib import Path

import pytest

from partner_b.decomposition.block import decompose_blocks
from partner_b.mutation.mutator import (
    mutate_comparison,
    mutate_boolean,
)

PROBLEMS_DIR = Path("data/problems")


def load_problem(problem_id: str) -> dict:
    path = PROBLEMS_DIR / f"{problem_id}.json"

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_comparison_mutation_on_mbpp_003():
    problem = load_problem("mbpp_003")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=problem["code"],
    )

    # block_05 contains: if mx == mn
    step = steps[4]

    result = mutate_comparison(
        solution_code=problem["code"],
        step=step,
    )

    assert result.changed is True
    assert result.original_operator == "=="
    assert result.mutated_operator == "!="
    assert result.mutation_type == "comparison_swap"

    assert "if mx != mn:" in result.mutated_code
    assert "if mx == mn:" not in result.mutated_code


def test_mutated_code_is_valid_python():
    problem = load_problem("mbpp_003")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=problem["code"],
    )

    result = mutate_comparison(
        solution_code=problem["code"],
        step=steps[4],
    )

    compile(result.mutated_code, "<mutated>", "exec")


def test_only_target_block_is_changed():
    problem = load_problem("mbpp_003")

    original = problem["code"]

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=original,
    )

    target = steps[4]

    result = mutate_comparison(
        solution_code=original,
        step=target,
    )

    changed_lines = []

    original_lines = original.splitlines()
    mutated_lines = result.mutated_code.splitlines()

    for index, (before, after) in enumerate(
        zip(original_lines, mutated_lines),
        start=1,
    ):
        if before != after:
            changed_lines.append(index)

    assert len(changed_lines) == 1
    assert target.start_line <= changed_lines[0] <= target.end_line


def test_no_comparison_returns_unchanged():
    problem = load_problem("mbpp_003")

    steps = decompose_blocks(
        problem_id=problem["pilot_id"],
        solution_id="mbpp_003_reference",
        source_code=problem["code"],
    )

    # block_01 is RGB normalization and has no comparison.
    step = steps[0]

    result = mutate_comparison(
        solution_code=problem["code"],
        step=step,
    )

    assert result.changed is False
    assert result.mutated_code == problem["code"]


@pytest.mark.parametrize(
    "operator, expected",
    [
        ("==", "!="),
        ("!=", "=="),
        ("<", ">="),
        (">=", "<"),
        (">", "<="),
        ("<=", ">"),
    ],
)
def test_comparison_operator_mapping(operator, expected):
    source = f"""
def test(x, y):
    return x {operator} y
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_comparison(source, Step())

    assert result.changed is True
    assert result.original_operator == operator
    assert result.mutated_operator == expected
def test_boolean_and_to_or():
    source = """
def test(x, y):
    return x > 0 and y > 0
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_boolean(source, Step())

    assert result.changed is True
    assert result.original_operator == "and"
    assert result.mutated_operator == "or"
    assert "x > 0 or y > 0" in result.mutated_code


def test_boolean_or_to_and():
    source = """
def test(x, y):
    return x > 0 or y > 0
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_boolean(source, Step())

    assert result.changed is True
    assert result.original_operator == "or"
    assert result.mutated_operator == "and"
    assert "x > 0 and y > 0" in result.mutated_code


def test_boolean_true_to_false():
    source = """
def test():
    return True
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_boolean(source, Step())

    assert result.changed is True
    assert result.original_operator == "True"
    assert result.mutated_operator == "False"
    assert "return False" in result.mutated_code


def test_boolean_false_to_true():
    source = """
def test():
    return False
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_boolean(source, Step())

    assert result.changed is True
    assert result.original_operator == "False"
    assert result.mutated_operator == "True"
    assert "return True" in result.mutated_code


def test_boolean_mutation_is_syntax_valid():
    source = """
def test(x, y):
    return x > 0 and y > 0
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_01"
        start_line = 3
        end_line = 3

    result = mutate_boolean(source, Step())

    compile(result.mutated_code, "<mutated>", "exec")


def test_boolean_mutation_only_changes_target_line():
    source = """
def test(x, y):
    value = x > 0
    return x > 0 and y > 0
"""

    class Step:
        problem_id = "test"
        solution_id = "solution"
        step_id = "block_02"
        start_line = 4
        end_line = 4

    result = mutate_boolean(source, Step())

    original_lines = source.splitlines()
    mutated_lines = result.mutated_code.splitlines()

    changed_lines = [
        index
        for index, (before, after)
        in enumerate(
            zip(original_lines, mutated_lines),
            start=1,
        )
        if before != after
    ]

    assert changed_lines == [4]