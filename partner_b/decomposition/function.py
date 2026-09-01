"""
Function-level AST decomposition for StepGuard Stage 0A.

Each top-level function definition is represented as one logical step.
The decomposer preserves problem_id and solution_id so that every step
can be traced back to its source solution.
"""

import ast
from dataclasses import dataclass
from typing import List

from shared.schema import DecompositionType


@dataclass
class FunctionStep:
    problem_id: str
    solution_id: str
    decomposition_type: DecompositionType
    step_id: str
    step_text: str
    start_line: int
    end_line: int


def decompose_functions(
    problem_id: str,
    solution_id: str,
    source_code: str,
) -> List[FunctionStep]:
    """
    Decompose Python source code into function-level steps.

    Each top-level FunctionDef is treated as one step.

    Raises:
        SyntaxError: If source_code is not valid Python.
    """
    tree = ast.parse(source_code)

    steps: List[FunctionStep] = []

    function_index = 1

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            step_id = f"func_{function_index:02d}"

            step_text = ast.get_source_segment(source_code, node)

            if step_text is None:
                lines = source_code.splitlines()
                step_text = "\n".join(
                    lines[node.lineno - 1 : node.end_lineno]
                )

            steps.append(
                FunctionStep(
                    problem_id=problem_id,
                    solution_id=solution_id,
                    decomposition_type=DecompositionType.FUNCTION,
                    step_id=step_id,
                    step_text=step_text,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                )
            )

            function_index += 1

    return steps