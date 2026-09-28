from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class DecompositionType(str, Enum):
    FUNCTION = "function"
    BLOCK = "block"


class MutationType(str, Enum):
    COMPARISON_SWAP = "comparison_swap"
    BOOLEAN_FLIP = "boolean_flip"
    OFF_BY_ONE = "off_by_one"


class MutationStatus(str, Enum):
    KILLED = "KILLED"
    SURVIVED = "SURVIVED"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    HARNESS_ERROR = "HARNESS_ERROR"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ExecutionResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class CoverageStatus(str, Enum):
    COVERED = "COVERED"
    PARTIALLY_COVERED = "PARTIALLY_COVERED"
    UNEXECUTED = "UNEXECUTED"


class ExecutionOutcome(str, Enum):
    PASS = "PASS"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    RUNTIME_EXCEPTION = "RUNTIME_EXCEPTION"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"


@dataclass
class MutationInput:
    problem_id: str
    solution_id: str
    decomposition_type: DecompositionType
    step_id: str
    step_text: str
    mutation_type: MutationType
    mutated_code: str


@dataclass
class Evidence:
    problem_id: str
    solution_id: str
    decomposition_type: DecompositionType
    step_id: str
    step_text: str
    mutation_type: MutationType
    original_result: ExecutionResult
    mutated_result: ExecutionResult
    mutation_status: MutationStatus
    outcome_flip: bool
    error_message: Optional[str] = None
    execution_detail: Optional[str] = None


@dataclass
class StepCoverage:
    problem_id: str
    solution_id: str
    step_id: str
    decomposition_type: DecompositionType
    executable_lines: List[int]
    executed_lines: List[int]
    coverage_status: CoverageStatus
    line_coverage_ratio: float


@dataclass
class ExecutionTrace:
    status: ExecutionOutcome
    executed_lines: List[int]
    stdout: str
    stderr: str
    returncode: Optional[int]
    duration_seconds: float
    exception_type: Optional[str] = None
    exception_lineno: Optional[int] = None
