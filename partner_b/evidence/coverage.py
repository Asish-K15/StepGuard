"""
AST Statement Reachability and Step Coverage Mapping for StepGuard Stage 1.4 (Phase 1).

Maps dynamic executed-line traces to AST decomposition steps (FunctionStep and BlockStep).
Evaluates statement/executed-line reachability (NOT branch coverage) and supports
multi-granularity line attribution across hierarchical steps.
"""

import ast
from typing import Any, Iterable, List, Sequence, Set, Union

from shared.schema import CoverageStatus, ExecutionTrace, StepCoverage


def extract_executable_lines(source_code: str) -> List[int]:
    """
    Extract line numbers of executable statements from Python source code.

    Filters out:
    - Blank lines
    - Standalone comments (which produce no AST nodes)
    - Module, function, and class docstrings
    - Standalone string literal expressions

    Returns:
        Sorted list of 1-based line numbers containing executable statements.
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    docstring_lines: Set[int] = set()

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                docstring_lines.add(node.body[0].lineno)

    executable_lines: Set[int] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.stmt):
            if node.lineno in docstring_lines:
                continue

            # Skip standalone string literal expressions acting as inline comments/docstrings
            if (
                isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                continue

            executable_lines.add(node.lineno)

    return sorted(executable_lines)


def _get_executed_set(trace_or_lines: Union[ExecutionTrace, Iterable[int]]) -> Set[int]:
    """Extract set of executed line numbers from ExecutionTrace or iterable of ints."""
    if isinstance(trace_or_lines, ExecutionTrace):
        return set(trace_or_lines.executed_lines)
    return set(trace_or_lines)


def map_step_coverage(
    step: Any,
    candidate_code: str,
    trace_or_lines: Union[ExecutionTrace, Iterable[int]],
) -> StepCoverage:
    """
    Map dynamic executed-line traces to a single decomposition step.

    Parameters:
        step: BlockStep or FunctionStep instance with start_line, end_line, step_id, etc.
        candidate_code: Full candidate source code.
        trace_or_lines: ExecutionTrace object or iterable of executed line numbers.

    Returns:
        StepCoverage with executable lines, executed lines, reachability ratio, and status.
    """
    all_executable = extract_executable_lines(candidate_code)
    executed_set = _get_executed_set(trace_or_lines)

    start_line = getattr(step, "start_line", 1)
    end_line = getattr(step, "end_line", len(candidate_code.splitlines()))

    step_executable = [
        line for line in all_executable if start_line <= line <= end_line
    ]
    step_executed = [line for line in step_executable if line in executed_set]

    if step_executable and len(step_executed) == len(step_executable):
        status = CoverageStatus.COVERED
    elif step_executed:
        status = CoverageStatus.PARTIALLY_COVERED
    else:
        status = CoverageStatus.UNEXECUTED

    ratio = (
        len(step_executed) / len(step_executable)
        if step_executable
        else 0.0
    )

    return StepCoverage(
        problem_id=getattr(step, "problem_id", ""),
        solution_id=getattr(step, "solution_id", ""),
        step_id=getattr(step, "step_id", ""),
        decomposition_type=getattr(step, "decomposition_type"),
        executable_lines=step_executable,
        executed_lines=step_executed,
        coverage_status=status,
        line_coverage_ratio=ratio,
    )


def map_steps_coverage(
    steps: Sequence[Any],
    candidate_code: str,
    trace_or_lines: Union[ExecutionTrace, Iterable[int]],
) -> List[StepCoverage]:
    """
    Map dynamic executed-line traces across an entire sequence of decomposition steps.
    """
    return [
        map_step_coverage(step, candidate_code, trace_or_lines)
        for step in steps
    ]
