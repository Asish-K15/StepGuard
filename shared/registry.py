"""StepGuard F3 Slice 3: Authoritative Artifact Registry Module.

Provides raw binary artifact hashing, duplicate/conflict registration controls,
exact 6-field Merkle leaf construction, and Merkle tree computation
reusing released Slice 1 primitives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from shared.contracts import (
    CANONICAL_REGISTRY_REL_PATH,
    ArtifactRegistryManifest,
    ArtifactStatus,
    AuthoritativeArtifactRecord,
)
from shared.identity import build_artifact_id, build_registry_id, is_valid_canonical_id
from shared.merkle import (
    EMPTY_MERKLE_ROOT,
    canonical_leaf_bytes,
    hash_internal,
    hash_leaf,
)


def compute_file_sha256(file_path: Union[str, Path]) -> Tuple[str, int]:
    """Read exact raw bytes of a file in binary mode and compute (sha256_hex, size_bytes)."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Artifact file not found: {p}")
    raw_bytes = p.read_bytes()
    sha256_hex = hashlib.sha256(raw_bytes).hexdigest().lower()
    return (sha256_hex, len(raw_bytes))


def canonical_artifact_leaf_payload(
    record: Union[AuthoritativeArtifactRecord, Dict[str, Any]]
) -> Dict[str, Any]:
    """Normalize an artifact record to the exact approved 6-field Merkle leaf dictionary.

    Approved 6-field leaf payload:
    - canonical_artifact_id
    - content_sha256
    - registered_at_commit
    - relative_path
    - size_bytes
    - status
    """
    if isinstance(record, AuthoritativeArtifactRecord):
        return {
            "canonical_artifact_id": record.canonical_artifact_id,
            "content_sha256": record.content_sha256.lower(),
            "registered_at_commit": record.registered_at_commit.lower(),
            "relative_path": record.relative_path,
            "size_bytes": record.size_bytes,
            "status": record.status.value if isinstance(record.status, ArtifactStatus) else str(record.status),
        }
    elif isinstance(record, dict):
        status_val = record.get("status")
        if not status_val:
            raise ValueError("Missing 'status' field in artifact record dictionary.")
        status_str = status_val.value if isinstance(status_val, ArtifactStatus) else str(status_val)
        return {
            "canonical_artifact_id": record["canonical_artifact_id"],
            "content_sha256": record["content_sha256"].lower(),
            "registered_at_commit": str(record.get("registered_at_commit", "")).lower(),
            "relative_path": record["relative_path"],
            "size_bytes": int(record["size_bytes"]),
            "status": status_str,
        }
    else:
        raise TypeError(f"Expected AuthoritativeArtifactRecord or dict, got {type(record).__name__}")


def compute_artifact_merkle_root(
    artifacts: Sequence[Union[AuthoritativeArtifactRecord, Dict[str, Any]]]
) -> str:
    """Compute deterministic Merkle root over 6-field artifact records using Slice 1 algorithm."""
    if not artifacts:
        return EMPTY_MERKLE_ROOT

    # Normalize to exact 6-field dictionary
    leaf_payloads: List[Dict[str, Any]] = [
        canonical_artifact_leaf_payload(a) for a in artifacts
    ]

    # Sort strictly by canonical_artifact_id bytes
    sorted_records = sorted(
        leaf_payloads,
        key=lambda r: r["canonical_artifact_id"].encode("utf-8"),
    )

    current_level: List[bytes] = [
        hash_leaf(canonical_leaf_bytes(r)) for r in sorted_records
    ]

    while len(current_level) > 1:
        next_level: List[bytes] = []
        n = len(current_level)
        for i in range(0, n, 2):
            if i + 1 < n:
                next_level.append(hash_internal(current_level[i], current_level[i + 1]))
            else:
                next_level.append(current_level[i])
        current_level = next_level

    return current_level[0].hex().lower()


def build_artifact_registry(
    relative_paths: Sequence[str],
    repo_root: Path,
    status_map: Dict[str, ArtifactStatus],
    purpose_map: Dict[str, str],
    git_commit_sha: str,
    environment_fingerprint_id: str,
    registry_name: str = "authoritative",
    version: str = "1.0",
) -> ArtifactRegistryManifest:
    """Construct an ArtifactRegistryManifest from on-disk files with duplicate/conflict protection."""
    seen_paths: Dict[str, str] = {}  # rel_path -> content_sha256
    artifact_records: List[AuthoritativeArtifactRecord] = []

    for rel_path_raw in relative_paths:
        clean_rel = rel_path_raw.replace("\\", "/").strip("/").strip()
        abs_path = repo_root / clean_rel

        sha256_hex, size_bytes = compute_file_sha256(abs_path)

        if clean_rel in seen_paths:
            existing_sha = seen_paths[clean_rel]
            if existing_sha != sha256_hex:
                raise ValueError(
                    f"Registration conflict: path '{clean_rel}' registered multiple times with differing hashes "
                    f"('{existing_sha}' vs '{sha256_hex}')."
                )
            continue

        seen_paths[clean_rel] = sha256_hex
        artifact_id = build_artifact_id(clean_rel, sha256_hex)
        status = status_map.get(clean_rel, ArtifactStatus.ACTIVE_EXPERIMENTAL)
        purpose = purpose_map.get(clean_rel, f"Registered artifact {clean_rel}")

        record = AuthoritativeArtifactRecord(
            canonical_artifact_id=artifact_id,
            relative_path=clean_rel,
            content_sha256=sha256_hex,
            size_bytes=size_bytes,
            status=status,
            registered_at_commit=git_commit_sha,
            purpose=purpose,
        )
        artifact_records.append(record)

    merkle_root = compute_artifact_merkle_root(artifact_records)
    registry_id = build_registry_id(registry_name, version)
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return ArtifactRegistryManifest(
        registry_id=registry_id,
        schema_version="1.0.0",
        created_at=created_at,
        git_commit_sha=git_commit_sha,
        environment_fingerprint_id=environment_fingerprint_id,
        total_artifacts=len(artifact_records),
        aggregate_merkle_root=merkle_root,
        artifacts=artifact_records,
    )


def verify_artifact_registry(
    manifest: Union[Dict[str, Any], ArtifactRegistryManifest],
    repo_root: Path,
) -> Tuple[bool, List[str]]:
    """Verify raw-byte hashes on disk and aggregate Merkle root for a registered manifest."""
    m_obj = manifest if isinstance(manifest, ArtifactRegistryManifest) else ArtifactRegistryManifest.from_dict(manifest)
    violations: List[str] = []

    for a in m_obj.artifacts:
        target_file = repo_root / a.relative_path
        if not target_file.exists():
            violations.append(f"MISSING_ARTIFACT:{a.relative_path}")
            continue
        if not target_file.is_file():
            violations.append(f"NOT_A_FILE:{a.relative_path}")
            continue

        raw_sha256, raw_size = compute_file_sha256(target_file)
        if raw_sha256.lower() != a.content_sha256.lower():
            violations.append(
                f"RECORD_HASH_MISMATCH:{a.relative_path}:expected={a.content_sha256.lower()},actual={raw_sha256.lower()}"
            )
        if raw_size != a.size_bytes:
            violations.append(
                f"SIZE_MISMATCH:{a.relative_path}:expected={a.size_bytes},actual={raw_size}"
            )

    computed_root = m_obj.calculate_merkle_root()
    if computed_root.lower() != m_obj.aggregate_merkle_root.lower():
        violations.append(
            f"REGISTRY_MERKLE_ROOT_MISMATCH:declared={m_obj.aggregate_merkle_root.lower()},computed={computed_root.lower()}"
        )

    if m_obj.total_artifacts != len(m_obj.artifacts):
        violations.append(
            f"ARTIFACT_COUNT_MISMATCH:declared={m_obj.total_artifacts},actual={len(m_obj.artifacts)}"
        )

    violations.sort()
    return (len(violations) == 0, violations)
