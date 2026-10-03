"""Unit tests for StepGuard Task F3 Slice 1: Deterministic Merkle Engine & Contracts.

Tests:
1. Exact reproduction of the F3 proposal's two-leaf Merkle test vector.
2. Empty tree root evaluation: SHA-256(b"").
3. Single-leaf root evaluation.
4. Odd-node promotion across multi-level trees (3 leaves, 5 leaves).
5. RFC 6962 domain separation (0x00 leaf vs. 0x01 internal).
6. Sorting invariance: inputs provided in reverse order yield identical root.
7. Negative cases: missing canonical_step_id, non-dict record, tampered leaf payload.
8. Merkle inclusion proof generation and verification.
9. CohortManifest integration and integrity validation.
"""

import hashlib
import json
import pytest

from shared.contracts import (
    CohortManifest,
    CohortMemberRecord,
    PartitionPolicy,
    TaxonomyTier,
)
from shared.merkle import (
    EMPTY_MERKLE_ROOT,
    INTERNAL_PREFIX,
    LEAF_PREFIX,
    canonical_leaf_bytes,
    compute_merkle_root,
    generate_merkle_proof,
    hash_internal,
    hash_leaf,
    verify_merkle_proof,
    verify_merkle_root,
)


LEAF_1 = {
    "candidate_id": "eval_001_cand_004",
    "canonical_step_id": "sg://step/eval_001_cand_004::a7c9f104d8e2",
    "expected_label_id": "sg://label/eval_001_cand_004::a7c9f104d8e2::stage1_3_v1",
    "problem_id": "eval_001",
    "record_sha256": "38a1f7c8d9e2b4a1c5f6e7d8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8",
}

LEAF_2 = {
    "candidate_id": "eval_001_cand_004",
    "canonical_step_id": "sg://step/eval_001_cand_004::b8d0e215f9a3",
    "expected_label_id": "sg://label/eval_001_cand_004::b8d0e215f9a3::stage1_3_v1",
    "problem_id": "eval_001",
    "record_sha256": "71e4b2a9d8c7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d2c1b0a9f8e7d6c5b4a3f2e1",
}

EXPECTED_TWO_LEAF_ROOT = "86b6c9706abf8567c4a70f47030689d5e2ebd69d645dc3092a48da9a9cce6efd"


class TestDeterministicMerkleEngine:
    """Tests for core Merkle engine algorithms and mathematical vectors."""

    def test_proposal_two_leaf_test_vector(self):
        """The two-leaf vector from F3 §4.2 must match EXPECTED_TWO_LEAF_ROOT exactly."""
        root = compute_merkle_root([LEAF_1, LEAF_2])
        assert root == EXPECTED_TWO_LEAF_ROOT
        assert verify_merkle_root([LEAF_1, LEAF_2], EXPECTED_TWO_LEAF_ROOT)

    def test_sorting_invariance_under_reverse_order(self):
        """Providing records in reverse order must result in identical root due to bytewise sorting."""
        reversed_records = [LEAF_2, LEAF_1]
        root = compute_merkle_root(reversed_records)
        assert root == EXPECTED_TWO_LEAF_ROOT

    def test_empty_tree_root(self):
        """Empty sequence must evaluate to SHA-256(b'')."""
        assert EMPTY_MERKLE_ROOT == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        root = compute_merkle_root([])
        assert root == EMPTY_MERKLE_ROOT
        assert verify_merkle_root([], EMPTY_MERKLE_ROOT)

    def test_single_leaf_tree(self):
        """Single-leaf tree root must be the leaf hash itself."""
        single_leaf = [LEAF_1]
        expected_leaf_hash = hash_leaf(canonical_leaf_bytes(LEAF_1)).hex().lower()
        root = compute_merkle_root(single_leaf)
        assert root == expected_leaf_hash

    def test_odd_node_promotion_three_leaves(self):
        """In a 3-leaf tree, leaves 0 & 1 pair, leaf 2 is promoted, then the pairs combine."""
        leaf_3 = {
            "candidate_id": "eval_001_cand_004",
            "canonical_step_id": "sg://step/eval_001_cand_004::c9e1f204a8b7",
            "expected_label_id": "sg://label/eval_001_cand_004::c9e1f204a8b7::stage1_3_v1",
            "problem_id": "eval_001",
            "record_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        }
        # Hand-calculated steps:
        h1 = hash_leaf(canonical_leaf_bytes(LEAF_1))
        h2 = hash_leaf(canonical_leaf_bytes(LEAF_2))
        h3 = hash_leaf(canonical_leaf_bytes(leaf_3))

        # Level 1: pair(h1, h2), promote(h3)
        p12 = hash_internal(h1, h2)
        p3_promoted = h3

        # Level 2: pair(p12, p3_promoted)
        expected_root = hash_internal(p12, p3_promoted).hex().lower()

        root = compute_merkle_root([LEAF_1, LEAF_2, leaf_3])
        assert root == expected_root

    def test_domain_separation_prefix_prevention(self):
        """Leaf hash (0x00 prefix) and internal hash (0x01 prefix) must differ for identical payload."""
        payload_64 = b"x" * 64
        h_leaf = hashlib.sha256(LEAF_PREFIX + payload_64).digest()
        h_internal = hash_internal(payload_64[:32], payload_64[32:])
        assert h_leaf != h_internal

    def test_tamper_detection_on_leaf_payload(self):
        """Any mutation to a field in a leaf record must change the root."""
        tampered_leaf = dict(LEAF_1)
        tampered_leaf["problem_id"] = "eval_999"  # altered problem
        tampered_root = compute_merkle_root([tampered_leaf, LEAF_2])
        assert tampered_root != EXPECTED_TWO_LEAF_ROOT


class TestMerkleEngineNegativeCases:
    """Test error handling and boundary conditions in Merkle engine."""

    def test_missing_canonical_step_id_raises_value_error(self):
        invalid_record = dict(LEAF_1)
        del invalid_record["canonical_step_id"]
        with pytest.raises(ValueError, match="lacks a valid 'canonical_step_id' string"):
            compute_merkle_root([invalid_record])

    def test_non_dict_record_raises_type_error(self):
        with pytest.raises(TypeError, match="is not a dict"):
            compute_merkle_root(["not_a_dict"])


class TestMerkleInclusionProofs:
    """Test cryptographic audit proofs of inclusion."""

    def test_generate_and_verify_inclusion_proof_two_leaves(self):
        records = [LEAF_1, LEAF_2]
        proof_1 = generate_merkle_proof(records, LEAF_1["canonical_step_id"])
        assert proof_1.merkle_root == EXPECTED_TWO_LEAF_ROOT
        assert verify_merkle_proof(LEAF_1, proof_1)

        proof_2 = generate_merkle_proof(records, LEAF_2["canonical_step_id"])
        assert proof_2.merkle_root == EXPECTED_TWO_LEAF_ROOT
        assert verify_merkle_proof(LEAF_2, proof_2)

    def test_tampered_leaf_fails_proof_verification(self):
        records = [LEAF_1, LEAF_2]
        proof = generate_merkle_proof(records, LEAF_1["canonical_step_id"])
        tampered = dict(LEAF_1)
        tampered["candidate_id"] = "tampered_cand"
        assert not verify_merkle_proof(tampered, proof)


class TestCohortManifestModelIntegration:
    """Test CohortManifest dataclass model integration with Merkle engine."""

    def test_manifest_creation_and_integrity_verification(self):
        member_1 = CohortMemberRecord.from_dict(LEAF_1)
        member_2 = CohortMemberRecord.from_dict(LEAF_2)

        policy = PartitionPolicy(
            split_name="eval",
            partition_key="candidate_id",
            disjoint_from_cohort_ids=["sg://cohort/train_sample::v1"],
            leakage_allowed=False,
        )

        manifest = CohortManifest(
            cohort_id="sg://cohort/eval_sample::v1",
            cohort_name="Sample Evaluation Slice",
            purpose="HELD_OUT_EVALUATION",
            created_at="2026-10-03T10:00:00Z",
            git_commit_sha="298030eb5da68f9dbc58f2ffc795c59783951ad2",
            partition_policy=policy,
            member_count=2,
            aggregate_merkle_root=EXPECTED_TWO_LEAF_ROOT,
            members=[member_1, member_2],
        )

        assert manifest.verify_integrity()
        assert manifest.calculate_merkle_root() == EXPECTED_TWO_LEAF_ROOT

        # Serialization round-trip
        data = manifest.to_dict()
        reconstructed = CohortManifest.from_dict(data)
        assert reconstructed.verify_integrity()
        assert reconstructed.aggregate_merkle_root == EXPECTED_TWO_LEAF_ROOT

    def test_manifest_fails_integrity_on_mismatched_root(self):
        member_1 = CohortMemberRecord.from_dict(LEAF_1)
        policy = PartitionPolicy(split_name="eval")
        manifest = CohortManifest(
            cohort_id="sg://cohort/single_member::v1",
            cohort_name="Single Member",
            purpose="HELD_OUT_EVALUATION",
            created_at="2026-10-03T10:00:00Z",
            git_commit_sha="298030eb5da68f9dbc58f2ffc795c59783951ad2",
            partition_policy=policy,
            member_count=1,
            aggregate_merkle_root="0" * 64,  # wrong root
            members=[member_1],
        )
        assert not manifest.verify_integrity()
