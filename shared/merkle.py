"""StepGuard Task F3 Slice 1: Deterministic Merkle Engine.

Implements the deterministic Merkle tree algorithm specified in F3 §4.1:
- RFC 8785 / JCS canonical JSON leaf serialization.
- Domain separation: 0x00 prefix for leaves, 0x01 prefix for internal nodes.
- Strict ascending lexicographical ordering by canonical_step_id bytes.
- Left-to-right adjacent node pairing: SHA-256(0x01 || left || right).
- Odd-node promotion: unpaired trailing node promoted directly to next level.
- Lowercase 64-character hexadecimal root representation.
- Empty-tree root defined as SHA-256(b"").
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Domain separation prefixes (RFC 6962 compliant)
LEAF_PREFIX: bytes = b"\x00"
INTERNAL_PREFIX: bytes = b"\x01"

# Empty-tree root: SHA-256(b"")
EMPTY_MERKLE_ROOT: str = hashlib.sha256(b"").hexdigest()


def canonical_leaf_bytes(record: Dict[str, Any]) -> bytes:
    """Serialize a leaf record dictionary to canonical bytes under RFC 8785 rules.

    Keys are sorted lexicographically, separators are exactly (',', ':') with
    zero extraneous whitespace, and encoding is UTF-8.
    """
    if not isinstance(record, dict):
        raise TypeError(f"Leaf record must be a dict, got {type(record).__name__}.")
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def hash_leaf(data_bytes: bytes) -> bytes:
    """Compute the 32-byte cryptographic leaf hash with 0x00 domain separation prefix."""
    return hashlib.sha256(LEAF_PREFIX + data_bytes).digest()


def hash_internal(left: bytes, right: bytes) -> bytes:
    """Compute the 32-byte cryptographic internal node hash with 0x01 domain separation prefix."""
    if len(left) != 32 or len(right) != 32:
        raise ValueError("Internal tree hashes must be exactly 32 raw bytes each.")
    return hashlib.sha256(INTERNAL_PREFIX + left + right).digest()


def sort_manifest_records(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort manifest records strictly in ascending lexicographical order by canonical_step_id bytes."""
    for idx, r in enumerate(records):
        if not isinstance(r, dict):
            raise TypeError(f"Record at index {idx} is not a dict.")
        step_id = r.get("canonical_step_id")
        if not step_id or not isinstance(step_id, str):
            raise ValueError(f"Record at index {idx} lacks a valid 'canonical_step_id' string.")
    return sorted(records, key=lambda r: r["canonical_step_id"].encode("utf-8"))


def compute_merkle_root(records: Sequence[Dict[str, Any]]) -> str:
    """Compute the deterministic 64-character hexadecimal Merkle root for a sequence of manifest records.

    Rules:
    - Empty sequence: returns EMPTY_MERKLE_ROOT (SHA-256 of empty bytes).
    - Sorts records strictly by canonical_step_id bytes.
    - Serializes each record using canonical_leaf_bytes and hashes with 0x00 prefix.
    - Iteratively pairs adjacent nodes (left, right) and hashes with 0x01 prefix.
    - If a level has an odd number of nodes, the trailing unpaired node is promoted directly to the next level.
    """
    if not records:
        return EMPTY_MERKLE_ROOT

    sorted_records = sort_manifest_records(records)
    current_level: List[bytes] = [
        hash_leaf(canonical_leaf_bytes(r)) for r in sorted_records
    ]

    while len(current_level) > 1:
        next_level: List[bytes] = []
        n = len(current_level)
        for i in range(0, n, 2):
            if i + 1 < n:
                # Pair left and right nodes
                next_level.append(hash_internal(current_level[i], current_level[i + 1]))
            else:
                # Odd-node promotion: unpaired node is promoted directly to next level
                next_level.append(current_level[i])
        current_level = next_level

    return current_level[0].hex().lower()


def verify_merkle_root(records: Sequence[Dict[str, Any]], expected_root: str) -> bool:
    """Verify that records evaluate to expected_root under the deterministic Merkle specification."""
    if not expected_root or not isinstance(expected_root, str):
        return False
    computed = compute_merkle_root(records)
    return computed.lower() == expected_root.strip().lower()


@dataclass(frozen=True)
class MerkleProofStep:
    """A single sibling hash and direction in an inclusion proof."""
    sibling_hash: str  # 64-char hex string
    is_left: bool      # True if sibling was on the left of target, False if on the right


@dataclass(frozen=True)
class MerkleInclusionProof:
    """Cryptographic audit proof demonstrating inclusion of a specific record in a cohort manifest."""
    canonical_step_id: str
    leaf_hash: str
    merkle_root: str
    steps: List[MerkleProofStep]


def generate_merkle_proof(
    records: Sequence[Dict[str, Any]], target_canonical_step_id: str
) -> MerkleInclusionProof:
    """Generate a cryptographic inclusion proof for a target canonical_step_id."""
    if not records:
        raise ValueError("Cannot generate proof from empty record set.")

    sorted_records = sort_manifest_records(records)
    target_idx: Optional[int] = None
    for idx, r in enumerate(sorted_records):
        if r["canonical_step_id"] == target_canonical_step_id:
            target_idx = idx
            break

    if target_idx is None:
        raise KeyError(f"Target '{target_canonical_step_id}' not found in records.")

    current_level: List[bytes] = [
        hash_leaf(canonical_leaf_bytes(r)) for r in sorted_records
    ]
    curr_idx = target_idx
    target_leaf_hash = current_level[target_idx].hex()
    proof_steps: List[MerkleProofStep] = []

    while len(current_level) > 1:
        next_level: List[bytes] = []
        n = len(current_level)
        next_target_idx: Optional[int] = None

        for i in range(0, n, 2):
            if i + 1 < n:
                parent = hash_internal(current_level[i], current_level[i + 1])
                next_level.append(parent)
                if i == curr_idx:
                    proof_steps.append(
                        MerkleProofStep(sibling_hash=current_level[i + 1].hex(), is_left=False)
                    )
                    next_target_idx = len(next_level) - 1
                elif i + 1 == curr_idx:
                    proof_steps.append(
                        MerkleProofStep(sibling_hash=current_level[i].hex(), is_left=True)
                    )
                    next_target_idx = len(next_level) - 1
            else:
                # Odd node promoted directly
                next_level.append(current_level[i])
                if i == curr_idx:
                    # Promoted directly, no sibling at this level
                    next_target_idx = len(next_level) - 1

        current_level = next_level
        if next_target_idx is not None:
            curr_idx = next_target_idx

    merkle_root = current_level[0].hex().lower()
    return MerkleInclusionProof(
        canonical_step_id=target_canonical_step_id,
        leaf_hash=target_leaf_hash,
        merkle_root=merkle_root,
        steps=proof_steps,
    )


def verify_merkle_proof(leaf_record: Dict[str, Any], proof: MerkleInclusionProof) -> bool:
    """Verify a cryptographic inclusion proof against a leaf record and its root."""
    calc_leaf = hash_leaf(canonical_leaf_bytes(leaf_record))
    if calc_leaf.hex() != proof.leaf_hash:
        return False

    current_hash = calc_leaf
    for step in proof.steps:
        sibling_bytes = bytes.fromhex(step.sibling_hash)
        if step.is_left:
            current_hash = hash_internal(sibling_bytes, current_hash)
        else:
            current_hash = hash_internal(current_hash, sibling_bytes)

    return current_hash.hex().lower() == proof.merkle_root.lower()
