import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = ROOT / "data" / "evidence" / "pilot_manifest.json"
BASELINE = ROOT / "data" / "solutions" / "baseline_results.jsonl"
MUTATIONS = ROOT / "data" / "mutations" / "mutation_execution_results.jsonl"


def load_json(path):
    with path.open(encoding="utf-8-sig") as f:
        return json.load(f)


def load_jsonl(path):
    with path.open(encoding="utf-8-sig") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    manifest = load_json(MANIFEST)
    baseline = load_jsonl(BASELINE)
    mutations = load_jsonl(MUTATIONS)

    scope = manifest["scope"]
    results = manifest["mutation_evaluation"]

    baseline_pass_count = sum(
        record.get("baseline_result") == "PASS" for record in baseline
    )

    detected_count = sum(
        record.get("mutation_result") in {"FAIL", "RUNTIME_ERROR"}
        for record in mutations
    )

    undetected_count = sum(
        record.get("mutation_result") == "PASS"
        for record in mutations
    )

    assert len(baseline) == scope["candidate_count"]
    assert baseline_pass_count == scope["baseline_pass_count"]

    assert len(mutations) == results["mutation_count"]
    assert detected_count == results["detected_count"]
    assert undetected_count == results["undetected_count"]
    assert detected_count + undetected_count == len(mutations)

    calculated_rate = detected_count / len(mutations)
    assert calculated_rate == results["detection_rate"]

    print("Pilot manifest validation: PASS")
    print("Baseline candidates:", len(baseline))
    print("Baseline PASS:", baseline_pass_count)
    print("Mutations:", len(mutations))
    print("Detected:", detected_count)
    print("Undetected:", undetected_count)
    print("Detection rate:", f"{calculated_rate:.4f}")


if __name__ == "__main__":
    main()
