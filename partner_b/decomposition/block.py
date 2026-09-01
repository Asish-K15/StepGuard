"""
Non-overlapping block-level AST decomposition for StepGuard Stage 0A.

A block is a logical, mutation-targetable region.

Design rules:
1. Returned blocks must not overlap.
2. Simple executable statements are blocks.
3. If/elif/else branches are blocks.
4. Loop containers are structural context, not mutation targets.
5. Nested control-flow is recursively decomposed.
"""

import ast
from dataclasses import dataclass
from typing import List, Sequence

from shared.schema import DecompositionType


@dataclass
class BlockStep:
    problem_id: str
    solution_id: str
    decomposition_type: DecompositionType
    step_id: str
    step_text: str
    start_line: int
    end_line: int


def _source_segment(source_code: str, node: ast.AST) -> str:
    """Return exact source text for an AST node."""

    segment = ast.get_source_segment(source_code, node)

    if segment is not None:
        return segment

    lines = source_code.splitlines()

    if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
        return "\n".join(
            lines[node.lineno - 1:node.end_lineno]
        )

    return ""


def _add_step(
    steps: List[BlockStep],
    problem_id: str,
    solution_id: str,
    source_code: str,
    node: ast.AST,
) -> None:
    """Add one non-overlapping source region."""

    steps.append(
        BlockStep(
            problem_id=problem_id,
            solution_id=solution_id,
            decomposition_type=DecompositionType.BLOCK,
            step_id=f"block_{len(steps) + 1:02d}",
            step_text=_source_segment(source_code, node),
            start_line=node.lineno,
            end_line=node.end_lineno,
        )
    )


def _add_branch(
    steps: List[BlockStep],
    problem_id: str,
    solution_id: str,
    source_code: str,
    start_line: int,
    end_line: int,
) -> None:
    """Add a branch using its complete source span."""

    lines = source_code.splitlines()

    text = "\n".join(
        lines[start_line - 1:end_line]
    )

    steps.append(
        BlockStep(
            problem_id=problem_id,
            solution_id=solution_id,
            decomposition_type=DecompositionType.BLOCK,
            step_id=f"block_{len(steps) + 1:02d}",
            step_text=text,
            start_line=start_line,
            end_line=end_line,
        )
    )


def _decompose_sequence(
    body: Sequence[ast.stmt],
    source_code: str,
    problem_id: str,
    solution_id: str,
    steps: List[BlockStep],
) -> None:
    """Decompose statements into non-overlapping logical blocks."""

    for node in body:

        # Simple executable statements.
        if isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
                ast.AugAssign,
                ast.Expr,
                ast.Return,
                ast.Raise,
                ast.Assert,
                ast.Delete,
                ast.Pass,
                ast.Break,
                ast.Continue,
            ),
        ):
            _add_step(
                steps,
                problem_id,
                solution_id,
                source_code,
                node,
            )
            continue

        # Conditional branches.
        if isinstance(node, ast.If):
            _decompose_if(
                node,
                source_code,
                problem_id,
                solution_id,
                steps,
            )
            continue

        # Loops are structural context.
        # We do NOT add the entire loop as a block.
        if isinstance(
            node,
            (
                ast.For,
                ast.AsyncFor,
                ast.While,
            ),
        ):
            _decompose_sequence(
                node.body,
                source_code,
                problem_id,
                solution_id,
                steps,
            )

            _decompose_sequence(
                node.orelse,
                source_code,
                problem_id,
                solution_id,
                steps,
            )
            continue

        # Try/except/finally.
        if isinstance(node, ast.Try):
            _decompose_try(
                node,
                source_code,
                problem_id,
                solution_id,
                steps,
            )
            continue

        # With statements.
        if isinstance(
            node,
            (
                ast.With,
                ast.AsyncWith,
            ),
        ):
            _decompose_sequence(
                node.body,
                source_code,
                problem_id,
                solution_id,
                steps,
            )
            continue

        # Match statements.
        if isinstance(node, ast.Match):
            for case in node.cases:
                _decompose_sequence(
                    case.body,
                    source_code,
                    problem_id,
                    solution_id,
                    steps,
                )


def _decompose_if(
    node: ast.If,
    source_code: str,
    problem_id: str,
    solution_id: str,
    steps: List[BlockStep],
) -> None:
    """
    Represent each if/elif/else branch as a logical block.

    Nested control-flow inside a branch is handled separately.
    """

    current = node

    while True:

        if current.body:

            start_line = current.lineno
            end_line = current.body[-1].end_lineno

            _add_branch(
                steps,
                problem_id,
                solution_id,
                source_code,
                start_line,
                end_line,
            )

        # elif
        if (
            len(current.orelse) == 1
            and isinstance(current.orelse[0], ast.If)
        ):
            current = current.orelse[0]
            continue

        # else
        if current.orelse:

            else_body = current.orelse

            start_line = else_body[0].lineno
            end_line = else_body[-1].end_lineno

            lines = source_code.splitlines()

            # Find the actual "else:" line above the body.
            else_index = start_line - 2

            while else_index >= 0:
                if lines[else_index].strip() == "else:":
                    start_line = else_index + 1
                    break

                else_index -= 1

            _add_branch(
                steps,
                problem_id,
                solution_id,
                source_code,
                start_line,
                end_line,
            )

        break

    # Recursively process nested control-flow.
    for child in node.body:

        if isinstance(
            child,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.With,
                ast.AsyncWith,
                ast.Match,
            ),
        ):
            _decompose_sequence(
                [child],
                source_code,
                problem_id,
                solution_id,
                steps,
            )


def _decompose_try(
    node: ast.Try,
    source_code: str,
    problem_id: str,
    solution_id: str,
    steps: List[BlockStep],
) -> None:

    _decompose_sequence(
        node.body,
        source_code,
        problem_id,
        solution_id,
        steps,
    )

    for handler in node.handlers:
        _decompose_sequence(
            handler.body,
            source_code,
            problem_id,
            solution_id,
            steps,
        )

    _decompose_sequence(
        node.orelse,
        source_code,
        problem_id,
        solution_id,
        steps,
    )

    _decompose_sequence(
        node.finalbody,
        source_code,
        problem_id,
        solution_id,
        steps,
    )


def decompose_blocks(
    problem_id: str,
    solution_id: str,
    source_code: str,
) -> List[BlockStep]:
    """Decompose Python source into non-overlapping logical blocks."""

    tree = ast.parse(source_code)

    steps: List[BlockStep] = []

    for node in tree.body:

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            _decompose_sequence(
                node.body,
                source_code,
                problem_id,
                solution_id,
                steps,
            )

    return steps