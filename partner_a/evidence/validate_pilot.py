import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

VALIDATORS = [
    (
        "Manifest consistency",
        ROOT / "partner_a" / "evidence" / "validate_pilot_manifest.py",
    ),
    (
        "Evidence paths",
        ROOT / "partner_a" / "evidence" / "validate_evidence_paths.py",
    ),
    (
        "Reproducibility",
        ROOT / "partner_a" / "evidence" / "validate_pilot_reproducibility.py",
    ),
]


def run_validator(path):
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main():
    failures = []

    for name, path in VALIDATORS:
        result = run_validator(path)

        if result.returncode == 0:
            print(f"{name}: PASS")
        else:
            print(f"{name}: FAIL")
            failures.append(name)

    if failures:
        print("StepGuard pilot validation: FAIL")
        for failure in failures:
            print(f"Failed check: {failure}")
        raise SystemExit(1)

    print("StepGuard pilot validation: PASS")


if __name__ == "__main__":
    main()
