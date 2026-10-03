# StepGuard F3 Slice 3: Integration & Validator CLI Tests
import json
import pytest
import tempfile
from pathlib import Path

from shared.contracts import (
    CANONICAL_REGISTRY_REL_PATH,
    ArtifactRegistryManifest,
    ArtifactStatus,
    AuthoritativeArtifactRecord,
    EnvironmentFingerprintRecord,
)
from shared.environment import (
    capture_environment_fingerprint,
    derive_git_commit_sha,
)
from shared.registry import (
    build_artifact_registry,
    compute_file_sha256,
)
from shared.validator import (
    EvidenceValidator,
    G7ProvenanceInfrastructureError,
    main as validator_main,
)


def test_evidence_validator_environment_parity():
    validator = EvidenceValidator()
    env = capture_environment_fingerprint()

    # Self comparison must pass
    rep_pass = validator.validate_environment(env, baseline=env, require_exact_commit=True)
    assert rep_pass.is_valid is True
    assert rep_pass.environment_parity_clean is True

    # Modified commit must fail with require_exact_commit=True
    mod_env = EnvironmentFingerprintRecord(
        schema_version=env.schema_version,
        python_version=env.python_version,
        python_implementation=env.python_implementation,
        platform_system=env.platform_system,
        platform_machine=env.platform_machine,
        core_dependencies=env.core_dependencies,
        execution_device=env.execution_device,
        git_commit_sha="0" * 40,
        extra_metadata=env.extra_metadata,
        fingerprint_sha256="0" * 64,
        environment_id="sg://env/canonical::" + "0" * 64,
    )
    rep_fail = validator.validate_environment(env, baseline=mod_env, require_exact_commit=True)
    assert rep_fail.is_valid is False
    assert rep_fail.environment_parity_clean is False
    assert any("GIT_COMMIT_SHA_MISMATCH" in m for m in rep_fail.environment_mismatches)


def test_evidence_validator_artifact_registry():
    validator = EvidenceValidator()
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sample = root / "data" / "eval.json"
        sample.parent.mkdir(parents=True, exist_ok=True)
        sample.write_text('{"eval": true}')

        manifest = build_artifact_registry(
            relative_paths=["data/eval.json"],
            repo_root=root,
            status_map={"data/eval.json": ArtifactStatus.FROZEN_EVALUATION},
            purpose_map={"data/eval.json": "Evaluation set"},
            git_commit_sha=derive_git_commit_sha(),
            environment_fingerprint_id="sg://env/canonical::" + "e" * 64,
        )

        rep = validator.validate_artifact_registry(manifest, repo_root=root)
        assert rep.is_valid is True
        assert len(rep.violations) == 0

        # Tamper with file on disk
        sample.write_text('{"eval": false, "tampered": true}')
        rep_tampered = validator.validate_artifact_registry(manifest, repo_root=root)
        assert rep_tampered.is_valid is False
        assert any(v.rule_id == "RULE_7_2_TAMPERED_FROZEN_ARTIFACT_REGISTRY" for v in rep_tampered.violations)


def test_validator_cli_slice3_flags(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        env = capture_environment_fingerprint(repo_root=root)
        baseline_p = root / "baseline_env.json"
        baseline_p.write_text(json.dumps(env.to_dict()), encoding="utf-8")

        # Run CLI with --verify-environment and --baseline-environment
        code = validator_main([
            "--repo-root", str(root),
            "--verify-environment",
            "--baseline-environment", str(baseline_p),
            "--quiet",
        ])
        assert code == 0


def test_validator_cli_check_registry_canonical_path_default():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create an artifact and canonical manifest at data/registry/authoritative_manifest.json
        art = root / "data" / "f1.json"
        art.parent.mkdir(parents=True, exist_ok=True)
        art.write_text('{"test": true}')

        manifest = build_artifact_registry(
            relative_paths=["data/f1.json"],
            repo_root=root,
            status_map={"data/f1.json": ArtifactStatus.FROZEN_BASELINE},
            purpose_map={"data/f1.json": "Baseline"},
            git_commit_sha=derive_git_commit_sha(),
            environment_fingerprint_id="sg://env/canonical::" + "0" * 64,
        )

        canonical_dest = root / CANONICAL_REGISTRY_REL_PATH
        canonical_dest.parent.mkdir(parents=True, exist_ok=True)
        canonical_dest.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

        # Run CLI with bare --check-registry flag (resolves to CANONICAL_REGISTRY_REL_PATH)
        code = validator_main([
            "--repo-root", str(root),
            "--check-registry",
            "--quiet",
        ])
        assert code == 0
