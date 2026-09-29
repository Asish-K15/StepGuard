"""
Unit tests for StepGuard Stage 1.4 Phase 1.5 Process isolation, timeouts, and baseline artifact preservation.
Approved test coverage:
12. test_unexecuted_step_bypasses_mutations
13. test_covered_step_executes_mutations_under_opt_in
14. test_baseline_crash_aborts_all_mutations
15. test_process_timeout_and_containment
16. test_frozen_baseline_artifacts_remain_unmodified
"""

import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from partner_b.evidence.phase_1_5 import build_candidate_evidence
from partner_b.execution.tracer import trace_candidate_execution
from shared.schema import CoverageStatus, ExecutionOutcome


ROOT = Path(__file__).resolve().parents[1]


def test_unexecuted_step_bypasses_mutations():
    """Test 12: Live opt-in confirms 0 mutation subprocesses for unreached step (MBPP Task 783 block_08)."""
    prob_file = ROOT / "data" / "problems" / "mbpp_003.json"
    prob_data = json.loads(prob_file.read_text(encoding="utf-8"))
    code = prob_data["code"]
    tests = prob_data["test_list"]

    # Wrap trace_candidate_execution to track all calls
    recorded_calls = []

    def spy_tracer(c, t, timeout_seconds=5.0):
        recorded_calls.append(c)
        return trace_candidate_execution(c, t, timeout_seconds=timeout_seconds)

    rec = build_candidate_evidence(
        problem_id="mbpp_003",
        candidate_code=code,
        tests=tests,
        test_suite_id="mbpp_pilot_standard_tests",
        candidate_id="cand_mbpp_003_opt_in",
        live_execution=True,  # Opt-in live execution
        tracer_fn=spy_tracer,
    )

    block_08 = next((s for s in rec.steps if s.step_id == "block_08"), None)
    assert block_08 is not None, "block_08 must exist in MBPP Task 783"
    assert block_08.coverage_status == CoverageStatus.UNEXECUTED
    assert len(block_08.mutations) == 0

    # Ensure no calls were made to tracer for mutated codes modifying lines 12 or 13 (block_08)
    for called_code in recorded_calls[1:]:  # skip baseline
        lines = called_code.splitlines()
        # Verify lines 12 and 13 match original code
        orig_lines = code.splitlines()
        assert lines[11] == orig_lines[11]
        assert lines[12] == orig_lines[12]


def test_covered_step_executes_mutations_under_opt_in():
    """Test 13: Live opt-in executes mutations on covered steps (e.g. block_05)."""
    prob_file = ROOT / "data" / "problems" / "mbpp_003.json"
    prob_data = json.loads(prob_file.read_text(encoding="utf-8"))
    code = prob_data["code"]
    tests = prob_data["test_list"]

    rec = build_candidate_evidence(
        problem_id="mbpp_003",
        candidate_code=code,
        tests=tests,
        test_suite_id="mbpp_pilot_standard_tests",
        candidate_id="cand_mbpp_003_opt_in_covered",
        live_execution=True,
    )

    block_05 = next((s for s in rec.steps if s.step_id == "block_05"), None)
    assert block_05 is not None
    assert block_05.coverage_status == CoverageStatus.COVERED
    assert len(block_05.mutations) > 0

    # At least one mutation was tested and produced valid outcome telemetry
    mut = block_05.mutations[0]
    assert mut.mutation_outcome in (
        "PASS",
        "ASSERTION_FAILURE",
        "RUNTIME_EXCEPTION",
        "TIMEOUT",
        "SYNTAX_ERROR",
    )
    assert isinstance(mut.detected, bool)


def test_baseline_crash_aborts_all_mutations():
    """Test 14: Syntax/runtime crash in baseline halts all mutation execution immediately."""
    broken_code = (
        "def crashing_candidate(x):\n"
        "    if x > 0:\n"
        "        raise RuntimeError('Deliberate baseline crash')\n"
        "    return 0\n"
    )
    tests = ["assert crashing_candidate(5) == 0"]

    spy_tracer = MagicMock(side_effect=trace_candidate_execution)

    rec = build_candidate_evidence(
        problem_id="mbpp_test_crash",
        candidate_code=broken_code,
        tests=tests,
        test_suite_id="mbpp_pilot_standard_tests",
        candidate_id="cand_crashing_01",
        live_execution=True,
        tracer_fn=spy_tracer,
    )

    # Baseline failed
    assert rec.baseline_outcome in (
        ExecutionOutcome.RUNTIME_EXCEPTION,
        ExecutionOutcome.ASSERTION_FAILURE,
    )

    # Tracer was called ONLY once (for baseline), zero times for mutations
    assert spy_tracer.call_count == 1

    # All steps have zero mutations (aborted)
    for s in rec.steps:
        assert len(s.mutations) == 0


def test_process_timeout_and_containment():
    """Test 15: Subprocess timeout terminates hanging candidates safely without deadlock."""
    infinite_loop_code = (
        "def hanging_candidate(n):\n"
        "    while True:\n"
        "        pass\n"
        "    return n\n"
    )
    tests = ["assert hanging_candidate(1) == 1"]

    rec = build_candidate_evidence(
        problem_id="mbpp_test_timeout",
        candidate_code=infinite_loop_code,
        tests=tests,
        test_suite_id="mbpp_pilot_standard_tests",
        candidate_id="cand_hanging_01",
        live_execution=True,
        timeout_seconds=1.0,
    )

    assert rec.baseline_outcome == ExecutionOutcome.TIMEOUT
    for s in rec.steps:
        assert len(s.mutations) == 0


def test_frozen_baseline_artifacts_remain_unmodified():
    """Test 16: Byte-for-byte SHA-256 verification of historical evidence artifacts."""
    expected_hashes = {
        ROOT / "data" / "evidence" / "step_evidence.jsonl": (
            "554aa8621f9edb33e82c0970d1b37d5ba16dc25220e50e0e0acda953a87d0c23"
        ),
        ROOT / "data" / "evidence" / "step_analysis.jsonl": (
            "e22a7c5fcc1fce9ace488cdcf95bafc67a584f0705412c857cd2516a8f1b4746"
        ),
        ROOT / "data" / "mutations" / "mutation_execution_results.jsonl": (
            "554aa8621f9edb33e82c0970d1b37d5ba16dc25220e50e0e0acda953a87d0c23"
        ),
        ROOT / "data" / "solutions" / "baseline_results.jsonl": (
            "8fa60269ce982201c8d36951b840354ff8af9df06b01705d8d685457cc2072b0"
        ),
        ROOT / "data" / "solutions" / "candidates.jsonl": (
            "96ceecb77630e48076c67c7361c6891d4e934ad757e37b1f9428b6f117a0c62c"
        ),
    }

    for path, expected_sha in expected_hashes.items():
        assert path.exists(), f"Frozen historical artifact {path} is missing!"
        actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, (
            f"Frozen historical artifact {path.name} was modified! "
            f"Expected {expected_sha}, got {actual_sha}"
        )
