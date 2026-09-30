"""
StepGuard Stage 1.4 Phase 1.6 Schema Module.

Defines schemas and serialization helpers for candidate-level descriptive analysis
of Phase 1.5 evidence.

Guarantees:
- Descriptive telemetry only.
- Strict absence of correctness labels, adequacy scores, PRM rankings, or evaluative verdicts.
- Explicit non-join fields and data availability disclaimers.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence


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

FORBIDDEN_VERDICT_TERMS = {
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
class StepDescriptiveSummary:
    """Descriptive metrics for a single decomposition step."""
    step_id: str
    decomposition_type: str
    coverage_status: str
    executable_line_count: int
    executed_line_count: int
    line_coverage_ratio: float
    mutations_count: int
    mutations_detected: int
    mutations_undetected: int
    mutation_types: List[str] = field(default_factory=list)


@dataclass
class CandidateAnalysisRecord:
    """
    Phase 1.6 candidate-level descriptive analysis record.
    Preserves canonical candidate identity and reports empirical telemetry distributions.
    Strictly descriptive: contains zero evaluative, adequacy, or correctness verdicts.
    """
    problem_id: str
    candidate_id: str
    test_suite_id: str
    record_key: str
    phase_1_5_fingerprint: str
    baseline_outcome: str
    total_executable_lines: int
    total_executed_lines: int
    candidate_line_coverage_ratio: float
    total_steps: int
    function_steps_count: int
    block_steps_count: int
    covered_steps_count: int
    partially_covered_steps_count: int
    unexecuted_steps_count: int
    total_mutations: int
    detected_mutations: int
    undetected_mutations: int
    mutation_detection_rate: Optional[float]
    step_summaries: List[Dict[str, Any]]
    mutation_breakdown_by_type: Dict[str, Dict[str, int]]
    mutation_outcomes: Dict[str, int]
    analysis_fingerprint: str
    legacy_solution_id: Optional[str] = None
    identity_mapped: bool = False
    phase_1_traces_available: bool = False
    cross_phase_join_performed: bool = False
    data_availability_notice: str = DATA_AVAILABILITY_NOTICE
    evaluation_disclaimer: str = DISCLAIMER_TEXT


def compute_analysis_fingerprint(
    problem_id: str,
    candidate_id: str,
    test_suite_id: str,
    phase_1_5_fingerprint: str,
    total_steps: int,
    total_mutations: int,
    detected_mutations: int,
    step_summaries: Sequence[Dict[str, Any]],
    mutation_breakdown: Dict[str, Dict[str, int]],
    legacy_solution_id: Optional[str] = None,
    identity_mapped: bool = False,
) -> str:
    """
    Compute a deterministic SHA-256 fingerprint for a CandidateAnalysisRecord.
    Uses canonical JSON representation with sorted keys.
    """
    payload = {
        "problem_id": str(problem_id),
        "candidate_id": str(candidate_id),
        "test_suite_id": str(test_suite_id),
        "phase_1_5_fingerprint": str(phase_1_5_fingerprint),
        "total_steps": int(total_steps),
        "total_mutations": int(total_mutations),
        "detected_mutations": int(detected_mutations),
        "step_summaries": [
            {
                "step_id": str(s["step_id"]),
                "decomposition_type": str(s["decomposition_type"]),
                "coverage_status": str(s["coverage_status"]),
                "mutations_count": int(s.get("mutations_count", 0)),
                "mutations_detected": int(s.get("mutations_detected", 0)),
            }
            for s in step_summaries
        ],
        "mutation_breakdown": {
            k: {
                "total": int(v.get("total", 0)),
                "detected": int(v.get("detected", 0)),
                "undetected": int(v.get("undetected", 0)),
            }
            for k, v in sorted(mutation_breakdown.items())
        },
        "legacy_solution_id": str(legacy_solution_id) if legacy_solution_id is not None else None,
        "identity_mapped": bool(identity_mapped),
        "phase_1_traces_available": False,
        "cross_phase_join_performed": False,
    }
    canonical_repr = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


def candidate_analysis_to_dict(analysis: CandidateAnalysisRecord) -> Dict[str, Any]:
    """Serialize CandidateAnalysisRecord to an ordered dictionary."""
    return {
        "problem_id": analysis.problem_id,
        "candidate_id": analysis.candidate_id,
        "test_suite_id": analysis.test_suite_id,
        "record_key": analysis.record_key,
        "phase_1_5_fingerprint": analysis.phase_1_5_fingerprint,
        "analysis_fingerprint": analysis.analysis_fingerprint,
        "legacy_solution_id": analysis.legacy_solution_id,
        "identity_mapped": bool(analysis.identity_mapped),
        "baseline_outcome": analysis.baseline_outcome,
        "total_executable_lines": analysis.total_executable_lines,
        "total_executed_lines": analysis.total_executed_lines,
        "candidate_line_coverage_ratio": float(analysis.candidate_line_coverage_ratio),
        "total_steps": analysis.total_steps,
        "function_steps_count": analysis.function_steps_count,
        "block_steps_count": analysis.block_steps_count,
        "covered_steps_count": analysis.covered_steps_count,
        "partially_covered_steps_count": analysis.partially_covered_steps_count,
        "unexecuted_steps_count": analysis.unexecuted_steps_count,
        "total_mutations": analysis.total_mutations,
        "detected_mutations": analysis.detected_mutations,
        "undetected_mutations": analysis.undetected_mutations,
        "mutation_detection_rate": analysis.mutation_detection_rate,
        "step_summaries": analysis.step_summaries,
        "mutation_breakdown_by_type": analysis.mutation_breakdown_by_type,
        "mutation_outcomes": analysis.mutation_outcomes,
        "phase_1_traces_available": bool(analysis.phase_1_traces_available),
        "cross_phase_join_performed": bool(analysis.cross_phase_join_performed),
        "data_availability_notice": analysis.data_availability_notice,
        "evaluation_disclaimer": analysis.evaluation_disclaimer,
    }


def dict_to_candidate_analysis(data: Dict[str, Any]) -> CandidateAnalysisRecord:
    """Deserialize dictionary into CandidateAnalysisRecord."""
    return CandidateAnalysisRecord(
        problem_id=str(data["problem_id"]),
        candidate_id=str(data["candidate_id"]),
        test_suite_id=str(data["test_suite_id"]),
        record_key=str(data["record_key"]),
        phase_1_5_fingerprint=str(data["phase_1_5_fingerprint"]),
        analysis_fingerprint=str(data["analysis_fingerprint"]),
        legacy_solution_id=data.get("legacy_solution_id"),
        identity_mapped=bool(data.get("identity_mapped", False)),
        baseline_outcome=str(data["baseline_outcome"]),
        total_executable_lines=int(data["total_executable_lines"]),
        total_executed_lines=int(data["total_executed_lines"]),
        candidate_line_coverage_ratio=float(data["candidate_line_coverage_ratio"]),
        total_steps=int(data["total_steps"]),
        function_steps_count=int(data["function_steps_count"]),
        block_steps_count=int(data["block_steps_count"]),
        covered_steps_count=int(data["covered_steps_count"]),
        partially_covered_steps_count=int(data["partially_covered_steps_count"]),
        unexecuted_steps_count=int(data["unexecuted_steps_count"]),
        total_mutations=int(data["total_mutations"]),
        detected_mutations=int(data["detected_mutations"]),
        undetected_mutations=int(data["undetected_mutations"]),
        mutation_detection_rate=(
            float(data["mutation_detection_rate"])
            if data.get("mutation_detection_rate") is not None
            else None
        ),
        step_summaries=list(data.get("step_summaries", [])),
        mutation_breakdown_by_type=dict(data.get("mutation_breakdown_by_type", {})),
        mutation_outcomes=dict(data.get("mutation_outcomes", {})),
        phase_1_traces_available=bool(data.get("phase_1_traces_available", False)),
        cross_phase_join_performed=bool(data.get("cross_phase_join_performed", False)),
        data_availability_notice=str(data.get("data_availability_notice", DATA_AVAILABILITY_NOTICE)),
        evaluation_disclaimer=str(data.get("evaluation_disclaimer", DISCLAIMER_TEXT)),
    )
