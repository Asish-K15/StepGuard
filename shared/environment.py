"""StepGuard Task F3 Slice 3: Deterministic Environment Fingerprinting.

Implements exact 9-field canonical schema, closed dependency set,
deterministic JCS-subset JSON serialization, SHA-256 fingerprinting,
and baseline parity verification.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from shared.contracts import EnvironmentFingerprintRecord
from shared.identity import build_environment_id, is_valid_canonical_id

SCHEMA_VERSION_V1 = "1.0.0"
CORE_DEPENDENCY_PACKAGES = (
    "joblib",
    "numpy",
    "pytest",
    "scikit-learn",
    "torch",
)
UNAVAILABLE_VALUE = "unavailable"


def derive_git_commit_sha(repo_root: Optional[Union[str, Path]] = None) -> str:
    """Derive current Git HEAD SHA-256/commit hex without hardcoding, or return 'unknown'."""
    cwd = Path(repo_root) if repo_root else Path.cwd()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            sha = res.stdout.strip().lower()
            if len(sha) == 40 and all(c in "0123456789abcdef" for c in sha):
                return sha
    except Exception:
        pass
    return "unknown"


def canonical_environment_payload(
    git_commit_sha: Union[str, Dict[str, Any], EnvironmentFingerprintRecord, None] = None,
    execution_device: str = "cpu",
    extra_metadata: Optional[Dict[str, str]] = None,
    python_version: Optional[str] = None,
    python_implementation: Optional[str] = None,
    platform_system: Optional[str] = None,
    platform_machine: Optional[str] = None,
    core_dependencies: Optional[Dict[str, str]] = None,
    repo_root: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Assemble and normalize the exact 9-field canonical environment payload."""
    if isinstance(git_commit_sha, EnvironmentFingerprintRecord):
        return {
            "schema_version": git_commit_sha.schema_version,
            "python_version": git_commit_sha.python_version,
            "python_implementation": git_commit_sha.python_implementation,
            "platform_system": git_commit_sha.platform_system,
            "platform_machine": git_commit_sha.platform_machine,
            "core_dependencies": dict(sorted(git_commit_sha.core_dependencies.items())),
            "execution_device": git_commit_sha.execution_device,
            "git_commit_sha": git_commit_sha.git_commit_sha,
            "extra_metadata": dict(sorted(git_commit_sha.extra_metadata.items())),
        }
    elif isinstance(git_commit_sha, dict):
        return {
            "schema_version": git_commit_sha.get("schema_version", SCHEMA_VERSION_V1),
            "python_version": git_commit_sha.get("python_version", UNAVAILABLE_VALUE),
            "python_implementation": git_commit_sha.get("python_implementation", UNAVAILABLE_VALUE),
            "platform_system": git_commit_sha.get("platform_system", UNAVAILABLE_VALUE),
            "platform_machine": git_commit_sha.get("platform_machine", UNAVAILABLE_VALUE),
            "core_dependencies": dict(sorted(git_commit_sha.get("core_dependencies", {}).items())),
            "execution_device": git_commit_sha.get("execution_device", "cpu"),
            "git_commit_sha": git_commit_sha.get("git_commit_sha", UNAVAILABLE_VALUE),
            "extra_metadata": dict(sorted(git_commit_sha.get("extra_metadata", {}).items())),
        }

    if git_commit_sha is None:
        clean_sha = derive_git_commit_sha(repo_root)
    else:
        clean_sha = str(git_commit_sha).strip().lower() if str(git_commit_sha).strip() else "unknown"

    if python_version is not None:
        clean_py_ver = python_version.strip() if python_version else UNAVAILABLE_VALUE
    else:
        clean_py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    if python_implementation is not None:
        clean_py_impl = python_implementation.strip().lower() if python_implementation else UNAVAILABLE_VALUE
    else:
        clean_py_impl = platform.python_implementation().strip().lower()

    if platform_system is not None:
        clean_sys = platform_system.strip().lower() if platform_system else UNAVAILABLE_VALUE
    else:
        clean_sys = platform.system().strip().lower()

    if platform_machine is not None:
        clean_mach = platform_machine.strip().lower() if platform_machine else UNAVAILABLE_VALUE
    else:
        clean_mach = platform.machine().strip().lower()

    deps: Dict[str, str] = {}
    if core_dependencies is not None:
        for pkg in sorted(CORE_DEPENDENCY_PACKAGES):
            ver = core_dependencies.get(pkg)
            deps[pkg] = ver.strip() if ver and isinstance(ver, str) and ver.strip() else UNAVAILABLE_VALUE
    else:
        for pkg in sorted(CORE_DEPENDENCY_PACKAGES):
            try:
                ver = importlib.metadata.version(pkg)
                deps[pkg] = ver.strip() if ver else UNAVAILABLE_VALUE
            except Exception:
                deps[pkg] = UNAVAILABLE_VALUE

    clean_device = execution_device.strip().lower() if execution_device and execution_device.strip() else UNAVAILABLE_VALUE

    clean_meta: Dict[str, str] = {}
    if extra_metadata:
        for k, v in extra_metadata.items():
            if isinstance(k, str) and isinstance(v, str):
                clean_meta[k.strip().lower()] = v.strip()

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "python_version": clean_py_ver,
        "python_implementation": clean_py_impl,
        "platform_system": clean_sys,
        "platform_machine": clean_mach,
        "core_dependencies": dict(sorted(deps.items())),
        "execution_device": clean_device,
        "git_commit_sha": clean_sha,
        "extra_metadata": dict(sorted(clean_meta.items())),
    }


def canonical_environment_bytes(
    payload_or_rec: Union[Dict[str, Any], EnvironmentFingerprintRecord]
) -> bytes:
    """Serialize the 9-field environment payload according to JCS-subset rules."""
    payload = canonical_environment_payload(payload_or_rec)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def capture_environment_fingerprint(
    git_commit_sha: Optional[str] = None,
    execution_device: str = "cpu",
    extra_metadata: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Union[str, Path]] = None,
) -> EnvironmentFingerprintRecord:
    """Capture runtime environment, compute canonical SHA-256 and return typed record."""
    payload = canonical_environment_payload(
        git_commit_sha=git_commit_sha,
        execution_device=execution_device,
        extra_metadata=extra_metadata,
        repo_root=repo_root,
    )
    c_bytes = canonical_environment_bytes(payload)
    sha256_hex = hashlib.sha256(c_bytes).hexdigest().lower()
    env_id = build_environment_id(sha256_hex)

    return EnvironmentFingerprintRecord(
        schema_version=payload["schema_version"],
        python_version=payload["python_version"],
        python_implementation=payload["python_implementation"],
        platform_system=payload["platform_system"],
        platform_machine=payload["platform_machine"],
        core_dependencies=payload["core_dependencies"],
        execution_device=payload["execution_device"],
        git_commit_sha=payload["git_commit_sha"],
        extra_metadata=payload["extra_metadata"],
        fingerprint_sha256=sha256_hex,
        environment_id=env_id,
    )


def verify_environment_parity(
    baseline: Union[Dict[str, Any], EnvironmentFingerprintRecord],
    current: Union[Dict[str, Any], EnvironmentFingerprintRecord],
    require_exact_commit: bool = True,
) -> Tuple[bool, List[str]]:
    """Compare two environment fingerprint records field-by-field and report mismatches."""
    b_dict = baseline.to_dict() if isinstance(baseline, EnvironmentFingerprintRecord) else baseline
    c_dict = current.to_dict() if isinstance(current, EnvironmentFingerprintRecord) else current

    mismatches: List[str] = []

    scalar_keys = [
        "schema_version",
        "python_version",
        "python_implementation",
        "platform_system",
        "platform_machine",
        "execution_device",
    ]
    if require_exact_commit:
        scalar_keys.append("git_commit_sha")

    for key in scalar_keys:
        b_val = str(b_dict.get(key, UNAVAILABLE_VALUE)).strip()
        c_val = str(c_dict.get(key, UNAVAILABLE_VALUE)).strip()
        if key in ("python_implementation", "platform_system", "platform_machine", "execution_device"):
            b_val = b_val.lower()
            c_val = c_val.lower()

        if b_val != c_val:
            mismatches.append(f"{key.upper()}_MISMATCH:baseline={b_val},current={c_val}")

    b_deps = b_dict.get("core_dependencies", {})
    c_deps = c_dict.get("core_dependencies", {})
    for pkg in sorted(CORE_DEPENDENCY_PACKAGES):
        b_ver = str(b_deps.get(pkg, UNAVAILABLE_VALUE)).strip()
        c_ver = str(c_deps.get(pkg, UNAVAILABLE_VALUE)).strip()
        if b_ver != c_ver:
            mismatches.append(f"DEPENDENCY_MISMATCH:{pkg}:baseline={b_ver},current={c_ver}")

    mismatches.sort()
    return (len(mismatches) == 0, mismatches)
