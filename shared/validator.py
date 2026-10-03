"""StepGuard Task F3 Slice 2: Referential Integrity & Bounded G1–G6 Validation Engine.

Provides:
- Typed exception hierarchy for StepGuard evidence contract violations (G1 through G6).
- Structured validation violations and validation reports with deterministic ordering.
- Non-circular record content hash computation (omitting record_sha256).
- Cohort manifest validation (G1 structural + trusted repository registration, G6 Merkle integrity).
- Multi-phase execution lineage and referential integrity validation (G2 foreign keys, G3 identity anchoring, G4 label provenance).
- Normalized candidate/problem partition disjointness verification (G5 non-leakage).
- Bijective evaluation cohort manifest <-> prediction mapping (G2).
- Standalone fail-closed CLI validator.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from shared.contracts import (
    CanonicalStepRecord,
    CohortManifest,
    CohortMemberRecord,
    LabelProvenanceRecord,
    PartitionPolicy,
    TaxonomyTier,
)
from shared.identity import (
    CANONICAL_URI_PATTERN,
    COHORT_ID_PATTERN,
    LABEL_ID_PATTERN,
    STEP_ID_PATTERN,
    CandidateIdentityMapping,
    build_candidate_id,
    build_cohort_id,
    build_label_id,
    build_mutation_id,
    build_prediction_id,
    build_problem_id,
    build_step_id,
    is_valid_canonical_id,
    parse_canonical_id,
    resolve_candidate_identity,
)
from shared.merkle import (
    canonical_leaf_bytes,
    compute_merkle_root,
    verify_merkle_root,
)


# ---------------------------------------------------------------------------
# Typed Exception Hierarchy (G1–G6)
# ---------------------------------------------------------------------------

class EvidenceContractError(Exception):
    """Base exception for all StepGuard contract and referential integrity violations."""

    def __init__(
        self,
        message: str,
        fault_class: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.fault_class = fault_class
        self.details = details or {}


class G1UnregisteredCohortError(EvidenceContractError):
    """Raised when cohort manifests are missing, empty, or fail trusted repository registration."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G1", details=details)


class G2OrphanEntityError(EvidenceContractError):
    """Raised when foreign-key references or evaluation-prediction mappings break."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G2", details=details)


class G3IdentityAnchoringError(EvidenceContractError):
    """Raised when coordinate-only, unmapped legacy, or non-canonical identifiers are detected."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G3", details=details)


class G4LabelProvenanceError(EvidenceContractError):
    """Raised when label provenance, rulesets, lineage cardinality, or epistemic tiers fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G4", details=details)


class G5PartitionLeakageError(EvidenceContractError):
    """Raised when candidate or problem identities overlap across disjoint partitions."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G5", details=details)


class G6ContentIntegrityError(EvidenceContractError):
    """Raised when record content hashes or Merkle roots fail cryptographic recomputation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, fault_class="G6", details=details)


FAULT_CLASS_EXCEPTION_MAP = {
    "G1": G1UnregisteredCohortError,
    "G2": G2OrphanEntityError,
    "G3": G3IdentityAnchoringError,
    "G4": G4LabelProvenanceError,
    "G5": G5PartitionLeakageError,
    "G6": G6ContentIntegrityError,
}


# ---------------------------------------------------------------------------
# Structured Validation Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationViolation:
    """Represents a single contract or integrity violation."""

    fault_class: str          # "G1" through "G6"
    rule_id: str              # e.g., "RULE_2_5_MISSING_PREDICTION"
    entity_id: str            # e.g., "sg://step/..."
    message: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ManifestRegistrationEntry:
    """External registration evidence proving a cohort manifest was pre-registered in the repository."""

    cohort_id: str
    expected_manifest_sha256: str
    expected_git_commit_sha: str
    repo_relative_path: str


@dataclass
class ValidationReport:
    """Consolidated report produced by EvidenceValidator."""

    is_valid: bool
    total_checks: int
    violations: List[ValidationViolation]
    summary_by_class: Dict[str, int]
    merkle_roots_verified: List[str]
    registration_status: str  # "VERIFIED_REGISTERED" | "UNVERIFIED_REGISTRATION_PROVENANCE"

    def raise_for_violations(self, fault_class: Optional[str] = None) -> None:
        """Fail-closed: raise the specific EvidenceContractError for the first violation (or matching fault_class)."""
        if not self.violations:
            return
        target = self.violations[0]
        if fault_class is not None:
            matching = [v for v in self.violations if v.fault_class == fault_class]
            if matching:
                target = matching[0]
        exc_cls = FAULT_CLASS_EXCEPTION_MAP.get(target.fault_class, EvidenceContractError)
        raise exc_cls(
            message=f"[{target.fault_class}:{target.rule_id}] {target.message} (Entity: {target.entity_id})",
            details={
                "rule_id": target.rule_id,
                "entity_id": target.entity_id,
                "context": target.context,
                "total_violations": len(self.violations),
                "summary_by_class": self.summary_by_class,
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_checks": self.total_checks,
            "violations": [
                {
                    "fault_class": v.fault_class,
                    "rule_id": v.rule_id,
                    "entity_id": v.entity_id,
                    "message": v.message,
                    "context": v.context,
                }
                for v in self.violations
            ],
            "summary_by_class": self.summary_by_class,
            "merkle_roots_verified": self.merkle_roots_verified,
            "registration_status": self.registration_status,
        }


# ---------------------------------------------------------------------------
# Cryptographic Content Hashing (G6 Non-Circularity Resolution)
# ---------------------------------------------------------------------------

def compute_record_content_hash(record: Union[Dict[str, Any], CohortMemberRecord]) -> str:
    """Compute the cryptographic SHA-256 digest of a record's content payload.

    To eliminate self-referential hash circularity (G6), 'record_sha256' itself
    is strictly omitted from the serialization prior to hashing.
    Keys are sorted recursively, separators are canonical (',', ':'), encoding is UTF-8.
    """
    if isinstance(record, CohortMemberRecord):
        raw_dict = record.to_dict()
    elif isinstance(record, dict):
        raw_dict = dict(record)
    else:
        raise TypeError(f"Expected dict or CohortMemberRecord, got {type(record).__name__}.")

    content_payload = {k: v for k, v in raw_dict.items() if k != "record_sha256"}
    canonical_bytes = json.dumps(
        content_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest().lower()


# ---------------------------------------------------------------------------
# EvidenceValidator Engine
# ---------------------------------------------------------------------------

class EvidenceValidator:
    """Configurable, fail-closed validation engine for StepGuard evidence contracts."""

    REQUIRED_MANIFEST_FIELDS = {
        "cohort_id",
        "cohort_name",
        "purpose",
        "created_at",
        "git_commit_sha",
        "partition_policy",
        "member_count",
        "aggregate_merkle_root",
        "members",
    }

    REQUIRED_MEMBER_FIELDS = {
        "canonical_step_id",
        "candidate_id",
        "problem_id",
        "record_sha256",
        "expected_label_id",
    }

    VALID_PURPOSES = {
        "TRAINING",
        "HELD_OUT_EVALUATION",
        "BLIND_HUMAN_REVIEW",
        "SANITY_AUDIT",
    }

    VALID_TAXONOMY_TIERS = {tier.value for tier in TaxonomyTier}

    def __init__(
        self,
        trusted_registry: Optional[Dict[str, ManifestRegistrationEntry]] = None,
        candidate_mapping: Optional[Union[Dict[str, str], CandidateIdentityMapping]] = None,
    ) -> None:
        self.trusted_registry = trusted_registry or {}
        if candidate_mapping is not None:
            if isinstance(candidate_mapping, CandidateIdentityMapping):
                self.candidate_mapping: Optional[CandidateIdentityMapping] = candidate_mapping
            elif isinstance(candidate_mapping, dict):
                self.candidate_mapping = CandidateIdentityMapping(mapping=candidate_mapping)
            else:
                raise TypeError("candidate_mapping must be a dict or CandidateIdentityMapping instance.")
        else:
            self.candidate_mapping = None

    def _build_report(
        self,
        violations: List[ValidationViolation],
        total_checks: int,
        merkle_roots: List[str],
        registration_status: str,
    ) -> ValidationReport:
        # Deterministic sorting of violations: by fault_class, entity_id, rule_id, message
        sorted_violations = sorted(
            violations,
            key=lambda v: (v.fault_class, v.entity_id, v.rule_id, v.message),
        )
        summary: Dict[str, int] = {f"G{i}": 0 for i in range(1, 7)}
        for v in sorted_violations:
            summary[v.fault_class] = summary.get(v.fault_class, 0) + 1

        return ValidationReport(
            is_valid=(len(sorted_violations) == 0),
            total_checks=total_checks,
            violations=sorted_violations,
            summary_by_class=summary,
            merkle_roots_verified=sorted(list(set(merkle_roots))),
            registration_status=registration_status,
        )

    # -----------------------------------------------------------------------
    # G1 & G6: Manifest & Merkle Validation
    # -----------------------------------------------------------------------

    def validate_manifest(
        self,
        manifest: Union[CohortManifest, Dict[str, Any], str, Path],
        manifest_raw_content: Optional[Union[str, bytes]] = None,
    ) -> ValidationReport:
        """Validate cohort manifest structural integrity, G6 Merkle root, and G1 registration."""
        violations: List[ValidationViolation] = []
        checks = 0
        merkle_roots: List[str] = []
        raw_bytes: Optional[bytes] = None

        if isinstance(manifest_raw_content, bytes):
            raw_bytes = manifest_raw_content
        elif isinstance(manifest_raw_content, str):
            raw_bytes = manifest_raw_content.encode("utf-8")

        # Load manifest if passed as path or JSON string
        manifest_dict: Dict[str, Any]
        if isinstance(manifest, (str, Path)):
            p = Path(manifest)
            if p.is_file():
                raw_bytes = p.read_bytes()
                manifest_dict = json.loads(raw_bytes.decode("utf-8"))
            else:
                try:
                    manifest_dict = json.loads(str(manifest))
                    if raw_bytes is None:
                        raw_bytes = str(manifest).encode("utf-8")
                except Exception as e:
                    violations.append(
                        ValidationViolation(
                            fault_class="G1",
                            rule_id="RULE_1_1_UNPARSEABLE_MANIFEST",
                            entity_id="manifest",
                            message=f"Failed to parse manifest: {e}",
                        )
                    )
                    return self._build_report(violations, 1, [], "UNVERIFIED_REGISTRATION_PROVENANCE")
        elif isinstance(manifest, CohortManifest):
            manifest_dict = manifest.to_dict()
        elif isinstance(manifest, dict):
            manifest_dict = dict(manifest)
        else:
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_1_INVALID_MANIFEST_TYPE",
                    entity_id="manifest",
                    message=f"Unsupported manifest type: {type(manifest).__name__}",
                )
            )
            return self._build_report(violations, 1, [], "UNVERIFIED_REGISTRATION_PROVENANCE")

        # Check required fields
        checks += 1
        missing_fields = sorted(list(self.REQUIRED_MANIFEST_FIELDS - set(manifest_dict.keys())))
        if missing_fields:
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_1_MISSING_REQUIRED_FIELDS",
                    entity_id=str(manifest_dict.get("cohort_id", "manifest")),
                    message=f"Manifest missing required fields: {missing_fields}",
                    context={"missing_fields": missing_fields},
                )
            )

        cohort_id = manifest_dict.get("cohort_id", "")
        checks += 1
        if not is_valid_canonical_id(str(cohort_id), "cohort"):
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_1_INVALID_COHORT_ID",
                    entity_id=str(cohort_id or "manifest"),
                    message=f"Invalid cohort_id '{cohort_id}'. Must match sg://cohort/{{name}}::v{{version}}",
                )
            )

        purpose = manifest_dict.get("purpose", "")
        checks += 1
        if purpose not in self.VALID_PURPOSES:
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_1_INVALID_PURPOSE",
                    entity_id=str(cohort_id or "manifest"),
                    message=f"Invalid purpose '{purpose}'. Allowed: {sorted(list(self.VALID_PURPOSES))}",
                )
            )

        declared_count = manifest_dict.get("member_count")
        members = manifest_dict.get("members", [])
        if not isinstance(members, list):
            members = []

        checks += 1
        if declared_count != len(members):
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_2_MEMBER_COUNT_MISMATCH",
                    entity_id=str(cohort_id or "manifest"),
                    message=f"Declared member_count ({declared_count}) != actual members length ({len(members)}).",
                    context={"declared": declared_count, "actual": len(members)},
                )
            )

        checks += 1
        if len(members) == 0:
            violations.append(
                ValidationViolation(
                    fault_class="G1",
                    rule_id="RULE_1_2_EMPTY_COHORT",
                    entity_id=str(cohort_id or "manifest"),
                    message="Cohort manifest contains zero members; cohorts must be non-empty.",
                )
            )

        # Validate member records and check for duplicate canonical_step_id
        seen_step_ids: Set[str] = set()
        member_records_for_merkle: List[Dict[str, Any]] = []

        for idx, m in enumerate(members):
            checks += 1
            if isinstance(m, CohortMemberRecord):
                m_dict = m.to_dict()
            elif isinstance(m, dict):
                m_dict = dict(m)
            else:
                violations.append(
                    ValidationViolation(
                        fault_class="G1",
                        rule_id="RULE_1_3_INVALID_MEMBER_TYPE",
                        entity_id=f"member_{idx}",
                        message=f"Member at index {idx} is not a dictionary.",
                    )
                )
                continue

            # Check required member fields
            m_missing = sorted(list(self.REQUIRED_MEMBER_FIELDS - set(m_dict.keys())))
            if m_missing:
                violations.append(
                    ValidationViolation(
                        fault_class="G1",
                        rule_id="RULE_1_3_MISSING_MEMBER_FIELDS",
                        entity_id=str(m_dict.get("canonical_step_id", f"member_{idx}")),
                        message=f"Member at index {idx} missing required fields: {m_missing}",
                        context={"missing": m_missing},
                    )
                )

            step_id = m_dict.get("canonical_step_id", "")
            if not is_valid_canonical_id(str(step_id), "step"):
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_2_INVALID_STEP_URI",
                        entity_id=str(step_id or f"member_{idx}"),
                        message=f"Member at index {idx} has invalid canonical_step_id '{step_id}'.",
                    )
                )
            elif step_id in seen_step_ids:
                violations.append(
                    ValidationViolation(
                        fault_class="G1",
                        rule_id="RULE_1_4_DUPLICATE_MEMBER_STEP",
                        entity_id=str(step_id),
                        message=f"Duplicate member canonical_step_id '{step_id}' in manifest.",
                    )
                )
            else:
                seen_step_ids.add(step_id)

            label_id = m_dict.get("expected_label_id", "")
            if not is_valid_canonical_id(str(label_id), "label"):
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_2_INVALID_LABEL_URI",
                        entity_id=str(label_id or f"member_{idx}"),
                        message=f"Member at index {idx} has invalid expected_label_id '{label_id}'.",
                    )
                )

            # G6 non-circular content hash check
            declared_sha = m_dict.get("record_sha256", "")
            if declared_sha:
                computed_sha = compute_record_content_hash(m_dict)
                if declared_sha.lower() != computed_sha:
                    violations.append(
                        ValidationViolation(
                            fault_class="G6",
                            rule_id="RULE_6_1_RECORD_HASH_MISMATCH",
                            entity_id=str(step_id or f"member_{idx}"),
                            message=f"Member record_sha256 mismatch: declared '{declared_sha}', computed '{computed_sha}'.",
                            context={"declared": declared_sha, "computed": computed_sha},
                        )
                    )

            member_records_for_merkle.append(m_dict)

        # G6 Merkle root recomputation
        declared_root = manifest_dict.get("aggregate_merkle_root", "")
        checks += 1
        if len(member_records_for_merkle) > 0 and declared_root:
            try:
                computed_root = compute_merkle_root(member_records_for_merkle)
                if computed_root.lower() != declared_root.strip().lower():
                    violations.append(
                        ValidationViolation(
                            fault_class="G6",
                            rule_id="RULE_6_2_MERKLE_ROOT_MISMATCH",
                            entity_id=str(cohort_id or "manifest"),
                            message=f"Manifest Merkle root mismatch: declared '{declared_root}', computed '{computed_root}'.",
                            context={"declared": declared_root, "computed": computed_root},
                        )
                    )
                else:
                    merkle_roots.append(computed_root.lower())
            except Exception as e:
                violations.append(
                    ValidationViolation(
                        fault_class="G6",
                        rule_id="RULE_6_2_MERKLE_COMPUTATION_ERROR",
                        entity_id=str(cohort_id or "manifest"),
                        message=f"Error computing Merkle root: {e}",
                    )
                )

        # G1 External trusted registration verification
        registration_status = "UNVERIFIED_REGISTRATION_PROVENANCE"
        if self.trusted_registry:
            checks += 1
            if cohort_id not in self.trusted_registry:
                violations.append(
                    ValidationViolation(
                        fault_class="G1",
                        rule_id="RULE_1_5_UNREGISTERED_COHORT",
                        entity_id=str(cohort_id),
                        message=f"Cohort '{cohort_id}' is not present in the trusted repository registry.",
                        context={"cohort_id": cohort_id},
                    )
                )
            else:
                entry = self.trusted_registry[cohort_id]
                git_commit_sha = manifest_dict.get("git_commit_sha", "")
                if git_commit_sha.lower() != entry.expected_git_commit_sha.lower():
                    violations.append(
                        ValidationViolation(
                            fault_class="G1",
                            rule_id="RULE_1_5_COMMIT_SHA_MISMATCH",
                            entity_id=str(cohort_id),
                            message=f"Manifest git_commit_sha '{git_commit_sha}' != expected '{entry.expected_git_commit_sha}'.",
                            context={"declared": git_commit_sha, "expected": entry.expected_git_commit_sha},
                        )
                    )

                if raw_bytes is not None:
                    file_sha = hashlib.sha256(raw_bytes).hexdigest().lower()
                    if file_sha != entry.expected_manifest_sha256.lower():
                        violations.append(
                            ValidationViolation(
                                fault_class="G1",
                                rule_id="RULE_1_5_MANIFEST_FILE_HASH_MISMATCH",
                                entity_id=str(cohort_id),
                                message=f"Manifest file SHA-256 '{file_sha}' != expected '{entry.expected_manifest_sha256}'.",
                                context={"computed": file_sha, "expected": entry.expected_manifest_sha256},
                            )
                        )

                # If no G1 registration violations were added for this cohort, mark as verified
                g1_reg_violations = [
                    v for v in violations if v.fault_class == "G1" and v.rule_id.startswith("RULE_1_5")
                ]
                if not g1_reg_violations:
                    registration_status = "VERIFIED_REGISTERED"

        return self._build_report(violations, checks, merkle_roots, registration_status)

    # -----------------------------------------------------------------------
    # G2, G3, G4, G6: Lineage & Relational DAG Validation
    # -----------------------------------------------------------------------

    def validate_lineage(
        self,
        candidates: Sequence[Dict[str, Any]],
        steps: Sequence[Dict[str, Any]],
        mutations: Sequence[Dict[str, Any]],
        traces: Sequence[Dict[str, Any]],
        labels: Optional[Sequence[Dict[str, Any]]] = None,
        predictions: Optional[Sequence[Dict[str, Any]]] = None,
        manifest: Optional[Union[CohortManifest, Dict[str, Any]]] = None,
    ) -> ValidationReport:
        """Validate foreign-key integrity, canonical identity anchoring, and label provenance."""
        violations: List[ValidationViolation] = []
        checks = 0
        merkle_roots: List[str] = []

        # 1. Candidate processing & anchoring (G3)
        valid_candidate_ids: Set[str] = set()
        valid_candidate_uris: Set[str] = set()

        for c in candidates:
            checks += 1
            cand_id = c.get("candidate_id")
            sol_id = c.get("solution_id")

            try:
                canonical_cand, legacy_sol, is_mapped = resolve_candidate_identity(
                    candidate_id=cand_id,
                    solution_id=sol_id,
                    mapping=self.candidate_mapping,
                )
                valid_candidate_ids.add(canonical_cand)
                valid_candidate_uris.add(build_candidate_id(canonical_cand))
            except ValueError as e:
                err_msg = str(e)
                rule_id = (
                    "RULE_3_3_UNMAPPED_SOLUTION_ID"
                    if "without an explicit mapping" in err_msg or "Direct string equivalence" in err_msg
                    else "RULE_3_3_CONFLICTING_CANDIDATE_IDENTITY"
                )
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id=rule_id,
                        entity_id=str(cand_id or sol_id or "candidate"),
                        message=err_msg,
                    )
                )

        # 2. Step processing & foreign keys (G2, G3, G6)
        valid_step_ids: Set[str] = set()
        for s in steps:
            checks += 1
            # Check coordinate-only identity (G3)
            has_coords = ("line" in s or "line_number" in s or "col" in s or "column_number" in s)
            step_id = s.get("canonical_step_id")

            if not step_id:
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_1_COORDINATE_ONLY_IDENTITY",
                        entity_id="unanchored_step",
                        message="Step record is identified solely by coordinates or lacks canonical_step_id.",
                        context={"record": s},
                    )
                )
                continue

            if not is_valid_canonical_id(str(step_id), "step"):
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_2_INVALID_STEP_URI",
                        entity_id=str(step_id),
                        message=f"Step identifier '{step_id}' does not match canonical sg://step/ schema.",
                    )
                )
                continue

            # Candidate Foreign Key (G2)
            step_match = STEP_ID_PATTERN.match(step_id)
            step_cand = s.get("candidate_id") or (step_match.group("candidate_id") if step_match else None)
            if step_cand not in valid_candidate_ids and f"sg://candidate/{step_cand}" not in valid_candidate_uris:
                violations.append(
                    ValidationViolation(
                        fault_class="G2",
                        rule_id="RULE_2_1_ORPHAN_STEP",
                        entity_id=str(step_id),
                        message=f"Step '{step_id}' references unknown candidate '{step_cand}'.",
                        context={"candidate_id": step_cand},
                    )
                )
            else:
                valid_step_ids.add(step_id)

            # G6 non-circular content hash if step declares record_sha256
            if "record_sha256" in s:
                checks += 1
                declared_sha = s["record_sha256"]
                computed_sha = compute_record_content_hash(s)
                if declared_sha.lower() != computed_sha:
                    violations.append(
                        ValidationViolation(
                            fault_class="G6",
                            rule_id="RULE_6_1_RECORD_HASH_MISMATCH",
                            entity_id=str(step_id),
                            message=f"Step record_sha256 mismatch: declared '{declared_sha}', computed '{computed_sha}'.",
                            context={"declared": declared_sha, "computed": computed_sha},
                        )
                    )

        # 3. Mutation processing & foreign keys (G2, G3)
        valid_mutation_ids: Set[str] = set()
        for m in mutations:
            checks += 1
            mut_id = m.get("mutation_id", "")
            if not is_valid_canonical_id(str(mut_id), "mutation"):
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_2_INVALID_MUTATION_URI",
                        entity_id=str(mut_id or "mutation"),
                        message=f"Mutation identifier '{mut_id}' does not match canonical sg://mutation/ schema.",
                    )
                )
                continue

            # Parent Step Foreign Key (G2)
            parent_step = m.get("canonical_step_id") or m.get("step_id")
            if not parent_step:
                # Attempt to extract from mutation_id
                # sg://mutation/{candidate_id}::{ast_hash}::{op}::{idx}
                parts = mut_id.replace("sg://mutation/", "").split("::")
                if len(parts) >= 2:
                    parent_step = f"sg://step/{parts[0]}::{parts[1]}"

            if not parent_step or parent_step not in valid_step_ids:
                violations.append(
                    ValidationViolation(
                        fault_class="G2",
                        rule_id="RULE_2_2_ORPHAN_MUTATION",
                        entity_id=str(mut_id),
                        message=f"Mutation '{mut_id}' references unknown parent step '{parent_step}'.",
                        context={"parent_step": parent_step},
                    )
                )
            else:
                valid_mutation_ids.add(mut_id)

        # 4. Trace processing & foreign keys (G2, G3)
        valid_trace_ids: Set[str] = set()
        for t in traces:
            checks += 1
            trace_id = t.get("trace_id", "")
            if not is_valid_canonical_id(str(trace_id), "trace"):
                violations.append(
                    ValidationViolation(
                        fault_class="G3",
                        rule_id="RULE_3_2_INVALID_TRACE_URI",
                        entity_id=str(trace_id or "trace"),
                        message=f"Trace identifier '{trace_id}' does not match canonical sg://trace/ schema.",
                    )
                )
                continue

            # Parent Mutation Foreign Key (G2)
            parent_mut = t.get("mutation_id") or t.get("parent_mutation_id")
            if not parent_mut:
                # Attempt to extract from trace_id
                # sg://trace/{candidate_id}::{ast_hash}::{op}::{idx}::{test_hash}
                parts = trace_id.replace("sg://trace/", "").split("::")
                if len(parts) >= 4:
                    parent_mut = f"sg://mutation/{parts[0]}::{parts[1]}::{parts[2]}::{parts[3]}"

            if not parent_mut or parent_mut not in valid_mutation_ids:
                violations.append(
                    ValidationViolation(
                        fault_class="G2",
                        rule_id="RULE_2_3_ORPHAN_TRACE",
                        entity_id=str(trace_id),
                        message=f"Trace '{trace_id}' references unknown mutation '{parent_mut}'.",
                        context={"parent_mutation": parent_mut},
                    )
                )
            else:
                valid_trace_ids.add(trace_id)

        # 5. Label processing & provenance (G2, G3, G4)
        if labels is not None:
            for l in labels:
                checks += 1
                label_id = l.get("label_id", "")
                if not is_valid_canonical_id(str(label_id), "label"):
                    violations.append(
                        ValidationViolation(
                            fault_class="G3",
                            rule_id="RULE_3_2_INVALID_LABEL_URI",
                            entity_id=str(label_id or "label"),
                            message=f"Label identifier '{label_id}' does not match canonical sg://label/ schema.",
                        )
                    )
                    continue

                # Step Foreign Key (G2)
                parent_step = l.get("canonical_step_id")
                if not parent_step or parent_step not in valid_step_ids:
                    violations.append(
                        ValidationViolation(
                            fault_class="G2",
                            rule_id="RULE_2_4_ORPHAN_LABEL",
                            entity_id=str(label_id),
                            message=f"Label '{label_id}' references unknown parent step '{parent_step}'.",
                            context={"parent_step": parent_step},
                        )
                    )

                # Taxonomy Tier compliance (G4)
                tier_raw = l.get("taxonomy_tier", "")
                tier_val = tier_raw.value if hasattr(tier_raw, "value") else str(tier_raw)
                if tier_val not in self.VALID_TAXONOMY_TIERS:
                    violations.append(
                        ValidationViolation(
                            fault_class="G4",
                            rule_id="RULE_4_1_INVALID_TAXONOMY_TIER",
                            entity_id=str(label_id),
                            message=f"Invalid taxonomy_tier '{tier_val}'. Allowed: {sorted(list(self.VALID_TAXONOMY_TIERS))}",
                        )
                    )

                # Heuristic derivation requirements (G4)
                if tier_val == TaxonomyTier.MUTATION_HEURISTIC_DERIVED.value:
                    derivation = l.get("derivation_metadata")
                    if not derivation or not isinstance(derivation, dict):
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_MISSING_DERIVATION_METADATA",
                                entity_id=str(label_id),
                                message="Heuristic label is missing derivation_metadata.",
                            )
                        )
                        continue

                    # Lineage cardinality: len(input_execution_ids) == input_evidence_count > 0
                    exec_ids = derivation.get("input_execution_ids", [])
                    evidence_count = derivation.get("input_evidence_count")

                    if not isinstance(exec_ids, list):
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_INVALID_EXECUTION_IDS_TYPE",
                                entity_id=str(label_id),
                                message="input_execution_ids must be a list of trace URIs.",
                            )
                        )
                        exec_ids = []

                    checks += 1
                    if evidence_count is None or not isinstance(evidence_count, int) or evidence_count <= 0:
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_LINEAGE_CARDINALITY_MISMATCH",
                                entity_id=str(label_id),
                                message=f"input_evidence_count must be integer > 0, got {evidence_count}.",
                                context={"input_evidence_count": evidence_count},
                            )
                        )
                    elif len(exec_ids) != evidence_count:
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_LINEAGE_CARDINALITY_MISMATCH",
                                entity_id=str(label_id),
                                message=f"Lineage cardinality mismatch: len(input_execution_ids)={len(exec_ids)} != input_evidence_count={evidence_count}.",
                                context={"len_execution_ids": len(exec_ids), "input_evidence_count": evidence_count},
                            )
                        )

                    # Duplicate execution IDs
                    checks += 1
                    if len(set(exec_ids)) != len(exec_ids):
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_DUPLICATE_EXECUTION_IDS",
                                entity_id=str(label_id),
                                message="Duplicate execution IDs detected in input_execution_ids.",
                                context={"execution_ids": exec_ids},
                            )
                        )

                    # Trace resolution check (G2/G4)
                    for exec_id in exec_ids:
                        checks += 1
                        if exec_id not in valid_trace_ids:
                            violations.append(
                                ValidationViolation(
                                    fault_class="G2",
                                    rule_id="RULE_2_4_UNRESOLVED_TRACE_LINEAGE",
                                    entity_id=str(label_id),
                                    message=f"Referenced execution ID '{exec_id}' not found in trace pool.",
                                    context={"missing_trace_id": exec_id},
                                )
                            )

                    # Partition sum invariant: kill_count + survivor_count + runtime_error_count == input_evidence_count
                    kill_count = derivation.get("kill_count", 0)
                    survivor_count = derivation.get("survivor_count", 0)
                    error_count = derivation.get("runtime_error_count", 0)
                    part_sum = kill_count + survivor_count + error_count
                    checks += 1
                    if isinstance(evidence_count, int) and part_sum != evidence_count:
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_PARTITION_SUM_MISMATCH",
                                entity_id=str(label_id),
                                message=f"Partition sum mismatch: kill({kill_count}) + survivor({survivor_count}) + error({error_count}) = {part_sum} != evidence_count({evidence_count}).",
                                context={"sum": part_sum, "expected": evidence_count},
                            )
                        )

                    # Ruleset & derivation script presence
                    checks += 1
                    if not derivation.get("ruleset_version") or not derivation.get("derivation_script"):
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_MISSING_RULESET_SPEC",
                                entity_id=str(label_id),
                                message="Heuristic label missing ruleset_version or derivation_script in metadata.",
                            )
                        )

                    # Epistemic disclaimer
                    disclaimer = l.get("epistemic_disclaimer", "")
                    checks += 1
                    if not disclaimer or not isinstance(disclaimer, str) or not disclaimer.strip():
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_2_MISSING_EPISTEMIC_DISCLAIMER",
                                entity_id=str(label_id),
                                message="Heuristic label missing mandatory epistemic_disclaimer.",
                            )
                        )

                # Human adjudicated reference requirements (G4)
                elif tier_val == TaxonomyTier.HUMAN_ADJUDICATED_REFERENCE.value:
                    checks += 1
                    disclaimer = l.get("epistemic_disclaimer", "")
                    if not disclaimer or not isinstance(disclaimer, str) or not disclaimer.strip():
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_3_MISSING_EPISTEMIC_DISCLAIMER",
                                entity_id=str(label_id),
                                message="Human adjudicated reference missing mandatory epistemic_disclaimer.",
                            )
                        )

                    # Claims of formal semantic correctness are strictly forbidden
                    claims_proof = l.get("claims_semantic_correctness")
                    if claims_proof is True:
                        violations.append(
                            ValidationViolation(
                                fault_class="G4",
                                rule_id="RULE_4_3_INVALID_SEMANTIC_PROOF_CLAIM",
                                entity_id=str(label_id),
                                message="Human adjudicated reference labels cannot claim formal semantic correctness.",
                            )
                        )

        # 6. Bijective Manifest <-> Prediction Mapping (G2)
        if manifest is not None and predictions is not None:
            manifest_step_ids: Set[str] = set()
            if isinstance(manifest, CohortManifest):
                manifest_step_ids = {m.canonical_step_id for m in manifest.members}
            elif isinstance(manifest, dict):
                manifest_step_ids = {
                    m.get("canonical_step_id") for m in manifest.get("members", []) if m.get("canonical_step_id")
                }

            prediction_step_ids: Set[str] = set()
            for p in predictions:
                checks += 1
                pred_id = p.get("prediction_id", "")
                if not is_valid_canonical_id(str(pred_id), "prediction"):
                    violations.append(
                        ValidationViolation(
                            fault_class="G3",
                            rule_id="RULE_3_2_INVALID_PREDICTION_URI",
                            entity_id=str(pred_id or "prediction"),
                            message=f"Invalid prediction_id '{pred_id}'.",
                        )
                    )

                step_ref = p.get("canonical_step_id")
                if not step_ref or not is_valid_canonical_id(str(step_ref), "step"):
                    violations.append(
                        ValidationViolation(
                            fault_class="G3",
                            rule_id="RULE_3_2_INVALID_STEP_URI",
                            entity_id=str(step_ref or "prediction"),
                            message=f"Prediction lacks valid canonical_step_id: '{step_ref}'.",
                        )
                    )
                else:
                    prediction_step_ids.add(step_ref)

            # Check bijection: Manifest Steps == Prediction Steps
            checks += 1
            missing_predictions = sorted(list(manifest_step_ids - prediction_step_ids))
            for m_step in missing_predictions:
                violations.append(
                    ValidationViolation(
                        fault_class="G2",
                        rule_id="RULE_2_5_MISSING_PREDICTION",
                        entity_id=str(m_step),
                        message=f"Evaluation manifest member '{m_step}' has no corresponding prediction.",
                        context={"missing_step": m_step},
                    )
                )

            checks += 1
            ghost_predictions = sorted(list(prediction_step_ids - manifest_step_ids))
            for g_step in ghost_predictions:
                violations.append(
                    ValidationViolation(
                        fault_class="G2",
                        rule_id="RULE_2_5_GHOST_PREDICTION",
                        entity_id=str(g_step),
                        message=f"Prediction for step '{g_step}' is not in the evaluation cohort manifest.",
                        context={"ghost_step": g_step},
                    )
                )

        return self._build_report(violations, checks, merkle_roots, "UNVERIFIED_REGISTRATION_PROVENANCE")

    # -----------------------------------------------------------------------
    # G5: Partition Leakage & Disjointness Validation
    # -----------------------------------------------------------------------

    def validate_partition_disjointness(
        self,
        cohort_a_records: Sequence[Dict[str, Any]],
        cohort_b_records: Sequence[Dict[str, Any]],
        partition_key: str = "candidate_id",
    ) -> ValidationReport:
        """Verify cross-cohort partition disjointness (G5 non-leakage).

        Normalizes candidate or problem identifiers to canonical sg:// URIs
        before calculating set intersections.
        """
        violations: List[ValidationViolation] = []
        checks = 1

        if partition_key not in ("candidate_id", "problem_id"):
            raise ValueError(f"Unsupported partition_key '{partition_key}'. Must be 'candidate_id' or 'problem_id'.")

        def _extract_canonical_keys(records: Sequence[Dict[str, Any]]) -> Set[str]:
            keys: Set[str] = set()
            for r in records:
                if partition_key == "candidate_id":
                    cand = r.get("candidate_id")
                    if not cand and "canonical_step_id" in r:
                        match = STEP_ID_PATTERN.match(r["canonical_step_id"])
                        if match:
                            cand = match.group("candidate_id")
                    if cand:
                        keys.add(build_candidate_id(cand))
                elif partition_key == "problem_id":
                    prob = r.get("problem_id")
                    if prob:
                        keys.add(build_problem_id(prob))
            return keys

        set_a = _extract_canonical_keys(cohort_a_records)
        set_b = _extract_canonical_keys(cohort_b_records)
        overlap = sorted(list(set_a.intersection(set_b)))

        for entity_uri in overlap:
            rule_id = (
                "RULE_5_1_CANDIDATE_PARTITION_LEAKAGE"
                if partition_key == "candidate_id"
                else "RULE_5_2_PROBLEM_PARTITION_LEAKAGE"
            )
            violations.append(
                ValidationViolation(
                    fault_class="G5",
                    rule_id=rule_id,
                    entity_id=entity_uri,
                    message=f"Cross-cohort partition leakage detected: '{entity_uri}' is present in both partitions.",
                    context={"partition_key": partition_key, "overlapping_entity": entity_uri},
                )
            )

        return self._build_report(violations, checks, [], "UNVERIFIED_REGISTRATION_PROVENANCE")

    def validate_cohort_disjointness(
        self,
        manifest_a: Union[CohortManifest, Dict[str, Any]],
        manifest_b: Union[CohortManifest, Dict[str, Any]],
    ) -> ValidationReport:
        """Validate partition disjointness between two cohort manifests based on their partition policy."""
        m_a = manifest_a.to_dict() if isinstance(manifest_a, CohortManifest) else manifest_a
        m_b = manifest_b.to_dict() if isinstance(manifest_b, CohortManifest) else manifest_b

        policy_a = m_a.get("partition_policy", {})
        partition_key = policy_a.get("partition_key", "candidate_id")

        return self.validate_partition_disjointness(
            cohort_a_records=m_a.get("members", []),
            cohort_b_records=m_b.get("members", []),
            partition_key=partition_key,
        )


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def _load_json_or_jsonl(path_str: str) -> List[Dict[str, Any]]:
    p = Path(path_str)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {path_str}")

    content = p.read_text(encoding="utf-8").strip()
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in content.splitlines() if line.strip()]
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError(f"Unexpected JSON data type: {type(data).__name__}")
    except json.JSONDecodeError:
        # Fall back to jsonl
        return [json.loads(line) for line in content.splitlines() if line.strip()]


def main(args: Optional[List[str]] = None) -> int:
    """CLI entry point for EvidenceValidator."""
    parser = argparse.ArgumentParser(
        description="StepGuard F3 Evidence Contracts & Referential Integrity Validator."
    )
    parser.add_argument("--manifest", type=str, help="Path to CohortManifest JSON")
    parser.add_argument("--steps", type=str, help="Path to steps JSON/JSONL")
    parser.add_argument("--mutations", type=str, help="Path to mutations JSON/JSONL")
    parser.add_argument("--traces", type=str, help="Path to traces JSON/JSONL")
    parser.add_argument("--labels", type=str, help="Path to labels JSON/JSONL")
    parser.add_argument("--predictions", type=str, help="Path to predictions JSON/JSONL")
    parser.add_argument("--candidates", type=str, help="Path to candidates JSON/JSONL")
    parser.add_argument("--candidate-mapping", type=str, help="Path to legacy candidate mapping JSON")
    parser.add_argument("--trusted-registry", type=str, help="Path to trusted manifest registry JSON")
    parser.add_argument("--report-out", type=str, help="Path to write validation report JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress console report summary")

    cli_args = parser.parse_args(args)

    trusted_registry: Optional[Dict[str, ManifestRegistrationEntry]] = None
    if cli_args.trusted_registry:
        try:
            reg_data = json.loads(Path(cli_args.trusted_registry).read_text(encoding="utf-8"))
            trusted_registry = {
                k: ManifestRegistrationEntry(
                    cohort_id=v["cohort_id"],
                    expected_manifest_sha256=v["expected_manifest_sha256"],
                    expected_git_commit_sha=v["expected_git_commit_sha"],
                    repo_relative_path=v["repo_relative_path"],
                )
                for k, v in reg_data.items()
            }
        except Exception as e:
            sys.stderr.write(f"Error loading trusted registry: {e}\n")
            return 2

    candidate_mapping: Optional[CandidateIdentityMapping] = None
    if cli_args.candidate_mapping:
        try:
            mapping_dict = json.loads(Path(cli_args.candidate_mapping).read_text(encoding="utf-8"))
            candidate_mapping = CandidateIdentityMapping(mapping=mapping_dict)
        except Exception as e:
            sys.stderr.write(f"Error loading candidate mapping: {e}\n")
            return 2

    validator = EvidenceValidator(
        trusted_registry=trusted_registry,
        candidate_mapping=candidate_mapping,
    )

    combined_violations: List[ValidationViolation] = []
    total_checks = 0
    merkle_roots: List[str] = []
    registration_status = "UNVERIFIED_REGISTRATION_PROVENANCE"

    manifest_obj: Optional[Dict[str, Any]] = None
    if cli_args.manifest:
        try:
            m_path = Path(cli_args.manifest)
            m_bytes = m_path.read_bytes()
            m_dict = json.loads(m_bytes.decode("utf-8"))
            manifest_obj = m_dict
            rep = validator.validate_manifest(m_dict, manifest_raw_content=m_bytes)
            combined_violations.extend(rep.violations)
            total_checks += rep.total_checks
            merkle_roots.extend(rep.merkle_roots_verified)
            registration_status = rep.registration_status
        except Exception as e:
            sys.stderr.write(f"Error validating manifest: {e}\n")
            return 2

    # Load lineage files if provided
    try:
        candidates = _load_json_or_jsonl(cli_args.candidates) if cli_args.candidates else []
        steps = _load_json_or_jsonl(cli_args.steps) if cli_args.steps else []
        mutations = _load_json_or_jsonl(cli_args.mutations) if cli_args.mutations else []
        traces = _load_json_or_jsonl(cli_args.traces) if cli_args.traces else []
        labels = _load_json_or_jsonl(cli_args.labels) if cli_args.labels else None
        predictions = _load_json_or_jsonl(cli_args.predictions) if cli_args.predictions else None

        if steps or mutations or traces or candidates:
            lineage_rep = validator.validate_lineage(
                candidates=candidates,
                steps=steps,
                mutations=mutations,
                traces=traces,
                labels=labels,
                predictions=predictions,
                manifest=manifest_obj,
            )
            combined_violations.extend(lineage_rep.violations)
            total_checks += lineage_rep.total_checks
    except Exception as e:
        sys.stderr.write(f"Error loading lineage files: {e}\n")
        return 2

    final_report = validator._build_report(
        combined_violations,
        total_checks,
        merkle_roots,
        registration_status,
    )

    if cli_args.report_out:
        try:
            out_p = Path(cli_args.report_out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(final_report.to_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            sys.stderr.write(f"Error writing report to '{cli_args.report_out}': {e}\n")
            return 2

    if not cli_args.quiet:
        status_str = "PASSED" if final_report.is_valid else "FAILED"
        print(f"--- StepGuard Evidence Contract Validation [{status_str}] ---")
        print(f"Total Checks: {final_report.total_checks}")
        print(f"Total Violations: {len(final_report.violations)}")
        print(f"Violations by Class: {final_report.summary_by_class}")
        print(f"Registration Status: {final_report.registration_status}")
        if final_report.merkle_roots_verified:
            print(f"Merkle Roots Verified: {len(final_report.merkle_roots_verified)}")
        if final_report.violations:
            print("\nViolations:")
            for v in final_report.violations:
                print(f"  [{v.fault_class}:{v.rule_id}] {v.entity_id}: {v.message}")

    return 0 if final_report.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
