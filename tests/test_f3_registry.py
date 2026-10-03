# StepGuard F3 Slice 3: Authoritative Artifact Registry Unit Tests
import pytest
import tempfile
from pathlib import Path

from shared.contracts import (
    CANONICAL_REGISTRY_REL_PATH,
    ArtifactRegistryManifest,
    ArtifactStatus,
    AuthoritativeArtifactRecord,
)
from shared.identity import build_registry_id, build_artifact_id, is_valid_canonical_id
from shared.merkle import canonical_leaf_bytes, hash_leaf
from shared.registry import (
    build_artifact_registry,
    canonical_artifact_leaf_payload,
    compute_artifact_merkle_root,
    compute_file_sha256,
    verify_artifact_registry,
)


def test_artifact_status_closed_taxonomy():
    # Verify all five approved enum values
    expected = {
        "FROZEN_BASELINE",
        "FROZEN_EVALUATION",
        "HISTORICAL_PROVENANCE_GAPPED",
        "CANONICAL_RELEASE",
        "ACTIVE_EXPERIMENTAL",
    }
    assert set(s.value for s in ArtifactStatus) == expected
    assert len(ArtifactStatus) == 5


def test_authoritative_artifact_record_from_dict_and_roundtrip():
    # Valid round-trip for all 5 statuses
    for status in ArtifactStatus:
        data = {
            "canonical_artifact_id": f"sg://artifact/test_{status.value.lower()}::" + "a" * 64,
            "relative_path": f"data/test_{status.value.lower()}.json",
            "content_sha256": "a" * 64,
            "size_bytes": 128,
            "status": status.value,
            "registered_at_commit": "e6c359c595eb9f2e4bbaaf0298ea7dd7e4024a94",
            "purpose": "unit test",
            "provenance_note": "verified",
        }
        rec = AuthoritativeArtifactRecord.from_dict(data)
        assert rec.status == status
        assert rec.to_dict()["status"] == status.value

    # Reject unknown status
    invalid_data = {
        "canonical_artifact_id": "sg://artifact/test::" + "a" * 64,
        "relative_path": "data/test.json",
        "content_sha256": "a" * 64,
        "size_bytes": 128,
        "status": "SUPERSEDED",
        "registered_at_commit": "e6c359c595eb9f2e4bbaaf0298ea7dd7e4024a94",
    }
    with pytest.raises(ValueError, match="Invalid ArtifactStatus"):
        AuthoritativeArtifactRecord.from_dict(invalid_data)


def test_canonical_registry_rel_path():
    assert CANONICAL_REGISTRY_REL_PATH == "data/registry/authoritative_manifest.json"


def test_build_registry_id_format():
    reg_id = build_registry_id("authoritative", version="1.0")
    assert reg_id == "sg://registry/authoritative::v1.0"
    reg_id_default = build_registry_id()
    assert reg_id_default == "sg://registry/authoritative::v1.0"
    assert is_valid_canonical_id(reg_id)


def test_canonical_artifact_leaf_payload_exact_six_fields():
    rec = AuthoritativeArtifactRecord(
        canonical_artifact_id="sg://artifact/data/test.json::" + "c" * 64,
        relative_path="data/test.json",
        content_sha256="c" * 64,
        size_bytes=256,
        status=ArtifactStatus.FROZEN_BASELINE,
        registered_at_commit="e6c359c595eb9f2e4bbaaf0298ea7dd7e4024a94",
        purpose="extra metadata that must be excluded from leaf",
        provenance_note="extra provenance that must be excluded",
    )
    leaf = canonical_artifact_leaf_payload(rec)
    assert set(leaf.keys()) == {
        "canonical_artifact_id",
        "content_sha256",
        "registered_at_commit",
        "relative_path",
        "size_bytes",
        "status",
    }
    assert "purpose" not in leaf
    assert "provenance_note" not in leaf


def test_build_and_verify_artifact_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        art1 = root / "data" / "eval" / "test1.json"
        art1.parent.mkdir(parents=True, exist_ok=True)
        art1.write_text('{"item": 1}')

        art2 = root / "data" / "eval" / "test2.json"
        art2.write_text('{"item": 2}')

        manifest = build_artifact_registry(
            relative_paths=["data/eval/test1.json", "data/eval/test2.json"],
            repo_root=root,
            status_map={"data/eval/test1.json": ArtifactStatus.FROZEN_EVALUATION},
            purpose_map={"data/eval/test1.json": "Eval dataset 1"},
            git_commit_sha="e6c359c595eb9f2e4bbaaf0298ea7dd7e4024a94",
            environment_fingerprint_id="sg://env/canonical::" + "f" * 64,
        )

        assert manifest.registry_id == "sg://registry/authoritative::v1.0"
        assert manifest.total_artifacts == 2
        assert manifest.is_merkle_root_valid() is True

        is_valid, violations = verify_artifact_registry(manifest, repo_root=root)
        assert is_valid is True
        assert len(violations) == 0

        # Test tamper detection
        art1.write_text('{"item": 1, "tampered": true}')
        is_valid_tampered, violations_tampered = verify_artifact_registry(manifest, repo_root=root)
        assert is_valid_tampered is False
        assert any("RECORD_HASH_MISMATCH" in v for v in violations_tampered)


def test_registration_conflict_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        art = root / "data" / "test.json"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text('{"v": 1}')

        # Duplicate same path with same hash is handled idempotently
        manifest = build_artifact_registry(
            relative_paths=["data/test.json", "data/test.json"],
            repo_root=root,
            status_map={},
            purpose_map={},
            git_commit_sha="e6c359c595eb9f2e4bbaaf0298ea7dd7e4024a94",
            environment_fingerprint_id="sg://env/canonical::" + "f" * 64,
        )
        assert manifest.total_artifacts == 1
