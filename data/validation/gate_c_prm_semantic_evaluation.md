# StepGuard Gate C: PRM-vs-Human Semantic Evaluation Report

**Evaluation Protocol**: Gate C PRM-vs-Human Semantic Evaluation  
**Status**: **INCONCLUSIVE / THRESHOLD DEFICIENT (GOVERNANCE BLOCKED)**  
**Investigator**: Partner B (in compliance with Partner A Governance Protocol)  
**Date**: October 2026  
**Artifact Path**: `data/validation/gate_c_prm_semantic_evaluation.md`  
**Git Base Commit / Tag**: `f449bef54b71f8e9ecde2c78b7fa4e4002c2e340` (Branch: `feat/gate-c-preflight-protocol`)

---

## 1. Executive Summary & Evaluation Objective

This document reports the read-only, execution-grounded semantic evaluation of historical **StepGuard Process Reward Model (PRM)** predictions against the finalized **N=37 Human-Annotated & Adjudicated Gate C Evaluation Cohort**.

Under the authorized Gate C evaluation charter:
- Independent annotations were conducted by **Evaluator 1 (Partner A)** and **Evaluator 2 (Chandu)** on the frozen, strictly blinded evaluation sheet ([`data/validation/gate_c_blind_evaluation_sheet.md`](file:///C:/Users/ashis/Desktop/StepGuard-f3-slice4/data/validation/gate_c_blind_evaluation_sheet.md)).
- The single inter-evaluator disagreement on sample `SG-GATE-C-025` was formally resolved through third-party adjudication by **Srilu (Adjudicator)**.
- Historical PRM predictions were extracted deterministically from the recovered Stage 2 PRM checkpoint (`data/evaluation/stage_2/checkpoint/model_weights.pt` and `extractor.joblib`) evaluated on the 37 held-out evaluation samples in [`data/evaluation/stage_1/verifier_eval.jsonl`](file:///C:/Users/ashis/Desktop/StepGuard-f3-slice4/data/evaluation/stage_1/verifier_eval.jsonl).

---

## 2. Frozen Evaluation Inputs & Provenance Verification

All evaluation metrics, human labels, and PRM predictions are grounded strictly in the following immutable artifacts:

1. **Held-Out Evaluation Split**: `data/evaluation/stage_1/verifier_eval.jsonl` (37 records, zero overlap with the 119-record training split `data/evaluation/stage_1/verifier_train.jsonl`).
2. **Blinded Evaluation Sheet**: `data/validation/gate_c_blind_evaluation_sheet.md` (37 distinct target steps, sha256 verified).
3. **PRM Checkpoint & Feature Extractor**: `data/evaluation/stage_2/checkpoint/` (73-dimensional non-leaking feature extractor).
4. **Annotator Submissions**: Locked submissions from Evaluator 1 (Partner A: 33 A, 0 B, 4 C), Evaluator 2 (Chandu: 34 A, 0 B, 3 C), and Adjudicator (Srilu: 1 resolved sample `SG-GATE-C-025`).

> [!IMPORTANT]
> **GOVERNANCE INVARIANT CONFIRMATION**:
> Zero training records were evaluated. No model retraining, fine-tuning, threshold tuning, or post-hoc label manipulation was performed.

---

## 3. Human Evaluator Inter-Rater Reliability (E1 vs E2)

Human evaluation followed a three-class semantic rubric:
- **`A` (Clearly correct)**: The step represents a mathematically and semantically sound, valid intermediate or terminal operation.
- **`B` (Clearly incorrect)**: The step introduces a semantic bug, violated invariant, or incorrect control flow.
- **`C` (Cannot confidently determine / Uncertain)**: The step exhibits inherent ambiguity, unexercised boundary behavior, or under-constrained test specifications.

### Inter-Rater Concordance Metrics

| Metric | Value | Denominator | Authorized Threshold | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Evaluator Concordance (Raw Agreement)** | **97.30%** (36/37) | 37 evaluated samples | $\ge 80.0\%$ | **PASS** |
| **Chance-Expected Agreement ($P_e$)** | **82.83%** (1134/1369 $\approx 0.828342$) | 37 evaluated samples | N/A | N/A |
| **Cohen's Kappa ($\kappa$)** | **0.8426** ($198/235 \approx 0.842553$) | 37 evaluated samples | $\ge 0.75$ | **PASS** |
| **Sole Disagreement Requiring Adjudication** | **1 sample** (`SG-GATE-C-025`) | 37 evaluated samples | N/A | Adjudicated by Srilu |

### Sole Disagreement & Adjudication Record (`SG-GATE-C-025`)
- **Sample ID**: `SG-GATE-C-025` (`eval_014` / `eval_014_sol_003` / `block_01`)
- **Evaluator 1 (Partner A)**: `C`
- **Evaluator 2 (Chandu)**: `A`
- **Adjudicator (Srilu)**: `C`
- **Confidence**: High
- **Adjudication Rationale**: The RGB→HSV function is incomplete because `...` hides essential calculations, especially hue.
- **Final Adjudicated Human Label**: `C`

*(Note: `SG-GATE-C-022` was unanimously evaluated as `A` by both Evaluator 1 and Evaluator 2; `SG-GATE-C-025` is the sole disagreement across the entire 37-sample evaluation cohort).*

---

## 4. Final Human Label Distribution

Following consensus and formal adjudication of `SG-GATE-C-025`, the finalized human ground truth distribution across the $N=37$ cohort is:

| Category | Description | Count | Percentage | Denominator |
| :--- | :--- | :--- | :--- | :--- |
| **Class A** | Clearly Correct | **33** | **89.19%** | 37 total samples |
| **Class B** | Clearly Incorrect | **0** | **0.00%** | 37 total samples |
| **Class C** | Cannot Confidently Determine (Uncertain) | **4** | **10.81%** | 37 total samples |
| **Total Cohort** | All evaluated held-out steps | **37** | **100.00%** | 37 total samples |

### Explicit Protocol on Class C Samples
The 4 samples labeled `C` (`SG-GATE-C-025`, `SG-GATE-C-026`, `SG-GATE-C-031`, `SG-GATE-C-034`) represent boundary initialization or loop logic with unexercised edge cases. In strict adherence to the Gate C Evaluation Charter:
- **`C` samples are strictly excluded** from the definitive A/B evaluation denominator ($N_{\text{def}} = 33$).
- **`C` samples are NOT silently converted** or mapped to either `A` or `B`.

---

## 5. PRM Performance Against Definitive Human Labels (A / B)

The definitive evaluation cohort comprises all samples with non-ambiguous human ground truth ($N_{\text{def}} = 33$, consisting entirely of Class `A` samples).

### Confusion Matrix on Definitive Cohort ($N=33$)

| | Human Ground Truth: `A` (Correct) | Human Ground Truth: `B` (Incorrect) | Total PRM Predictions |
| :--- | :---: | :---: | :---: |
| **PRM Predicts: `correct`** | **20** (True Positive) | **0** (False Positive) | **20** |
| **PRM Predicts: `uncertain`** | **13** (False Negative) | **0** (True Negative) | **13** |
| **Total Human Labels** | **33** | **0** | **33** |

### Accuracy & Performance Metrics

| Metric | Formula | Value | Denominator | Authorized Threshold | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Definitive Cohort Accuracy** | $\frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$ | **60.61%** (20/33) | 33 definitive samples | $\ge 85.0\%$ | **FAIL** |
| **Sensitivity / Recall on Class A** | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ | **60.61%** (20/33) | 33 Class A samples | N/A | — |
| **Specificity on Class B** | $\frac{\text{TN}}{\text{TN} + \text{FP}}$ | **Undefined (0/0)** | 0 Class B samples | N/A | Undefined (0/0) |
| **Data Leakage Check** | Train $\cap$ Eval | **0 overlapping records** | 37 eval records | Exactly 0 | **PASS** |
| **Cohort Integrity** | Eval Sample Count | **37 records** | 37 expected records | Exactly 37 | **PASS** |

---

## 6. Critical Methodological Limitations & Distribution Skew Analysis

> [!WARNING]
> **CRITICAL METHODOLOGICAL LIMITATION: ZERO NEGATIVE CLASS SAMPLES ($B = 0$)**
>
> 1. **Complete Absence of Negative Counterexamples**:
>    The finalized human evaluation dataset contains exactly **0 definitive incorrect steps (`B = 0`)**. All 33 definitive human-validated steps are correct (`A = 33`).
>
> 2. **Lack of Empirical Discriminant Evidence**:
>    Because the definitive ground truth contains no `B` samples, **it is mathematically impossible to evaluate the PRM's ability to discriminate correct steps from incorrect steps**. A trivial model predicting "always correct" would achieve 100% accuracy on this definitive cohort without possessing any semantic verification ability.
>
> 3. **False Negative Divergence (Heuristic Sensitivity vs Semantic Soundness)**:
>    The PRM predicted `uncertain` for 13 steps that human evaluators verified as semantically correct (`A`). In each of these cases, the PRM accurately captured Stage 1 dynamic mutation survival (e.g., redundant loops, under-tested constants), reflecting test-suite sensitivity rather than semantic invalidity. This confirms that **mutation survival indicates potential test blindspots, NOT semantic incorrectness**.

---

## 7. Comprehensive 37-Sample Provenance & Evaluation Record

| Sample ID | Index | Problem ID | Solution ID | Step ID | E1 (Partner A) | E2 (Chandu) | Srilu (Adj) | Final Human | PRM Pred | $P(\text{corr})$ | Definitive Eval |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| `SG-GATE-C-001` | 00 | `eval_001` | `eval_001_sol_004` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-002` | 01 | `eval_001` | `eval_001_sol_005` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-003` | 02 | `eval_002` | `eval_002_sol_001` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-004` | 03 | `eval_004` | `eval_004_sol_002` | `block_02` | A | A | - | **A** | `uncertain` | 0.0003 | Mismatch (FN) |
| `SG-GATE-C-005` | 04 | `eval_004` | `eval_004_sol_002` | `block_05` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-006` | 05 | `eval_004` | `eval_004_sol_002` | `block_06` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-007` | 06 | `eval_004` | `eval_004_sol_002` | `block_07` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-008` | 07 | `eval_004` | `eval_004_sol_002` | `block_08` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-009` | 08 | `eval_004` | `eval_004_sol_002` | `func_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-010` | 09 | `eval_004` | `eval_004_sol_004` | `block_02` | A | A | - | **A** | `uncertain` | 0.0003 | Mismatch (FN) |
| `SG-GATE-C-011` | 10 | `eval_004` | `eval_004_sol_004` | `block_05` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-012` | 11 | `eval_004` | `eval_004_sol_004` | `block_06` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-013` | 12 | `eval_004` | `eval_004_sol_004` | `block_07` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-014` | 13 | `eval_004` | `eval_004_sol_004` | `block_08` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-015` | 14 | `eval_004` | `eval_004_sol_004` | `func_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-016` | 15 | `eval_004` | `eval_004_sol_005` | `block_02` | A | A | - | **A** | `uncertain` | 0.0003 | Mismatch (FN) |
| `SG-GATE-C-017` | 16 | `eval_004` | `eval_004_sol_005` | `block_05` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-018` | 17 | `eval_004` | `eval_004_sol_005` | `block_06` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-019` | 18 | `eval_004` | `eval_004_sol_005` | `block_07` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-020` | 19 | `eval_004` | `eval_004_sol_005` | `block_08` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-021` | 20 | `eval_004` | `eval_004_sol_005` | `func_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-022` | 21 | `eval_007` | `eval_007_sol_004` | `block_01` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-023` | 22 | `eval_007` | `eval_007_sol_004` | `block_02` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-024` | 23 | `eval_013` | `eval_013_sol_005` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-025` | 24 | `eval_014` | `eval_014_sol_003` | `block_01` | C | A | C | **C** | `uncertain` | 0.0002 | Excluded (Class C) |
| `SG-GATE-C-026` | 25 | `eval_014` | `eval_014_sol_004` | `block_01` | C | C | - | **C** | `uncertain` | 0.0002 | Excluded (Class C) |
| `SG-GATE-C-027` | 26 | `eval_016` | `eval_016_sol_002` | `block_04` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-028` | 27 | `eval_016` | `eval_016_sol_002` | `block_05` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-029` | 28 | `eval_016` | `eval_016_sol_002` | `func_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-030` | 29 | `mbpp_002` | `mbpp_002_sol_001` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-031` | 30 | `mbpp_004` | `mbpp_004_sol_004` | `block_04` | C | C | - | **C** | `uncertain` | 0.0002 | Excluded (Class C) |
| `SG-GATE-C-032` | 31 | `mbpp_004` | `mbpp_004_sol_004` | `block_05` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-033` | 32 | `mbpp_004` | `mbpp_004_sol_004` | `block_06` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-034` | 33 | `mbpp_004` | `mbpp_004_sol_004` | `block_07` | C | C | - | **C** | `uncertain` | 0.0002 | Excluded (Class C) |
| `SG-GATE-C-035` | 34 | `mbpp_004` | `mbpp_004_sol_004` | `func_01` | A | A | - | **A** | `uncertain` | 0.0002 | Mismatch (FN) |
| `SG-GATE-C-036` | 35 | `mbpp_005` | `mbpp_005_sol_004` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |
| `SG-GATE-C-037` | 36 | `mbpp_005` | `mbpp_005_sol_005` | `block_01` | A | A | - | **A** | `correct` | 0.9999 | Correct (TP) |

---

## 8. Formal Gate C Determination

Based on the authorized Gate C thresholds:

1. **Inter-Rater Reliability (Cohen's $\kappa \ge 0.75$, Raw $\ge 80\%$)**: **PASS** ($\kappa = 0.8426$, Raw = $97.30\%$).
2. **Data Leakage & Cohort Integrity (0 leakage, $N=37$)**: **PASS** (0 leakage, 37 records).
3. **PRM Semantic Accuracy on Definitive Labels ($\ge 85\%$)**: **FAIL** ($60.61\% < 85\%$).
4. **Discriminant Validation on Negative Class ($B > 0$)**: **UNSATISFIED / STRUCTURALLY CONSTRAINED** ($B = 0$).

### Final Verdict: `INCONCLUSIVE / THRESHOLD DEFICIENT`
The PRM cannot be validated as a general semantic verifier on Gate C due to:
- PRM accuracy on the definitive human subset ($20/33 = 60.61\%$) falling below the $85\%$ threshold.
- The complete absence of negative human gold labels ($B=0$) in the held-out candidate pool, preventing empirical verification of bug detection.

**Action**: Release of Gate C as a validated semantic ground truth is **BLOCKED**. StepGuard continues to operate strictly as an execution-grounded mutation diagnostic tool.
