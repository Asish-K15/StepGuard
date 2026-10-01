"""
Tests for StepGuard Stage 1.4 Phase 1.7 Analysis and Lineage Contracts.
"""

from pathlib import Path
import pytest
import json

from partner_b.evidence.phase_1_7 import (
    discover_phase_1_persisted_artifacts,
    validate_input_contracts,
    build_candidate_lineage_records,
    compile_summary_document,
)
from partner_b.evidence.phase_1_7_schema import (
    APPROVED_RELATIONSHIPS,
    DISCLAIMER_TEXT,
    DATA_AVAILABILITY_NOTICE,
    PROCESS_ISOLATION_NOTICE,
    FORBIDDEN_VERDICT_TERMS,
    CandidateLineageRecord,
    PhaseContractRelationshipRecord,
    candidate_lineage_to_dict,
    dict_to_candidate_lineage,
    contract_relationship_to_dict,
    dict_to_contract_relationship,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_discover_phase_1_persisted_artifacts_returns_unavailable(repo_root: Path):
    """Confirm active discovery confirms 0 persisted Phase 1 candidate trace files."""
    audit = discover_phase_1_persisted_artifacts(repo_root)
    assert audit["persisted_candidate_records_found"] is False
    assert len(audit["discovered_files"]) == 0
    assert "in-memory only" in audit["audit_note"]


def test_input_loading_and_contract_validation(repo_root: Path):
    """Verify loading and contract validation of Phase 1.5 and 1.6 inputs."""
    (
        p15_recs,
        p15_sum,
        p16_recs,
        p16_sum,
        digests,
    ) = validate_input_contracts(repo_root)

    assert len(p15_recs) == 25
    assert len(p16_recs) == 25
    assert len(digests) == 5
    assert "data/evidence/stage_1_4_phase_1_5/evidence.jsonl" in digests
    assert "data/evidence/stage_1_4_phase_1_6/analysis.jsonl" in digests


def test_candidate_lineage_record_generation_and_vocabulary(repo_root: Path):
    """Verify candidate lineage records strictly adhere to the approved relationship vocabulary."""
    (
        p15_recs,
        _,
        p16_recs,
        _,
        _,
    ) = validate_input_contracts(repo_root)

    cand_recs, contract_recs, audit = build_candidate_lineage_records(p15_recs, p16_recs)

    assert len(cand_recs) == 25
    assert len(contract_recs) == 2
    assert audit["conflict_count"] == 0

    for cand in cand_recs:
        assert cand.record_type == "candidate_observation"
        assert cand.identity_mapped is True
        assert cand.notices["evaluation_disclaimer"] == DISCLAIMER_TEXT
        assert cand.notices["data_availability_notice"] == DATA_AVAILABILITY_NOTICE
        assert cand.notices["process_isolation_notice"] == PROCESS_ISOLATION_NOTICE

        # Verify all relationships are within approved vocabulary
        for target, rel in cand.relationships.items():
            status = rel["status"]
            assert status in APPROVED_RELATIONSHIPS

        assert cand.relationships["phase_1_persisted_trace"]["status"] == "UNAVAILABLE"
        assert cand.relationships["phase_1_contract"]["status"] == "DESCRIPTIVE_ONLY"
        assert cand.relationships["phase_1_5_evidence"]["status"] == "DIRECTLY_LINKED"
        assert cand.relationships["phase_1_6_analysis"]["status"] == "DIRECTLY_LINKED"
        assert cand.relationships["legacy_stage_0a"]["status"] == "DESCRIPTIVE_ONLY"

    for cr in contract_recs:
        assert cr.record_type == "phase_contract_relationship"
        assert cr.relationship_status in APPROVED_RELATIONSHIPS
        assert cr.disclaimer == DISCLAIMER_TEXT


def test_conflict_detection_marks_ambiguous():
    """Verify conflicting duplicate candidate identities are explicitly detected and marked AMBIGUOUS."""
    base_rec = {
        "problem_id": "mbpp_001",
        "candidate_id": "cand_01",
        "test_suite_id": "standard",
        "baseline_outcome": "PASS",
        "total_executable_lines": 5,
        "total_executed_lines": 5,
        "candidate_line_coverage_ratio": 1.0,
        "steps": [],
        "fingerprint": "fp_01",
        "legacy_solution_id": "sol_01",
        "identity_mapped": True,
    }
    # Duplicate with conflicting fingerprint
    conflicting_rec = dict(base_rec)
    conflicting_rec["fingerprint"] = "fp_CONFLICTING"

    cand_recs, _, audit = build_candidate_lineage_records(
        phase_1_5_records=[base_rec, conflicting_rec],
        phase_1_6_records=[],
    )

    assert audit["conflict_count"] == 1
    assert len(cand_recs) == 1
    assert cand_recs[0].relationships["phase_1_5_evidence"]["status"] == "AMBIGUOUS"


def test_strictly_no_evaluative_or_correctness_terms(repo_root: Path):
    """Verify no forbidden evaluative, correctness, or ranking terms appear in Phase 1.7 records."""
    (p15_recs, _, p16_recs, _, _) = validate_input_contracts(repo_root)
    cand_recs, contract_recs, _ = build_candidate_lineage_records(p15_recs, p16_recs)

    def scan_for_forbidden(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                k_lower = k.lower()
                for term in FORBIDDEN_VERDICT_TERMS:
                    assert term not in k_lower, f"Forbidden term '{term}' in key '{path}.{k}'"
                scan_for_forbidden(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                scan_for_forbidden(item, f"{path}[{i}]")
        elif isinstance(obj, str):
            # Exclude known legal notices from substring search
            if obj in (DISCLAIMER_TEXT, DATA_AVAILABILITY_NOTICE, PROCESS_ISOLATION_NOTICE):
                return
            obj_lower = obj.lower()
            for term in FORBIDDEN_VERDICT_TERMS:
                assert term not in obj_lower, f"Forbidden term '{term}' in value at '{path}': {obj}"

    for cand in cand_recs:
        d = candidate_lineage_to_dict(cand)
        scan_for_forbidden(d)

    for cr in contract_recs:
        d = contract_relationship_to_dict(cr)
        scan_for_forbidden(d)


def test_serialization_roundtrip(repo_root: Path):
    """Verify lossless serialization and deserialization of CandidateLineageRecord and PhaseContractRelationshipRecord."""
    (p15_recs, _, p16_recs, _, _) = validate_input_contracts(repo_root)
    cand_recs, contract_recs, _ = build_candidate_lineage_records(p15_recs, p16_recs)

    for cand in cand_recs:
        d = candidate_lineage_to_dict(cand)
        s = json.dumps(d)
        restored = dict_to_candidate_lineage(json.loads(s))
        assert restored.record_key == cand.record_key
        assert restored.lineage_fingerprint == cand.lineage_fingerprint
        assert restored.relationships == cand.relationships

    for cr in contract_recs:
        d = contract_relationship_to_dict(cr)
        s = json.dumps(d)
        restored = dict_to_contract_relationship(json.loads(s))
        assert restored.relationship_id == cr.relationship_id
        assert restored.relationship_fingerprint == cr.relationship_fingerprint
