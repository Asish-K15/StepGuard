"""
Unit tests for Partner B AST statement reachability and step coverage mapping (StepGuard Stage 1.4 Phase 1).
"""

import json
from pathlib import Path

from partner_b.decomposition.block import decompose_blocks
from partner_b.decomposition.function import decompose_functions
from partner_b.evidence.coverage import (
    extract_executable_lines,
    map_step_coverage,
    map_steps_coverage,
)
from partner_b.execution.tracer import trace_candidate_execution
from shared.schema import CoverageStatus, DecompositionType


ROOT = Path(__file__).resolve().parents[1]


def test_unreached_branch_reachability():
    """Criterion 3: Unreached statement reachability detection on MBPP Task 783."""
    problem_file = ROOT / "data" / "problems" / "mbpp_003.json"
    problem_data = json.loads(problem_file.read_text(encoding="utf-8"))

    code = problem_data["code"]
    original_tests = problem_data["test_list"]

    # Decompose into block steps
    blocks = decompose_blocks("mbpp_003", "mbpp_003_sol_001", code)
    block_08 = next((b for b in blocks if b.step_id == "block_08"), None)
    assert block_08 is not None, "block_08 (blue dominant branch) must exist"

    # Trace execution under original tests
    trace = trace_candidate_execution(code, original_tests)

    # Map coverage for block_08
    step_cov = map_step_coverage(block_08, code, trace)

    assert step_cov.step_id == "block_08"
    assert step_cov.executable_lines == [12, 13]
    assert step_cov.executed_lines == []
    assert step_cov.coverage_status == CoverageStatus.UNEXECUTED
    assert step_cov.line_coverage_ratio == 0.0


def test_nested_step_line_sharing():
    """Criterion 4: Multi-granularity step mapping & line sharing across hierarchies."""
    problem_file = ROOT / "data" / "problems" / "mbpp_003.json"
    problem_data = json.loads(problem_file.read_text(encoding="utf-8"))

    code = problem_data["code"]
    tests = problem_data["test_list"]

    funcs = decompose_functions("mbpp_003", "mbpp_003_sol_001", code)
    blocks = decompose_blocks("mbpp_003", "mbpp_003_sol_001", code)

    func_01 = funcs[0]
    block_05 = next(b for b in blocks if b.step_id == "block_05")

    trace = trace_candidate_execution(code, tests)

    func_cov = map_step_coverage(func_01, code, trace)
    block_cov = map_step_coverage(block_05, code, trace)

    # Line 6 is 'if mx == mn:' which executed under tests
    assert 6 in func_cov.executed_lines
    assert 6 in block_cov.executed_lines

    # func_01 contains lines 10-13 which were not executed, so it is PARTIALLY_COVERED
    assert func_cov.coverage_status == CoverageStatus.PARTIALLY_COVERED

    # block_05 has lines [6, 7] both executed, so it is COVERED
    assert block_cov.coverage_status == CoverageStatus.COVERED

    # Verify intra-granularity invariant: block steps must be non-overlapping
    for i, b1 in enumerate(blocks):
        for j, b2 in enumerate(blocks):
            if i != j:
                range1 = set(range(b1.start_line, b1.end_line + 1))
                range2 = set(range(b2.start_line, b2.end_line + 1))
                assert range1.isdisjoint(range2), (
                    f"Block steps {b1.step_id} and {b2.step_id} overlap!"
                )


def test_docstrings_and_comments_excluded():
    """Verify docstrings, comments, and empty lines are excluded from executable statements."""
    code = (
        'def demo(x):\n'
        '    """Function docstring that should not be counted."""\n'
        '    # A standalone comment\n'
        '\n'
        '    y = x + 1\n'
        '    return y\n'
    )
    executable = extract_executable_lines(code)
    # Line 1 (def), Line 5 (y = x + 1), Line 6 (return y)
    assert executable == [1, 5, 6]
    assert 2 not in executable  # docstring
    assert 3 not in executable  # comment
    assert 4 not in executable  # empty line


def test_batch_coverage_mapping():
    """Verify batch mapping over all steps for a solution."""
    code = "def f(x):\n    return x * 2\n"
    blocks = decompose_blocks("prob_01", "sol_01", code)
    trace = trace_candidate_execution(code, ["assert f(3) == 6"])

    all_cov = map_steps_coverage(blocks, code, trace)
    assert len(all_cov) == len(blocks)
    for cov in all_cov:
        assert cov.coverage_status == CoverageStatus.COVERED
        assert cov.line_coverage_ratio == 1.0
