import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "evidence" / "pilot_manifest.json"


def load_manifest():
    with MANIFEST.open(encoding="utf-8-sig") as f:
        return json.load(f)


def test_manifest_exists():
    assert MANIFEST.exists()


def test_manifest_scope():
    manifest = load_manifest()
    scope = manifest["scope"]

    assert manifest["project"] == "StepGuard"
    assert manifest["experiment"] == "pilot"
    assert scope["problem_count"] == 5
    assert scope["candidate_count"] == 25
    assert scope["baseline_pass_count"] == 25
    assert scope["baseline_pass_rate"] == 1.0


def test_manifest_mutation_evaluation():
    manifest = load_manifest()
    results = manifest["mutation_evaluation"]

    assert results["mutation_count"] == 99
    assert results["detected_count"] == 86
    assert results["undetected_count"] == 13
    assert results["detection_rate"] == 86 / 99


def test_manifest_mutation_types():
    manifest = load_manifest()

    assert set(manifest["mutation_types"]) == {
        "boolean_flip",
        "comparison_swap",
        "off_by_one",
    }


def test_manifest_evidence_paths():
    manifest = load_manifest()
    evidence = manifest["evidence"]

    expected = {
        "mutation_execution_results": "data/mutations/mutation_execution_results.jsonl",
        "step_evidence": "data/evidence/step_evidence.jsonl",
        "step_analysis": "data/evidence/step_analysis.jsonl",
        "pilot_findings": "data/evidence/pilot_findings.json",
        "mutation_type_analysis": "data/evidence/mutation_type_analysis.json",
        "undetected_mutation_analysis": "data/evidence/undetected_mutation_analysis.json",
        "survivor_classification": "data/evidence/survivor_classification.json",
        "pilot_summary": "data/evidence/pilot_summary.json",
        "pilot_report": "data/evidence/pilot_report.md",
        "pilot_limitations": "data/evidence/pilot_limitations.md",
    }

    assert evidence == expected


def test_manifest_reproducibility():
    manifest = load_manifest()
    reproducibility = manifest["reproducibility"]

    assert reproducibility["baseline_generation"] == "Qwen qwen2.5-coder:7b"
    assert reproducibility["test_command"] == "python -m pytest -q"


def test_manifest_interpretation():
    manifest = load_manifest()
    interpretation = manifest["interpretation"]

    assert interpretation["status"] == "exploratory_pilot"
    assert (
        interpretation["generalization"]
        == "not_supported_beyond_evaluated_dataset"
    )

