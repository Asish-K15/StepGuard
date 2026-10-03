# StepGuard F3 Slice 3: Environment Fingerprint Unit Tests
import platform
import pytest
import subprocess
import sys
from pathlib import Path

from shared.contracts import EnvironmentFingerprintRecord
from shared.environment import (
    CORE_DEPENDENCY_PACKAGES,
    SCHEMA_VERSION_V1,
    UNAVAILABLE_VALUE,
    canonical_environment_bytes,
    canonical_environment_payload,
    capture_environment_fingerprint,
    derive_git_commit_sha,
    verify_environment_parity,
)
from shared.identity import build_environment_id, is_valid_canonical_id


def test_derive_git_commit_sha():
    sha = derive_git_commit_sha()
    assert isinstance(sha, str)
    assert (len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)) or sha == "unknown"


def test_derive_git_commit_sha_fallback(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("git fail")))
    sha = derive_git_commit_sha()
    assert sha == "unknown"


def test_canonical_environment_payload_defaults():
    payload = canonical_environment_payload()
    assert payload["schema_version"] == SCHEMA_VERSION_V1
    assert "python_version" in payload
    assert "python_implementation" in payload
    assert "platform_system" in payload
    assert "platform_machine" in payload
    assert "core_dependencies" in payload
    assert "execution_device" in payload
    assert "git_commit_sha" in payload
    assert "extra_metadata" in payload
    assert len(payload) == 9


def test_canonical_environment_bytes_determinism():
    payload1 = canonical_environment_payload(git_commit_sha="a" * 40)
    payload2 = canonical_environment_payload(git_commit_sha="a" * 40)
    b1 = canonical_environment_bytes(payload1)
    b2 = canonical_environment_bytes(payload2)
    assert b1 == b2
    assert b'"schema_version":"1.0.0"' in b1


def test_capture_environment_fingerprint():
    rec = capture_environment_fingerprint()
    assert isinstance(rec, EnvironmentFingerprintRecord)
    assert len(rec.fingerprint_sha256) == 64
    assert rec.environment_id == f"sg://env/{rec.fingerprint_sha256[:12]}"
    assert is_valid_canonical_id(rec.environment_id)


def test_verify_environment_parity_match():
    rec1 = capture_environment_fingerprint(git_commit_sha="b" * 40)
    rec2 = capture_environment_fingerprint(git_commit_sha="b" * 40)
    is_match, mismatches = verify_environment_parity(rec1, rec2, require_exact_commit=True)
    assert is_match is True
    assert len(mismatches) == 0


def test_verify_environment_parity_commit_mismatch():
    rec1 = capture_environment_fingerprint(git_commit_sha="1" * 40)
    rec2 = capture_environment_fingerprint(git_commit_sha="2" * 40)
    
    # Strict parity requires exact commit match
    is_match, mismatches = verify_environment_parity(rec1, rec2, require_exact_commit=True)
    assert is_match is False
    assert any("GIT_COMMIT_SHA_MISMATCH" in m for m in mismatches)

    # Lenient parity permits commit divergence
    is_match_lenient, mismatches_lenient = verify_environment_parity(rec1, rec2, require_exact_commit=False)
    assert is_match_lenient is True
    assert len(mismatches_lenient) == 0


def test_verify_environment_parity_dependency_mismatch():
    rec1 = capture_environment_fingerprint()
    mod_deps = dict(rec1.core_dependencies)
    mod_deps["pytest"] = "0.0.0-tampered"
    rec2 = EnvironmentFingerprintRecord(
        schema_version=rec1.schema_version,
        python_version=rec1.python_version,
        python_implementation=rec1.python_implementation,
        platform_system=rec1.platform_system,
        platform_machine=rec1.platform_machine,
        core_dependencies=mod_deps,
        execution_device=rec1.execution_device,
        git_commit_sha=rec1.git_commit_sha,
        extra_metadata=rec1.extra_metadata,
        fingerprint_sha256="0" * 64,
        environment_id="sg://env/canonical::" + "0" * 64,
    )
    is_match, mismatches = verify_environment_parity(rec1, rec2)
    assert is_match is False
    assert any("DEPENDENCY_MISMATCH:pytest" in m for m in mismatches)
