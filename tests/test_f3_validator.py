"""StepGuard Task F3 Slice 2 Test Suite: Evidence Contracts & Referential Integrity Validator.

Comprehensive test suite verifying:
- Positive golden-fixture tests (end-to-end lineage, Merkle root recomputation, non-circular hashing).
- Isolated negative fault injection tests for every specified fault class:
  - G1: Unregistered cohort, missing fields, count mismatch, empty cohort, duplicate members, registry mismatch.
  - G2: Orphan step, orphan mutation, orphan trace, orphan label, unresolved trace lineage, manifest<->prediction bijection.
  - G3: Coordinate-only identity, non-canonical URIs, unmapped legacy solution_id, conflicting candidate identities.
  - G4: Taxonomy tier compliance, lineage cardinality, trace duplication, partition sum, missing disclaimer, semantic proof disclaimer.
  - G5: Candidate partition leakage, problem partition leakage.
  - G6: Tampered record content hash, tampered Merkle root, altered member content.
- Standalone CLI execution contract.
- Deterministic violation ordering.
"""

import json
from pathlib import Path
import tempfile
from typing import Any, Dict, List

import pytest

from shared.contracts import (
    CanonicalStepRecord,
    CohortManifest,
    CohortMemberRecord,
    PartitionPolicy,
    TaxonomyTier,
)
from shared.identity import (
    CandidateIdentityMapping,
    build_candidate_id,
    build_cohort_id,
    build_label_id,
    build_mutation_id,
    build_prediction_id,
    build_problem_id,
    build_step_id,
    build_trace_id,
)
from shared.merkle import compute_merkle_root
from shared.validator import (
    EvidenceValidator,
    G1UnregisteredCohortError,
    G2OrphanEntityError,
    G3IdentityAnchoringError,
    G4LabelProvenanceError,
    G5PartitionLeakageError,
    G6ContentIntegrityError,
    ManifestRegistrationEntry,
    ValidationReport,
    ValidationViolation,
    compute_record_content_hash,
    main as cli_main,
)


# ---------------------------------------------------------------------------
# Golden Fixture Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_pipeline_fixtures() -> Dict[str, Any]:
    """Build a complete, 100% compliant lineage fixture set."""
    prob_id = "eval_001"
    cand_id = "eval_001_cand_004"
    step_code = "total = sum(items)"
    step_id = build_step_id(cand_id, step_code)
    ast_hash = step_id.split("::")[1]

    candidates = [{"candidate_id": cand_id, "problem_id": prob_id}]
    steps = [
        {
            "canonical_step_id": step_id,
            "candidate_id": cand_id,
            "problem_id": prob_id,
            "code": step_code,
            "ast_hash": ast_hash,
            "step_type": "assignment",
        }
    ]

    mut_id = build_mutation_id(cand_id, ast_hash, "operator_swap", 1)
    mutations = [
        {
            "mutation_id": mut_id,
            "canonical_step_id": step_id,
            "operator": "operator_swap",
            "node_index": 1,
        }
    ]

    trace_1_id = build_trace_id(cand_id, ast_hash, "operator_swap", 1, "test_01")
    trace_2_id = build_trace_id(cand_id, ast_hash, "operator_swap", 1, "test_02")
    traces = [
        {"trace_id": trace_1_id, "mutation_id": mut_id, "status": "killed"},
        {"trace_id": trace_2_id, "mutation_id": mut_id, "status": "killed"},
    ]

    label_id = build_label_id(cand_id, ast_hash, "stage1_3_v1")
    labels = [
        {
            "label_id": label_id,
            "canonical_step_id": step_id,
            "assigned_label": "correct",
            "taxonomy_tier": TaxonomyTier.MUTATION_HEURISTIC_DERIVED.value,
            "epistemic_disclaimer": "Label reflects empirical test mutation sensitivity only; NOT formal semantic proof of correctness.",
            "derivation_metadata": {
                "ruleset_version": "stage_1_3_reconciliation_v1",
                "derivation_script": "partner_a/evidence/derive_verifier_labels.py",
                "input_evidence_count": 2,
                "input_execution_ids": [trace_1_id, trace_2_id],
                "kill_count": 2,
                "survivor_count": 0,
                "runtime_error_count": 0,
            },
        }
    ]

    member_dict = {
        "candidate_id": cand_id,
        "canonical_step_id": step_id,
        "expected_label_id": label_id,
        "problem_id": prob_id,
    }
    member_dict["record_sha256"] = compute_record_content_hash(member_dict)
    merkle_root = compute_merkle_root([member_dict])

    cohort_id = build_cohort_id("eval_sample", "v1")
    manifest = {
        "cohort_id": cohort_id,
        "cohort_name": "Stage 2 Sample Evaluation Slice",
        "purpose": "HELD_OUT_EVALUATION",
        "schema_version": "1.0.0",
        "created_at": "2026-10-03T09:55:00Z",
        "git_commit_sha": "f62d12e5c661366e9ef939b700159f70100a3e69",
        "partition_policy": {
            "split_name": "eval",
            "partition_key": "candidate_id",
            "disjoint_from_cohort_ids": ["sg://cohort/train_sample::v1"],
            "leakage_allowed": False,
        },
        "member_count": 1,
        "aggregate_merkle_root": merkle_root,
        "members": [member_dict],
    }

    pred_id = build_prediction_id(cand_id, ast_hash, "4a0b37e4")
    predictions = [
        {
            "prediction_id": pred_id,
            "canonical_step_id": step_id,
            "predicted_label": "correct",
            "probability": 0.98,
        }
    ]

    return {
        "prob_id": prob_id,
        "cand_id": cand_id,
        "step_id": step_id,
        "mut_id": mut_id,
        "trace_1_id": trace_1_id,
        "trace_2_id": trace_2_id,
        "label_id": label_id,
        "cohort_id": cohort_id,
        "pred_id": pred_id,
        "candidates": candidates,
        "steps": steps,
        "mutations": mutations,
        "traces": traces,
        "labels": labels,
        "manifest": manifest,
        "predictions": predictions,
        "merkle_root": merkle_root,
    }


# ---------------------------------------------------------------------------
# 1. Positive Tests (Golden Fixtures)
# ---------------------------------------------------------------------------

def test_positive_clean_lineage_and_manifest(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    """Verify that a 100% compliant pipeline passes manifest and lineage validation."""
    data = clean_pipeline_fixtures
    validator = EvidenceValidator()

    m_rep = validator.validate_manifest(data["manifest"])
    assert m_rep.is_valid is True
    assert len(m_rep.violations) == 0
    assert m_rep.registration_status == "UNVERIFIED_REGISTRATION_PROVENANCE"
    assert len(m_rep.merkle_roots_verified) == 1

    l_rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=data["labels"],
        predictions=data["predictions"],
        manifest=data["manifest"],
    )
    assert l_rep.is_valid is True
    assert len(l_rep.violations) == 0


def test_positive_trusted_repository_registration(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    """Verify that trusted registration evidence validates with VERIFIED_REGISTERED status."""
    data = clean_pipeline_fixtures
    manifest_bytes = json.dumps(data["manifest"], sort_keys=True).encode("utf-8")
    import hashlib
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()

    trusted_registry = {
        data["cohort_id"]: ManifestRegistrationEntry(
            cohort_id=data["cohort_id"],
            expected_manifest_sha256=manifest_sha,
            expected_git_commit_sha="f62d12e5c661366e9ef939b700159f70100a3e69",
            repo_relative_path="data/evaluation/stage_2/cohort_manifest.json",
        )
    }

    validator = EvidenceValidator(trusted_registry=trusted_registry)
    rep = validator.validate_manifest(data["manifest"], manifest_raw_content=manifest_bytes)
    assert rep.is_valid is True
    assert rep.registration_status == "VERIFIED_REGISTERED"
    assert len(rep.violations) == 0


def test_positive_non_circular_record_content_hash() -> None:
    """Verify non-circular hashing: record_sha256 is omitted from the hashed payload."""
    member_record = {
        "candidate_id": "eval_001_cand_004",
        "canonical_step_id": "sg://step/eval_001_cand_004::a7c9f104d8e2",
        "expected_label_id": "sg://label/eval_001_cand_004::a7c9f104d8e2::stage1_3_v1",
        "problem_id": "eval_001",
    }
    hash_without_sha = compute_record_content_hash(member_record)

    # Now add record_sha256 with any value
    record_with_sha = dict(member_record)
    record_with_sha["record_sha256"] = "deadbeef" * 8
    hash_with_sha = compute_record_content_hash(record_with_sha)

    # Hash must be strictly identical because record_sha256 does not participate in its own hash
    assert hash_without_sha == hash_with_sha

    # Changing a semantic attribute must alter the hash
    modified_record = dict(member_record)
    modified_record["problem_id"] = "eval_002"
    assert compute_record_content_hash(modified_record) != hash_without_sha


def test_positive_legacy_candidate_identity_mapping(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    """Verify legacy solution_id is accepted when mapped via CandidateIdentityMapping."""
    data = clean_pipeline_fixtures
    mapping = CandidateIdentityMapping(mapping={"eval_001_sol_004": data["cand_id"]})
    validator = EvidenceValidator(candidate_mapping=mapping)

    # Candidate record specifies legacy solution_id
    legacy_candidates = [{"solution_id": "eval_001_sol_004", "problem_id": data["prob_id"]}]

    rep = validator.validate_lineage(
        candidates=legacy_candidates,
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=data["labels"],
    )
    assert rep.is_valid is True
    assert len(rep.violations) == 0


def test_positive_all_four_taxonomy_tiers(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    """Verify that all four taxonomy tiers pass when valid metadata is supplied."""
    data = clean_pipeline_fixtures
    validator = EvidenceValidator()

    tier1 = data["labels"][0]

    tier2 = {
        "label_id": build_label_id(data["cand_id"], "a7c9f104d8e2", "unilateral_rev1"),
        "canonical_step_id": data["step_id"],
        "assigned_label": "uncertain",
        "taxonomy_tier": TaxonomyTier.HUMAN_EXPERT_UNILATERAL.value,
        "epistemic_disclaimer": "Unilateral human observation by single reviewer; subjective proxy.",
    }

    tier3 = {
        "label_id": build_label_id(data["cand_id"], "a7c9f104d8e2", "adjudicated_rev2"),
        "canonical_step_id": data["step_id"],
        "assigned_label": "correct",
        "taxonomy_tier": TaxonomyTier.HUMAN_ADJUDICATED_REFERENCE.value,
        "epistemic_disclaimer": "Human-adjudicated reference label; does NOT constitute mathematical or formal semantic proof.",
        "claims_semantic_correctness": False,
    }

    tier4 = {
        "label_id": build_label_id(data["cand_id"], "a7c9f104d8e2", "formal_sat_v1"),
        "canonical_step_id": data["step_id"],
        "assigned_label": "correct",
        "taxonomy_tier": TaxonomyTier.FORMAL_VERIFICATION.value,
        "epistemic_disclaimer": "Machine-certified semantic proof via formal solver.",
    }

    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[tier1, tier2, tier3, tier4],
    )
    assert rep.is_valid is True
    assert len(rep.violations) == 0


def test_positive_partition_disjointness_candidate_and_problem() -> None:
    """Verify candidate and problem partition disjointness checks."""
    validator = EvidenceValidator()

    # Disjoint candidates
    cohort_train = [{"candidate_id": "cand_001", "problem_id": "prob_001"}]
    cohort_eval = [{"candidate_id": "cand_002", "problem_id": "prob_001"}]

    cand_rep = validator.validate_partition_disjointness(
        cohort_train, cohort_eval, partition_key="candidate_id"
    )
    assert cand_rep.is_valid is True

    # Disjoint problems
    cohort_prob_eval = [{"candidate_id": "cand_002", "problem_id": "prob_002"}]
    prob_rep = validator.validate_partition_disjointness(
        cohort_train, cohort_prob_eval, partition_key="problem_id"
    )
    assert prob_rep.is_valid is True


# ---------------------------------------------------------------------------
# 2. Negative Tests: Class G1 (Unregistered Cohort Faults)
# ---------------------------------------------------------------------------

def test_negative_g1_missing_required_manifest_fields(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    del manifest["git_commit_sha"]
    del manifest["purpose"]

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G1" and v.rule_id == "RULE_1_1_MISSING_REQUIRED_FIELDS" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


def test_negative_g1_member_count_mismatch(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    manifest["member_count"] = 99  # Actual length is 1

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G1" and v.rule_id == "RULE_1_2_MEMBER_COUNT_MISMATCH" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


def test_negative_g1_empty_cohort(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    manifest["members"] = []
    manifest["member_count"] = 0

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G1" and v.rule_id == "RULE_1_2_EMPTY_COHORT" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


def test_negative_g1_duplicate_member_canonical_step_id(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    member = manifest["members"][0]
    manifest["members"] = [member, dict(member)]  # Duplicate step ID
    manifest["member_count"] = 2
    manifest["aggregate_merkle_root"] = compute_merkle_root(manifest["members"])

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G1" and v.rule_id == "RULE_1_4_DUPLICATE_MEMBER_STEP" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


def test_negative_g1_trusted_registry_mismatches(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    trusted_registry = {
        data["cohort_id"]: ManifestRegistrationEntry(
            cohort_id=data["cohort_id"],
            expected_manifest_sha256="deadbeef" * 8,
            expected_git_commit_sha="0000000000000000000000000000000000000000",
            repo_relative_path="data/evaluation/manifest.json",
        )
    }

    validator = EvidenceValidator(trusted_registry=trusted_registry)
    raw_content = json.dumps(data["manifest"]).encode("utf-8")
    rep = validator.validate_manifest(data["manifest"], manifest_raw_content=raw_content)

    assert rep.is_valid is False
    assert rep.registration_status == "UNVERIFIED_REGISTRATION_PROVENANCE"
    assert any(v.rule_id == "RULE_1_5_COMMIT_SHA_MISMATCH" for v in rep.violations)
    assert any(v.rule_id == "RULE_1_5_MANIFEST_FILE_HASH_MISMATCH" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


def test_negative_g1_cohort_not_in_trusted_registry(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    trusted_registry = {
        "sg://cohort/other_cohort::v1": ManifestRegistrationEntry(
            cohort_id="sg://cohort/other_cohort::v1",
            expected_manifest_sha256="a" * 64,
            expected_git_commit_sha="b" * 40,
            repo_relative_path="path",
        )
    }
    validator = EvidenceValidator(trusted_registry=trusted_registry)
    rep = validator.validate_manifest(data["manifest"])
    assert rep.is_valid is False
    assert any(v.rule_id == "RULE_1_5_UNREGISTERED_COHORT" for v in rep.violations)

    with pytest.raises(G1UnregisteredCohortError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 3. Negative Tests: Class G2 (Orphan Entities & Bijection)
# ---------------------------------------------------------------------------

def test_negative_g2_orphan_step(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    # Step references unknown candidate
    orphan_step = dict(data["steps"][0])
    orphan_step["candidate_id"] = "unknown_candidate_999"
    orphan_step["canonical_step_id"] = build_step_id("unknown_candidate_999", "x = 1")

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=[orphan_step],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_1_ORPHAN_STEP" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_orphan_mutation(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    orphan_mut = dict(data["mutations"][0])
    orphan_mut["canonical_step_id"] = "sg://step/ghost_cand::deadbeef1234"

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=[orphan_mut],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_2_ORPHAN_MUTATION" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_orphan_trace(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    orphan_trace = dict(data["traces"][0])
    orphan_trace["mutation_id"] = "sg://mutation/cand::hash::op::99"

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=[orphan_trace],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_3_ORPHAN_TRACE" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_orphan_label(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    orphan_label = dict(data["labels"][0])
    orphan_label["canonical_step_id"] = "sg://step/cand::000000000000"

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[orphan_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_4_ORPHAN_LABEL" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_unresolved_trace_in_label(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    label = dict(data["labels"][0])
    derivation = dict(label["derivation_metadata"])
    derivation["input_execution_ids"] = [data["trace_1_id"], "sg://trace/unresolved::trace::id"]
    derivation["input_evidence_count"] = 2
    derivation["kill_count"] = 2
    label["derivation_metadata"] = derivation

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_4_UNRESOLVED_TRACE_LINEAGE" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_manifest_prediction_bijection_missing(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    validator = EvidenceValidator()

    # Empty predictions -> manifest member is unpredicted
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        predictions=[],
        manifest=data["manifest"],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_5_MISSING_PREDICTION" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


def test_negative_g2_manifest_prediction_bijection_ghost(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    validator = EvidenceValidator()

    # Prediction for a step not in manifest
    ghost_pred = {
        "prediction_id": "sg://prediction/cand::010101010101::ckpt001",
        "canonical_step_id": "sg://step/cand::010101010101",
        "predicted_label": "correct",
    }
    predictions = data["predictions"] + [ghost_pred]

    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        predictions=predictions,
        manifest=data["manifest"],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G2" and v.rule_id == "RULE_2_5_GHOST_PREDICTION" for v in rep.violations)

    with pytest.raises(G2OrphanEntityError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 4. Negative Tests: Class G3 (Identity Anchoring Faults)
# ---------------------------------------------------------------------------

def test_negative_g3_coordinate_only_step(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    coord_step = {"line": 15, "col": 4, "candidate_id": data["cand_id"]}

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=[coord_step],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G3" and v.rule_id == "RULE_3_1_COORDINATE_ONLY_IDENTITY" for v in rep.violations)

    with pytest.raises(G3IdentityAnchoringError):
        rep.raise_for_violations()


def test_negative_g3_non_canonical_uri(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_step = dict(data["steps"][0])
    bad_step["canonical_step_id"] = "step_without_sg_uri"

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=[bad_step],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G3" and v.rule_id == "RULE_3_2_INVALID_STEP_URI" for v in rep.violations)

    with pytest.raises(G3IdentityAnchoringError):
        rep.raise_for_violations()


def test_negative_g3_unmapped_solution_id(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    # Unmapped solution_id passed with no mapping
    legacy_candidate = [{"solution_id": "eval_001_sol_004", "problem_id": data["prob_id"]}]

    validator = EvidenceValidator(candidate_mapping=None)
    rep = validator.validate_lineage(
        candidates=legacy_candidate,
        steps=[],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G3" and v.rule_id == "RULE_3_3_UNMAPPED_SOLUTION_ID" for v in rep.violations)

    with pytest.raises(G3IdentityAnchoringError):
        rep.raise_for_violations()


def test_negative_g3_conflicting_candidate_identity(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    mapping = CandidateIdentityMapping(mapping={"eval_001_sol_004": "eval_001_cand_004"})
    # Candidate specifies both candidate_id and solution_id, but they conflict
    conflicting = [{
        "candidate_id": "eval_001_cand_999",
        "solution_id": "eval_001_sol_004",
        "problem_id": data["prob_id"],
    }]

    validator = EvidenceValidator(candidate_mapping=mapping)
    rep = validator.validate_lineage(
        candidates=conflicting,
        steps=[],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G3" and v.rule_id == "RULE_3_3_CONFLICTING_CANDIDATE_IDENTITY" for v in rep.violations)

    with pytest.raises(G3IdentityAnchoringError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 5. Negative Tests: Class G4 (Label Provenance Faults)
# ---------------------------------------------------------------------------

def test_negative_g4_invalid_taxonomy_tier(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_label = dict(data["labels"][0])
    bad_label["taxonomy_tier"] = "INVALID_MAGIC_TIER"

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_1_INVALID_TAXONOMY_TIER" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


def test_negative_g4_lineage_cardinality_mismatch(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_label = dict(data["labels"][0])
    derivation = dict(bad_label["derivation_metadata"])
    # 2 execution IDs, but declared evidence count is 10
    derivation["input_evidence_count"] = 10
    bad_label["derivation_metadata"] = derivation

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_2_LINEAGE_CARDINALITY_MISMATCH" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


def test_negative_g4_duplicate_execution_ids(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_label = dict(data["labels"][0])
    derivation = dict(bad_label["derivation_metadata"])
    # Duplicate trace ID
    derivation["input_execution_ids"] = [data["trace_1_id"], data["trace_1_id"]]
    derivation["input_evidence_count"] = 2
    derivation["kill_count"] = 2
    bad_label["derivation_metadata"] = derivation

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_2_DUPLICATE_EXECUTION_IDS" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


def test_negative_g4_partition_sum_mismatch(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_label = dict(data["labels"][0])
    derivation = dict(bad_label["derivation_metadata"])
    # 2 traces, but sum is 1 + 0 + 0 = 1
    derivation["input_evidence_count"] = 2
    derivation["kill_count"] = 1
    derivation["survivor_count"] = 0
    derivation["runtime_error_count"] = 0
    bad_label["derivation_metadata"] = derivation

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_2_PARTITION_SUM_MISMATCH" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


def test_negative_g4_missing_epistemic_disclaimer(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_label = dict(data["labels"][0])
    bad_label["epistemic_disclaimer"] = ""

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_label],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_2_MISSING_EPISTEMIC_DISCLAIMER" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


def test_negative_g4_human_reference_semantic_proof_claim(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    bad_tier3 = {
        "label_id": build_label_id(data["cand_id"], "a7c9f104d8e2", "adjudicated_rev2"),
        "canonical_step_id": data["step_id"],
        "assigned_label": "correct",
        "taxonomy_tier": TaxonomyTier.HUMAN_ADJUDICATED_REFERENCE.value,
        "epistemic_disclaimer": "Consensus reference.",
        "claims_semantic_correctness": True,  # Strictly forbidden!
    }

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=data["steps"],
        mutations=data["mutations"],
        traces=data["traces"],
        labels=[bad_tier3],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G4" and v.rule_id == "RULE_4_3_INVALID_SEMANTIC_PROOF_CLAIM" for v in rep.violations)

    with pytest.raises(G4LabelProvenanceError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 6. Negative Tests: Class G5 (Partition Leakage Faults)
# ---------------------------------------------------------------------------

def test_negative_g5_candidate_partition_leakage() -> None:
    validator = EvidenceValidator()
    train_records = [
        {"candidate_id": "cand_shared_001", "problem_id": "prob_001"},
        {"candidate_id": "cand_train_002", "problem_id": "prob_001"},
    ]
    eval_records = [
        {"candidate_id": "cand_eval_003", "problem_id": "prob_002"},
        {"candidate_id": "cand_shared_001", "problem_id": "prob_002"},  # Leaked candidate!
    ]

    rep = validator.validate_partition_disjointness(
        train_records, eval_records, partition_key="candidate_id"
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G5" and v.rule_id == "RULE_5_1_CANDIDATE_PARTITION_LEAKAGE" for v in rep.violations)

    with pytest.raises(G5PartitionLeakageError):
        rep.raise_for_violations()


def test_negative_g5_problem_partition_leakage() -> None:
    validator = EvidenceValidator()
    train_records = [{"candidate_id": "cand_001", "problem_id": "prob_shared_001"}]
    eval_records = [{"candidate_id": "cand_002", "problem_id": "prob_shared_001"}]

    rep = validator.validate_partition_disjointness(
        train_records, eval_records, partition_key="problem_id"
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G5" and v.rule_id == "RULE_5_2_PROBLEM_PARTITION_LEAKAGE" for v in rep.violations)

    with pytest.raises(G5PartitionLeakageError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 7. Negative Tests: Class G6 (Content & Merkle Integrity Faults)
# ---------------------------------------------------------------------------

def test_negative_g6_tampered_record_sha256(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    tampered_member = dict(manifest["members"][0])
    tampered_member["record_sha256"] = "deadbeef" * 8
    manifest["members"] = [tampered_member]
    manifest["aggregate_merkle_root"] = compute_merkle_root([tampered_member])

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G6" and v.rule_id == "RULE_6_1_RECORD_HASH_MISMATCH" for v in rep.violations)

    with pytest.raises(G6ContentIntegrityError):
        rep.raise_for_violations()


def test_negative_g6_tampered_merkle_root(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    manifest = dict(clean_pipeline_fixtures["manifest"])
    manifest["aggregate_merkle_root"] = "cafebabe" * 8

    validator = EvidenceValidator()
    rep = validator.validate_manifest(manifest)
    assert rep.is_valid is False
    assert any(v.fault_class == "G6" and v.rule_id == "RULE_6_2_MERKLE_ROOT_MISMATCH" for v in rep.violations)

    with pytest.raises(G6ContentIntegrityError):
        rep.raise_for_violations()


def test_negative_g6_tampered_step_record_in_lineage(clean_pipeline_fixtures: Dict[str, Any]) -> None:
    data = clean_pipeline_fixtures
    tampered_step = dict(data["steps"][0])
    tampered_step["record_sha256"] = "badc0de" * 9 + "bad"  # 64 hex

    validator = EvidenceValidator()
    rep = validator.validate_lineage(
        candidates=data["candidates"],
        steps=[tampered_step],
        mutations=[],
        traces=[],
    )
    assert rep.is_valid is False
    assert any(v.fault_class == "G6" and v.rule_id == "RULE_6_1_RECORD_HASH_MISMATCH" for v in rep.violations)

    with pytest.raises(G6ContentIntegrityError):
        rep.raise_for_violations()


# ---------------------------------------------------------------------------
# 8. Deterministic Violation Ordering & Serialization
# ---------------------------------------------------------------------------

def test_deterministic_violation_ordering() -> None:
    validator = EvidenceValidator()
    # Inject multiple violations out of order
    v1 = ValidationViolation("G4", "RULE_4_1", "sg://step/b", "msg B")
    v2 = ValidationViolation("G1", "RULE_1_1", "sg://cohort/a", "msg A")
    v3 = ValidationViolation("G1", "RULE_1_2", "sg://cohort/a", "msg C")
    v4 = ValidationViolation("G2", "RULE_2_1", "sg://step/c", "msg D")

    rep = validator._build_report([v1, v2, v3, v4], 4, [], "UNVERIFIED_REGISTRATION_PROVENANCE")

    # Order must be strictly ascending by (fault_class, entity_id, rule_id, message)
    fault_classes = [v.fault_class for v in rep.violations]
    assert fault_classes == ["G1", "G1", "G2", "G4"]
    assert rep.violations[0].rule_id == "RULE_1_1"
    assert rep.violations[1].rule_id == "RULE_1_2"

    # Verify serialization
    as_dict = rep.to_dict()
    assert as_dict["is_valid"] is False
    assert as_dict["total_checks"] == 4
    assert len(as_dict["violations"]) == 4


# ---------------------------------------------------------------------------
# 9. Standalone CLI Contract
# ---------------------------------------------------------------------------

def test_cli_success(clean_pipeline_fixtures: Dict[str, Any], tmp_path: Path) -> None:
    data = clean_pipeline_fixtures
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(data["manifest"]), encoding="utf-8")

    steps_file = tmp_path / "steps.jsonl"
    steps_file.write_text("\n".join(json.dumps(s) for s in data["steps"]), encoding="utf-8")

    mutations_file = tmp_path / "mutations.jsonl"
    mutations_file.write_text("\n".join(json.dumps(m) for m in data["mutations"]), encoding="utf-8")

    traces_file = tmp_path / "traces.jsonl"
    traces_file.write_text("\n".join(json.dumps(t) for t in data["traces"]), encoding="utf-8")

    candidates_file = tmp_path / "candidates.jsonl"
    candidates_file.write_text("\n".join(json.dumps(c) for c in data["candidates"]), encoding="utf-8")

    report_out = tmp_path / "report.json"

    exit_code = cli_main([
        "--manifest", str(manifest_file),
        "--steps", str(steps_file),
        "--mutations", str(mutations_file),
        "--traces", str(traces_file),
        "--candidates", str(candidates_file),
        "--report-out", str(report_out),
        "--quiet",
    ])

    assert exit_code == 0
    assert report_out.is_file()
    saved_report = json.loads(report_out.read_text(encoding="utf-8"))
    assert saved_report["is_valid"] is True
    assert len(saved_report["violations"]) == 0


def test_cli_failure_on_violations(clean_pipeline_fixtures: Dict[str, Any], tmp_path: Path) -> None:
    data = clean_pipeline_fixtures
    manifest_bad = dict(data["manifest"])
    manifest_bad["aggregate_merkle_root"] = "0" * 64

    manifest_file = tmp_path / "bad_manifest.json"
    manifest_file.write_text(json.dumps(manifest_bad), encoding="utf-8")

    report_out = tmp_path / "bad_report.json"

    exit_code = cli_main([
        "--manifest", str(manifest_file),
        "--report-out", str(report_out),
        "--quiet",
    ])

    assert exit_code == 1
    assert report_out.is_file()
    saved_report = json.loads(report_out.read_text(encoding="utf-8"))
    assert saved_report["is_valid"] is False
    assert len(saved_report["violations"]) > 0
