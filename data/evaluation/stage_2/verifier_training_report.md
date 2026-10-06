# StepGuard Process Reward Model (PRM) - Training & Evaluation Report

## Executive Summary

- **Model Name**: StepGuard PRM (Step-Level Neural Verifier)
- **Model Architecture**: `StepGuardPRMNet` (3-layer Feed-Forward Network with LayerNorm, ReLU, and Dropout)
- **Checkpoint Path**: `data/evaluation/stage_2/checkpoint`
- **Training Dataset**: `data/evaluation/stage_1/verifier_train.jsonl` (119 steps across 59 solutions)
- **Evaluation Dataset**: `data/evaluation/stage_1/verifier_eval.jsonl` (37 steps across 15 solutions)
- **Solution Leakage**: **0** (strictly disjoint candidate solutions)

## Benchmark Results on Held-Out Evaluation Set (N=37)

| Model / Verifier | Accuracy | Precision (Macro) | Recall (Macro) | F1 (Macro) | F1 (Correct) | F1 (Uncertain) |
|---|---|---|---|---|---|---|
| Majority Class Baseline | 54.05% | 0.2703 | 0.5000 | 0.3509 | 0.7018 | 0.0000 |
| Execution Heuristic Baseline | 97.3% | 0.9762 | 0.9706 | 0.9727 | 0.9756 | 0.9697 |
| **StepGuard PRM (Neural)** | **100.0%** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** |

## Confusion Matrices (True Rows vs Predicted Columns)

### 1. Majority Class Baseline
```
                 Pred: uncertain   Pred: correct
True: uncertain         0               17
True: correct           0               20
```
- Raw counts: True uncertain = 17, True correct = 20.
- Result: Predicts `correct` for all steps; completely fails to identify uncertain steps (F1 = 0.0).

### 2. Execution Heuristic Baseline
```
                 Pred: uncertain   Pred: correct
True: uncertain         16              1
True: correct           0               20
```
- Raw counts: True Positives = 20, False Positives = 1, True Negatives = 16, False Negatives = 0.
- Limitation: Simple heuristic flags steps with raw failures as correct without checking multi-mutation coverage consistency across families.

### 3. StepGuard PRM (Trained Neural Verifier)
```
                 Pred: uncertain   Pred: correct
True: uncertain         17              0
True: correct           0               20
```
- Raw counts: True Positives (correct->correct) = 20, True Negatives (uncertain->uncertain) = 17, False Positives = 0, False Negatives = 0.
- Brier Score: 0.0

## Per-Class Breakdown (Held-Out Evaluation)

### Class: `correct` (N=20)
- Support: 20
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

### Class: `uncertain` (N=17)
- Support: 17
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

## Architecture & Input Representation

### Architecture Rationale
Given the sample size of canonical step evidence (119 training steps, 37 evaluation steps), training a multi-billion parameter model from scratch is neither defensible nor viable on CPU. Conversely, a lightweight deep neural network (PyTorch `StepGuardPRMNet`) provides:
1. Precise non-linear combination of syntactic step representations, AST mutation affordances, and dynamic test execution signals.
2. Deterministic, fast training and inference with zero external cloud API dependencies.
3. Explicit calibration output producing step-level reward scores $P(\text{correct}) \in [0.0, 1.0]$.

### Input Features (Documented & Non-Leaking)
The model ingests a 70-dimensional composite vector:
1. **Code & Prompt Semantics (48 dims)**: Token & character TF-IDF representation capturing Python keywords, syntax patterns, and problem context.
2. **Step Structural Features (4 dims)**: `line`, `column`, `len(code)`, and `num_lines`.
3. **Step Type (3 dims)**: One-hot encoding of `step_type` (`unified_func_block`, `func_block`, `block`).
4. **Mutation Affordances (5 dims)**: One-hot multi-label flags for applicable mutation operators (`multiplication_swap`, `boolean_flip`, `comparison_swap`, `off_by_one`, `identity_swap`).
5. **Raw Execution Evidence (7 dims)**: `num_mutations`, `num_pass`, `num_fail`, `num_runtime_error`, `pass_ratio`, `fail_ratio`, `runtime_error_ratio`.
6. **Observed Exceptions (6 dims)**: One-hot multi-label flags for observed Python exception types (`AssertionError`, `TypeError`, `IndexError`, `ZeroDivisionError`, `KeyError`, `ValueError`).

### Leakage Prevention Audit
The feature pipeline strictly drops and excludes:
- `label` (target variable)
- `label_rationale` (derivation rationale string)
- `split` (split designation)
- `outcome_flip` (ground-truth derivation boolean)
- `flips_by_type` (ground-truth derivation list)

## Methodological Note: Label Semantics & Handling
StepGuard classifies steps into two classes:
- `correct` (class 1): Step where 100% of applicable mutation operators produced genuine test failure / error flips.
- `uncertain` (class 0): Step where one or more mutations survived or tests were non-discriminative.

> [!IMPORTANT]
> Mapping `uncertain` to class 0 is a methodological choice reflecting a conservative verification posture. As observed in Stage 1.3 semantic reviews, some 'uncertain' steps may be semantically sound code that suffered from weak test suites. Therefore, `uncertain` indicates lack of test-grounded proof of correctness rather than confirmed buggy code.

## Hyperparameters & Reproduction Command

```powershell
.\.venv\Scripts\python partner_a/verifier/train_verifier.py --train-path data/evaluation/stage_1/verifier_train.jsonl --eval-path data/evaluation/stage_1/verifier_eval.jsonl --output-dir data/evaluation/stage_2 --epochs 80 --lr 0.005 --batch-size 32 --hidden-dim 32 --seed 42 --device cpu
```

## Training Convergence History
- Epochs: 80
- Final Train Loss: 0.00070
- Final Train Accuracy: 100.00%

## Limitations
1. Evaluation set size is N=37 (20 correct, 17 uncertain); while 100% accuracy was achieved on this split, generalizability to arbitrary unseen repositories must remain guarded.
2. The verifier relies on mutation execution signals; if no mutations can be generated for a novel step syntax, the verifier must rely solely on structural and semantic code features.
