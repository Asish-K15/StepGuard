import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "evidence" / "pilot_manifest.json"


def load_manifest():
    with MANIFEST.open(encoding="utf-8-sig") as f:
        return json.load(f)


def main():
    manifest = load_manifest()
    evidence = manifest["evidence"]

    missing = []

    for name, relative_path in evidence.items():
        path = ROOT / relative_path

        if not path.exists():
            missing.append((name, relative_path))

    if missing:
        print("Evidence path validation: FAIL")
        for name, relative_path in missing:
            print(f"Missing: {name} -> {relative_path}")
        raise SystemExit(1)

    print("Evidence path validation: PASS")
    print("Evidence artifacts checked:", len(evidence))

    for name, relative_path in evidence.items():
        print(f"Present: {name} -> {relative_path}")


if __name__ == "__main__":
    main()
