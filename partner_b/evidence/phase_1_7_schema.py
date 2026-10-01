"""
StepGuard Stage 1.4 Phase 1.7 Schema Module.

Defines schemas, relationship vocabulary, and serialization helpers for
cross-phase lineage, provenance, and relationship auditing across Phase 1,
Phase 1.5, Phase 1.6, and legacy Stage 0A evidence.

Guarantees:
- Strict adherence to approved relationship vocabulary:
  DIRECTLY_LINKED, DESCRIPTIVE_ONLY, UNAVAILABLE, AMBIGUOUS.
- Strictly descriptive telemetry only.
- Strict absence of correctness labels, adequacy scores, PRM rankings, or evaluative verdicts.
- Explicit non-join fields and data availability disclaimers.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Set


DISCLAIMER_TEXT = (
    "Execution reachability is an observation of the supplied test execution and is not semantic correctness, branch coverage, or a comprehensive test-adequacy assessment."
)

DATA_AVAILABILITY_NOTICE = (
    "Persisted Phase 1 execution traces are unavailable; no cross-phase join performed."
)

PROCESS_ISOLATION_NOTICE = (
    "Subprocess execution used in Stage 1.4 tracing provides execution containment "
    "and timeout handling; it is not a hardened operating system security sandbox."
)

APPROVED_RELATIONSHIPS: Set[str] = {
    "DIRECTLY_LINKED",
    "DESCRIPTIVE_ONLY",
    "UNAVAILABLE",
    "AMBIGUOUS",
}

FORBIDDEN_VERDICT_TERMS: Set[str] = {
    "correct",
    "correctness",
    "adequate",
    "adequacy",
    "ranking",
    "prm_score",
    "evaluative_verdict",
    "quality_score",
}


@dataclass
class CandidateLineageRecord:
    """
    Phase 1.7 candidate-level lineage and relationship record.
    Represents one candidate source observation from Phase 1.5.
    """
    record_type: str
    record_key: str
    problem_id: str
    candidate_id: str
    test_suite_id: str
    legacy_solution_id: Optional[str]
    identity_mapped: bool
    relationships: Dict[str, Dict[str, Any]]
    telemetry_provenance: Dict[str, Any]
    lineage_fingerprint: str
    phase_1_5_fingerprint: str
    phase_1_6_fingerprint: str
    notices: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.record_type != "candidate_observation":
            raise ValueError(
                f"CandidateLineageRecord must have record_type='candidate_observation', got '{self.record_type}'"
            )
        for target, rel in self.relationships.items():
            status = rel.get("status")
            if status not in APPROVED_RELATIONSHIPS:
                raise ValueError(
                    f"Relationship '{target}' has invalid status '{status}'. "
                    f"Must be one of {sorted(APPROVED_RELATIONSHIPS)}"
                )


@dataclass
class PhaseContractRelationshipRecord:
    """
    Phase 1.7 relationship-only record for contract-level / phase-level relationships.
    Has a distinct, deterministic record type and does not duplicate candidate relationships.
    """
    record_type: str
    relationship_id: str
    source_phase: str
    target_phase: str
    relationship_status: str
    relationship_scope: str
    rationale: str
    relationship_fingerprint: str
    disclaimer: str = DISCLAIMER_TEXT

    def __post_init__(self) -> None:
        if self.record_type != "phase_contract_relationship":
            raise ValueError(
                f"PhaseContractRelationshipRecord must have record_type='phase_contract_relationship', got '{self.record_type}'"
            )
        if self.relationship_status not in APPROVED_RELATIONSHIPS:
            raise ValueError(
                f"Invalid relationship_status '{self.relationship_status}'. "
                f"Must be one of {sorted(APPROVED_RELATIONSHIPS)}"
            )


def compute_candidate_lineage_fingerprint(
    problem_id: str,
    candidate_id: str,
    test_suite_id: str,
    phase_1_5_fingerprint: str,
    phase_1_6_fingerprint: str,
    relationships: Dict[str, Dict[str, Any]],
    telemetry_provenance: Dict[str, Any],
    legacy_solution_id: Optional[str] = None,
    identity_mapped: bool = False,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a CandidateLineageRecord."""
    payload = {
        "problem_id": str(problem_id),
        "candidate_id": str(candidate_id),
        "test_suite_id": str(test_suite_id),
        "phase_1_5_fingerprint": str(phase_1_5_fingerprint),
        "phase_1_6_fingerprint": str(phase_1_6_fingerprint),
        "relationships": {
            k: {
                "status": v["status"],
                "target_role": v.get("target_role", ""),
                "evidence_type": v.get("evidence_type", ""),
                "join_key": v.get("join_key"),
                "target_fingerprint": v.get("target_fingerprint"),
            }
            for k, v in sorted(relationships.items())
        },
        "telemetry_provenance": {
            k: telemetry_provenance[k]
            for k in sorted(telemetry_provenance.keys())
        },
        "legacy_solution_id": str(legacy_solution_id) if legacy_solution_id is not None else None,
        "identity_mapped": bool(identity_mapped),
    }
    canonical_repr = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def compute_contract_relationship_fingerprint(
    relationship_id: str,
    source_phase: str,
    target_phase: str,
    relationship_status: str,
    relationship_scope: str,
    rationale: str,
) -> str:
    """Compute a deterministic SHA-256 fingerprint for a PhaseContractRelationshipRecord."""
    payload = {
        "relationship_id": str(relationship_id),
        "source_phase": str(source_phase),
        "target_phase": str(target_phase),
        "relationship_status": str(relationship_status),
        "relationship_scope": str(relationship_scope),
        "rationale": str(rationale),
    }
    canonical_repr = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def candidate_lineage_to_dict(record: CandidateLineageRecord) -> Dict[str, Any]:
    """Serialize CandidateLineageRecord to an ordered dictionary."""
    return {
        "record_type": record.record_type,
        "record_key": record.record_key,
        "problem_id": record.problem_id,
        "candidate_id": record.candidate_id,
        "test_suite_id": record.test_suite_id,
        "legacy_solution_id": record.legacy_solution_id,
        "identity_mapped": bool(record.identity_mapped),
        "lineage_fingerprint": record.lineage_fingerprint,
        "phase_1_5_fingerprint": record.phase_1_5_fingerprint,
        "phase_1_6_fingerprint": record.phase_1_6_fingerprint,
        "relationships": record.relationships,
        "telemetry_provenance": record.telemetry_provenance,
        "notices": record.notices,
    }


def dict_to_candidate_lineage(data: Dict[str, Any]) -> CandidateLineageRecord:
    """Deserialize dictionary into CandidateLineageRecord."""
    return CandidateLineageRecord(
        record_type=str(data["record_type"]),
        record_key=str(data["record_key"]),
        problem_id=str(data["problem_id"]),
        candidate_id=str(data["candidate_id"]),
        test_suite_id=str(data["test_suite_id"]),
        legacy_solution_id=data.get("legacy_solution_id"),
        identity_mapped=bool(data.get("identity_mapped", False)),
        lineage_fingerprint=str(data["lineage_fingerprint"]),
        phase_1_5_fingerprint=str(data["phase_1_5_fingerprint"]),
        phase_1_6_fingerprint=str(data["phase_1_6_fingerprint"]),
        relationships=dict(data.get("relationships", {})),
        telemetry_provenance=dict(data.get("telemetry_provenance", {})),
        notices=dict(data.get("notices", {})),
    )


def contract_relationship_to_dict(record: PhaseContractRelationshipRecord) -> Dict[str, Any]:
    """Serialize PhaseContractRelationshipRecord to an ordered dictionary."""
    return {
        "record_type": record.record_type,
        "relationship_id": record.relationship_id,
        "source_phase": record.source_phase,
        "target_phase": record.target_phase,
        "relationship_status": record.relationship_status,
        "relationship_scope": record.relationship_scope,
        "rationale": record.rationale,
        "relationship_fingerprint": record.relationship_fingerprint,
        "disclaimer": record.disclaimer,
    }


def dict_to_contract_relationship(data: Dict[str, Any]) -> PhaseContractRelationshipRecord:
    """Deserialize dictionary into PhaseContractRelationshipRecord."""
    return PhaseContractRelationshipRecord(
        record_type=str(data["record_type"]),
        relationship_id=str(data["relationship_id"]),
        source_phase=str(data["source_phase"]),
        target_phase=str(data["target_phase"]),
        relationship_status=str(data["relationship_status"]),
        relationship_scope=str(data["relationship_scope"]),
        rationale=str(data["rationale"]),
        relationship_fingerprint=str(data["relationship_fingerprint"]),
        disclaimer=str(data.get("disclaimer", DISCLAIMER_TEXT)),
    )
