from dataclasses import dataclass
from enum import Enum
from typing import Optional


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