"""
StepGuard Stage 1.4 Phase 1.6 Analysis and Pipeline Orchestrator.

Implements deterministic, read-only descriptive analysis of verified Phase 1.5 evidence.

Core Guarantees:
- Purely descriptive telemetry distributions.
- Zero correctness verdicts, adequacy scoring, PRM training/ranking, or evaluative classifications.
- Explicit recording that persisted Phase 1 traces are unavailable; zero cross-phase joins performed.
- Deterministic, byte-stable output serialization across identical inputs.
- Safe output handling with explicit overwrite control and zero mutation of frozen source files.
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from partner_b.evidence.phase_1_6_schema import (
    CandidateAnalysisRecord,
    DATA_AVAILABILITY_NOTICE,
    DISCLAIMER_TEXT,
    PROCESS_ISOLATION_NOTICE,
    candidate_analysis_to_dict,
    compute_analysis_fingerprint,
    dict_to_candidate_analysis,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHASE_1_5_EVIDENCE = (
    ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "evidence.jsonl"
)
DEFAULT_PHASE_1_5_SUMMARY = (
    ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "summary.json"
)
DEFAULT_OUTPUT_DIR = (
    ROOT / "data" / "evidence" / "stage_1_4_phase_1_6"
)


def compute_file_sha256(path: Path) -> str:
    """Compute the SHA-256 digest of raw file bytes."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hash computation: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _to_rel_posix(path: Path) -> str:
    """Convert path to relative POSIX string if under ROOT, else file name."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except (ValueError, RuntimeError):
        return path.name


def read_and_validate_phase_1_5_evidence(path: Path) -> List[Dict[str, Any]]:
    """
    Read and validate Phase 1.5 JSONL evidence file.
    Rejects malformed, incomplete, or corrupted records fail-fast.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Phase 1.5 evidence file not found: {path}")

    records = []
    required_keys = {
        "problem_id",
        "candidate_id",
        "test_suite_id",
        "baseline_outcome",
        "total_executable_lines",
        "total_executed_lines",
        "candidate_line_coverage_ratio",
        "steps",
        "record_key",
        "fingerprint",
    }

    with path.open("r", encoding="utf-8") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_no} in {path}: {exc}"
                ) from exc

            missing = required_keys - data.keys()
            if missing:
                raise ValueError(
                    f"Line {line_no} in {path} missing required fields: {sorted(missing)}"
                )

            cand_id = data.get("candidate_id")
            if not cand_id or not isinstance(cand_id, str) or not cand_id.strip():
                raise ValueError(
                    f"Line {line_no} in {path} has empty or invalid candidate_id"
                )

            suite_id = data.get("test_suite_id")
            if not suite_id or not isinstance(suite_id, str) or not suite_id.strip():
                raise ValueError(
                    f"Line {line_no} in {path} has empty or invalid test_suite_id"
                )

            steps = data.get("steps")
            if not isinstance(steps, list):
                raise ValueError(
                    f"Line {line_no} in {path} has non-list 'steps' field"
                )

            for step_idx, step in enumerate(steps):
                if not isinstance(step, dict):
                    raise ValueError(
                        f"Line {line_no} step {step_idx} is not a valid object"
                    )
                for step_req in ("step_id", "decomposition_type", "coverage_status", "mutations"):
                    if step_req not in step:
                        raise ValueError(
                            f"Line {line_no} step {step_idx} missing required field '{step_req}'"
                        )
                if not isinstance(step.get("mutations"), list):
                    raise ValueError(
                        f"Line {line_no} step {step_idx} 'mutations' must be a list"
                    )

            records.append(data)

    if not records:
        raise ValueError(f"Phase 1.5 evidence file is empty: {path}")

    return records


def analyze_candidate_record(record: Dict[str, Any]) -> CandidateAnalysisRecord:
    """
    Produce a descriptive CandidateAnalysisRecord from a validated Phase 1.5 record.
    Strictly descriptive: no PRM scores, quality labels, or correctness verdicts.
    """
    problem_id = str(record["problem_id"])
    candidate_id = str(record["candidate_id"]).strip()
    test_suite_id = str(record["test_suite_id"]).strip()
    record_key = str(record["record_key"])
    phase_1_5_fp = str(record["fingerprint"])
    legacy_solution_id = record.get("legacy_solution_id")
    identity_mapped = bool(record.get("identity_mapped", False))

    baseline_outcome = str(record["baseline_outcome"])
    total_executable = int(record["total_executable_lines"])
    total_executed = int(record["total_executed_lines"])
    cand_coverage_ratio = float(record["candidate_line_coverage_ratio"])

    steps = record.get("steps", [])
    total_steps = len(steps)

    func_steps = 0
    block_steps = 0
    covered_steps = 0
    partially_covered_steps = 0
    unexecuted_steps = 0

    total_mutations = 0
    detected_mutations = 0
    undetected_mutations = 0

    step_summaries: List[Dict[str, Any]] = []
    mutation_breakdown: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total": 0, "detected": 0, "undetected": 0}
    )
    mutation_outcomes: Dict[str, int] = defaultdict(int)

    for s in steps:
        decomp_type = str(s.get("decomposition_type"))
        cov_status = str(s.get("coverage_status"))

        if decomp_type == "function":
            func_steps += 1
        elif decomp_type == "block":
            block_steps += 1

        if cov_status == "COVERED":
            covered_steps += 1
        elif cov_status == "PARTIALLY_COVERED":
            partially_covered_steps += 1
        elif cov_status == "UNEXECUTED":
            unexecuted_steps += 1

        muts = s.get("mutations", [])
        step_mut_total = len(muts)
        step_mut_det = 0
        step_mut_undet = 0
        step_mut_types = []

        for m in muts:
            total_mutations += 1
            m_type = str(m.get("mutation_type", "unknown"))
            m_detected = bool(m.get("detected", False))
            m_outcome = str(m.get("mutation_outcome", "UNKNOWN"))

            mutation_outcomes[m_outcome] += 1
            mutation_breakdown[m_type]["total"] += 1

            if m_detected:
                detected_mutations += 1
                step_mut_det += 1
                mutation_breakdown[m_type]["detected"] += 1
            else:
                undetected_mutations += 1
                step_mut_undet += 1
                mutation_breakdown[m_type]["undetected"] += 1

            if m_type not in step_mut_types:
                step_mut_types.append(m_type)

        step_exec_lines = list(s.get("executable_lines", []))
        step_exec_cnt = len(step_exec_lines)
        step_done_lines = list(s.get("executed_lines", []))
        step_done_cnt = len(step_done_lines)
        step_ratio = (
            float(s.get("line_coverage_ratio", 0.0))
            if step_exec_cnt > 0
            else 0.0
        )

        step_summaries.append({
            "step_id": str(s.get("step_id")),
            "decomposition_type": decomp_type,
            "coverage_status": cov_status,
            "executable_line_count": step_exec_cnt,
            "executed_line_count": step_done_cnt,
            "line_coverage_ratio": round(step_ratio, 4),
            "mutations_count": step_mut_total,
            "mutations_detected": step_mut_det,
            "mutations_undetected": step_mut_undet,
            "mutation_types": sorted(step_mut_types),
        })

    mut_detection_rate = (
        round(detected_mutations / total_mutations, 4)
        if total_mutations > 0
        else None
    )

    clean_breakdown = {
        k: dict(v)
        for k, v in sorted(mutation_breakdown.items())
    }
    clean_outcomes = dict(sorted(mutation_outcomes.items()))

    analysis_fp = compute_analysis_fingerprint(
        problem_id=problem_id,
        candidate_id=candidate_id,
        test_suite_id=test_suite_id,
        phase_1_5_fingerprint=phase_1_5_fp,
        total_steps=total_steps,
        total_mutations=total_mutations,
        detected_mutations=detected_mutations,
        step_summaries=step_summaries,
        mutation_breakdown=clean_breakdown,
        legacy_solution_id=legacy_solution_id,
        identity_mapped=identity_mapped,
    )

    return CandidateAnalysisRecord(
        problem_id=problem_id,
        candidate_id=candidate_id,
        test_suite_id=test_suite_id,
        record_key=record_key,
        phase_1_5_fingerprint=phase_1_5_fp,
        baseline_outcome=baseline_outcome,
        total_executable_lines=total_executable,
        total_executed_lines=total_executed,
        candidate_line_coverage_ratio=cand_coverage_ratio,
        total_steps=total_steps,
        function_steps_count=func_steps,
        block_steps_count=block_steps,
        covered_steps_count=covered_steps,
        partially_covered_steps_count=partially_covered_steps,
        unexecuted_steps_count=unexecuted_steps,
        total_mutations=total_mutations,
        detected_mutations=detected_mutations,
        undetected_mutations=undetected_mutations,
        mutation_detection_rate=mut_detection_rate,
        step_summaries=step_summaries,
        mutation_breakdown_by_type=clean_breakdown,
        mutation_outcomes=clean_outcomes,
        analysis_fingerprint=analysis_fp,
        legacy_solution_id=legacy_solution_id,
        identity_mapped=identity_mapped,
        phase_1_traces_available=False,
        cross_phase_join_performed=False,
        data_availability_notice=DATA_AVAILABILITY_NOTICE,
        evaluation_disclaimer=DISCLAIMER_TEXT,
    )


def generate_phase_1_6_summary(
    analyses: Sequence[CandidateAnalysisRecord],
    phase_1_5_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Compile aggregate descriptive statistics across all analyzed candidates."""
    total_candidates = len(analyses)

    problem_counts = Counter(a.problem_id for a in analyses)
    total_steps = sum(a.total_steps for a in analyses)
    func_steps = sum(a.function_steps_count for a in analyses)
    block_steps = sum(a.block_steps_count for a in analyses)
    covered_steps = sum(a.covered_steps_count for a in analyses)
    partially_covered = sum(a.partially_covered_steps_count for a in analyses)
    unexecuted_steps = sum(a.unexecuted_steps_count for a in analyses)

    total_exec_sum = sum(a.total_executable_lines for a in analyses)
    total_done_sum = sum(a.total_executed_lines for a in analyses)
    overall_coverage = (
        round(total_done_sum / total_exec_sum, 4)
        if total_exec_sum > 0
        else 0.0
    )

    total_mutations = sum(a.total_mutations for a in analyses)
    detected_mutations = sum(a.detected_mutations for a in analyses)
    undetected_mutations = sum(a.undetected_mutations for a in analyses)
    overall_detection_rate = (
        round(detected_mutations / total_mutations, 4)
        if total_mutations > 0
        else 0.0
    )

    mut_type_agg: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "detected": 0, "undetected": 0}
    )
    outcome_agg: Dict[str, int] = defaultdict(int)

    for a in analyses:
        for m_type, counts in a.mutation_breakdown_by_type.items():
            mut_type_agg[m_type]["total"] += counts["total"]
            mut_type_agg[m_type]["detected"] += counts["detected"]
            mut_type_agg[m_type]["undetected"] += counts["undetected"]

        for outcome, cnt in a.mutation_outcomes.items():
            outcome_agg[outcome] += cnt

    mutations_by_type = {}
    for m_type, counts in sorted(mut_type_agg.items()):
        t = counts["total"]
        d = counts["detected"]
        u = counts["undetected"]
        rate = round(d / t, 4) if t > 0 else 0.0
        mutations_by_type[m_type] = {
            "total": t,
            "detected": d,
            "undetected": u,
            "detection_rate": rate,
        }

    return {
        "stage": "1.4",
        "phase": "1.6",
        "analysis_type": "descriptive_telemetry_distribution",
        "record_granularity": "candidate_level",
        "total_candidates_analyzed": total_candidates,
        "total_problems": len(problem_counts),
        "problem_distribution": dict(sorted(problem_counts.items())),
        "step_metrics": {
            "total_steps": total_steps,
            "function_steps_count": func_steps,
            "block_steps_count": block_steps,
            "covered_steps_count": covered_steps,
            "partially_covered_steps_count": partially_covered,
            "unexecuted_steps_count": unexecuted_steps,
            "overall_line_coverage_ratio": overall_coverage,
        },
        "mutation_metrics": {
            "total_mutations_executed": total_mutations,
            "detected_mutations_count": detected_mutations,
            "undetected_mutations_count": undetected_mutations,
            "mutation_detection_rate": overall_detection_rate,
            "mutations_by_type": mutations_by_type,
            "mutations_by_outcome": dict(sorted(outcome_agg.items())),
        },
        "cross_phase_contracts": {
            "phase_1_persisted_traces_available": False,
            "cross_phase_join_performed": False,
            "reason_for_no_cross_phase_join": (
                "Phase 1 execution tracer is in-memory only; no persisted trace dataset exists "
                "in the closure commit, and Phase 1 schemas lack canonical candidate_id and test_suite_id."
            ),
            "precomputed_evidence_notice": (
                "Persisted Phase 1.5 evidence reflects precomputed-first execution. "
                "100% statement reachability in baseline records reflects precomputed passing candidates "
                "and does not assert dynamic branch coverage."
            ),
            "process_isolation_notice": PROCESS_ISOLATION_NOTICE,
            "evaluation_disclaimer": DISCLAIMER_TEXT,
        },
    }


def generate_phase_1_6_manifest(
    input_evidence_path: Path,
    input_summary_path: Path,
    output_analysis_path: Path,
    output_summary_path: Path,
    analyses: Sequence[CandidateAnalysisRecord],
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate manifest documenting inputs, outputs, hashes, and data quality findings."""
    ts = (
        created_at
        if created_at is not None
        else datetime.now(timezone.utc).isoformat()
    )

    ev_sha = compute_file_sha256(input_evidence_path)
    sum_sha = compute_file_sha256(input_summary_path)

    out_analysis_sha = compute_file_sha256(output_analysis_path)
    out_summary_sha = compute_file_sha256(output_summary_path)

    return {
        "manifest_version": "1.0.0",
        "stage": "1.4",
        "phase": "1.6",
        "created_at": ts,
        "commit_base": "66a5d6ddd97c24fdaea7ae47377d98791e764ad5",
        "inputs": [
            {
                "path": _to_rel_posix(input_evidence_path),
                "role": "phase_1_5_candidate_evidence",
                "format": "jsonl",
                "record_count": len(analyses),
                "sha256": ev_sha,
            },
            {
                "path": _to_rel_posix(input_summary_path),
                "role": "phase_1_5_summary",
                "format": "json",
                "sha256": sum_sha,
            },
        ],
        "missing_inputs": {
            "persisted_phase_1_traces": {
                "status": "UNAVAILABLE",
                "explanation": (
                    "Phase 1 execution tracer is in-memory only; no persisted trace dataset exists "
                    "in the closure commit."
                ),
                "cross_phase_join": "OMITTED",
            }
        },
        "outputs": [
            {
                "path": _to_rel_posix(output_analysis_path),
                "role": "candidate_level_descriptive_analysis",
                "format": "jsonl",
                "record_count": len(analyses),
                "sha256": out_analysis_sha,
            },
            {
                "path": _to_rel_posix(output_summary_path),
                "role": "aggregate_descriptive_summary",
                "format": "json",
                "sha256": out_summary_sha,
            },
        ],
        "data_quality_findings": {
            "all_candidates_valid_phase_1_5": True,
            "all_candidates_identity_mapped": all(a.identity_mapped for a in analyses),
            "total_candidates_analyzed": len(analyses),
            "schema_validation_passed": True,
            "no_verdicts_or_rankings_enforced": True,
        },
        "security_and_containment_notice": PROCESS_ISOLATION_NOTICE,
    }


def run_phase_1_6_pipeline(
    evidence_path: Optional[Path] = None,
    phase_1_5_summary_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    overwrite: bool = True,
    created_at: Optional[str] = None,
) -> Tuple[Path, Path, Path]:
    """
    Execute Phase 1.6 analysis pipeline:
    1. Read and validate Phase 1.5 inputs without modification.
    2. Generate candidate-level descriptive analysis records.
    3. Compile aggregate descriptive summary.
    4. Confine writes strictly to output_dir with safe overwrite checks.
    5. Write analysis.jsonl, summary.json, and manifest.json using canonical serialization.
    6. Re-verify source input hashes to guarantee zero mutation.

    Returns:
        (analysis_file, summary_file, manifest_file)
    """
    ev_path = Path(evidence_path) if evidence_path else DEFAULT_PHASE_1_5_EVIDENCE
    sum_path = Path(phase_1_5_summary_path) if phase_1_5_summary_path else DEFAULT_PHASE_1_5_SUMMARY
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    # Record pre-execution source hashes
    pre_ev_sha = compute_file_sha256(ev_path)
    pre_sum_sha = compute_file_sha256(sum_path)

    # 1. Read and validate
    raw_records = read_and_validate_phase_1_5_evidence(ev_path)
    phase_1_5_summary_data = None
    if sum_path.exists():
        try:
            phase_1_5_summary_data = json.loads(sum_path.read_text(encoding="utf-8"))
        except Exception:
            phase_1_5_summary_data = None

    # 2. Analyze candidates
    analyses = [analyze_candidate_record(r) for r in raw_records]

    # 3. Compile summary
    summary_data = generate_phase_1_6_summary(analyses, phase_1_5_summary_data)

    # 4. Safe output handling
    out_dir.mkdir(parents=True, exist_ok=True)
    analysis_file = out_dir / "analysis.jsonl"
    summary_file = out_dir / "summary.json"
    manifest_file = out_dir / "manifest.json"

    if not overwrite:
        for out_file in (analysis_file, summary_file, manifest_file):
            if out_file.exists():
                raise FileExistsError(
                    f"Refusing to overwrite existing output file under overwrite=False: {out_file}"
                )

    # 5. Write analysis.jsonl (deterministic per-line canonical JSON)
    with analysis_file.open("w", encoding="utf-8", newline="\n") as f:
        for a in analyses:
            d = candidate_analysis_to_dict(a)
            # Strict deterministic serialization
            line_str = json.dumps(d, ensure_ascii=False, sort_keys=True)
            f.write(line_str + "\n")

    # 6. Write summary.json
    with summary_file.open("w", encoding="utf-8", newline="\n") as f:
        summary_str = json.dumps(summary_data, indent=2, sort_keys=True, ensure_ascii=False)
        f.write(summary_str + "\n")

    # 7. Generate and write manifest.json
    manifest_data = generate_phase_1_6_manifest(
        input_evidence_path=ev_path,
        input_summary_path=sum_path,
        output_analysis_path=analysis_file,
        output_summary_path=summary_file,
        analyses=analyses,
        created_at=created_at,
    )
    with manifest_file.open("w", encoding="utf-8", newline="\n") as f:
        manifest_str = json.dumps(manifest_data, indent=2, sort_keys=True, ensure_ascii=False)
        f.write(manifest_str + "\n")

    # 8. Post-execution source hash verification
    post_ev_sha = compute_file_sha256(ev_path)
    post_sum_sha = compute_file_sha256(sum_path)

    if pre_ev_sha != post_ev_sha:
        raise RuntimeError(
            f"FATAL: Source input {ev_path} was modified during Phase 1.6 execution!"
        )
    if pre_sum_sha != post_sum_sha:
        raise RuntimeError(
            f"FATAL: Source input {sum_path} was modified during Phase 1.6 execution!"
        )

    return analysis_file, summary_file, manifest_file
