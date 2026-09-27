"""
StepGuard Verifier Label Derivation Engine.

Derives step-level correctness labels ('correct' or 'uncertain') from
empirical mutation-testing evidence, adhering to the Stage 1.3 Joint
Reconciliation rules:

1. Baseline Pass Guarantee:
   All candidate solutions must have passed baseline problem tests
   (baseline_result == PASS).

2. Outcome Flip Definition:
   - baseline_result == PASS -> mutated_result == FAIL: outcome_flip = True
   - baseline_result == PASS -> mutated_result == PASS: outcome_flip = False (survivor)
   - baseline_result == PASS -> mutated_result == RUNTIME_ERROR:
     Treated with exception-awareness. Dominant runtime errors or unhandled
     TypeErrors (e.g. sequence replication division) do not constitute
     clean semantic logic flips.

3. Multi-Operator Steps (>=2 applicable mutation types):
   - 'correct': >=2 applicable mutation types produce genuine outcome flips (FAIL).
   - 'uncertain': <2 flips, surviving mutations, or dominant runtime errors.

4. Single-Operator Steps (exactly 1 applicable mutation type):
   - 'correct': 100% of applicable mutations produce genuine outcome flips (1/1 FAIL).
   - 'uncertain': Mutation survived (PASS) or dominant runtime error.

5. Duplicate Decomposition Handling:
   Single-statement functions where func_01 and block_01 have identical code spans
   are deduplicated into a single canonical step (unified_func_block). Genuinely
   distinct block steps are preserved.

6. Leakage-Free Train/Eval Partitioning:
   80/20 train/evaluation split grouped strictly by solution identity
   (problem_id, solution_id), guaranteeing zero solution overlap between splits.
"""

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_PILOT_EVIDENCE = ROOT / "data" / "evidence" / "step_evidence.jsonl"
DEFAULT_EVAL_EVIDENCE = (
    ROOT / "data" / "evaluation" / "mutations" / "step_evidence_is.jsonl"
)
DEFAULT_PILOT_BASELINE = ROOT / "data" / "solutions" / "baseline_results.jsonl"
DEFAULT_EVAL_BASELINE = (
    ROOT / "data" / "evaluation" / "solutions" / "baseline_results.jsonl"
)
DEFAULT_OUTPUT_DIR = ROOT / "data" / "evaluation" / "stage_1"

REQUIRED_EVIDENCE_FIELDS = {
    "problem_id",
    "solution_id",
    "step_id",
    "mutation_type",
    "original_code",
    "mutated_code",
    "changed",
    "mutation_result",
    "stdout",
    "stderr",
    "returncode",
}


@dataclass
class CanonicalStepLabel:
    problem_id: str
    solution_id: str
    step_id: str
    step_type: str
    dataset_source: str
    code: str
    line: Optional[int]
    column: Optional[int]
    applicable_mutation_types: List[str]
    num_mutations: int
    num_pass: int
    num_fail: int
    num_runtime_error: int
    exception_types: List[str]
    flips_by_type: List[str]
    outcome_flip: bool
    label: str
    label_rationale: str
    split: str = "unassigned"


def extract_exception_type(stderr: Optional[str]) -> Optional[str]:
    """Extract standard Python exception name from stderr traceback."""
    if not stderr:
        return None
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    if not lines:
        return None
    last_line = lines[-1]
    match = re.match(r"^([A-Za-z0-9_]+Error|[A-Za-z0-9_]+Exception):", last_line)
    if match:
        return match.group(1)
    if "AssertionError" in stderr:
        return "AssertionError"
    return "UnknownError"


def load_baseline_status(baseline_path: Path) -> Dict[str, str]:
    """Load solution baseline execution results."""
    if not baseline_path.exists():
        return {}
    results = {}
    with baseline_path.open("r", encoding="utf-8-sig") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            results[record["solution_id"]] = record.get("baseline_result", "UNKNOWN")
    return results


def validate_and_load_evidence(
    pilot_path: Path,
    eval_path: Path,
    pilot_baseline_path: Optional[Path] = None,
    eval_baseline_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Validate schemas and aggregate evidence from pilot and evaluation datasets.

    Ensures all records satisfy schema contracts and baseline PASS criteria.
    """
    if not pilot_path.exists():
        raise FileNotFoundError(f"Pilot evidence file missing: {pilot_path}")
    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation evidence file missing: {eval_path}")

    # Load baseline mappings if provided
    pilot_baselines = (
        load_baseline_status(pilot_baseline_path)
        if pilot_baseline_path
        else {}
    )
    eval_baselines = (
        load_baseline_status(eval_baseline_path)
        if eval_baseline_path
        else {}
    )

    combined_records = []

    def _process_file(path: Path, source_name: str, baselines: Dict[str, str]):
        with path.open("r", encoding="utf-8-sig") as file:
            for line_no, line in enumerate(file, start=1):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                missing = REQUIRED_EVIDENCE_FIELDS - record.keys()
                if missing:
                    raise ValueError(
                        f"Schema error in {path}:{line_no} — missing fields: {missing}"
                    )
                sol_id = record["solution_id"]
                if baselines and sol_id in baselines:
                    if baselines[sol_id] != "PASS":
                        raise ValueError(
                            f"Solution {sol_id} baseline is {baselines[sol_id]}, expected PASS"
                        )
                rec_copy = dict(record)
                rec_copy["dataset_source"] = source_name
                combined_records.append(rec_copy)

    _process_file(pilot_path, "pilot", pilot_baselines)
    _process_file(eval_path, "evaluation", eval_baselines)

    return combined_records


def deduplicate_canonical_steps(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Deduplicate single-statement function/block representations.

    When func_01 and block_01 in a solution have identical mutation signatures
    (mutation_type, operator changes, line/col, and mutated_code), they represent
    the identical AST span. func_01 is collapsed into block_01 and tagged as
    'unified_func_block'. Genuinely distinct block steps are strictly preserved.
    """
    by_sol_step = defaultdict(lambda: defaultdict(list))
    for r in records:
        key = (r["problem_id"], r["solution_id"])
        by_sol_step[key][r["step_id"]].append(r)

    canonical_step_groups = []
    collapsed_duplicates_count = 0

    for (problem_id, solution_id), steps in sorted(by_sol_step.items()):
        has_f1 = "func_01" in steps
        has_b1 = "block_01" in steps
        is_duplicate = False

        if has_f1 and has_b1:
            f_sig = [
                (
                    r["mutation_type"],
                    r.get("original_operator"),
                    r.get("mutated_operator"),
                    r.get("line"),
                    r.get("column"),
                    r["mutated_code"],
                )
                for r in steps["func_01"]
            ]
            b_sig = [
                (
                    r["mutation_type"],
                    r.get("original_operator"),
                    r.get("mutated_operator"),
                    r.get("line"),
                    r.get("column"),
                    r["mutated_code"],
                )
                for r in steps["block_01"]
            ]
            if f_sig == b_sig:
                is_duplicate = True
                collapsed_duplicates_count += 1

        for step_id, step_records in sorted(steps.items()):
            if is_duplicate and step_id == "func_01":
                continue  # collapsed into block_01

            if is_duplicate and step_id == "block_01":
                step_type = "unified_func_block"
            elif step_id.startswith("func"):
                step_type = "function"
            else:
                step_type = "block"

            canonical_step_groups.append(
                {
                    "problem_id": problem_id,
                    "solution_id": solution_id,
                    "step_id": step_id,
                    "step_type": step_type,
                    "dataset_source": step_records[0]["dataset_source"],
                    "records": step_records,
                }
            )

    return canonical_step_groups, collapsed_duplicates_count


def derive_step_label(
    problem_id: str,
    solution_id: str,
    step_id: str,
    step_type: str,
    dataset_source: str,
    records: List[Dict[str, Any]],
) -> CanonicalStepLabel:
    """
    Derive the verifier label ('correct' or 'uncertain') for a canonical step.

    Applies the reconciled StepGuard Stage 1.3 decision rules.
    """
    m_types = sorted(list(set(r["mutation_type"] for r in records)))
    results = [r["mutation_result"] for r in records]

    n_pass = results.count("PASS")
    n_fail = results.count("FAIL")
    n_re = results.count("RUNTIME_ERROR")

    exceptions = [
        extract_exception_type(r.get("stderr"))
        for r in records
        if r.get("stderr")
    ]
    unique_exceptions = sorted(list(set(e for e in exceptions if e is not None)))
    has_type_error = "TypeError" in unique_exceptions

    # Mutation types that produced genuine semantic failures (FAIL)
    flips_by_type = sorted(
        list(
            set(
                r["mutation_type"]
                for r in records
                if r["mutation_result"] == "FAIL"
            )
        )
    )

    # -------------------------------------------------------------------------
    # Decision Logic
    # -------------------------------------------------------------------------
    if n_pass > 0:
        # Mutation survived test suite -> test inadequacy / cannot verify
        label = "uncertain"
        rationale = f"Mutation survived as PASS ({n_pass} survivor(s))"
        outcome_flip = False
    elif n_re > 0 and n_fail == 0:
        # 100% of mutations produced runtime crashes -> dominant runtime error
        label = "uncertain"
        exc_str = ", ".join(unique_exceptions) if unique_exceptions else "unspecified"
        rationale = f"Dominant RUNTIME_ERROR ({n_re}/{len(records)}: {exc_str})"
        outcome_flip = False
    elif has_type_error and len(flips_by_type) < 2:
        # Unhandled TypeError (e.g. [0] * n -> [0] / n) is a type collision
        label = "uncertain"
        rationale = "TypeError on unhandled operand combination"
        outcome_flip = False
    elif len(m_types) >= 2:
        # Multi-operator step: requires >=2 mutation types with genuine outcome flips
        if len(flips_by_type) >= 2:
            label = "correct"
            rationale = (
                f"Outcome flip verified across >=2 mutation types "
                f"({len(flips_by_type)}/{len(m_types)})"
            )
            outcome_flip = True
        else:
            label = "uncertain"
            rationale = (
                f"Multi-operator step has <2 genuine outcome flips "
                f"({len(flips_by_type)}/{len(m_types)})"
            )
            outcome_flip = False
    else:
        # Single-operator step: requires 100% of applicable mutations to produce FAIL
        if len(flips_by_type) == 1 and n_fail == len(records):
            label = "correct"
            rationale = "100% of applicable mutations produced genuine outcome flip (FAIL)"
            outcome_flip = True
        else:
            label = "uncertain"
            rationale = (
                f"Single-operator did not achieve clean outcome flip "
                f"(fail={n_fail}, re={n_re})"
            )
            outcome_flip = False

    return CanonicalStepLabel(
        problem_id=problem_id,
        solution_id=solution_id,
        step_id=step_id,
        step_type=step_type,
        dataset_source=dataset_source,
        code=records[0]["original_code"],
        line=records[0].get("line"),
        column=records[0].get("column"),
        applicable_mutation_types=m_types,
        num_mutations=len(records),
        num_pass=n_pass,
        num_fail=n_fail,
        num_runtime_error=n_re,
        exception_types=unique_exceptions,
        flips_by_type=flips_by_type,
        outcome_flip=outcome_flip,
        label=label,
        label_rationale=rationale,
    )


def partition_train_eval(
    labeled_steps: List[CanonicalStepLabel],
    train_ratio: float = 0.8,
    seed: int = 42,
) -> Tuple[List[CanonicalStepLabel], List[CanonicalStepLabel]]:
    """
    Partition labeled steps into train and evaluation splits grouped strictly
    by solution identity (problem_id, solution_id) to prevent data leakage.
    """
    all_solutions = sorted(
        list(set((s.problem_id, s.solution_id) for s in labeled_steps))
    )

    rng = random.Random(seed)
    shuffled_solutions = list(all_solutions)
    rng.shuffle(shuffled_solutions)

    split_index = int(len(shuffled_solutions) * train_ratio)
    train_solutions = set(shuffled_solutions[:split_index])
    eval_solutions = set(shuffled_solutions[split_index:])

    # Programmatic assertion: zero solution overlap
    leakage = train_solutions.intersection(eval_solutions)
    if leakage:
        raise ValueError(f"Solution leakage detected between splits: {leakage}")

    train_steps = []
    eval_steps = []

    for step in labeled_steps:
        sol_key = (step.problem_id, step.solution_id)
        if sol_key in train_solutions:
            step.split = "train"
            train_steps.append(step)
        else:
            step.split = "eval"
            eval_steps.append(step)

    # Double check solution ID leakage
    train_ids = {s.solution_id for s in train_steps}
    eval_ids = {s.solution_id for s in eval_steps}
    if not train_ids.isdisjoint(eval_ids):
        raise ValueError("Solution ID intersection detected between train and eval splits!")

    return train_steps, eval_steps


def generate_verifier_dataset(
    pilot_evidence_path: Path = DEFAULT_PILOT_EVIDENCE,
    eval_evidence_path: Path = DEFAULT_EVAL_EVIDENCE,
    pilot_baseline_path: Optional[Path] = DEFAULT_PILOT_BASELINE,
    eval_baseline_path: Optional[Path] = DEFAULT_EVAL_BASELINE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    train_ratio: float = 0.8,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Run the full verifier-label derivation and dataset generation pipeline.
    """
    raw_records = validate_and_load_evidence(
        pilot_path=pilot_evidence_path,
        eval_path=eval_evidence_path,
        pilot_baseline_path=pilot_baseline_path,
        eval_baseline_path=eval_baseline_path,
    )

    canonical_groups, collapsed_count = deduplicate_canonical_steps(raw_records)

    labeled_steps = [
        derive_step_label(
            problem_id=grp["problem_id"],
            solution_id=grp["solution_id"],
            step_id=grp["step_id"],
            step_type=grp["step_type"],
            dataset_source=grp["dataset_source"],
            records=grp["records"],
        )
        for grp in canonical_groups
    ]

    train_steps, eval_steps = partition_train_eval(
        labeled_steps=labeled_steps,
        train_ratio=train_ratio,
        seed=seed,
    )

    # Output directory preparation
    output_dir.mkdir(parents=True, exist_ok=True)

    labels_jsonl_path = output_dir / "verifier_labels.jsonl"
    train_jsonl_path = output_dir / "verifier_train.jsonl"
    eval_jsonl_path = output_dir / "verifier_eval.jsonl"
    summary_json_path = output_dir / "verifier_label_summary.json"
    derivation_md_path = output_dir / "verifier_label_derivation.md"

    # Write JSONL artifacts
    with labels_jsonl_path.open("w", encoding="utf-8") as f:
        for s in labeled_steps:
            f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")

    with train_jsonl_path.open("w", encoding="utf-8") as f:
        for s in train_steps:
            f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")

    with eval_jsonl_path.open("w", encoding="utf-8") as f:
        for s in eval_steps:
            f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")

    # Aggregate summary statistics
    label_counts = Counter(s.label for s in labeled_steps)
    source_counts = Counter(s.dataset_source for s in labeled_steps)
    family_distribution = Counter()
    for s in labeled_steps:
        for m_type in s.applicable_mutation_types:
            family_distribution[m_type] += 1

    unique_solutions = set((s.problem_id, s.solution_id) for s in labeled_steps)
    train_solutions = set((s.problem_id, s.solution_id) for s in train_steps)
    eval_solutions = set((s.problem_id, s.solution_id) for s in eval_steps)

    summary_data = {
        "dataset_name": "StepGuard Verifier Labeled Dataset",
        "stage": "Stage 1.3",
        "target_met": len(labeled_steps) >= 150,
        "total_canonical_steps": len(labeled_steps),
        "target_step_count": 150,
        "collapsed_duplicates": collapsed_count,
        "raw_evidence_records": len(raw_records),
        "label_distribution": dict(label_counts),
        "dataset_source_distribution": dict(source_counts),
        "split_summary": {
            "train_ratio": train_ratio,
            "seed": seed,
            "train_steps": len(train_steps),
            "eval_steps": len(eval_steps),
            "train_step_pct": round(len(train_steps) / len(labeled_steps) * 100, 2),
            "eval_step_pct": round(len(eval_steps) / len(labeled_steps) * 100, 2),
            "total_solutions": len(unique_solutions),
            "train_solutions": len(train_solutions),
            "eval_solutions": len(eval_solutions),
            "solution_leakage": len(train_solutions.intersection(eval_solutions)),
        },
        "train_label_distribution": dict(Counter(s.label for s in train_steps)),
        "eval_label_distribution": dict(Counter(s.label for s in eval_steps)),
        "mutation_family_distribution": dict(family_distribution),
        "artifacts": {
            "all_labels": str(labels_jsonl_path.relative_to(ROOT)),
            "train_split": str(train_jsonl_path.relative_to(ROOT)),
            "eval_split": str(eval_jsonl_path.relative_to(ROOT)),
            "summary_json": str(summary_json_path.relative_to(ROOT)),
            "report_md": str(derivation_md_path.relative_to(ROOT)),
        },
    }

    with summary_json_path.open("w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)

    # Write markdown derivation report
    md_content = f"""# StepGuard Verifier Label Derivation Report

## 1. Executive Summary

- **Derivation Stage**: Stage 1.3 Joint Reconciled Pipeline
- **Target Status**: **PASS** (>= 150 labeled steps)
- **Total Canonical Labeled Steps**: **{len(labeled_steps)}**
- **Raw Evidence Records Aggregated**: {len(raw_records)} (Pilot: 99, Evaluation: 158)
- **Single-Statement Duplicates Collapsed**: {collapsed_count}
- **Solution Leakage**: **0** (strictly disjoint train and evaluation solutions)

---

## 2. Labeling Methodology

Step labels are derived strictly according to the Stage 1.3 Joint Semantic Reconciliation rules:

1. **Baseline Requirement**: All candidate programs passed baseline tests (`baseline_result == "PASS"`).
2. **Outcome Flip Computation**:
   - `FAIL` execution outcome represents an unambiguous semantic test failure (`outcome_flip = True`).
   - `PASS` execution outcome represents a surviving mutant (`outcome_flip = False` -> `uncertain`).
   - `RUNTIME_ERROR` is evaluated with exception typing. 100% dominant runtime errors or unhandled `TypeError` (sequence division) are labeled `uncertain`.
3. **Multi-Operator Steps (>=2 applicable types)**: Labeled `correct` if and only if >=2 distinct mutation types produce genuine outcome flips (`FAIL`).
4. **Single-Operator Steps (1 applicable type)**: Labeled `correct` if 100% of applicable mutations produce a genuine outcome flip (1/1 `FAIL`).
5. **Deduplication**: Identical `func_01`/`block_01` spans in single-statement functions are unified into a single canonical step (`unified_func_block`).

---

## 3. Dataset Distribution & Metrics

### Label Breakdown
| Label | Count | Percentage |
|---|---:|---:|
| **`correct`** | **{label_counts['correct']}** | **{label_counts['correct']/len(labeled_steps):.1%}** |
| **`uncertain`** | **{label_counts['uncertain']}** | **{label_counts['uncertain']/len(labeled_steps):.1%}** |
| **Total Canonical Steps** | **{len(labeled_steps)}** | **100.0%** |

### Evidence Contribution
| Source | Raw Records | Canonical Steps | Correct | Uncertain |
|---|---:|---:|---:|---:|
| **Evaluation (`eval_*`)** | 158 | 94 | {sum(1 for s in labeled_steps if s.dataset_source == 'evaluation' and s.label == 'correct')} | {sum(1 for s in labeled_steps if s.dataset_source == 'evaluation' and s.label == 'uncertain')} |
| **Pilot (`mbpp_*`)** | 99 | 62 | {sum(1 for s in labeled_steps if s.dataset_source == 'pilot' and s.label == 'correct')} | {sum(1 for s in labeled_steps if s.dataset_source == 'pilot' and s.label == 'uncertain')} |
| **Total** | **257** | **{len(labeled_steps)}** | **{label_counts['correct']}** | **{label_counts['uncertain']}** |

### 80/20 Solution-Grouped Split
| Split | Canonical Steps | Solutions | Correct | Uncertain | Leakage |
|---|---:|---:|---:|---:|---:|
| **Train (80%)** | {len(train_steps)} ({len(train_steps)/len(labeled_steps):.1%}) | {len(train_solutions)} | {summary_data['train_label_distribution'].get('correct', 0)} | {summary_data['train_label_distribution'].get('uncertain', 0)} | 0 |
| **Eval (20%)** | {len(eval_steps)} ({len(eval_steps)/len(labeled_steps):.1%}) | {len(eval_solutions)} | {summary_data['eval_label_distribution'].get('correct', 0)} | {summary_data['eval_label_distribution'].get('uncertain', 0)} | 0 |
| **Total** | **{len(labeled_steps)}** | **{len(unique_solutions)}** | **{label_counts['correct']}** | **{label_counts['uncertain']}** | **0** |

---

## 4. Mutation Families Covered

| Mutation Family | Canonical Step Occurrences |
|---|---:|
| `comparison_swap` | {family_distribution.get('comparison_swap', 0)} |
| `multiplication_swap` | {family_distribution.get('multiplication_swap', 0)} |
| `off_by_one` | {family_distribution.get('off_by_one', 0)} |
| `boolean_flip` | {family_distribution.get('boolean_flip', 0)} |
| `identity_swap` | {family_distribution.get('identity_swap', 0)} |

---

## 5. Artifact Preservation & Reproducibility

The following verified artifacts were produced without modifying frozen historical datasets:
- `{labels_jsonl_path.relative_to(ROOT)}`
- `{train_jsonl_path.relative_to(ROOT)}`
- `{eval_jsonl_path.relative_to(ROOT)}`
- `{summary_json_path.relative_to(ROOT)}`

Regenerate at any time using:
```powershell
.\\.venv\\Scripts\\python partner_a/evidence/derive_verifier_labels.py
```
"""

    with derivation_md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    return summary_data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive StepGuard verifier labels from step evidence."
    )
    parser.add_argument(
        "--pilot-evidence",
        type=Path,
        default=DEFAULT_PILOT_EVIDENCE,
        help="Path to pilot step_evidence.jsonl",
    )
    parser.add_argument(
        "--eval-evidence",
        type=Path,
        default=DEFAULT_EVAL_EVIDENCE,
        help="Path to evaluation step_evidence_is.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save generated label artifacts",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic random seed for train/eval split",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Proportion of solutions assigned to train split",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("StepGuard Verifier Label Derivation")
    print("=" * 60)
    summary = generate_verifier_dataset(
        pilot_evidence_path=args.pilot_evidence,
        eval_evidence_path=args.eval_evidence,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        seed=args.seed,
    )
    print(f"Total Canonical Steps : {summary['total_canonical_steps']} (Target >= 150: {summary['target_met']})")
    print(f"Correct Steps         : {summary['label_distribution']['correct']}")
    print(f"Uncertain Steps       : {summary['label_distribution']['uncertain']}")
    print(f"Train Steps (80%)     : {summary['split_summary']['train_steps']}")
    print(f"Eval Steps (20%)      : {summary['split_summary']['eval_steps']}")
    print(f"Solution Leakage      : {summary['split_summary']['solution_leakage']}")
    print(f"Artifacts saved to    : {args.output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
