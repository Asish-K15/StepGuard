"""
Legacy compatibility regression tests for StepGuard Stage 1.4 (Phase 1).

Verifies that all Phase 1 capabilities are strictly additive, that legacy execution
paths remain unaltered, and that re-generating evidence outputs into an isolated
temporary directory yields exact byte-for-byte and SHA-256 hash identity against
the frozen Stage 0A–1.3 baseline artifacts:
- data/evidence/step_evidence.jsonl
- data/evidence/step_analysis.jsonl
- data/evidence/pilot_findings.json
"""

import hashlib
import json
import tempfile
from pathlib import Path

import partner_a.evidence.pilot_findings as pf_module
from partner_a.evidence.analyze_evidence import analyze
from partner_a.execution.harness import run_candidate
from partner_b.evidence.build_evidence import (
    build_evidence_record,
    read_jsonl,
    validate_execution_record,
    write_jsonl,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINE_STEP_EVIDENCE = ROOT / "data" / "evidence" / "step_evidence.jsonl"
BASELINE_STEP_ANALYSIS = ROOT / "data" / "evidence" / "step_analysis.jsonl"
BASELINE_PILOT_FINDINGS = ROOT / "data" / "evidence" / "pilot_findings.json"
INPUT_MUTATION_RESULTS = (
    ROOT / "data" / "mutations" / "mutation_execution_results.jsonl"
)


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's raw bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_legacy_evidence_generation_matches_baseline_hashes():
    """
    Criterion 6: Verify end-to-end legacy evidence pipeline generation in an isolated
    tempdir produces exact SHA-256 and deterministic record matches with baseline artifacts.
    """
    with tempfile.TemporaryDirectory(prefix="stepguard_legacy_val_") as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_step_evidence = temp_dir_path / "step_evidence.jsonl"
        temp_step_analysis = temp_dir_path / "step_analysis.jsonl"
        temp_pilot_findings = temp_dir_path / "pilot_findings.json"

        # 1. Generate step_evidence.jsonl from raw mutation execution records
        raw_execution_records = read_jsonl(INPUT_MUTATION_RESULTS)
        evidence_records = []
        for record in raw_execution_records:
            validate_execution_record(record)
            evidence_records.append(build_evidence_record(record))
        write_jsonl(temp_step_evidence, evidence_records)

        # Assert SHA-256 and line count match
        assert _sha256(temp_step_evidence) == _sha256(BASELINE_STEP_EVIDENCE), (
            "Generated step_evidence.jsonl SHA-256 does not match baseline!"
        )
        assert len(evidence_records) == 99

        # 2. Generate step_analysis.jsonl from step_evidence.jsonl
        analyzed_records = analyze(read_jsonl(temp_step_evidence))
        with temp_step_analysis.open("w", encoding="utf-8") as f:
            for rec in analyzed_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        # Assert SHA-256 and step count match
        assert _sha256(temp_step_analysis) == _sha256(BASELINE_STEP_ANALYSIS), (
            "Generated step_analysis.jsonl SHA-256 does not match baseline!"
        )
        assert len(analyzed_records) == 77

        # 3. Generate pilot_findings.json using redirected OUTPUT
        old_output = pf_module.OUTPUT
        try:
            pf_module.OUTPUT = temp_pilot_findings
            pf_module.main()
        finally:
            pf_module.OUTPUT = old_output

        # Assert SHA-256 and JSON object equality match
        assert _sha256(temp_pilot_findings) == _sha256(BASELINE_PILOT_FINDINGS), (
            "Generated pilot_findings.json SHA-256 does not match baseline!"
        )
        gen_json = json.loads(temp_pilot_findings.read_text(encoding="utf-8"))
        base_json = json.loads(BASELINE_PILOT_FINDINGS.read_text(encoding="utf-8"))
        assert gen_json == base_json


def test_legacy_harness_unaffected_by_phase_1():
    """Verify legacy run_candidate returns standard legacy dictionary format."""
    code = "def f(x):\n    return x + 1\n"
    tests = ["assert f(1) == 2"]

    result = run_candidate(code, tests)

    assert isinstance(result, dict)
    assert set(result.keys()) == {"status", "stdout", "stderr", "returncode"}
    assert result["status"] == "PASS"
    assert result["returncode"] == 0
