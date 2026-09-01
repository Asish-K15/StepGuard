"""
Targeted mutation engine for StepGuard Stage 0A.

B3.1: comparison-operator mutation.

Guarantee:
- Only the requested BlockStep source span is considered.
- Exactly one comparison operator is mutated per result.
- The rest of the solution remains unchanged.
- The resulting program must parse successfully.
"""

import ast
from dataclasses import dataclass
from typing import Optional


COMPARISON_MUTATIONS = {
    "==": "!=",
    "!=": "==",
    "<": ">=",
    ">=": "<",
    ">": "<=",
    "<=": ">",
}


@dataclass
class MutationResult:
    problem_id: str
    solution_id: str
    step_id: str
    mutation_type: str
    original_code: str
    mutated_code: str
    changed: bool
    original_operator: Optional[str] = None
    mutated_operator: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


def _operator_text(operator: ast.cmpop) -> Optional[str]:
    """Convert an AST comparison operator to source text."""

    mapping = {
        ast.Eq: "==",
        ast.NotEq: "!=",
        ast.Lt: "<",
        ast.LtE: "<=",
        ast.Gt: ">",
        ast.GtE: ">=",
    }

    for operator_type, text in mapping.items():
        if isinstance(operator, operator_type):
            return text

    return None


def _line_offsets(source_code: str) -> list[int]:
    """Return absolute character offsets for each source line."""

    offsets = [0]

    for index, char in enumerate(source_code):
        if char == "\n":
            offsets.append(index + 1)

    return offsets


def _absolute_offset(
    offsets: list[int],
    line: int,
    column: int,
) -> int:
    """Convert AST line/column coordinates to an absolute offset."""

    return offsets[line - 1] + column


def _find_operator_offset(
    source_code: str,
    compare_node: ast.Compare,
    operator_text: str,
) -> Optional[int]:
    """
    Find the exact character offset of a comparison operator.

    Python's AST gives the comparison node's span but does not directly
    expose the operator's character span. We therefore search only
    inside the exact comparison expression.
    """

    offsets = _line_offsets(source_code)

    start = _absolute_offset(
        offsets,
        compare_node.lineno,
        compare_node.col_offset,
    )

    end = _absolute_offset(
        offsets,
        compare_node.end_lineno,
        compare_node.end_col_offset,
    )

    segment = source_code[start:end]

    index = segment.find(operator_text)

    if index == -1:
        return None

    return start + index


def _mutate_block_comparison(
    solution_code: str,
    start_line: int,
    end_line: int,
) -> Optional[tuple[str, str, str, int, int]]:
    """
    Mutate the first supported comparison operator inside a block.

    Returns:
        mutated_code,
        original_operator,
        mutated_operator,
        line,
        column

    or None when no supported comparison exists.
    """

    tree = ast.parse(solution_code)

    offsets = _line_offsets(solution_code)

    candidates = []

    for node in ast.walk(tree):

        if not isinstance(node, ast.Compare):
            continue

        # Only comparisons whose complete AST span lies inside the
        # requested block are eligible.
        if node.lineno < start_line:
            continue

        if node.end_lineno > end_line:
            continue

        for operator in node.ops:

            original_operator = _operator_text(operator)

            if original_operator is None:
                continue

            if original_operator not in COMPARISON_MUTATIONS:
                continue

            operator_offset = _find_operator_offset(
                solution_code,
                node,
                original_operator,
            )

            if operator_offset is None:
                continue

            candidates.append(
                (
                    operator_offset,
                    original_operator,
                    COMPARISON_MUTATIONS[original_operator],
                    node.lineno,
                )
            )

    if not candidates:
        return None

    # Deterministic: mutate the first eligible comparison.
    (
        operator_offset,
        original_operator,
        mutated_operator,
        line,
    ) = sorted(candidates)[0]

    mutated_code = (
        solution_code[:operator_offset]
        + mutated_operator
        + solution_code[
            operator_offset + len(original_operator):
        ]
    )

    # The mutation must still be valid Python.
    ast.parse(mutated_code)

    column = operator_offset - offsets[line - 1]

    return (
        mutated_code,
        original_operator,
        mutated_operator,
        line,
        column,
    )


def mutate_comparison(
    solution_code: str,
    step,
) -> MutationResult:
    """
    Apply one comparison mutation inside exactly one BlockStep.

    If no supported comparison exists in the target block,
    changed=False is returned.
    """

    result = _mutate_block_comparison(
        solution_code=solution_code,
        start_line=step.start_line,
        end_line=step.end_line,
    )

    if result is None:
        return MutationResult(
            problem_id=step.problem_id,
            solution_id=step.solution_id,
            step_id=step.step_id,
            mutation_type="comparison_swap",
            original_code=solution_code,
            mutated_code=solution_code,
            changed=False,
        )

    (
        mutated_code,
        original_operator,
        mutated_operator,
        line,
        column,
    ) = result

    return MutationResult(
        problem_id=step.problem_id,
        solution_id=step.solution_id,
        step_id=step.step_id,
        mutation_type="comparison_swap",
        original_code=solution_code,
        mutated_code=mutated_code,
        changed=True,
        original_operator=original_operator,
        mutated_operator=mutated_operator,
        line=line,
        column=column,
    )