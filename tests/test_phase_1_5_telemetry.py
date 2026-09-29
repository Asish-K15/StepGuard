"""
Unit tests for StepGuard Stage 1.4 Phase 1.5 Telemetry and Identity module.
Approved test coverage:
1. test_canonical_candidate_identity_direct
2. test_legacy_solution_identity_requires_explicit_mapping
3. test_no_silent_identity_equivalence
4. test_ambiguous_and_conflicting_identity_rejected
5. test_test_suite_identity_mandatory_and_no_defaults
6. test_candidate_deterministic_fingerprint
7. test_step_telemetry_aggregation
"""

import pytest

from partner_b.evidence.telemetry import (
    CandidateEvidenceRecord,
    CandidateIdentityMapping,
    MutationTelemetry,
    StepTelemetry,
    compute_candidate_fingerprint,
    compute_candidate_record_key,
    extract_candidate_steps,
    resolve_candidate_identity,
    validate_test_suite_id,
)
from shared.schema import CoverageStatus, DecompositionType, ExecutionOutcome


def test_canonical_candidate_identity_direct():
    """Test 1: Canonical candidate_id accepted directly without mapping."""
    canonical_id, legacy_id, is_mapped = resolve_candidate_identity(candidate_id="cand_mbpp_001_01")
    assert canonical_id == "cand_mbpp_001_01"
    assert legacy_id is None
    assert is_mapped is False

    # Also works with leading/trailing whitespace stripped
    canonical_id_stripped, _, _ = resolve_candidate_identity(candidate_id="  cand_mbpp_001_02  ")
    assert canonical_id_stripped == "cand_mbpp_001_02"


def test_legacy_solution_identity_requires_explicit_mapping():
    """Test 2: Legacy solution_id requires explicit, deterministic mapping."""
    # Without mapping, unmapped legacy solution_id is strictly rejected
    with pytest.raises(ValueError, match="explicit candidate identity mapping"):
        resolve_candidate_identity(solution_id="mbpp_001_sol_001")

    # With explicit mapping dict
    mapping = {"mbpp_001_sol_001": "cand_mbpp_001_sol_001"}
    canonical_id, legacy_id, is_mapped = resolve_candidate_identity(
        solution_id="mbpp_001_sol_001", mapping=mapping
    )
    assert canonical_id == "cand_mbpp_001_sol_001"
    assert legacy_id == "mbpp_001_sol_001"
    assert is_mapped is True

    # With CandidateIdentityMapping instance
    obj_mapping = CandidateIdentityMapping(mapping=mapping)
    canonical_id_2, legacy_id_2, is_mapped_2 = resolve_candidate_identity(
        solution_id="mbpp_001_sol_001", mapping=obj_mapping
    )
    assert canonical_id_2 == "cand_mbpp_001_sol_001"
    assert legacy_id_2 == "mbpp_001_sol_001"
    assert is_mapped_2 is True

    # Missing from mapping raises KeyError
    with pytest.raises(KeyError, match="not in the explicit candidate identity mapping"):
        resolve_candidate_identity(solution_id="unknown_solution", mapping=mapping)


def test_no_silent_identity_equivalence():
    """Test 3: Equivalence is NEVER inferred merely because solution_id and candidate_id strings match."""
    # When both are passed with the exact same string value, but without explicit mapping:
    with pytest.raises(ValueError, match="Equivalence cannot be silently inferred"):
        resolve_candidate_identity(
            candidate_id="same_id_value",
            solution_id="same_id_value",
            mapping=None,
        )


def test_ambiguous_and_conflicting_identity_rejected():
    """Test 4: Ambiguous or conflicting candidate identities fail fast."""
    # Case A: Neither candidate_id nor solution_id supplied
    with pytest.raises(ValueError, match="Missing candidate identity"):
        resolve_candidate_identity()

    with pytest.raises(ValueError, match="Missing candidate identity"):
        resolve_candidate_identity(candidate_id="", solution_id="  ")

    # Case B: Both supplied with mapping, but they conflict
    mapping = {"legacy_01": "cand_canonical_A"}
    with pytest.raises(ValueError, match="Conflicting identity"):
        resolve_candidate_identity(
            candidate_id="cand_canonical_B",
            solution_id="legacy_01",
            mapping=mapping,
        )

    # Case C: Both supplied with mapping and they agree
    canonical_id, legacy_id, is_mapped = resolve_candidate_identity(
        candidate_id="cand_canonical_A",
        solution_id="legacy_01",
        mapping=mapping,
    )
    assert canonical_id == "cand_canonical_A"
    assert legacy_id == "legacy_01"
    assert is_mapped is True

    # Case D: Invalid mapping type
    with pytest.raises(TypeError, match="mapping must be a dict or CandidateIdentityMapping"):
        resolve_candidate_identity(candidate_id="c1", mapping="not_a_mapping")


def test_test_suite_identity_mandatory_and_no_defaults():
    """Test 5: Canonical test_suite_id is strictly mandatory with no implicit defaults."""
    with pytest.raises(ValueError, match="Canonical test_suite_id is required"):
        validate_test_suite_id(None)

    with pytest.raises(ValueError, match="Canonical test_suite_id is required"):
        validate_test_suite_id("")

    with pytest.raises(ValueError, match="Canonical test_suite_id is required"):
        validate_test_suite_id("   ")

    # Valid suite ID is accepted and stripped
    valid_id = validate_test_suite_id("  mbpp_pilot_standard_tests  ")
    assert valid_id == "mbpp_pilot_standard_tests"


def test_candidate_deterministic_fingerprint():
    """Test 6: Candidate fingerprint is deterministic SHA-256 fingerprint/hash."""
    step = StepTelemetry(
        step_id="block_01",
        decomposition_type=DecompositionType.BLOCK,
        coverage_status=CoverageStatus.COVERED,
        executable_lines=[2, 3],
        executed_lines=[2, 3],
        line_coverage_ratio=1.0,
        mutations=[
            MutationTelemetry(
                mutation_type="comparison",
                original_operator="==",
                mutated_operator="!=",
                line=2,
                column=4,
                mutation_outcome="FAIL",
                detected=True,
            )
        ],
        start_line=2,
        end_line=3,
    )

    fp1 = compute_candidate_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_001",
        test_suite_id="suite_alpha",
        baseline_outcome=ExecutionOutcome.PASS,
        executed_lines=[2, 3],
        steps=[step],
        legacy_solution_id=None,
        identity_mapped=False,
    )

    # Identical inputs produce bitwise identical fingerprint
    fp2 = compute_candidate_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_001",
        test_suite_id="suite_alpha",
        baseline_outcome=ExecutionOutcome.PASS,
        executed_lines=[2, 3],
        steps=[step],
        legacy_solution_id=None,
        identity_mapped=False,
    )
    assert fp1 == fp2
    assert len(fp1) == 64

    # Altering candidate_id alters fingerprint
    fp_diff_cand = compute_candidate_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_002",
        test_suite_id="suite_alpha",
        baseline_outcome=ExecutionOutcome.PASS,
        executed_lines=[2, 3],
        steps=[step],
        legacy_solution_id=None,
        identity_mapped=False,
    )
    assert fp_diff_cand != fp1

    # Altering test_suite_id alters fingerprint
    fp_diff_suite = compute_candidate_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_001",
        test_suite_id="suite_beta",
        baseline_outcome=ExecutionOutcome.PASS,
        executed_lines=[2, 3],
        steps=[step],
        legacy_solution_id=None,
        identity_mapped=False,
    )
    assert fp_diff_suite != fp1

    # Top-level record key does NOT contain step_id
    rec_key = compute_candidate_record_key("mbpp_001", "cand_001", "suite_alpha")
    assert rec_key == "mbpp_001::cand_001::suite_alpha"
    assert "block_01" not in rec_key


def test_step_telemetry_aggregation():
    """Test 7: Step extraction decomposes candidates and produces valid steps."""
    code = (
        "def compute_sum(a, b):\n"
        "    if a > 0:\n"
        "        return a + b\n"
        "    return b\n"
    )
    steps = extract_candidate_steps("mbpp_001", "cand_001", code)
    assert len(steps) > 0

    func_steps = [s for s in steps if getattr(s, "decomposition_type", None) == DecompositionType.FUNCTION]
    block_steps = [s for s in steps if getattr(s, "decomposition_type", None) == DecompositionType.BLOCK]

    assert len(func_steps) == 1
    assert len(block_steps) >= 2
    assert func_steps[0].start_line == 1
    assert func_steps[0].end_line == 4
