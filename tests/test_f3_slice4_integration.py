# StepGuard F3 Slice 4: Integration Test Suite for End-to-End Provenance Pipeline
import json
import pytest
import subprocess
import tempfile
from pathlib import Path

from shared.contracts import (
    CANONICAL_REGISTRY_REL_PATH,
    ArtifactRegistryManifest,
    ArtifactStatus,
    AuthoritativeArtifactRecord,
    CohortManifest,
    CohortMemberRecord,
    EnvironmentFingerprintRecord,
    PartitionPolicy,
    ProvenanceBundleManifest,
)
from shared.environment import capture_environment_fingerprint, derive_git_commit_sha
from shared.registry import build_artifact_registry
from shared.bundle import create_provenance_bundle, verify_provenance_bundle
from shared.validator import main as validator_main


def _setup_mock_repo(tmpdir: Path):
    # 1. Create a dummy data file
    data_file = tmpdir / "data" / "eval" / "test_artifact.json"
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text('{"evaluation_scope": "mbpp_pilot"}', encoding="utf-8")

    # 2. Build Authoritative Artifact Registry
    reg = build_artifact_registry(
        relative_paths=["data/eval/test_artifact.json"],
        repo_root=tmpdir,
        status_map={"data/eval/test_artifact.json": ArtifactStatus.FROZEN_EVALUATION},
        purpose_map={"data/eval/test_artifact.json": "Evaluation pilot set"},
        git_commit_sha=derive_git_commit_sha(tmpdir),
        environment_fingerprint_id="sg://env/canonical::" + "0" * 64,
    )
    reg_dest = tmpdir / CANONICAL_REGISTRY_REL_PATH
    reg_dest.parent.mkdir(parents=True, exist_ok=True)
    reg_dest.write_text(json.dumps(reg.to_dict(), indent=2), encoding="utf-8")

    # 3. Environment Record
    env = capture_environment_fingerprint(repo_root=tmpdir)

    # 4. Cohort Manifest
    coh = CohortManifest(
        cohort_id="sg://cohort/pilot_eval::v1.0",
        cohort_name="pilot_eval",
        purpose="HELD_OUT_EVALUATION",
        created_at="2026-10-05T10:00:00Z",
        git_commit_sha=env.git_commit_sha,
        partition_policy=PartitionPolicy(split_name="test"),
        member_count=1,
        aggregate_merkle_root="a" * 64,
        members=[
            CohortMemberRecord(
                canonical_step_id="sg://step/mbpp_003_cand01::" + "1" * 12,
                candidate_id="mbpp_003_cand01",
                problem_id="mbpp_003",
                record_sha256="2" * 64,
                expected_label_id="sg://label/mbpp_003_cand01::" + "1" * 12 + "::v1",
            )
        ],
    )
    return tmpdir, reg, env, coh


def test_e2e_valid_provenance_bundle_verification():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
            bundle_name="full_pipeline",
            version="1.0",
        )

        rep = verify_provenance_bundle(bundle, repo_root=root, enforce_environment=True)
        assert rep.is_valid is True
        assert len(rep.violations) == 0
        assert rep.environment_verified is True
        assert rep.registry_verified is True
        assert rep.bundle_hash_verified is True
        assert rep.lineage_verified is True


def test_e2e_bundle_verification_fails_on_tampered_registry():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
        )

        # Tamper with registered file on disk
        data_file = root / "data" / "eval" / "test_artifact.json"
        data_file.write_text('{"tampered": true}', encoding="utf-8")

        rep = verify_provenance_bundle(bundle, repo_root=root, enforce_environment=False)
        assert rep.is_valid is False
        assert rep.registry_verified is False
        assert any(v.rule_id == "RULE_8_3_BUNDLE_REGISTRY_FAILURE" for v in rep.violations)


def test_e2e_bundle_verification_fails_on_environment_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        # Modify pinned environment commit SHA
        mod_env_dict = env.to_dict()
        mod_env_dict["git_commit_sha"] = "0" * 40
        mod_env = EnvironmentFingerprintRecord.from_dict(mod_env_dict)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=mod_env,
        )

        rep = verify_provenance_bundle(bundle, repo_root=root, enforce_environment=True)
        assert rep.is_valid is False
        assert rep.environment_verified is False
        assert any(v.rule_id == "RULE_8_2_BUNDLE_ENV_MISMATCH" for v in rep.violations)


def test_e2e_bundle_verification_fails_on_unregistered_artifact():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
        )

        # Verify passing an unregistered artifact path
        rep = verify_provenance_bundle(
            bundle,
            repo_root=root,
            enforce_environment=False,
            pipeline_referenced_artifacts=["data/unregistered_secret.json"],
        )
        assert rep.is_valid is False
        assert rep.unregistered_artifact_count == 1
        assert any(v.rule_id == "RULE_8_4_UNREGISTERED_ARTIFACT" for v in rep.violations)


def test_e2e_historical_provenance_gapped_preservation():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create historical file
        hist_file = root / "data" / "historical" / "f1.json"
        hist_file.parent.mkdir(parents=True, exist_ok=True)
        hist_file.write_text('{"f1_evidence": "historical"}', encoding="utf-8")

        reg = build_artifact_registry(
            relative_paths=["data/historical/f1.json"],
            repo_root=root,
            status_map={"data/historical/f1.json": ArtifactStatus.HISTORICAL_PROVENANCE_GAPPED},
            purpose_map={"data/historical/f1.json": "F1 historical benchmark"},
            git_commit_sha=derive_git_commit_sha(root),
            environment_fingerprint_id="sg://env/canonical::" + "0" * 64,
        )
        reg_dest = root / CANONICAL_REGISTRY_REL_PATH
        reg_dest.parent.mkdir(parents=True, exist_ok=True)
        reg_dest.write_text(json.dumps(reg.to_dict(), indent=2), encoding="utf-8")

        env = capture_environment_fingerprint(repo_root=root)
        coh = CohortManifest(
            cohort_id="sg://cohort/hist::v1.0",
            cohort_name="hist",
            purpose="SANITY_AUDIT",
            created_at="2026-10-05T10:00:00Z",
            git_commit_sha=env.git_commit_sha,
            partition_policy=PartitionPolicy(split_name="hist"),
            member_count=0,
            aggregate_merkle_root="0" * 64,
            members=[],
        )

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
        )

        rep = verify_provenance_bundle(bundle, repo_root=root, enforce_environment=False)
        assert rep.historical_artifacts_count == 1
        assert rep.historical_provenance_gapped is True


def test_validator_cli_verify_bundle_flag_success(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
        )
        b_path = root / "bundle.json"
        b_path.write_text(json.dumps(bundle.to_dict(), indent=2), encoding="utf-8")

        code = validator_main([
            "--repo-root", str(root),
            "--verify-bundle", str(b_path),
            "--quiet",
        ])
        assert code == 0


def test_validator_cli_verify_bundle_flag_failure(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        root, reg, env, coh = _setup_mock_repo(root)

        bundle = create_provenance_bundle(
            cohort_manifests=[coh],
            registry_manifest=reg,
            environment_record=env,
        )
        b_dict = bundle.to_dict()
        b_dict["aggregate_bundle_hash"] = "0" * 64  # Corrupt hash

        b_path = root / "corrupt_bundle.json"
        b_path.write_text(json.dumps(b_dict, indent=2), encoding="utf-8")

        code = validator_main([
            "--repo-root", str(root),
            "--verify-bundle", str(b_path),
            "--quiet",
        ])
        assert code == 1


def test_frozen_baseline_and_historical_data_invariance():
    # Assert data/ diff remains empty
    res = subprocess.run(["git", "diff", "--", "data/"], capture_output=True, text=True, check=True)
    assert res.stdout.strip() == ""
