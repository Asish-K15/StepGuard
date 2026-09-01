import json
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_TIMEOUT_SECONDS = 5


def build_test_program(code: str, tests: list[str]) -> str:
    """Build a standalone Python program containing candidate code and tests."""

    test_code = "\n".join(tests)

    return f"""
{code}

# MBPP tests
{test_code}

print("__STEPGUARD_PASS__")
"""


def classify_process(result: subprocess.CompletedProcess) -> str:
    """Classify the result of a candidate subprocess."""

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    if result.returncode == 0 and "__STEPGUARD_PASS__" in stdout:
        return "PASS"

    if "AssertionError" in stderr or "AssertionError" in stdout:
        return "FAIL"

    if "SyntaxError" in stderr or "SyntaxError" in stdout:
        return "SYNTAX_ERROR"

    return "RUNTIME_ERROR"


def run_candidate(
    code: str,
    tests: list[str],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Execute candidate code in an isolated subprocess."""

    program = build_test_program(code, tests)

    try:
        compile(program, "<candidate>", "exec")
    except SyntaxError as exc:
        return {
            "status": "SYNTAX_ERROR",
            "stdout": "",
            "stderr": str(exc),
            "returncode": None,
        }

    with tempfile.TemporaryDirectory(prefix="stepguard_") as temp_dir:
        script_path = Path(temp_dir) / "candidate.py"
        script_path.write_text(program, encoding="utf-8")

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=temp_dir,
            )

        except subprocess.TimeoutExpired as exc:
            return {
                "status": "TIMEOUT",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "returncode": None,
            }

        except OSError as exc:
            return {
                "status": "HARNESS_ERROR",
                "stdout": "",
                "stderr": str(exc),
                "returncode": None,
            }

    return {
        "status": classify_process(result),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def main():
    problems_dir = Path("data/problems")
    solutions_path = Path("data/solutions/candidates.jsonl")

    problems = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in problems_dir.glob("mbpp_*.json")
    }

    solutions = [
        json.loads(line)
        for line in solutions_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    for solution in solutions:
        problem_id = solution["problem_id"]

        if problem_id not in problems:
            print(
                solution["solution_id"],
                "-> HARNESS_ERROR",
                f"(unknown problem: {problem_id})",
            )
            continue

        problem = problems[problem_id]

        result = run_candidate(
            solution["code"],
            problem["test_list"],
        )

        print(
            solution["solution_id"],
            "->",
            result["status"],
        )


if __name__ == "__main__":
    main()