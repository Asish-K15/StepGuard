"""
Determinism tests for StepGuard Stage 1.4 Phase 1.6 analysis pipeline.

Verifies:
- Repeated runs produce byte-for-byte identical output files.
- Canonical JSON key ordering is strictly deterministic.
- Analysis record fingerprinting is stable and collision-resistant.
"""

import hashlib
import json
from pathlib import Path

from partner_b.evidence.phase_1_6 import (
    analyze_candidate_record,
    compute_file_sha256,
    read_and_validate_phase_1_5_evidence,
    run_phase_1_6_pipeline,
)
from partner_b.evidence.phase_1_6_schema import compute_analysis_fingerprint


ROOT = Path(__file__).resolve().parents[1]
PHASE_1_5_EVIDENCE = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "evidence.jsonl"
PHASE_1_5_SUMMARY = ROOT / "data" / "evidence" / "stage_1_4_phase_1_5" / "summary.json"


def test_repeated_pipeline_runs_produce_byte_identical_analysis_and_summary(tmp_path: Path):
    """Verify that repeated runs over identical inputs produce byte-identical analysis and summary files."""
    run1_dir = tmp_path / "run1"
    run2_dir = tmp_path / "run2"

    a1, s1, m1 = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=run1_dir,
        created_at="2026-09-29T12:00:00Z",
    )

    a2, s2, m2 = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=run2_dir,
        created_at="2026-09-29T12:00:00Z",
    )

    # 1. Byte-for-byte identity of analysis.jsonl
    bytes_a1 = a1.read_bytes()
    bytes_a2 = a2.read_bytes()
    assert bytes_a1 == bytes_a2
    assert hashlib.sha256(bytes_a1).hexdigest() == hashlib.sha256(bytes_a2).hexdigest()

    # 2. Byte-for-byte identity of summary.json
    bytes_s1 = s1.read_bytes()
    bytes_s2 = s2.read_bytes()
    assert bytes_s1 == bytes_s2
    assert hashlib.sha256(bytes_s1).hexdigest() == hashlib.sha256(bytes_s2).hexdigest()

    # 3. Byte-for-byte identity of manifest.json under fixed timestamp
    bytes_m1 = m1.read_bytes()
    bytes_m2 = m2.read_bytes()
    assert bytes_m1 == bytes_m2
    assert hashlib.sha256(bytes_m1).hexdigest() == hashlib.sha256(bytes_m2).hexdigest()


def test_analysis_fingerprint_determinism_and_sensitivity():
    """Verify analysis fingerprint is deterministic across calls and changes when inputs change."""
    fp1 = compute_analysis_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_mbpp_001_sol_001",
        test_suite_id="mbpp_pilot_standard_tests",
        phase_1_5_fingerprint="abc123",
        total_steps=2,
        total_mutations=1,
        detected_mutations=1,
        step_summaries=[{"step_id": "func_01", "decomposition_type": "function", "coverage_status": "COVERED"}],
        mutation_breakdown={"comparison_swap": {"total": 1, "detected": 1, "undetected": 0}},
    )
    fp2 = compute_analysis_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_mbpp_001_sol_001",
        test_suite_id="mbpp_pilot_standard_tests",
        phase_1_5_fingerprint="abc123",
        total_steps=2,
        total_mutations=1,
        detected_mutations=1,
        step_summaries=[{"step_id": "func_01", "decomposition_type": "function", "coverage_status": "COVERED"}],
        mutation_breakdown={"comparison_swap": {"total": 1, "detected": 1, "undetected": 0}},
    )
    assert fp1 == fp2, "Fingerprint must be deterministic"
    assert len(fp1) == 64

    # Sensitivity check: change candidate_id
    fp_diff_cand = compute_analysis_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_mbpp_001_sol_002",
        test_suite_id="mbpp_pilot_standard_tests",
        phase_1_5_fingerprint="abc123",
        total_steps=2,
        total_mutations=1,
        detected_mutations=1,
        step_summaries=[{"step_id": "func_01", "decomposition_type": "function", "coverage_status": "COVERED"}],
        mutation_breakdown={"comparison_swap": {"total": 1, "detected": 1, "undetected": 0}},
    )
    assert fp1 != fp_diff_cand, "Changing candidate_id must change fingerprint"

    # Sensitivity check: change mutation count
    fp_diff_muts = compute_analysis_fingerprint(
        problem_id="mbpp_001",
        candidate_id="cand_mbpp_001_sol_001",
        test_suite_id="mbpp_pilot_standard_tests",
        phase_1_5_fingerprint="abc123",
        total_steps=2,
        total_mutations=2,
        detected_mutations=1,
        step_summaries=[{"step_id": "func_01", "decomposition_type": "function", "coverage_status": "COVERED"}],
        mutation_breakdown={"comparison_swap": {"total": 1, "detected": 1, "undetected": 0}},
    )
    assert fp1 != fp_diff_muts, "Changing mutation count must change fingerprint"


def test_analysis_records_stable_key_ordering(tmp_path: Path):
    """Verify that all JSON keys in analysis.jsonl are lexicographically sorted."""
    a, _, _ = run_phase_1_6_pipeline(
        evidence_path=PHASE_1_5_EVIDENCE,
        phase_1_5_summary_path=PHASE_1_5_SUMMARY,
        output_dir=tmp_path,
    )

    with a.open("r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            keys = list(data.keys())
            assert keys == sorted(keys), f"Keys were not sorted in analysis line: {keys}"
