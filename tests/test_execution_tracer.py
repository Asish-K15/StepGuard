"""
Unit tests for Partner B subprocess-isolated execution tracer (StepGuard Stage 1.4 Phase 1).
"""

import sys
import time
import pytest

from partner_b.execution.tracer import trace_candidate_execution
from shared.schema import ExecutionOutcome


def test_subprocess_timeout_enforcement():
    """Criterion 1: Subprocess-level timeout enforcement and process cleanup."""
    code = """
def infinite_loop():
    while True:
        pass

infinite_loop()
"""
    tests = ["assert True"]

    start = time.perf_counter()
    trace = trace_candidate_execution(code, tests, timeout_seconds=2.0)
    elapsed = time.perf_counter() - start

    assert trace.status == ExecutionOutcome.TIMEOUT
    assert trace.returncode is None
    assert trace.executed_lines == []
    assert trace.exception_type == "TimeoutExpired"
    assert elapsed < 3.5, f"Execution took {elapsed:.2f}s, expected < 3.5s"


@pytest.mark.parametrize(
    "code,tests,expected_status,expected_exc_type",
    [
        (
            "def add(a, b):\n    return a + b\n",
            ["assert add(2, 3) == 5"],
            ExecutionOutcome.PASS,
            None,
        ),
        (
            "def add(a, b):\n    return a + b\n",
            ["assert add(2, 3) == 99"],
            ExecutionOutcome.ASSERTION_FAILURE,
            "AssertionError",
        ),
        (
            "def div(a, b):\n    return a / b\nres = div(10, 0)\n",
            ["assert True"],
            ExecutionOutcome.RUNTIME_EXCEPTION,
            "ZeroDivisionError",
        ),
        (
            "def bad_syntax(:\n    pass\n",
            ["assert True"],
            ExecutionOutcome.SYNTAX_ERROR,
            "SyntaxError",
        ),
        (
            "import os\nos._exit(139)\n",
            ["assert True"],
            ExecutionOutcome.INFRASTRUCTURE_FAILURE,
            "InfrastructureFailure",
        ),
    ],
)
def test_outcome_taxonomy(code, tests, expected_status, expected_exc_type):
    """Criterion 2: Unified ExecutionOutcome taxonomy differentiation."""
    trace = trace_candidate_execution(code, tests, timeout_seconds=5.0)

    assert trace.status == expected_status
    if expected_exc_type is not None:
        assert trace.exception_type == expected_exc_type
    else:
        assert trace.exception_type is None


def test_tracer_cleanup_isolation():
    """Criterion 5: Child-to-parent tracer containment and cleanup invariant."""
    parent_trace_before = sys.gettrace()

    crashing_code = "def boom():\n    raise ValueError('explosion')\nboom()\n"
    trace = trace_candidate_execution(crashing_code, ["assert True"], timeout_seconds=3.0)

    assert trace.status == ExecutionOutcome.RUNTIME_EXCEPTION
    assert trace.exception_type == "ValueError"

    parent_trace_after = sys.gettrace()
    assert parent_trace_before == parent_trace_after


def test_executed_lines_tracking():
    """Verify executed lines inside function bodies are correctly recorded."""
    code = (
        "def branch_fn(x):\n"
        "    if x > 0:\n"
        "        y = x * 2\n"
        "    else:\n"
        "        y = -x\n"
        "    return y\n"
    )
    tests = ["assert branch_fn(5) == 10"]
    trace = trace_candidate_execution(code, tests, timeout_seconds=3.0)

    assert trace.status == ExecutionOutcome.PASS
    # Lines 1 (def), 2 (if), 3 (y = x * 2), 6 (return) should be executed
    assert 1 in trace.executed_lines
    assert 2 in trace.executed_lines
    assert 3 in trace.executed_lines
    assert 6 in trace.executed_lines
    # Line 5 (else branch) must NOT be executed
    assert 5 not in trace.executed_lines
