"""StepGuard Task F3 Slice 1: Schema & Contract Models.

Provides strict, validated models for identity-bearing records and cohort manifests:
- Epistemic taxonomy tier enum.
- Partition policy specification with strict leakage prevention.
- Authoritative cohort member record and cohort manifest with Merkle integrity.
- Canonical step record and label provenance record.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from typing import Any, Dict, List, Optional, Sequence, Union

from shared.identity import (
    COHORT_ID_PATTERN,
    LABEL_ID_PATTERN,
    STEP_ID_PATTERN,
    is_valid_canonical_id,
    parse_canonical_id,
)
from shared.merkle import compute_merkle_root, verify_merkle_root


class TaxonomyTier(str, Enum):
    """Epistemic authority classification for step verification labels."""
    MUTATION_HEURISTIC_DERIVED = "MUTATION_HEURISTIC_DERIVED"
    HUMAN_EXPERT_UNILATERAL = "HUMAN_EXPERT_UNILATERAL"
    HUMAN_ADJUDICATED_REFERENCE = "HUMAN_ADJUDICATED_REFERENCE"
    FORMAL_VERIFICATION = "FORMAL_VERIFICATION"


@dataclass(frozen=True)
class PartitionPolicy:
    """Policy governing cohort partition and disjointness constraints."""
    split_name: str
    partition_key: str = "candidate_id"
    disjoint_from_cohort_ids: List[str] = field(default_factory=list)
    leakage_allowed: bool = False

    def __post_init__(self) -> None:
        if not self.split_name or not isinstance(self.split_name, str):
            raise ValueError("PartitionPolicy.split_name must be a non-empty string.")
        if self.partition_key not in ("candidate_id", "problem_id"):
            raise ValueError(
                f"PartitionPolicy.partition_key must be 'candidate_id' or 'problem_id', got '{self.partition_key}'."
            )


@dataclass(frozen=True)
class CohortMemberRecord:
    """A single canonical member step in an authoritative cohort manifest."""
    canonical_step_id: str
    candidate_id: str
    problem_id: str
    record_sha256: str
    expected_label_id: str

    def __post_init__(self) -> None:
        if not is_valid_canonical_id(self.canonical_step_id, "step"):
            raise ValueError(
                f"Invalid canonical_step_id '{self.canonical_step_id}'. Must match sg://step/..."
            )
        if not self.candidate_id or not isinstance(self.candidate_id, str):
            raise ValueError("candidate_id must be a non-empty string.")
        if not self.problem_id or not isinstance(self.problem_id, str):
            raise ValueError("problem_id must be a non-empty string.")
        if len(self.record_sha256) != 64 or not all(c in "0123456789abcdef" for c in self.record_sha256.lower()):
            raise ValueError(
                f"record_sha256 '{self.record_sha256}' must be a 64-character lowercase hex string."
            )
        if not is_valid_canonical_id(self.expected_label_id, "label"):
            raise ValueError(
                f"Invalid expected_label_id '{self.expected_label_id}'. Must match sg://label/..."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "canonical_step_id": self.canonical_step_id,
            "expected_label_id": self.expected_label_id,
            "problem_id": self.problem_id,
            "record_sha256": self.record_sha256.lower(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CohortMemberRecord":
        return cls(
            canonical_step_id=data["canonical_step_id"],
            candidate_id=data["candidate_id"],
            problem_id=data["problem_id"],
            record_sha256=data["record_sha256"],
            expected_label_id=data["expected_label_id"],
        )


@dataclass(frozen=True)
class CohortManifest:
    """Authoritative, pre-registered cohort manifest with Merkle integrity."""
    cohort_id: str
    cohort_name: str
    purpose: str
    created_at: str
    git_commit_sha: str
    partition_policy: PartitionPolicy
    member_count: int
    aggregate_merkle_root: str
    members: List[CohortMemberRecord]
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if not is_valid_canonical_id(self.cohort_id, "cohort"):
            raise ValueError(
                f"Invalid cohort_id '{self.cohort_id}'. Must match sg://cohort/{'{name}'}::v{'{version}'}"
            )
        if not self.cohort_name:
            raise ValueError("cohort_name cannot be empty.")
        if self.purpose not in ("TRAINING", "HELD_OUT_EVALUATION", "BLIND_HUMAN_REVIEW", "SANITY_AUDIT"):
            raise ValueError(f"Invalid purpose '{self.purpose}'.")
        if self.member_count != len(self.members):
            raise ValueError(
                f"member_count mismatch: declared {self.member_count} but received {len(self.members)} members."
            )
        if len(self.aggregate_merkle_root) != 64 or not all(
            c in "0123456789abcdef" for c in self.aggregate_merkle_root.lower()
        ):
            raise ValueError(
                f"aggregate_merkle_root '{self.aggregate_merkle_root}' must be a 64-char lowercase hex string."
            )

    def calculate_merkle_root(self) -> str:
        """Compute the deterministic Merkle root over all members."""
        records = [m.to_dict() for m in self.members]
        return compute_merkle_root(records)

    def verify_integrity(self) -> bool:
        """Verify that member count and Merkle root match declarations exactly."""
        if self.member_count != len(self.members):
            return False
        computed = self.calculate_merkle_root()
        return computed.lower() == self.aggregate_merkle_root.strip().lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "$schema": "https://stepguard.dev/schemas/v1/cohort_manifest.json",
            "cohort_id": self.cohort_id,
            "cohort_name": self.cohort_name,
            "purpose": self.purpose,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "git_commit_sha": self.git_commit_sha,
            "partition_policy": {
                "split_name": self.partition_policy.split_name,
                "partition_key": self.partition_policy.partition_key,
                "disjoint_from_cohort_ids": self.partition_policy.disjoint_from_cohort_ids,
                "leakage_allowed": self.partition_policy.leakage_allowed,
            },
            "member_count": self.member_count,
            "aggregate_merkle_root": self.aggregate_merkle_root.lower(),
            "members": [m.to_dict() for m in self.members],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CohortManifest":
        policy_data = data["partition_policy"]
        policy = PartitionPolicy(
            split_name=policy_data["split_name"],
            partition_key=policy_data.get("partition_key", "candidate_id"),
            disjoint_from_cohort_ids=policy_data.get("disjoint_from_cohort_ids", []),
            leakage_allowed=policy_data.get("leakage_allowed", False),
        )
        members = [CohortMemberRecord.from_dict(m) for m in data.get("members", [])]
        return cls(
            cohort_id=data["cohort_id"],
            cohort_name=data["cohort_name"],
            purpose=data["purpose"],
            created_at=data["created_at"],
            git_commit_sha=data["git_commit_sha"],
            partition_policy=policy,
            member_count=data["member_count"],
            aggregate_merkle_root=data["aggregate_merkle_root"],
            members=members,
            schema_version=data.get("schema_version", "1.0.0"),
        )


@dataclass(frozen=True)
class CanonicalStepRecord:
    """Normalized step record with explicit candidate anchoring and optional legacy mapping."""
    canonical_step_id: str
    candidate_id: str
    problem_id: str
    code: str
    ast_hash: str
    step_type: str
    legacy_solution_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not is_valid_canonical_id(self.canonical_step_id, "step"):
            raise ValueError(
                f"Invalid canonical_step_id '{self.canonical_step_id}'. Must match sg://step/..."
            )
        if not self.candidate_id:
            raise ValueError("candidate_id cannot be empty.")
        if not self.problem_id:
            raise ValueError("problem_id cannot be empty.")


@dataclass(frozen=True)
class LabelProvenanceRecord:
    """Label record carrying mandatory epistemic taxonomy and derivation metadata."""
    label_id: str
    canonical_step_id: str
    assigned_label: str
    taxonomy_tier: TaxonomyTier
    epistemic_disclaimer: str
    derivation_metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        if not is_valid_canonical_id(self.label_id, "label"):
            raise ValueError(f"Invalid label_id '{self.label_id}'. Must match sg://label/...")
        if not is_valid_canonical_id(self.canonical_step_id, "step"):
            raise ValueError(
                f"Invalid canonical_step_id '{self.canonical_step_id}'. Must match sg://step/..."
            )
        if self.assigned_label not in ("correct", "uncertain"):
            raise ValueError(
                f"Invalid assigned_label '{self.assigned_label}'. Must be 'correct' or 'uncertain'."
            )
        if not self.epistemic_disclaimer:
            raise ValueError("epistemic_disclaimer cannot be empty.")
