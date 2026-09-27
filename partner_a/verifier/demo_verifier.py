"""StepGuard End-to-End Process Reward Model (PRM) Verifier Demo.

Demonstrates the StepGuard verification workflow on real evaluation evidence:
Candidate Solution -> Step Decomposition -> Mutation/Evidence -> StepGuardPRM -> P(correct) -> Label
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from partner_a.verifier.model import StepGuardPRM


def load_eval_record(eval_path: Path, index: int = 0) -> Dict[str, Any]:
    """Load a specific real step record from evaluation JSONL."""
    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {eval_path}")
    with open(eval_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    if not records:
        raise ValueError(f"No records found in {eval_path}")
    if index < 0 or index >= len(records):
        raise IndexError(f"Index {index} out of range [0, {len(records) - 1}]")
    return records[index]


def run_demo(
    checkpoint_dir: str | Path = "data/evaluation/stage_2/checkpoint",
    step_record: Optional[Dict[str, Any]] = None,
    eval_path: str | Path = "data/evaluation/stage_2/verifier_eval.jsonl",
    record_index: int = 0,
) -> Dict[str, Any]:
    """Execute end-to-end verifier inference on a real step record."""
    ckpt_path = Path(checkpoint_dir)
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint directory not found: {ckpt_path}")

    # Load trained model
    prm = StepGuardPRM.load_checkpoint(ckpt_path)

    # Use provided record or load from evaluation set
    if step_record is None:
        step_record = load_eval_record(Path(eval_path), index=record_index)

    # Validate input schema
    required_keys = {"problem_id", "solution_id", "step_id", "code"}
    missing = required_keys - set(step_record.keys())
    if missing:
        raise ValueError(f"Step record missing required keys: {missing}")

    # Predict with trained verifier
    probs = prm.predict_proba([step_record])[0]
    p_correct = float(probs[1])
    pred_label = "correct" if p_correct >= 0.5 else "uncertain"

    return {
        "problem_id": step_record.get("problem_id"),
        "solution_id": step_record.get("solution_id"),
        "step_id": step_record.get("step_id"),
        "step_type": step_record.get("step_type", "unified_func_block"),
        "code": step_record.get("code", ""),
        "gold_label": step_record.get("label"),
        "predicted_label": pred_label,
        "p_correct": round(p_correct, 6),
        "p_uncertain": round(float(probs[0]), 6),
        "mutation_families": step_record.get("applicable_mutation_types", []),
        "num_mutations": step_record.get("num_mutations", 0),
        "num_pass": step_record.get("num_pass", 0),
        "num_fail": step_record.get("num_fail", 0),
        "num_runtime_error": step_record.get("num_runtime_error", 0),
        "exception_types": step_record.get("exception_types", []),
        "checkpoint_path": str(ckpt_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="StepGuard Verifier (PRM) End-to-End Demo.")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="data/evaluation/stage_2/checkpoint",
        help="Path to trained StepGuard PRM checkpoint",
    )
    parser.add_argument(
        "--eval-path",
        type=str,
        default="data/evaluation/stage_2/verifier_eval.jsonl",
        help="Path to evaluation JSONL",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Index of evaluation example to demonstrate (0 to 36)",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default="",
        help="Optional path to a custom step record JSON file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run inference across all evaluation examples and print summary table",
    )

    args = parser.parse_args()

    print("=" * 72)
    print("STEPGUARD PROCESS REWARD MODEL (PRM) - END-TO-END DEMO")
    print("=" * 72)

    custom_record = None
    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            custom_record = json.load(f)

    if args.all:
        eval_path = Path(args.eval_path)
        with open(eval_path, "r", encoding="utf-8") as f:
            all_records = [json.loads(line) for line in f if line.strip()]
        print(f"Loaded {len(all_records)} held-out evaluation steps from: {eval_path}")
        print(f"Checkpoint: {args.checkpoint}\n")
        print(f"{'Idx':<4} | {'Problem':<9} | {'Solution':<18} | {'Step':<9} | {'Gold':<9} | {'Predicted':<9} | {'P(correct)':<10}")
        print("-" * 78)
        for i in range(len(all_records)):
            res = run_demo(checkpoint_dir=args.checkpoint, eval_path=eval_path, record_index=i)
            print(f"{i+1:<4} | {res['problem_id']:<9} | {res['solution_id']:<18} | {res['step_id']:<9} | {str(res['gold_label']):<9} | {res['predicted_label']:<9} | {res['p_correct']:<10.4f}")
        return

    # Single example demonstration
    res = run_demo(
        checkpoint_dir=args.checkpoint,
        step_record=custom_record,
        eval_path=args.eval_path,
        record_index=args.index,
    )

    print("\n--- 1. CANDIDATE STEP & PROBLEM CONTEXT ---")
    print(f"Problem ID:         {res['problem_id']}")
    print(f"Solution ID:        {res['solution_id']}")
    print(f"Step ID:            {res['step_id']}")
    print(f"Step Type:          {res['step_type']}")
    print("Candidate Step Code:")
    for line in res["code"].splitlines():
        print(f"    {line}")

    print("\n--- 2. STEP DECOMPOSITION & MUTATION EVIDENCE ---")
    print(f"Mutation Families:  {', '.join(res['mutation_families']) or 'None'}")
    print(f"Mutations Applied:  {res['num_mutations']}")
    print(f"Execution Outcome:  {res['num_fail']} FAIL, {res['num_pass']} PASS, {res['num_runtime_error']} RUNTIME_ERROR")
    print(f"Observed Exception: {', '.join(res['exception_types']) or 'None'}")

    print("\n--- 3. TRAINED STEPGUARD PRM VERIFIER INFERENCE ---")
    print(f"Loaded Checkpoint:  {res['checkpoint_path']}")
    print(f"Verification Score: P(correct) = {res['p_correct']:.6f}  (P(uncertain) = {res['p_uncertain']:.6f})")
    print(f"Predicted Label:    {res['predicted_label'].upper()}")
    if res["gold_label"]:
        print(f"Held-Out Gold:      {res['gold_label'].upper()}")
        is_match = res["predicted_label"] == res["gold_label"]
        print(f"Verification Match: {'PASSED (Exact Match)' if is_match else 'FAILED'}")

    print("\n" + "=" * 72)


if __name__ == "__main__":
    main()
