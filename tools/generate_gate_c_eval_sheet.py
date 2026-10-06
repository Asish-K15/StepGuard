#!/usr/bin/env python3
"""
StepGuard Gate C Blind Evaluation Sheet Generator.

Generates data/validation/gate_c_blind_evaluation_sheet.md from the frozen N=37
held-out evaluation dataset (data/evaluation/stage_1/verifier_eval.jsonl) and
corresponding problem specification files.

STRICT BLINDING PROTOCOL:
- Withholds all mutation-derived labels, heuristic rationales, PRM predictions,
  confidence scores, feature extractors, and mutation statistics.
- Explicitly flags unannotated protocol material.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from partner_b.decomposition.block import decompose_blocks
from partner_b.decomposition.function import decompose_functions


# Forbidden fields that must never be emitted into the blinded evaluation sheet
FORBIDDEN_LEAKAGE_FIELDS = {
    "label",
    "label_rationale",
    "applicable_mutation_types",
    "num_mutations",
    "num_pass",
    "num_fail",
    "num_runtime_error",
    "exception_types",
    "flips_by_type",
    "outcome_flip",
    "prm_prediction",
    "prm_confidence",
    "prm_probability",
    "features",
    "feature_vector",
}


def load_problem_spec(repo_root: Path, problem_id: str) -> Dict[str, Any]:
    """Load problem specification (prompt, tests, task_id) from problem JSON."""
    if problem_id.startswith("eval_"):
        prob_file = repo_root / "data" / "evaluation" / "problems" / f"{problem_id}.json"
    elif problem_id.startswith("mbpp_"):
        prob_file = repo_root / "data" / "problems" / f"{problem_id}.json"
    else:
        raise ValueError(f"Unknown problem ID format: {problem_id}")

    if not prob_file.exists():
        raise FileNotFoundError(f"Problem file not found: {prob_file}")

    data = json.loads(prob_file.read_text(encoding="utf-8"))
    return {
        "problem_id": problem_id,
        "task_id": data.get("task_id"),
        "prompt": data.get("prompt", "").strip(),
        "test_list": data.get("test_list", []),
    }


def format_code_with_target_step(
    code: str, start_line: int, end_line: int
) -> str:
    """Format candidate code with 1-based line numbers and '>>' prefix on target step lines."""
    lines = code.splitlines()
    formatted = []
    max_line_num_len = len(str(len(lines)))

    for i, line in enumerate(lines, 1):
        is_target = start_line <= i <= end_line
        marker = ">>" if is_target else "  "
        num_str = str(i).rjust(max_line_num_len)
        formatted.append(f"{marker} {num_str} | {line}")

    return "\n".join(formatted)


def generate_gate_c_eval_sheet(
    repo_root: Optional[Path] = None,
    eval_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> str:
    """Generate the deterministic Gate C blind evaluation sheet."""
    root = repo_root or REPO_ROOT
    eval_file = eval_path or root / "data" / "evaluation" / "stage_1" / "verifier_eval.jsonl"
    out_file = output_path or root / "data" / "validation" / "gate_c_blind_evaluation_sheet.md"

    if not eval_file.exists():
        raise FileNotFoundError(f"Held-out evaluation file not found: {eval_file}")

    eval_records = [
        json.loads(line)
        for line in eval_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    if len(eval_records) != 37:
        raise ValueError(
            f"Expected exactly 37 held-out records in {eval_file}, found {len(eval_records)}"
        )

    sections: List[str] = [
        "# StepGuard Gate C Blind Evaluation Study: N=37 Held-Out Assessment Sheet",
        "",
        "> [!IMPORTANT]",
        "> **UNANNOTATED PROTOCOL MATERIAL — NOT SEMANTIC GROUND TRUTH**",
        "> This evaluation sheet is strictly blinded and unannotated.",
        "> All mutation-derived labels, heuristic rationales, PRM predictions, detection outcomes,",
        "> confidence scores, and feature extractors have been withheld to guarantee evaluator independence.",
        "> Do not consult external mutation result logs, verifier labels, or training splits during annotation.",
        "",
        "## Evaluator Instructions",
        "For each of the 37 held-out evaluation samples below:",
        "1. Read the **Problem Specification** and the provided **Test Suite Assertions**.",
        "2. Review the **Complete Candidate Solution** and identify the highlighted **Target Step** (indicated with `>>`).",
        "3. Evaluate the step's correctness and semantic soundness in the context of the program:",
        "   - **`CORRECT`**: The step represents a mathematically and semantically sound, valid intermediate or terminal operation towards fulfilling the specification.",
        "   - **`UNCERTAIN`**: The step contains flawed logic, ineffective or redundant conditions, unverified edge case handling, or semantic ambiguity arising from an under-constrained test suite.",
        "4. Record your **Human / Evaluator Label** (`CORRECT` or `UNCERTAIN`) and your **Rationale / Evidence**.",
        "",
        "---",
        "",
    ]

    for idx, er in enumerate(eval_records, 1):
        sample_id = f"SG-GATE-C-{idx:03d}"
        problem_id = er["problem_id"]
        solution_id = er.get("solution_id") or er.get("candidate_id") or "unknown_solution"
        step_id = er["step_id"]
        step_type = er.get("step_type", "unknown_type")
        code = er["code"]

        # Load problem specification
        spec = load_problem_spec(root, problem_id)
        task_id = spec["task_id"]
        prompt = spec["prompt"]
        tests = spec["test_list"]

        # Determine target step boundary lines
        start_line = er.get("line", 1)
        end_line = start_line
        if "block" in step_id:
            blocks = decompose_blocks(problem_id, solution_id, code)
            target_block = next((b for b in blocks if b.step_id == step_id), None)
            if target_block:
                start_line = target_block.start_line
                end_line = target_block.end_line
        elif "func" in step_id:
            funcs = decompose_functions(problem_id, solution_id, code)
            target_func = next((f for f in funcs if f.step_id == step_id), None)
            if target_func:
                start_line = target_func.start_line
                end_line = target_func.end_line

        line_span = f"Line {start_line}" if start_line == end_line else f"Lines {start_line}-{end_line}"
        formatted_code = format_code_with_target_step(code, start_line, end_line)

        # Build test list markdown block
        test_block_lines = [f"assert {t}" if not t.startswith("assert") else t for t in tests]
        test_block_str = "\n".join(test_block_lines)

        sample_section = [
            f"## Sample ID: {sample_id}",
            "",
            "### 1. Problem Context",
            f"- **Problem Task ID**: `{problem_id}` (MBPP Task {task_id})" if task_id else f"- **Problem Task ID**: `{problem_id}`",
            "- **Prompt / Specification**:",
            f"  > {prompt}",
            "- **Available Test Assertions**:",
            "  ```python",
            f"  {test_block_str}",
            "  ```",
            "",
            "### 2. Relevant Candidate Solution and Target Step",
            f"- **Target Step Identifier**: `{step_id}` ({step_type.replace('_', ' ').capitalize()}, {line_span})",
            "- **Full Candidate Code** (target step lines indicated with `>>`):",
            "```python",
            formatted_code,
            "```",
            "",
            "### 3. Independent Semantic Evaluation (To be completed by Evaluator)",
            "- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`",
            "- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`",
            "",
            "---",
            "",
        ]
        sections.extend(sample_section)

    content = "\n".join(sections)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate StepGuard Gate C Blind Evaluation Sheet (N=37)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root directory (defaults to parent of tools/).",
    )
    parser.add_argument(
        "--eval-path",
        type=Path,
        default=None,
        help="Path to frozen verifier_eval.jsonl.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Path to write the blind evaluation sheet markdown.",
    )
    args = parser.parse_args()

    generate_gate_c_eval_sheet(
        repo_root=args.repo_root,
        eval_path=args.eval_path,
        output_path=args.output_path,
    )
    print("Successfully generated data/validation/gate_c_blind_evaluation_sheet.md (37 samples).")


if __name__ == "__main__":
    main()
