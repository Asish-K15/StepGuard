import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VALIDATOR = ROOT / "partner_a" / "evidence" / "validate_pilot.py"


def main():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
