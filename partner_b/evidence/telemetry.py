"""
StepGuard Stage 1.4 Phase 1.5 Telemetry and Identity Module.

Provides:
- Canonical candidate identity contract and explicit legacy mapping.
- Canonical test-suite identity enforcement (rejects implicit defaults).
- Candidate-level evidence schema with nested step-level telemetry.
- Deterministic record key and SHA-256 fingerprinting.
- Statement coverage aggregation and step telemetry extraction.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from partner_b.decomposition.block import decompose_blocks
from partner_b.decomposition.function import decompose_functions
from partner_b.evidence.coverage import extract_executable_lines, map_step_coverage, map_steps_coverage
from shared.schema import (
    CoverageStatus,
    DecompositionType,
    ExecutionOutcome,
    ExecutionTrace,
    StepCoverage,
)


@dataclass(frozen=True)
class CandidateIdentityMapping:
    """
    Explicit, documented, deterministic mapping from legacy solution_id to canonical candidate_id.
    Guarantees that equivalence is never inferred merely because string values match.
    """
    mapping: Dict[str, str]

    def map_solution_to_candidate(self, legacy_solution_id: str) -> str:
        if not legacy_solution_id or not isinstance(legacy_solution_id, str):
            raise ValueError("Legacy solution_id must be a non-empty string.")
        clean_sol = legacy_solution_id.strip()
        if clean_sol not in self.mapping:
            raise KeyError(
                f"Legacy solution_id '{clean_sol}' is not in the explicit candidate identity mapping."
            )
        return self.mapping[clean_sol]

    def get_canonical_id(self, legacy_solution_id: str) -> str:
        return self.map_solution_to_candidate(legacy_solution_id)


def resolve_candidate_identity(
    candidate_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    mapping: Optional[Union[Dict[str, str], CandidateIdentityMapping]] = None,
) -> Tuple[str, Optional[str], bool]:
    """
    Resolve and validate candidate identity under the Phase 1.5 identity contract.

    Rules:
    - candidate_id is the canonical identity.
    - Legacy solution_id is supported ONLY via an explicit, deterministic mapping.
    - Equivalence is NEVER inferred merely because solution_id and candidate_id strings match.
    - Ambiguous or conflicting combinations fail fast with ValueError.

    Returns:
        (canonical_candidate_id, legacy_solution_id, is_mapped)
    """
    clean_candidate = (
        candidate_id.strip()
        if candidate_id and isinstance(candidate_id, str) and candidate_id.strip()
        else None
    )
    clean_solution = (
        solution_id.strip()
        if solution_id and isinstance(solution_id, str) and solution_id.strip()
        else None
    )

    mapper: Optional[CandidateIdentityMapping] = None
    if mapping is not None:
        if isinstance(mapping, CandidateIdentityMapping):
            mapper = mapping
        elif isinstance(mapping, dict):
            mapper = CandidateIdentityMapping(mapping=mapping)
        else:
            raise TypeError("mapping must be a dict or CandidateIdentityMapping instance.")

    if clean_candidate:
        if clean_solution:
            if mapper is None:
                raise ValueError(
                    "Ambiguous identity: both canonical candidate_id and legacy solution_id were provided "
                    "without an explicit mapping. Equivalence cannot be silently inferred."
                )
            expected_candidate = mapper.get_canonical_id(clean_solution)
            if expected_candidate != clean_candidate:
                raise ValueError(
                    f"Conflicting identity: provided canonical candidate_id '{clean_candidate}' does not match "
                    f"mapped value '{expected_candidate}' for legacy solution_id '{clean_solution}'."
                )
            return clean_candidate, clean_solution, True
        return clean_candidate, None, False

    if clean_solution:
        if mapper is None:
            raise ValueError(
                f"Legacy solution_id '{clean_solution}' provided without explicit candidate identity mapping. "
                "Phase 1.5 requires canonical candidate_id or an explicit, documented mapping."
            )
        canonical_id = mapper.get_canonical_id(clean_solution)
        return canonical_id, clean_solution, True

    raise ValueError(
        "Missing candidate identity: caller must supply canonical candidate_id or an explicitly mapped legacy solution_id."
    )


def validate_test_suite_id(test_suite_id: Optional[str]) -> str:
    """
    Validate that the caller supplied an explicit, canonical test_suite_id.
    Explicitly refuses to fabricate or infer an implicit default (such as {problem_id}_baseline_tests).
    """
    if not test_suite_id or not isinstance(test_suite_id, str) or not test_suite_id.strip():
        raise ValueError(
            "Canonical test_suite_id is required and cannot be empty, null, or implicitly fabricated from problem_id."
        )
    return test_suite_id.strip()


@dataclass
class MutationTelemetry:
    """
    Outcome telemetry for a single mutation executed against the test suite.
    """
    mutation_type: str
    original_operator: Optional[str] = None
    mutated_operator: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    mutation_outcome: str = "PASS"
    detected: bool = False
    duration_seconds: float = 0.0
    returncode: Optional[int] = 0
    stdout: str = ""
    stderr: str = ""
    exception_type: Optional[str] = None


@dataclass
class StepTelemetry:
    """
    Statement-level reachability and mutation outcome telemetry for a single decomposition step.
    """
    step_id: str
    decomposition_type: DecompositionType
    coverage_status: CoverageStatus
    executable_lines: List[int]
    executed_lines: List[int]
    line_coverage_ratio: float
    mutations: List[MutationTelemetry] = field(default_factory=list)
    start_line: int = 1
    end_line: int = 1


@dataclass
class CandidateEvidenceRecord:
    """
    Approved Phase 1.5 Evidence Record: One record per (problem_id, candidate_id, test_suite_id) run.
    Contains nested step telemetry. step_id is strictly NOT part of the top-level identity.
    """
    problem_id: str
    candidate_id: str  # Canonical Phase 1.5 candidate identity
    test_suite_id: str  # Canonical test suite identity (required, caller-supplied)
    baseline_outcome: ExecutionOutcome
    total_executable_lines: int
    total_executed_lines: int
    candidate_line_coverage_ratio: float
    steps: List[StepTelemetry]
    record_key: str
    fingerprint: str
    legacy_solution_id: Optional[str] = None
    identity_mapped: bool = False


def compute_candidate_record_key(
    problem_id: str,
    candidate_id: str,
    test_suite_id: str,
) -> str:
    """
    Compute a deterministic canonical record key for a candidate-level evidence record.
    Notice: step_id is NOT in the top-level key.
    """
    return f"{problem_id}::{candidate_id}::{test_suite_id}"


def compute_candidate_fingerprint(
    problem_id: str,
    candidate_id: str,
    test_suite_id: str,
    baseline_outcome: Union[str, ExecutionOutcome],
    executed_lines: Sequence[int],
    steps: Sequence[Union[StepTelemetry, Dict[str, Any]]],
    legacy_solution_id: Optional[str] = None,
    identity_mapped: bool = False,
) -> str:
    """
    Compute a deterministic SHA-256 fingerprint/hash for a candidate-level evidence record.
    Incorporates canonical identity, suite identity, baseline outcome, executed lines,
    nested step summaries, and mapping metadata.
    """
    step_summaries = []
    for s in steps:
        if isinstance(s, StepTelemetry):
            step_summaries.append({
                "step_id": s.step_id,
                "decomposition_type": s.decomposition_type.value
                if isinstance(s.decomposition_type, DecompositionType)
                else str(s.decomposition_type),
                "coverage_status": s.coverage_status.value
                if isinstance(s.coverage_status, CoverageStatus)
                else str(s.coverage_status),
                "executed_lines": sorted(list(s.executed_lines)),
                "mutation_count": len(s.mutations),
                "detected_count": sum(1 for m in s.mutations if m.detected),
            })
        elif isinstance(s, dict):
            muts = s.get("mutations", [])
            step_summaries.append({
                "step_id": s["step_id"],
                "decomposition_type": str(s["decomposition_type"]),
                "coverage_status": str(s["coverage_status"]),
                "executed_lines": sorted(list(s.get("executed_lines", []))),
                "mutation_count": len(muts),
                "detected_count": sum(1 for m in muts if m.get("detected", False)),
            })

    payload = {
        "problem_id": str(problem_id),
        "candidate_id": str(candidate_id),
        "test_suite_id": str(test_suite_id),
        "baseline_outcome": str(getattr(baseline_outcome, "value", baseline_outcome)),
        "executed_lines": sorted(list(executed_lines)),
        "steps": step_summaries,
        "legacy_solution_id": str(legacy_solution_id) if legacy_solution_id is not None else None,
        "identity_mapped": bool(identity_mapped),
    }

    canonical_repr = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def extract_candidate_steps(
    problem_id: str,
    solution_id: str,
    candidate_code: str,
) -> List[Any]:
    """
    Decompose candidate into both function-level and block-level steps.
    """
    func_steps = decompose_functions(problem_id, solution_id, candidate_code)
    block_steps = decompose_blocks(problem_id, solution_id, candidate_code)
    return list(func_steps) + list(block_steps)
