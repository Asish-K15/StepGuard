"""Targeted mutation engine for StepGuard Stage 0A.

Current mutation types:
    B3.1 - comparison operator mutation
    B3.2 - boolean mutation

Design guarantees:
    - Mutation is restricted to the selected BlockStep.
    - Only one mutation is applied per result.
    - The resulting Python source must parse successfully.
    - Unchanged blocks return the original source unchanged.
"""

import ast
import re
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Mutation mappings
# ---------------------------------------------------------------------------

COMPARISON_MUTATIONS = {
    "==": "!=",
    "!=": "==",
    "<": ">=",
    ">=": "<",
    ">": "<=",
    "<=": ">",
}

BOOLEAN_MUTATIONS = {
    "and": "or",
    "or": "and",
    "True": "False",
    "False": "True",
}
OFF_BY_ONE_MUTATIONS = {
    "+ 1": "- 1",
    "- 1": "+ 1",
    "+1": "-1",
    "-1": "+1",
}

# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Shared source-position helpers
# ---------------------------------------------------------------------------

def _line_offsets(source_code: str) -> list[int]:
    """
    Return absolute character offsets for the beginning of every line.
    """

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
    """
    Convert a 1-based AST line and 0-based column to an absolute
    character offset.
    """

    return offsets[line - 1] + column


# ---------------------------------------------------------------------------
# Comparison mutation
# ---------------------------------------------------------------------------

def _operator_text(operator: ast.cmpop) -> Optional[str]:
    """
    Convert an AST comparison operator into source representation.
    """

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


def _find_operator_offset(
    source_code: str,
    compare_node: ast.Compare,
    operator_text: str,
) -> Optional[int]:
    """
    Find the exact character offset of a comparison operator.

    Search is restricted to the exact AST comparison expression.
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
    Find and mutate the first supported comparison operator completely
    contained within the target block.

    Returns:
        mutated_code,
        original_operator,
        mutated_operator,
        line,
        column

    or None if no supported comparison exists.
    """

    tree = ast.parse(solution_code)
    offsets = _line_offsets(solution_code)

    candidates = []

    for node in ast.walk(tree):

        if not isinstance(node, ast.Compare):
            continue

        # The complete comparison expression must belong to the target
        # block.
        if node.lineno < start_line:
            continue

        if node.end_lineno > end_line:
            continue

        for operator in node.ops:

            original_operator = _operator_text(operator)

            if original_operator is None:
                continue

            mutated_operator = COMPARISON_MUTATIONS.get(
                original_operator
            )

            if mutated_operator is None:
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
                    mutated_operator,
                    node.lineno,
                )
            )

    if not candidates:
        return None

    (
        operator_offset,
        original_operator,
        mutated_operator,
        line,
    ) = sorted(candidates, key=lambda item: item[0])[0]

    mutated_code = (
        solution_code[:operator_offset]
        + mutated_operator
        + solution_code[
            operator_offset + len(original_operator):
        ]
    )

    # Safety invariant: mutation must produce valid Python.
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
    Apply exactly one comparison mutation inside the selected BlockStep.

    If no supported comparison exists, return the original program
    unchanged with changed=False.
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


# ---------------------------------------------------------------------------
# Boolean mutation
# ---------------------------------------------------------------------------

def _find_boolean_mutation(
    solution_code: str,
    start_line: int,
    end_line: int,
):
    """
    Find the first supported boolean construct inside the target block.

    Supported:
        and -> or
        or  -> and
        True -> False
        False -> True

    Returns:
        absolute_offset,
        original_text,
        mutated_text,
        line

    or None if no supported boolean construct exists.
    """

    tree = ast.parse(solution_code)
    offsets = _line_offsets(solution_code)

    candidates = []

    for node in ast.walk(tree):

        # ---------------------------------------------------------------
        # Boolean operators: and / or
        # ---------------------------------------------------------------

        if isinstance(node, ast.BoolOp):

            if not (
                start_line <= node.lineno
                and node.end_lineno <= end_line
            ):
                continue

            if isinstance(node.op, ast.And):
                original = "and"
                mutated = "or"

            elif isinstance(node.op, ast.Or):
                original = "or"
                mutated = "and"

            else:
                continue

            start = _absolute_offset(
                offsets,
                node.lineno,
                node.col_offset,
            )

            end = _absolute_offset(
                offsets,
                node.end_lineno,
                node.end_col_offset,
            )

            segment = solution_code[start:end]

            # Match the exact boolean keyword token within the
            # AST source segment, regardless of surrounding spacing.
            match = re.search(
                rf"(?<![A-Za-z0-9_]){re.escape(original)}(?![A-Za-z0-9_])",
                segment,
            )

            if match is None:
                continue

            absolute_offset = start + match.start()

            candidates.append(
                (
                    absolute_offset,
                    original,
                    mutated,
                    node.lineno,
                )
            )

        # ---------------------------------------------------------------
        # Boolean constants: True / False
        # ---------------------------------------------------------------

        elif isinstance(node, ast.Constant):

            # IMPORTANT:
            # bool is a subclass of int in Python.
            # Therefore use `type(...) is bool` rather than isinstance().
            if type(node.value) is not bool:
                continue

            if not (
                start_line <= node.lineno
                and node.end_lineno <= end_line
            ):
                continue

            if node.value is True:
                original = "True"
                mutated = "False"
            else:
                original = "False"
                mutated = "True"

            absolute_offset = _absolute_offset(
                offsets,
                node.lineno,
                node.col_offset,
            )

            candidates.append(
                (
                    absolute_offset,
                    original,
                    mutated,
                    node.lineno,
                )
            )

    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda item: item[0],
    )[0]


def mutate_boolean(
    solution_code: str,
    step,
) -> MutationResult:
    """
    Apply exactly one boolean mutation inside the selected BlockStep.

    If no supported boolean construct exists, return the original
    program unchanged with changed=False.
    """

    result = _find_boolean_mutation(
        solution_code=solution_code,
        start_line=step.start_line,
        end_line=step.end_line,
    )

    if result is None:

        return MutationResult(
            problem_id=step.problem_id,
            solution_id=step.solution_id,
            step_id=step.step_id,
            mutation_type="boolean_flip",
            original_code=solution_code,
            mutated_code=solution_code,
            changed=False,
        )

    (
        offset,
        original,
        mutated,
        line,
    ) = result

    mutated_code = (
        solution_code[:offset]
        + mutated
        + solution_code[
            offset + len(original):
        ]
    )

    # Safety invariant: mutation must produce valid Python.
    ast.parse(mutated_code)

    offsets = _line_offsets(solution_code)
    column = offset - offsets[line - 1]

    return MutationResult(
        problem_id=step.problem_id,
        solution_id=step.solution_id,
        step_id=step.step_id,
        mutation_type="boolean_flip",
        original_code=solution_code,
        mutated_code=mutated_code,
        changed=True,
        original_operator=original,
        mutated_operator=mutated,
        line=line,
        column=column,
    )

def _build_parent_map(tree: ast.AST) -> dict:
    """Build child -> parent relationships for an AST."""
    parent_map = {}

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent

    return parent_map


def _is_subscript_offset(
    node: ast.BinOp,
    parent_map: dict,
) -> bool:
    """Return True when node is directly used as an index."""

    parent = parent_map.get(node)

    if not isinstance(parent, ast.Subscript):
        return False

    return parent.slice is node


def _is_range_argument(
    node: ast.BinOp,
    parent_map: dict,
) -> bool:
    """Return True when node is directly used as a range argument."""

    parent = parent_map.get(node)

    if not isinstance(parent, ast.Call):
        return False

    if not isinstance(parent.func, ast.Name):
        return False

    if parent.func.id != "range":
        return False

    return node in parent.args


def _find_binary_operator_offset(
    source_code: str,
    binop_node: ast.BinOp,
    operator_text: str,
):
    """Find the exact source position of + or -."""

    offsets = _line_offsets(source_code)

    start = _absolute_offset(
        offsets,
        binop_node.lineno,
        binop_node.col_offset,
    )

    end = _absolute_offset(
        offsets,
        binop_node.end_lineno,
        binop_node.end_col_offset,
    )

    segment = source_code[start:end]

    patterns = [
        f" {operator_text} ",
        f" {operator_text}",
        f"{operator_text} ",
    ]

    for pattern in patterns:
        index = segment.find(pattern)

        if index != -1:
            return (
                start
                + index
                + pattern.find(operator_text)
            )

    return None


def _find_off_by_one_mutation(
    solution_code: str,
    start_line: int,
    end_line: int,
):
    """
    Find the first index/range-aware off-by-one candidate.

    Supported:

        arr[i + 1] -> arr[i - 1]
        arr[i - 1] -> arr[i + 1]

        range(n + 1) -> range(n - 1)
        range(n - 1) -> range(n + 1)

    Arbitrary arithmetic such as x + 1 is ignored.
    """

    tree = ast.parse(solution_code)
    parent_map = _build_parent_map(tree)

    candidates = []

    for node in ast.walk(tree):

        if not isinstance(node, ast.BinOp):
            continue

        if not (
            start_line <= node.lineno
            and node.end_lineno <= end_line
        ):
            continue

        if not (
            isinstance(node.right, ast.Constant)
            and type(node.right.value) is int
            and node.right.value == 1
        ):
            continue

        if isinstance(node.op, ast.Add):
            original_operator = "+"
            mutated_operator = "-"

        elif isinstance(node.op, ast.Sub):
            original_operator = "-"
            mutated_operator = "+"

        else:
            continue

        is_index = _is_subscript_offset(
            node,
            parent_map,
        )

        is_range = _is_range_argument(
            node,
            parent_map,
        )

        if not (is_index or is_range):
            continue

        operator_offset = _find_binary_operator_offset(
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
                mutated_operator,
                node.lineno,
            )
        )

    if not candidates:
        return None

    return sorted(
        candidates,
        key=lambda item: item[0],
    )[0]


def mutate_off_by_one(
    solution_code: str,
    step,
) -> MutationResult:
    """
    Apply exactly one index/range-aware off-by-one mutation.
    """

    result = _find_off_by_one_mutation(
        solution_code=solution_code,
        start_line=step.start_line,
        end_line=step.end_line,
    )

    if result is None:

        return MutationResult(
            problem_id=step.problem_id,
            solution_id=step.solution_id,
            step_id=step.step_id,
            mutation_type="off_by_one",
            original_code=solution_code,
            mutated_code=solution_code,
            changed=False,
        )

    (
        operator_offset,
        original_operator,
        mutated_operator,
        line,
    ) = result

    mutated_code = (
        solution_code[:operator_offset]
        + mutated_operator
        + solution_code[
            operator_offset + len(original_operator):
        ]
    )

    ast.parse(mutated_code)

    offsets = _line_offsets(solution_code)
    column = operator_offset - offsets[line - 1]

    return MutationResult(
        problem_id=step.problem_id,
        solution_id=step.solution_id,
        step_id=step.step_id,
        mutation_type="off_by_one",
        original_code=solution_code,
        mutated_code=mutated_code,
        changed=True,
        original_operator=original_operator,
        mutated_operator=mutated_operator,
        line=line,
        column=column,
    )