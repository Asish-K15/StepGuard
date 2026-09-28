"""
Subprocess-isolated execution tracer for StepGuard Stage 1.4 (Phase 1).

Executes untrusted candidate code and test suites inside an isolated Python
subprocess with child-process `sys.settrace` containment, process-level timeout
enforcement, and unified execution outcome classification.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path
from typing import List, Optional

from shared.schema import ExecutionOutcome, ExecutionTrace


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIMEOUT_SECONDS = 5.0
SENTINEL_TOKEN = "__STEPGUARD_PASS__"


def _build_traced_program(code: str, tests: List[str]) -> str:
    """
    Build a standalone executable script from candidate code and assertions.

    Candidate code lines are placed strictly at the beginning so that line numbers
    1..N correspond 1-to-1 with the original candidate source text.
    """
    test_block = "\n".join(tests)
    return f"{code}\n\n# StepGuard Benchmark Tests\n{test_block}\n\nprint('{SENTINEL_TOKEN}')\n"


def _run_traced_child(code: str, tests: List[str]) -> dict:
    """
    Execute candidate code and tests within the child process using sys.settrace.

    Enforces that sys.settrace is contained within a try...finally block and deactivated
    cleanly before serialization.
    """
    candidate_lines = len(code.splitlines())
    program = _build_traced_program(code, tests)

    try:
        compiled = compile(program, "<candidate>", "exec")
    except SyntaxError as exc:
        return {
            "status": ExecutionOutcome.SYNTAX_ERROR.value,
            "executed_lines": [],
            "exception_type": "SyntaxError",
            "exception_lineno": exc.lineno,
        }

    executed_lines = set()

    def line_tracer(frame, event, arg):
        if event == "line":
            if frame.f_code.co_filename == "<candidate>":
                lineno = frame.f_lineno
                if 1 <= lineno <= candidate_lines:
                    executed_lines.add(lineno)
        return line_tracer

    execution_globals = {
        "__name__": "__main__",
        "__file__": "<candidate>",
    }

    status = ExecutionOutcome.PASS.value
    exception_type = None
    exception_lineno = None

    try:
        sys.settrace(line_tracer)
        exec(compiled, execution_globals)
    except AssertionError as exc:
        status = ExecutionOutcome.ASSERTION_FAILURE.value
        exception_type = "AssertionError"
        tb = traceback.extract_tb(sys.exc_info()[2])
        cand_frames = [f for f in tb if f.filename == "<candidate>"]
        exception_lineno = cand_frames[-1].lineno if cand_frames else getattr(exc, "lineno", None)
    except SyntaxError as exc:
        status = ExecutionOutcome.SYNTAX_ERROR.value
        exception_type = "SyntaxError"
        exception_lineno = exc.lineno
    except BaseException as exc:
        status = ExecutionOutcome.RUNTIME_EXCEPTION.value
        exception_type = type(exc).__name__
        tb = traceback.extract_tb(sys.exc_info()[2])
        cand_frames = [f for f in tb if f.filename == "<candidate>"]
        exception_lineno = cand_frames[-1].lineno if cand_frames else getattr(exc, "lineno", None)
    finally:
        sys.settrace(None)

    return {
        "status": status,
        "executed_lines": sorted(executed_lines),
        "exception_type": exception_type,
        "exception_lineno": exception_lineno,
    }


def _child_entrypoint() -> None:
    """Entry point for the child execution process."""
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python -m partner_b.execution.tracer <input_json> <output_json>\n")
        sys.exit(2)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        code = payload["code"]
        tests = payload.get("tests", [])

        result_data = _run_traced_child(code, tests)
        output_path.write_text(json.dumps(result_data), encoding="utf-8")

        if result_data["status"] != ExecutionOutcome.PASS.value:
            sys.exit(1)
        sys.exit(0)
    except Exception as exc:
        sys.stderr.write(f"Tracer child process error: {exc}\n")
        sys.exit(3)


def trace_candidate_execution(
    code: str,
    tests: List[str],
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    cwd: Optional[Path | str] = None,
) -> ExecutionTrace:
    """
    Execute candidate code in an isolated child process and capture dynamic trace telemetry.

    Parameters:
        code: Candidate solution source code.
        tests: List of assertion statements.
        timeout_seconds: Maximum allowed execution wall-clock time in seconds.
        cwd: Working directory for subprocess.

    Returns:
        ExecutionTrace with classified outcome, executed candidate lines, duration,
        stdout, stderr, and exception metadata.
    """
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{ROOT}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(ROOT)
    )

    with tempfile.TemporaryDirectory(prefix="stepguard_trace_") as temp_dir:
        temp_dir_path = Path(temp_dir)
        input_file = temp_dir_path / "payload.json"
        output_file = temp_dir_path / "trace_result.json"

        input_file.write_text(
            json.dumps({"code": code, "tests": tests}),
            encoding="utf-8",
        )

        cmd = [
            sys.executable,
            "-m",
            "partner_b.execution.tracer",
            str(input_file),
            str(output_file),
        ]

        work_dir = Path(cwd) if cwd is not None else temp_dir_path

        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=work_dir,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - start_time
            return ExecutionTrace(
                status=ExecutionOutcome.TIMEOUT,
                executed_lines=[],
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                returncode=None,
                duration_seconds=duration,
                exception_type="TimeoutExpired",
                exception_lineno=None,
            )
        except OSError as exc:
            duration = time.perf_counter() - start_time
            return ExecutionTrace(
                status=ExecutionOutcome.INFRASTRUCTURE_FAILURE,
                executed_lines=[],
                stdout="",
                stderr=str(exc),
                returncode=None,
                duration_seconds=duration,
                exception_type="OSError",
                exception_lineno=None,
            )

        duration = time.perf_counter() - start_time

        # Validate that the child process wrote valid JSON output
        if not output_file.exists():
            return ExecutionTrace(
                status=ExecutionOutcome.INFRASTRUCTURE_FAILURE,
                executed_lines=[],
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                returncode=result.returncode,
                duration_seconds=duration,
                exception_type="InfrastructureFailure",
                exception_lineno=None,
            )

        try:
            data = json.loads(output_file.read_text(encoding="utf-8"))
            raw_status = data.get("status")
            status = ExecutionOutcome(raw_status)
            executed_lines = data.get("executed_lines", [])
            exception_type = data.get("exception_type")
            exception_lineno = data.get("exception_lineno")

            # Check for silent failure where exit code is 0 but sentinel is absent
            if status == ExecutionOutcome.PASS and SENTINEL_TOKEN not in (result.stdout or ""):
                status = ExecutionOutcome.INFRASTRUCTURE_FAILURE

            return ExecutionTrace(
                status=status,
                executed_lines=executed_lines,
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                returncode=result.returncode,
                duration_seconds=duration,
                exception_type=exception_type,
                exception_lineno=exception_lineno,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            return ExecutionTrace(
                status=ExecutionOutcome.INFRASTRUCTURE_FAILURE,
                executed_lines=[],
                stdout=result.stdout or "",
                stderr=result.stderr or "",
                returncode=result.returncode,
                duration_seconds=duration,
                exception_type=type(exc).__name__,
                exception_lineno=None,
            )


if __name__ == "__main__":
    _child_entrypoint()
