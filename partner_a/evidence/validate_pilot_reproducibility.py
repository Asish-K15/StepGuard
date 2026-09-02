import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MANIFEST_VALIDATOR = (
    ROOT / "partner_a" / "evidence" / "validate_pilot_manifest.py"
)

PATH_VALIDATOR = (
    ROOT / "partner_a" / "evidence" / "validate_evidence_paths.py"
)


def run_validator(path):
    return subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def main():
    manifest_result = run_validator(MANIFEST_VALIDATOR)
    path_result = run_validator(PATH_VALIDATOR)

    if manifest_result.returncode != 0:
        print("Manifest consistency validation: FAIL")
        print(manifest_result.stdout)
        print(manifest_result.stderr)
        raise SystemExit(1)

    if path_result.returncode != 0:
        print("Evidence path validation: FAIL")
        print(path_result.stdout)
        print(path_result.stderr)
        raise SystemExit(1)

    print("Pilot reproducibility validation: PASS")
    print("Manifest consistency: PASS")
    print("Evidence paths: PASS")


if __name__ == "__main__":
    main()
