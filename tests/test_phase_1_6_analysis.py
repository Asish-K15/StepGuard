"""
Unit tests for StepGuard Stage 1.4 Phase 1.6 analysis logic and schema contracts.
"""

import json
from pathlib import Path
import pytest

from partner_b.evidence.phase_1_6 import (
    analyze_candidate_record,
    generate_phase_1_6_summary,
    read_and_validate_phase_1_5_evidence,
    run_phase_1_6_pipeline,
)
from partner_b.evidence.phase_1_6_schema import (
    CandidateAnalysisRecord,
    DATA_AVAILABILITY_NOTICE,
    DISCLAIMER_TEXT,
    FORBIDDEN_VERDICT_TERMS,
    candidate_analysis_to_dict,
    dict_to_candidate_analysis,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE_1_5_EVIDENCE = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "evidence.jsonl"
PHASE_1_5_SUMMARY = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "summary.json"


def test_phase_1_5_evidence_loading_and_validation():
    """Verify loading and schema validation of canonical Phase 1.5 evidence."""
    records = read_and_validate_phase_1_5_evidence(PHASE_1_5_EVIDENCE)
    assert len(records) == 25, f"Expected 25 candidate records, got {len(records)}"

    for r in records:
        assert "problem_id" in r
        assert "candidate_id" in r
        assert "test_suite_id" in r
        assert "baseline_outcome" in r
        assert "steps" in r
        assert len(r["steps"]) > 0
        assert r["test_suite_id"] == "mbpp_pilot_standard_tests"


def test_descriptive_aggregation_counts(tmp_path: Path):
    """Verify that aggregate descriptive statistics strictly match verified Phase 1.5 numbers."""
    analysis_file, summary_file, manifest_file = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
    )

    with summary_file.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["stage"] == "1.4"
    assert summary["phase"] == "1.6"
    assert summary["total_candidates_analyzed"] == 25
    assert summary["total_problems"] == 5
    assert summary["problem_distribution"] == {
        "mbpp_001": 5,
        "mbpp_002": 5,
        "mbpp_003": 5,
        "mbpp_004": 5,
        "mbpp_005": 5,
    }

    # Step metrics
    step_metrics = summary["step_metrics"]
    assert step_metrics["total_steps"] == 144
    assert step_metrics["function_steps_count"] == 25
    assert step_metrics["block_steps_count"] == 119
    assert step_metrics["covered_steps_count"] == 144
    assert step_metrics["partially_covered_steps_count"] == 0
    assert step_metrics["unexecuted_steps_count"] == 0
    assert step_metrics["overall_line_coverage_ratio"] == 1.0

    # Mutation metrics
    mut_metrics = summary["mutation_metrics"]
    assert mut_metrics["total_mutations_executed"] == 99
    assert mut_metrics["detected_mutations_count"] == 86
    assert mut_metrics["undetected_mutations_count"] == 13
    assert mut_metrics["mutation_detection_rate"] == 0.8687

    # Breakdown by type
    by_type = mut_metrics["mutations_by_type"]
    assert by_type["comparison_swap"]["total"] == 74
    assert by_type["comparison_swap"]["detected"] == 69
    assert by_type["comparison_swap"]["undetected"] == 5

    assert by_type["off_by_one"]["total"] == 14
    assert by_type["off_by_one"]["detected"] == 14
    assert by_type["off_by_one"]["undetected"] == 0

    assert by_type["boolean_flip"]["total"] == 11
    assert by_type["boolean_flip"]["detected"] == 3
    assert by_type["boolean_flip"]["undetected"] == 8

    # Breakdown by outcome
    by_outcome = mut_metrics["mutations_by_outcome"]
    assert by_outcome["FAIL"] == 67
    assert by_outcome["RUNTIME_ERROR"] == 19
    assert by_outcome["PASS"] == 13


def test_missing_phase_1_trace_explicitly_reported(tmp_path: Path):
    """Verify that Phase 1 trace absence and non-join are explicitly stated in every record and summary."""
    analysis_file, summary_file, manifest_file = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
    )

    with summary_file.open("r", encoding="utf-8") as f:
        summary = json.load(f)

    contracts = summary["cross_phase_contracts"]
    assert contracts["phase_1_persisted_traces_available"] is False
    assert contracts["cross_phase_join_performed"] is False
    assert "in-memory only" in contracts["reason_for_no_cross_phase_join"]
    assert "precomputed-first" in contracts["precomputed_evidence_notice"]
    assert contracts["evaluation_disclaimer"] == DISCLAIMER_TEXT

    # Check each analysis record
    with analysis_file.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            assert rec["phase_1_traces_available"] is False
            assert rec["cross_phase_join_performed"] is False
            assert rec["data_availability_notice"] == DATA_AVAILABILITY_NOTICE
            assert rec["evaluation_disclaimer"] == DISCLAIMER_TEXT


def test_strictly_no_evaluative_or_correctness_verdicts(tmp_path: Path):
    """Verify zero forbidden verdict/ranking/correctness keys appear in any output record or summary."""
    analysis_file, summary_file, _ = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
    )

    def check_no_forbidden(data, context=""):
        if isinstance(data, dict):
            for k, v in data.items():
                lower_k = k.lower()
                for forbidden in FORBIDDEN_VERDICT_TERMS:
                    assert forbidden not in lower_k, (
                        f"Forbidden verdict term '{forbidden}' found in key '{k}' under {context}"
                    )
                check_no_forbidden(v, f"{context}.{k}")
        elif isinstance(data, list):
            for i, elem in enumerate(data):
                check_no_forbidden(elem, f"{context}[{i}]")

    with summary_file.open("r", encoding="utf-8") as f:
        summary = json.load(f)
        check_no_forbidden(summary, "summary")

    with analysis_file.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            check_no_forbidden(rec, "analysis_record")


def test_rejection_of_invalid_and_incomplete_records(tmp_path: Path):
    """Verify fail-fast rejection for incomplete, malformed, or missing required fields."""
    bad_jsonl = tmp_path / "bad_evidence.jsonl"

    # Missing candidate_id
    bad_jsonl.write_text(
        json.dumps({
            "problem_id": "mbpp_001",
            "candidate_id": "",
            "test_suite_id": "suite_01",
            "baseline_outcome": "PASS",
            "total_executable_lines": 5,
            "total_executed_lines": 5,
            "candidate_line_coverage_ratio": 1.0,
            "steps": [],
            "record_key": "mbpp_001::::suite_01",
            "fingerprint": "123",
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty or invalid candidate_id"):
        read_and_validate_phase_1_5_evidence(bad_jsonl)

    # Missing test_suite_id
    bad_jsonl.write_text(
        json.dumps({
            "problem_id": "mbpp_001",
            "candidate_id": "cand_01",
            "test_suite_id": "   ",
            "baseline_outcome": "PASS",
            "total_executable_lines": 5,
            "total_executed_lines": 5,
            "candidate_line_coverage_ratio": 1.0,
            "steps": [],
            "record_key": "mbpp_001::cand_01::",
            "fingerprint": "123",
        }) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="empty or invalid test_suite_id"):
        read_and_validate_phase_1_5_evidence(bad_jsonl)

    # Malformed JSON
    bad_jsonl.write_text("NOT_VALID_JSON\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        read_and_validate_phase_1_5_evidence(bad_jsonl)

    # Missing required keys
    bad_jsonl.write_text(json.dumps({"problem_id": "mbpp_001"}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        read_and_validate_phase_1_5_evidence(bad_jsonl)


def test_serialization_roundtrip():
    """Verify CandidateAnalysisRecord serializes and deserializes losslessly."""
    raw_records = read_and_validate_phase_1_5_evidence(PHASE_1_5_EVIDENCE)
    rec0 = analyze_candidate_record(raw_records[0])

    d = candidate_analysis_to_dict(rec0)
    roundtrip = dict_to_candidate_analysis(d)

    assert roundtrip.candidate_id == rec0.candidate_id
    assert roundtrip.analysis_fingerprint == rec0.analysis_fingerprint
    assert roundtrip.total_steps == rec0.total_steps
    assert roundtrip.total_mutations == rec0.total_mutations
