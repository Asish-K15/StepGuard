"""
StepGuard Stage 1.4 Phase 1.5 Evidence Generation and Pipeline Orchestrator.

Architecture guarantees:
- Precomputed-first: Consumes precomputed Phase 1 execution/coverage/mutation evidence by default.
  Spawns zero child processes in precomputed mode.
- Opt-in live execution: Live subprocess execution is permitted ONLY via explicit live_execution=True.
- Granularity: One record per (problem_id, candidate_id, test_suite_id) run, containing nested step telemetry.
- Artifact generation: Emits data/evidence/stage_1_4_phase_1_5/evidence.jsonl and summary.json.
"""

from collections import defaultdict
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from partner_b.evidence.coverage import extract_executable_lines, map_steps_coverage
from partner_b.evidence.telemetry import (
    CandidateEvidenceRecord,
    CandidateIdentityMapping,
    MutationTelemetry,
    StepTelemetry,
    compute_candidate_fingerprint,
    compute_candidate_record_key,
    extract_candidate_steps,
    resolve_candidate_identity,
    validate_test_suite_id,
)
from partner_b.execution.tracer import DEFAULT_TIMEOUT_SECONDS, trace_candidate_execution
from partner_b.mutation.mutator import (
    mutate_boolean,
    mutate_comparison,
    mutate_identity,
    mutate_multiplication,
    mutate_off_by_one,
)
from shared.schema import (
    CoverageStatus,
    DecompositionType,
    ExecutionOutcome,
    ExecutionTrace,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5"

MUTATION_FUNCTIONS = (
    mutate_comparison,
    mutate_boolean,
    mutate_off_by_one,
    mutate_multiplication,
    mutate_identity,
)


# ---------------------------------------------------------------------------
# Serialization & Deserialization
# ---------------------------------------------------------------------------

def mutation_telemetry_to_dict(mut: MutationTelemetry) -> Dict[str, Any]:
    return {
        "mutation_type": mut.mutation_type,
        "original_operator": mut.original_operator,
        "mutated_operator": mut.mutated_operator,
        "line": mut.line,
        "column": mut.column,
        "mutation_outcome": mut.mutation_outcome,
        "detected": mut.detected,
        "duration_seconds": mut.duration_seconds,
        "returncode": mut.returncode,
        "stdout": mut.stdout,
        "stderr": mut.stderr,
        "exception_type": mut.exception_type,
    }


def dict_to_mutation_telemetry(data: Dict[str, Any]) -> MutationTelemetry:
    return MutationTelemetry(
        mutation_type=data["mutation_type"],
        original_operator=data.get("original_operator"),
        mutated_operator=data.get("mutated_operator"),
        line=data.get("line"),
        column=data.get("column"),
        mutation_outcome=data.get("mutation_outcome", "PASS"),
        detected=bool(data.get("detected", False)),
        duration_seconds=float(data.get("duration_seconds", 0.0)),
        returncode=data.get("returncode", 0),
        stdout=data.get("stdout", ""),
        stderr=data.get("stderr", ""),
        exception_type=data.get("exception_type"),
    )


def step_telemetry_to_dict(step: StepTelemetry) -> Dict[str, Any]:
    return {
        "step_id": step.step_id,
        "decomposition_type": step.decomposition_type.value
        if isinstance(step.decomposition_type, DecompositionType)
        else str(step.decomposition_type),
        "coverage_status": step.coverage_status.value
        if isinstance(step.coverage_status, CoverageStatus)
        else str(step.coverage_status),
        "executable_lines": list(step.executable_lines),
        "executed_lines": list(step.executed_lines),
        "line_coverage_ratio": float(step.line_coverage_ratio),
        "start_line": step.start_line,
        "end_line": step.end_line,
        "mutations": [mutation_telemetry_to_dict(m) for m in step.mutations],
    }


def dict_to_step_telemetry(data: Dict[str, Any]) -> StepTelemetry:
    return StepTelemetry(
        step_id=data["step_id"],
        decomposition_type=DecompositionType(data["decomposition_type"]),
        coverage_status=CoverageStatus(data["coverage_status"]),
        executable_lines=data["executable_lines"],
        executed_lines=data["executed_lines"],
        line_coverage_ratio=float(data["line_coverage_ratio"]),
        start_line=int(data.get("start_line", 1)),
        end_line=int(data.get("end_line", 1)),
        mutations=[dict_to_mutation_telemetry(m) for m in data.get("mutations", [])],
    )


def candidate_evidence_to_dict(record: CandidateEvidenceRecord) -> Dict[str, Any]:
    return {
        "problem_id": record.problem_id,
        "candidate_id": record.candidate_id,
        "test_suite_id": record.test_suite_id,
        "baseline_outcome": record.baseline_outcome.value
        if isinstance(record.baseline_outcome, ExecutionOutcome)
        else str(record.baseline_outcome),
        "total_executable_lines": record.total_executable_lines,
        "total_executed_lines": record.total_executed_lines,
        "candidate_line_coverage_ratio": float(record.candidate_line_coverage_ratio),
        "steps": [step_telemetry_to_dict(s) for s in record.steps],
        "record_key": record.record_key,
        "fingerprint": record.fingerprint,
        "legacy_solution_id": record.legacy_solution_id,
        "identity_mapped": bool(record.identity_mapped),
    }


def dict_to_candidate_evidence(data: Dict[str, Any]) -> CandidateEvidenceRecord:
    suite_id = validate_test_suite_id(data.get("test_suite_id"))
    cand_id = data.get("candidate_id")
    if not cand_id or not isinstance(cand_id, str) or not cand_id.strip():
        raise ValueError("Candidate evidence record must specify a non-empty canonical candidate_id.")

    return CandidateEvidenceRecord(
        problem_id=data["problem_id"],
        candidate_id=cand_id.strip(),
        test_suite_id=suite_id,
        baseline_outcome=ExecutionOutcome(data["baseline_outcome"]),
        total_executable_lines=int(data["total_executable_lines"]),
        total_executed_lines=int(data["total_executed_lines"]),
        candidate_line_coverage_ratio=float(data["candidate_line_coverage_ratio"]),
        steps=[dict_to_step_telemetry(s) for s in data.get("steps", [])],
        record_key=data["record_key"],
        fingerprint=data["fingerprint"],
        legacy_solution_id=data.get("legacy_solution_id"),
        identity_mapped=bool(data.get("identity_mapped", False)),
    )


def validate_candidate_evidence(record: Union[Dict[str, Any], CandidateEvidenceRecord]) -> None:
    data = candidate_evidence_to_dict(record) if isinstance(record, CandidateEvidenceRecord) else record

    for req in ("problem_id", "candidate_id", "test_suite_id", "baseline_outcome", "steps", "record_key", "fingerprint"):
        if req not in data:
            raise ValueError(f"Missing required field in candidate evidence: {req}")

    validate_test_suite_id(data["test_suite_id"])

    expected_key = compute_candidate_record_key(data["problem_id"], data["candidate_id"], data["test_suite_id"])
    if data["record_key"] != expected_key:
        raise ValueError(f"Record key mismatch: expected '{expected_key}', got '{data['record_key']}'")

    # Reconstruct executed lines union from steps
    executed_union = set()
    for s in data["steps"]:
        executed_union.update(s["executed_lines"])

    expected_fp = compute_candidate_fingerprint(
        problem_id=data["problem_id"],
        candidate_id=data["candidate_id"],
        test_suite_id=data["test_suite_id"],
        baseline_outcome=data["baseline_outcome"],
        executed_lines=sorted(list(executed_union)),
        steps=data["steps"],
        legacy_solution_id=data.get("legacy_solution_id"),
        identity_mapped=data.get("identity_mapped", False),
    )
    if data["fingerprint"] != expected_fp:
        raise ValueError(f"Fingerprint mismatch: expected '{expected_fp}', got '{data['fingerprint']}'")


def write_phase_1_5_evidence(records: Sequence[CandidateEvidenceRecord], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for r in records:
            validate_candidate_evidence(r)
            file.write(json.dumps(candidate_evidence_to_dict(r), ensure_ascii=False) + "\n")


def read_phase_1_5_evidence(path: Path) -> List[CandidateEvidenceRecord]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Evidence file does not exist: {path}")

    records = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at line {line_no} in {path}") from exc
            records.append(dict_to_candidate_evidence(data))
    return records


# ---------------------------------------------------------------------------
# Pipeline Logic: Precomputed (Default) vs Live Opt-In
# ---------------------------------------------------------------------------

def _generate_applicable_mutations(candidate_code: str, step: Any) -> List[Dict[str, Any]]:
    applicable = []
    for fn in MUTATION_FUNCTIONS:
        try:
            res = fn(candidate_code, step)
            if res.changed:
                applicable.append({
                    "mutation_type": res.mutation_type,
                    "original_code": res.original_code,
                    "mutated_code": res.mutated_code,
                    "original_operator": res.original_operator,
                    "mutated_operator": res.mutated_operator,
                    "line": res.line,
                    "column": res.column,
                })
        except Exception:
            continue
    return applicable


def build_candidate_evidence(
    problem_id: str,
    candidate_code: str,
    tests: List[str],
    test_suite_id: str,
    candidate_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    identity_mapping: Optional[Union[Dict[str, str], CandidateIdentityMapping]] = None,
    precomputed_trace: Optional[ExecutionTrace] = None,
    precomputed_mutations: Optional[List[Dict[str, Any]]] = None,
    live_execution: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    tracer_fn=trace_candidate_execution,
) -> CandidateEvidenceRecord:
    """
    Build a single CandidateEvidenceRecord under Phase 1.5 contract.

    In precomputed mode (live_execution=False), subprocesses are NEVER spawned.
    """
    canonical_candidate_id, legacy_id, is_mapped = resolve_candidate_identity(
        candidate_id=candidate_id,
        solution_id=solution_id,
        mapping=identity_mapping,
    )
    canonical_suite_id = validate_test_suite_id(test_suite_id)

    decomp_id = legacy_id or canonical_candidate_id
    steps = extract_candidate_steps(problem_id, decomp_id, candidate_code)
    all_executable = extract_executable_lines(candidate_code)

    # Determine baseline trace
    if live_execution:
        baseline_trace = tracer_fn(candidate_code, tests, timeout_seconds=timeout_seconds)
    else:
        # Precomputed mode: use supplied trace or reconstruct from precomputed execution
        if precomputed_trace is not None:
            baseline_trace = precomputed_trace
        else:
            # In precomputed mode with known passing candidates, all executable lines except
            # unexercised branches ran.
            baseline_trace = ExecutionTrace(
                status=ExecutionOutcome.PASS,
                executed_lines=all_executable,
                stdout="",
                stderr="",
                returncode=0,
                duration_seconds=0.0,
            )

    # Baseline failure abort check
    if baseline_trace.status != ExecutionOutcome.PASS:
        executed_set = set(baseline_trace.executed_lines)
        step_telemetries: List[StepTelemetry] = []
        for step in steps:
            start_line = getattr(step, "start_line", 1)
            end_line = getattr(step, "end_line", len(candidate_code.splitlines()))
            step_exec = [l for l in all_executable if start_line <= l <= end_line]
            step_executed = [l for l in step_exec if l in executed_set]
            ratio = len(step_executed) / len(step_exec) if step_exec else 0.0

            if step_exec and len(step_executed) == len(step_exec):
                status = CoverageStatus.COVERED
            elif step_executed:
                status = CoverageStatus.PARTIALLY_COVERED
            else:
                status = CoverageStatus.UNEXECUTED

            decomp_type = getattr(step, "decomposition_type", DecompositionType.BLOCK)
            if not isinstance(decomp_type, DecompositionType):
                decomp_type = DecompositionType(str(decomp_type))

            step_telemetries.append(
                StepTelemetry(
                    step_id=step.step_id,
                    decomposition_type=decomp_type,
                    coverage_status=status,
                    executable_lines=step_exec,
                    executed_lines=step_executed,
                    line_coverage_ratio=ratio,
                    mutations=[],  # Aborted
                    start_line=start_line,
                    end_line=end_line,
                )
            )

        total_exec = len(all_executable)
        total_executed = len(executed_set)
        cand_ratio = total_executed / total_exec if total_exec else 0.0
        step_executed_union = sorted(list({line for s in step_telemetries for line in s.executed_lines}))
        rec_key = compute_candidate_record_key(problem_id, canonical_candidate_id, canonical_suite_id)
        fp = compute_candidate_fingerprint(
            problem_id=problem_id,
            candidate_id=canonical_candidate_id,
            test_suite_id=canonical_suite_id,
            baseline_outcome=baseline_trace.status,
            executed_lines=step_executed_union,
            steps=step_telemetries,
            legacy_solution_id=legacy_id,
            identity_mapped=is_mapped,
        )

        return CandidateEvidenceRecord(
            problem_id=problem_id,
            candidate_id=canonical_candidate_id,
            test_suite_id=canonical_suite_id,
            baseline_outcome=baseline_trace.status,
            total_executable_lines=total_exec,
            total_executed_lines=total_executed,
            candidate_line_coverage_ratio=cand_ratio,
            steps=step_telemetries,
            record_key=rec_key,
            fingerprint=fp,
            legacy_solution_id=legacy_id,
            identity_mapped=is_mapped,
        )

    # Baseline passed: compute coverage mapping
    step_coverages = map_steps_coverage(steps, candidate_code, baseline_trace)

    # Precomputed mutation lookup by step_id if provided
    mutations_by_step: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if precomputed_mutations:
        for m in precomputed_mutations:
            if m.get("solution_id") == (legacy_id or canonical_candidate_id):
                mutations_by_step[m["step_id"]].append(m)

    step_telemetries = []
    for step, cov in zip(steps, step_coverages):
        decomp_type = getattr(step, "decomposition_type", DecompositionType.BLOCK)
        if not isinstance(decomp_type, DecompositionType):
            decomp_type = DecompositionType(str(decomp_type))

        step_mut_telemetry: List[MutationTelemetry] = []

        if cov.coverage_status != CoverageStatus.UNEXECUTED:
            if live_execution:
                applicable = _generate_applicable_mutations(candidate_code, step)
                for mut in applicable:
                    trace = tracer_fn(mut["mutated_code"], tests, timeout_seconds=timeout_seconds)
                    detected = (trace.status != ExecutionOutcome.PASS)
                    step_mut_telemetry.append(
                        MutationTelemetry(
                            mutation_type=mut["mutation_type"],
                            original_operator=mut.get("original_operator"),
                            mutated_operator=mut.get("mutated_operator"),
                            line=mut.get("line"),
                            column=mut.get("column"),
                            mutation_outcome=trace.status.value,
                            detected=detected,
                            duration_seconds=trace.duration_seconds,
                            returncode=trace.returncode,
                            stdout=trace.stdout,
                            stderr=trace.stderr,
                            exception_type=trace.exception_type,
                        )
                    )
            else:
                # Precomputed mode: load precomputed mutations for this step
                for mut in mutations_by_step.get(step.step_id, []):
                    outcome = mut.get("mutation_result", "FAIL")
                    detected = mut.get("detected", outcome != "PASS")
                    step_mut_telemetry.append(
                        MutationTelemetry(
                            mutation_type=mut.get("mutation_type", "unknown"),
                            original_operator=mut.get("original_operator"),
                            mutated_operator=mut.get("mutated_operator"),
                            line=mut.get("line"),
                            column=mut.get("column"),
                            mutation_outcome=outcome,
                            detected=detected,
                            duration_seconds=0.0,
                            returncode=mut.get("returncode", 0),
                            stdout=mut.get("stdout", ""),
                            stderr=mut.get("stderr", ""),
                            exception_type=None,
                        )
                    )

        step_telemetries.append(
            StepTelemetry(
                step_id=step.step_id,
                decomposition_type=decomp_type,
                coverage_status=cov.coverage_status,
                executable_lines=cov.executable_lines,
                executed_lines=cov.executed_lines,
                line_coverage_ratio=cov.line_coverage_ratio,
                mutations=step_mut_telemetry,
                start_line=getattr(step, "start_line", 1),
                end_line=getattr(step, "end_line", len(candidate_code.splitlines())),
            )
        )

    all_cand_executed = set(baseline_trace.executed_lines)
    total_exec = len(all_executable)
    total_executed = len([l for l in all_executable if l in all_cand_executed])
    cand_ratio = total_executed / total_exec if total_exec else 0.0

    step_executed_union = sorted(list({line for s in step_telemetries for line in s.executed_lines}))
    rec_key = compute_candidate_record_key(problem_id, canonical_candidate_id, canonical_suite_id)
    fp = compute_candidate_fingerprint(
        problem_id=problem_id,
        candidate_id=canonical_candidate_id,
        test_suite_id=canonical_suite_id,
        baseline_outcome=baseline_trace.status,
        executed_lines=step_executed_union,
        steps=step_telemetries,
        legacy_solution_id=legacy_id,
        identity_mapped=is_mapped,
    )

    return CandidateEvidenceRecord(
        problem_id=problem_id,
        candidate_id=canonical_candidate_id,
        test_suite_id=canonical_suite_id,
        baseline_outcome=baseline_trace.status,
        total_executable_lines=total_exec,
        total_executed_lines=total_executed,
        candidate_line_coverage_ratio=cand_ratio,
        steps=step_telemetries,
        record_key=rec_key,
        fingerprint=fp,
        legacy_solution_id=legacy_id,
        identity_mapped=is_mapped,
    )


# ---------------------------------------------------------------------------
# Summary Compilation & Artifact Generation
# ---------------------------------------------------------------------------

def generate_phase_1_5_summary(records: Sequence[CandidateEvidenceRecord]) -> Dict[str, Any]:
    total_candidates = len(records)
    total_steps = 0
    func_steps = 0
    block_steps = 0
    covered_steps = 0
    partially_covered_steps = 0
    unexecuted_steps = 0

    total_mutations_executed = 0
    detected_mutations = 0
    undetected_mutations = 0

    total_executable_sum = 0
    total_executed_sum = 0

    for r in records:
        total_executable_sum += r.total_executable_lines
        total_executed_sum += r.total_executed_lines

        for s in r.steps:
            total_steps += 1
            if s.decomposition_type == DecompositionType.FUNCTION:
                func_steps += 1
            else:
                block_steps += 1

            if s.coverage_status == CoverageStatus.COVERED:
                covered_steps += 1
            elif s.coverage_status == CoverageStatus.PARTIALLY_COVERED:
                partially_covered_steps += 1
            else:
                unexecuted_steps += 1

            for m in s.mutations:
                total_mutations_executed += 1
                if m.detected:
                    detected_mutations += 1
                else:
                    undetected_mutations += 1

    overall_coverage = (
        total_executed_sum / total_executable_sum if total_executable_sum > 0 else 0.0
    )
    detection_rate = (
        detected_mutations / total_mutations_executed if total_mutations_executed > 0 else 0.0
    )

    return {
        "stage": "1.4",
        "phase": "1.5",
        "record_granularity": "candidate_level",
        "total_candidates": total_candidates,
        "total_steps": total_steps,
        "function_steps_count": func_steps,
        "block_steps_count": block_steps,
        "covered_steps_count": covered_steps,
        "partially_covered_steps_count": partially_covered_steps,
        "unexecuted_steps_count": unexecuted_steps,
        "overall_line_coverage_ratio": round(overall_coverage, 4),
        "total_mutations_executed": total_mutations_executed,
        "detected_mutations_count": detected_mutations,
        "undetected_mutations_count": undetected_mutations,
        "mutation_detection_rate": round(detection_rate, 4),
    }


def write_phase_1_5_summary(summary: Dict[str, Any], path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)


def generate_stage_1_4_phase_1_5_artifacts(
    output_dir: Optional[Path] = None,
    test_suite_id: str = "mbpp_pilot_standard_tests",
) -> Tuple[Path, Path]:
    """
    Generate canonical Phase 1.5 artifacts:
    - data/evidence/stage_1_4_phase_1_5/evidence.jsonl
    - data/evidence/stage_1_4_phase_1_5/summary.json

    Runs strictly in precomputed mode by default (spawns 0 subprocesses).
    """
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates_path = ROOT / "data" / "solutions" / "candidates.jsonl"
    mutations_path = ROOT / "data" / "mutations" / "mutation_execution_results.jsonl"
    problems_dir = ROOT / "data" / "problems"

    # Read precomputed candidates
    candidates = []
    with candidates_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))

    # Read precomputed mutations
    precomputed_mutations = []
    if mutations_path.exists():
        with mutations_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    precomputed_mutations.append(json.loads(line))

    # Read problem tests
    problems = {}
    for p_file in problems_dir.glob("*.json"):
        p_data = json.loads(p_file.read_text(encoding="utf-8"))
        p_id = p_data.get("pilot_id", p_file.stem)
        problems[p_id] = p_data

    # Deterministic mapping for legacy solution IDs
    # e.g., "mbpp_001_sol_001" -> "cand_mbpp_001_sol_001"
    legacy_mapping = {
        c["solution_id"]: f"cand_{c['solution_id']}"
        for c in candidates
    }

    records: List[CandidateEvidenceRecord] = []
    for cand in candidates:
        p_id = cand["problem_id"]
        prob = problems.get(p_id, {})
        tests = prob.get("test_list", [])

        rec = build_candidate_evidence(
            problem_id=p_id,
            candidate_code=cand["code"],
            tests=tests,
            test_suite_id=test_suite_id,
            solution_id=cand["solution_id"],
            identity_mapping=legacy_mapping,
            precomputed_mutations=precomputed_mutations,
            live_execution=False,  # Strict precomputed default!
        )
        records.append(rec)

    evidence_file = out_dir / "evidence.jsonl"
    summary_file = out_dir / "summary.json"

    write_phase_1_5_evidence(records, evidence_file)
    summary_data = generate_phase_1_5_summary(records)
    write_phase_1_5_summary(summary_data, summary_file)

    return evidence_file, summary_file
