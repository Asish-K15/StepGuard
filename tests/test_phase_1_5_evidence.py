"""
Unit tests for StepGuard Stage 1.4 Phase 1.5 Evidence generation and serialization.
Approved test coverage:
8. test_candidate_level_schema_serialization_roundtrip
9. test_precomputed_evidence_generation_spawns_zero_subprocesses
10. test_phase_1_5_summary_metrics_structure
11. test_tamper_detection
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from partner_b.evidence.phase_1_5 import (
    build_candidate_evidence,
    candidate_evidence_to_dict,
    dict_to_candidate_evidence,
    generate_phase_1_5_summary,
    generate_stage_1_4_phase_1_5_artifacts,
    read_phase_1_5_evidence,
    validate_candidate_evidence,
    write_phase_1_5_evidence,
    write_phase_1_5_summary,
)
from partner_b.evidence.telemetry import (
    CandidateEvidenceRecord,
    MutationTelemetry,
    StepTelemetry,
    compute_candidate_fingerprint,
    compute_candidate_record_key,
)
from shared.schema import CoverageStatus, DecompositionType, ExecutionOutcome


def _create_sample_record(candidate_id: str = "cand_001") -> CandidateEvidenceRecord:
    step_01 = StepTelemetry(
        step_id="func_01",
        decomposition_type=DecompositionType.FUNCTION,
        coverage_status=CoverageStatus.COVERED,
        executable_lines=[1, 2, 3],
        executed_lines=[1, 2, 3],
        line_coverage_ratio=1.0,
        mutations=[
            MutationTelemetry(
                mutation_type="comparison",
                original_operator="<",
                mutated_operator="<=",
                line=2,
                column=5,
                mutation_outcome="FAIL",
                detected=True,
                duration_seconds=0.01,
            )
        ],
        start_line=1,
        end_line=3,
    )
    step_02 = StepTelemetry(
        step_id="block_01",
        decomposition_type=DecompositionType.BLOCK,
        coverage_status=CoverageStatus.PARTIALLY_COVERED,
        executable_lines=[2, 3],
        executed_lines=[2],
        line_coverage_ratio=0.5,
        mutations=[],
        start_line=2,
        end_line=3,
    )

    steps = [step_01, step_02]
    step_executed_union = sorted(list({line for s in steps for line in s.executed_lines}))
    rec_key = compute_candidate_record_key("mbpp_001", candidate_id, "mbpp_pilot_standard_tests")
    fp = compute_candidate_fingerprint(
        problem_id="mbpp_001",
        candidate_id=candidate_id,
        test_suite_id="mbpp_pilot_standard_tests",
        baseline_outcome=ExecutionOutcome.PASS,
        executed_lines=step_executed_union,
        steps=steps,
        legacy_solution_id="mbpp_001_sol_001",
        identity_mapped=True,
    )

    return CandidateEvidenceRecord(
        problem_id="mbpp_001",
        candidate_id=candidate_id,
        test_suite_id="mbpp_pilot_standard_tests",
        baseline_outcome=ExecutionOutcome.PASS,
        total_executable_lines=3,
        total_executed_lines=2,
        candidate_line_coverage_ratio=2 / 3,
        steps=steps,
        record_key=rec_key,
        fingerprint=fp,
        legacy_solution_id="mbpp_001_sol_001",
        identity_mapped=True,
    )


def test_candidate_level_schema_serialization_roundtrip(tmp_path: Path):
    """Test 8: Full candidate JSONL round-trip validation with nested step telemetry."""
    rec = _create_sample_record("cand_test_rt")

    # 1. Candidate-level granularity assertion: step_id is NOT in record_key
    assert rec.record_key == "mbpp_001::cand_test_rt::mbpp_pilot_standard_tests"
    assert "func_01" not in rec.record_key
    assert "block_01" not in rec.record_key

    # 2. Dictionary serialization & validation
    d = candidate_evidence_to_dict(rec)
    validate_candidate_evidence(d)
    assert d["record_key"] == "mbpp_001::cand_test_rt::mbpp_pilot_standard_tests"
    assert len(d["steps"]) == 2
    assert d["steps"][0]["step_id"] == "func_01"
    assert len(d["steps"][0]["mutations"]) == 1

    # 3. Deserialization
    rec_back = dict_to_candidate_evidence(d)
    assert rec_back.problem_id == rec.problem_id
    assert rec_back.candidate_id == rec.candidate_id
    assert rec_back.test_suite_id == rec.test_suite_id
    assert rec_back.record_key == rec.record_key
    assert rec_back.fingerprint == rec.fingerprint
    assert len(rec_back.steps) == len(rec.steps)

    # 4. JSONL file write & read
    file_path = tmp_path / "evidence_test.jsonl"
    write_phase_1_5_evidence([rec], file_path)
    loaded_records = read_phase_1_5_evidence(file_path)

    assert len(loaded_records) == 1
    loaded = loaded_records[0]
    assert loaded.candidate_id == "cand_test_rt"
    assert loaded.record_key == rec.record_key
    assert loaded.fingerprint == rec.fingerprint
    assert loaded.steps[0].mutations[0].mutated_operator == "<="


def test_precomputed_evidence_generation_spawns_zero_subprocesses():
    """Test 9: Pure precomputed evidence assembly spawns zero child processes."""
    mock_tracer = MagicMock()
    code = "def sample(n):\n    return n * 2\n"

    # Precomputed mode (live_execution=False by default)
    rec = build_candidate_evidence(
        problem_id="mbpp_001",
        candidate_code=code,
        tests=["assert sample(2) == 4"],
        test_suite_id="mbpp_pilot_standard_tests",
        candidate_id="cand_precomputed_01",
        live_execution=False,
        tracer_fn=mock_tracer,
    )

    # Tracer must NOT be invoked at all
    assert mock_tracer.call_count == 0
    assert rec.baseline_outcome == ExecutionOutcome.PASS
    assert len(rec.steps) > 0

    # Also verify that full artifact generation in precomputed mode makes 0 subprocess calls
    with patch("subprocess.run") as mock_run, patch("subprocess.Popen") as mock_popen:
        generate_stage_1_4_phase_1_5_artifacts()
        assert mock_run.call_count == 0
        assert mock_popen.call_count == 0


def test_phase_1_5_summary_metrics_structure(tmp_path: Path):
    """Test 10: Validates schema and numerical consistency of summary.json."""
    r1 = _create_sample_record("cand_sum_01")
    r2 = _create_sample_record("cand_sum_02")
    records = [r1, r2]

    summary = generate_phase_1_5_summary(records)

    # Required top-level keys
    assert summary["stage"] == "1.4"
    assert summary["phase"] == "1.5"
    assert summary["record_granularity"] == "candidate_level"
    assert summary["total_candidates"] == 2

    # Numerical invariants
    assert summary["total_steps"] == summary["function_steps_count"] + summary["block_steps_count"]
    assert (
        summary["total_steps"]
        == summary["covered_steps_count"]
        + summary["partially_covered_steps_count"]
        + summary["unexecuted_steps_count"]
    )
    assert (
        summary["total_mutations_executed"]
        == summary["detected_mutations_count"] + summary["undetected_mutations_count"]
    )
    assert 0.0 <= summary["overall_line_coverage_ratio"] <= 1.0
    assert 0.0 <= summary["mutation_detection_rate"] <= 1.0

    # Serialization roundtrip
    summary_path = tmp_path / "summary.json"
    write_phase_1_5_summary(summary, summary_path)
    loaded_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert loaded_summary == summary


def test_tamper_detection():
    """Test 11: Tampering with record identity, keys, or telemetry triggers validation errors."""
    rec = _create_sample_record("cand_tamper_test")
    valid_dict = candidate_evidence_to_dict(rec)

    # Tamper 1: Tampered record key (e.g. injecting step_id into top-level key)
    tampered_key = dict(valid_dict)
    tampered_key["record_key"] = f"{valid_dict['record_key']}::func_01"
    with pytest.raises(ValueError, match="Record key mismatch"):
        validate_candidate_evidence(tampered_key)

    # Tamper 2: Tampered fingerprint
    tampered_fp = dict(valid_dict)
    tampered_fp["fingerprint"] = "0" * 64
    with pytest.raises(ValueError, match="Fingerprint mismatch"):
        validate_candidate_evidence(tampered_fp)

    # Tamper 3: Tampered internal step execution data without updating fingerprint
    tampered_step = dict(valid_dict)
    tampered_step["steps"] = [dict(s) for s in valid_dict["steps"]]
    tampered_step["steps"][0]["executed_lines"] = [999]
    with pytest.raises(ValueError, match="Fingerprint mismatch"):
        validate_candidate_evidence(tampered_step)

    # Tamper 4: Empty candidate identity
    tampered_cand = dict(valid_dict)
    tampered_cand["candidate_id"] = ""
    with pytest.raises(ValueError, match="non-empty canonical candidate_id"):
        dict_to_candidate_evidence(tampered_cand)

    # Tamper 5: Empty test suite identity
    tampered_suite = dict(valid_dict)
    tampered_suite["test_suite_id"] = "   "
    with pytest.raises(ValueError, match="Canonical test_suite_id is required"):
        validate_candidate_evidence(tampered_suite)
