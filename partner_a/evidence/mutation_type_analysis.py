import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "data" / "evidence" / "step_evidence.jsonl"
OUTPUT = ROOT / "data" / "evidence" / "mutation_type_analysis.json"


def main():
    with INPUT.open(encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    by_type = {}

    for mutation_type in sorted({r["mutation_type"] for r in records}):
        rows = [r for r in records if r["mutation_type"] == mutation_type]
        results = Counter(r["mutation_result"] for r in rows)
        detected = results["FAIL"] + results["RUNTIME_ERROR"]

        by_type[mutation_type] = {
            "mutation_count": len(rows),
            "results": dict(sorted(results.items())),
            "detected_count": detected,
            "undetected_count": results["PASS"],
            "detection_rate": detected / len(rows),
        }

    result = {
        "mutation_count": len(records),
        "by_mutation_type": by_type,
    }

    OUTPUT.write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")
    for mutation_type, data in by_type.items():
        print(
            mutation_type,
            "mutations=", data["mutation_count"],
            "detected=", data["detected_count"],
            "undetected=", data["undetected_count"],
            "detection_rate=", f"{data['detection_rate']:.4f}",
        )


if __name__ == "__main__":
    main()
