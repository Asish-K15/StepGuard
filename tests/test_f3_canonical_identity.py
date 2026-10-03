"""Unit tests for StepGuard Task F3 Slice 1: Canonical Identity & Mapping Contracts.

Tests:
1. Canonical candidate_id identity contract (Phase 1.5 semantics).
2. Explicit solution_id -> candidate_id legacy mapping adapter.
3. Negative case: rejection of implicit string equivalence without mapping.
4. Negative case: unmapped legacy solution_id raises KeyError.
5. Negative case: conflicting candidate_id and solution_id raises ValueError.
6. Canonical serialized sg:// ID generation and parsing across all entity types.
7. Validation of sg:// URI patterns and rejection of malformed URIs.
8. Deterministic AST code normalization and 12-character SHA-256 hashing.
"""

import pytest

from shared.identity import (
    CandidateIdentityMapping,
    build_candidate_id,
    build_canonical_id,
    build_cohort_id,
    build_label_id,
    build_mutation_id,
    build_prediction_id,
    build_problem_id,
    build_step_id,
    build_trace_id,
    compute_ast_hash,
    is_valid_canonical_id,
    normalize_ast_code,
    parse_canonical_id,
    resolve_candidate_identity,
)


class TestCandidateIdentityAndLegacyMapping:
    """Test candidate_id canonical identity contract and explicit legacy mapping adapter."""

    def test_canonical_candidate_id_resolution(self):
        cand, sol, is_mapped = resolve_candidate_identity(candidate_id="eval_001_cand_004")
        assert cand == "eval_001_cand_004"
        assert sol is None
        assert not is_mapped

    def test_legacy_solution_mapping_adapter(self):
        mapping = CandidateIdentityMapping(
            mapping={"eval_001_sol_004": "eval_001_cand_004", "sol_42": "cand_42"}
        )
        assert mapping.map_solution_to_candidate("eval_001_sol_004") == "eval_001_cand_004"
        assert mapping.get_canonical_id("sol_42") == "cand_42"

        cand, sol, is_mapped = resolve_candidate_identity(
            solution_id="eval_001_sol_004", mapping=mapping
        )
        assert cand == "eval_001_cand_004"
        assert sol == "eval_001_sol_004"
        assert is_mapped

    def test_rejection_of_implicit_string_equivalence_without_mapping(self):
        """Equivalence must NEVER be silently inferred merely because solution_id is provided."""
        with pytest.raises(ValueError, match="Legacy solution_id 'eval_001_sol_004' provided without an explicit mapping"):
            resolve_candidate_identity(solution_id="eval_001_sol_004")

    def test_unmapped_legacy_solution_id_raises_key_error(self):
        mapping = CandidateIdentityMapping(mapping={"known_sol": "known_cand"})
        with pytest.raises(KeyError, match="not in the explicit candidate identity mapping"):
            mapping.map_solution_to_candidate("unknown_sol")

        with pytest.raises(KeyError):
            resolve_candidate_identity(solution_id="unknown_sol", mapping=mapping)

    def test_conflicting_candidate_and_solution_raises_value_error(self):
        mapping = {"eval_001_sol_004": "eval_001_cand_004"}
        with pytest.raises(ValueError, match="Conflicting identity"):
            resolve_candidate_identity(
                candidate_id="eval_001_cand_999",
                solution_id="eval_001_sol_004",
                mapping=mapping,
            )

    def test_ambiguous_candidate_and_solution_without_mapping_raises_value_error(self):
        with pytest.raises(ValueError, match="Ambiguous identity"):
            resolve_candidate_identity(
                candidate_id="eval_001_cand_004",
                solution_id="eval_001_sol_004",
            )

    def test_empty_identity_raises_value_error(self):
        with pytest.raises(ValueError, match="Neither candidate_id nor solution_id was provided"):
            resolve_candidate_identity()


class TestCanonicalSerializedURIs:
    """Test universal serialized sg:// canonical identifiers across all entity types."""

    def test_build_all_canonical_entity_types(self):
        prob = build_problem_id("eval_001")
        assert prob == "sg://problem/eval_001"

        cand = build_candidate_id("eval_001_cand_004")
        assert cand == "sg://candidate/eval_001_cand_004"

        step = build_step_id("eval_001_cand_004", "a7c9f104d8e2")
        assert step == "sg://step/eval_001_cand_004::a7c9f104d8e2"

        mut = build_mutation_id("eval_001_cand_004", "a7c9f104d8e2", "comparison_swap", 1)
        assert mut == "sg://mutation/eval_001_cand_004::a7c9f104d8e2::comparison_swap::01"

        trace = build_trace_id(
            "eval_001_cand_004", "a7c9f104d8e2", "comparison_swap", 1, "f49b12a0"
        )
        assert trace == "sg://trace/eval_001_cand_004::a7c9f104d8e2::comparison_swap::01::f49b12a0"

        lbl = build_label_id("eval_001_cand_004", "a7c9f104d8e2", "stage1_3_v1")
        assert lbl == "sg://label/eval_001_cand_004::a7c9f104d8e2::stage1_3_v1"

        pred = build_prediction_id("eval_001_cand_004", "a7c9f104d8e2", "4a0b37e480b1e87d")
        assert pred == "sg://prediction/eval_001_cand_004::a7c9f104d8e2::4a0b37e4"

        cohort = build_cohort_id("eval_n37", "v1")
        assert cohort == "sg://cohort/eval_n37::v1"

    def test_parse_valid_canonical_id(self):
        etype, key = parse_canonical_id("sg://step/eval_001_cand_004::a7c9f104d8e2")
        assert etype == "step"
        assert key == "eval_001_cand_004::a7c9f104d8e2"

    def test_is_valid_canonical_id(self):
        assert is_valid_canonical_id("sg://step/eval_001_cand_004::a7c9f104d8e2")
        assert is_valid_canonical_id("sg://step/eval_001_cand_004::a7c9f104d8e2", expected_entity_type="step")
        assert not is_valid_canonical_id("sg://step/eval_001_cand_004::a7c9f104d8e2", expected_entity_type="problem")

    def test_rejection_of_invalid_canonical_uris(self):
        with pytest.raises(ValueError, match="is not a valid canonical sg:// URI"):
            parse_canonical_id("http://stepguard.dev/eval_001")

        with pytest.raises(ValueError, match="is not a valid canonical sg:// URI"):
            parse_canonical_id("eval_001_cand_004")

        with pytest.raises(ValueError, match="is not supported"):
            parse_canonical_id("sg://unsupported_entity/key_123")

        with pytest.raises(ValueError, match="Invalid entity type"):
            build_canonical_id("unsupported_type", "key_123")


class TestASTNormalizationAndHashing:
    """Test deterministic AST code normalization and 12-char SHA-256 step hashing."""

    def test_ast_normalization_handles_whitespace_and_comments(self):
        code1 = "def foo(x):\n    # A comment\n    return x + 1\n"
        code2 = "def foo(x):\n\n    return x + 1"
        norm1 = normalize_ast_code(code1)
        norm2 = normalize_ast_code(code2)
        assert norm1 == norm2
        assert compute_ast_hash(code1) == compute_ast_hash(code2)
        assert len(compute_ast_hash(code1)) == 12

    def test_differing_logic_produces_differing_ast_hashes(self):
        code1 = "return x + 1"
        code2 = "return x - 1"
        assert compute_ast_hash(code1) != compute_ast_hash(code2)
