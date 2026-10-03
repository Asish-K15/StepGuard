# StepGuard — F2 PRM Recovery & Reproducibility Closeout Report

**Evaluation Task**: F2 (Process Reward Model Recovery & Evaluation Reproducibility)  
**Investigator**: Partner B (in collaboration with Partner A Review Protocol)  
**Status**: **GATE A ACCEPTED / GATE B ACCEPTED / CLOSEOUT READY FOR RELEASE AUTHORIZATION**  
**Protocol Compliance**: Strict Multi-Agent Governance Protocol. Zero existing frozen artifacts modified, zero active working-tree protected files altered, zero commits, zero pushes, Gate C strictly unauthorized and not executed.

---

## 1. Executive Summary & Review Context

Following the formal closeout of Task F1 (documenting the provenance gap of the historical 101-label cohort in [`data/validation/f1_provenance_gap_closeout.md`](file:///c:/Users/balin/Desktop/StepGuard/data/validation/f1_provenance_gap_closeout.md)), Task F2 was chartered to recover, verify integrity, and independently reproduce the historical StepGuard Process Reward Model (PRM) verifier artifacts and evaluation benchmarks.

Under strict multi-agent governance:
1. **Gate A (Artifact & Checkpoint Verification)** was executed and passed: all 18 historical PRM artifacts originating from commit `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1` were verified byte-for-byte against their Git object hashes; the checkpoint weights, configuration, and 73-dimensional non-leaking feature extractor were validated.
2. **Gate B (Historical Evaluation Reproduction)** was executed in an isolated environment and passed: the historical held-out evaluation on the frozen $N=37$ test set was reproduced with 100% exact numerical agreement across class counts, discrete predictions, macro metrics, confusion matrices, and Brier score.
3. **Partner A Formal Review**: Partner A reviewed the Gate B evaluation evidence and issued the formal decision: **"Gate B has been reviewed and is accepted. Prepare a final F2 PRM Recovery & Reproducibility Closeout Report."**

This report constitutes the comprehensive closeout record for Task F2, establishing provenance, reproducibility, boundary conditions, and scientific governance constraints prior to release authorization.

---

## 2. Gate A Verification: Historical Artifact Hashes & Checkpoint Integrity

### 2.1 Complete 18/18 Artifact Hash Audit (Approved Gate A Recovery Scope)

The 18 authorized artifacts constituting the Gate A PRM recovery scope originate strictly from Git commit `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1` (Branch `master`, Sun Sep 27 18:32:16 2026 +0530). Every artifact was verified against its authoritative Git blob SHA and full cryptographic SHA-256 hash:

| # | Artifact Relative Path | Git Blob SHA | SHA-256 Hash | Size (Bytes) | Verification Status |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | `partner_a/verifier/model.py` | `efc52e6084a62c55d2c0b00fe3e4f0355c00177b` | `a49f59db98a87574162eb316b892b276040e97d10ce037edb516f244095b142f` | 8,886 | **VERIFIED (Match)** |
| 2 | `partner_a/verifier/features.py` | `30818c53024fd5adc0f027e1966082ce4aa3bd95` | `a68903fd90057a91b2f78ded008762f560473518f9de139c3f5301a8c3569ab6` | 7,386 | **VERIFIED (Match)** |
| 3 | `partner_a/verifier/train_verifier.py` | `0806746426776148790030917052278342189f3a` | `80556a055f3d2c433552c37c4d449947d5669dc8016d2a9e848b5197bd805104` | 18,149 | **VERIFIED (Match)** |
| 4 | `partner_a/verifier/baselines.py` | `46fc196884b33a2f2e4494ae23c82b3f988336e7` | `8a4211911a63fdbd9c3619d099a738bc72c2858e70651c11ae04c57325162eac` | 2,727 | **VERIFIED (Match)** |
| 5 | `partner_a/verifier/metrics.py` | `a2c715623f8ca9742246e3916e4bfce35e2ba792` | `c0c117ac149520cbe2d88b4564fb91a4bf0d410e0ab0a59931fc7f22666a3a95` | 3,486 | **VERIFIED (Match)** |
| 6 | `partner_a/verifier/demo_verifier.py` | `2b475656620d74b8205e023ee4608c89acecad9b` | `39b5e5d9c52480e21775fdd01d07560ec8fe7c657ce3cebf9a6d2f94988c8fc7` | 6,938 | **VERIFIED (Match)** |
| 7 | `partner_a/verifier/__init__.py` | `70052e4f6007811840113f33943ef3f7ca0a2d78` | `18be731de7ad453fbf7c3d9f3f6ce80ffa471d3a6a2691e65c19681ec49f0e0c` | 518 | **VERIFIED (Match)** |
| 8 | `data/evaluation/stage_1/verifier_train.jsonl` | `83a51ab80328bca20620a49ba7f7d9a73a59d5b0` | `560bbff6c810d69f7d76f69d9135a6ae4a13e578a78b6406d72d1cf25e94764d` | 97,834 | **VERIFIED (Match)** |
| 9 | `data/evaluation/stage_1/verifier_eval.jsonl` | `b9a63507876bd9792487871b22e1e04476461870` | `6cab44d3267290b0d54aa46896ec32e872fb057f310077bbb8eff360da7dddae` | 33,267 | **VERIFIED (Match)** |
| 10 | `data/evaluation/stage_2/checkpoint/config.json` | `d9051ae900e0173525cd0069113f066d479cc6de` | `bf8e04ef5f314a2bb4e226eaae0d66ceba84049e017c6898b221f739f91e9f1d` | 231 | **VERIFIED (Match)** |
| 11 | `data/evaluation/stage_2/checkpoint/extractor.joblib` | `fb834a04afb003a7f65d674d43258f127598f8c5` | `9c6b624f2c84760f7a67f279a1f06c8211a47ed8a0511f69ea32bab4785d87b8` | 2,876 | **VERIFIED (Match)** |
| 12 | `data/evaluation/stage_2/checkpoint/model_weights.pt` | `aabf8621c65c070ad314b0119dbabf64633dcc27` | `4a0b37e480b1e87d7574f823f8601191049bb14658c9f1bffc192044144a8765` | 16,357 | **VERIFIED (Match)** |
| 13 | `tests/test_train_verifier.py` | `ae191bb0faa8d43215705ecd5c868cf1984b99e7` | `6094fc9b8549c47e3040e099129cab5a9ab4aed1537c9717ef91cf1caaec77d1` | 9,925 | **VERIFIED (Match)** |
| 14 | `tests/test_verifier_demo.py` | `5b9ad3384631f34f993f963c0d00cc6db5c4452c` | `dd008cf76c6d2064da5ca8dd4ca94f73d711f346be229798df1113119fb1f983` | 4,370 | **VERIFIED (Match)** |
| 15 | `data/evaluation/stage_2/verifier_metrics.json` | `cc198a4ad398ca0fb18c4c4b95b8967dbfaf3549` | `e4da5f73c07bf5e2d29a7723e68c32427376f8ab516d37ef01ba702c3eacc90c` | 4,061 | **VERIFIED (Match)** |
| 16 | `data/evaluation/stage_2/verifier_training_report.md` | `4f608dc79ea15ed5b16b82ccf90eb85b3e44924d` | `7e9ae9a9419b36673284673c99608d8411792255061bf95c96311f1621dad77c` | 5,922 | **VERIFIED (Match)** |
| 17 | `data/evaluation/stage_2/stage_2_evaluation_report.md` | `8608db05e0c91ac80b0a9298de3b5b522ec688d6` | `9a17f94b77117f737bd1e6e1e8ec65f9f0c401566dabd8960d5eb3b932d1f102` | 12,483 | **VERIFIED (Match)** |
| 18 | `data/evaluation/stage_2/verifier_ablation.md` | `153cc91d496b5d6893fd6d779bb844c62574c53e` | `b3de9988ff521a0d5403a5d7bb8e61d9c5aab780fa5554206f9d744800df55a9` | 3,664 | **VERIFIED (Match)** |

### 2.2 Contextual Historical Provenance (Non-Gate A Scope)

During closeout preparation and the historical lineage audit, additional historical files from commit `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1` were inspected for background provenance:
- Full label dataset: `data/evaluation/stage_1/verifier_labels.jsonl` (156 records, SHA-256: `6b06b4bcffd16d2f301a1ddb033f5b7a7c289af2ed5a625015e26037e6dd54e3`)
- Summary tallies: `data/evaluation/stage_1/verifier_label_summary.json` (SHA-256: `d771fd114f58076e1fd44832520a2e2c08a683cb2801069882dd63632a18e466`)
- Derivation and review documents: `verifier_label_derivation.md`, `stage_1_3_semantic_review.md`, `stage_1_3_partner_b_semantic_review.md`, `stage_1_3_semantic_reconciliation.md`, and `mutation_eligibility_identity.json`.

These contextual files provided necessary background on the upstream Stage 1 heuristic derivation process, but they are strictly auxiliary and are not represented as the 18 artifacts recovered and verified under Gate A.

---

### 2.3 Checkpoint Architecture & Integrity

The recovered checkpoint at `data/evaluation/stage_2/checkpoint/` consists of three constituent components whose integrity was confirmed:

1. **Model Configuration (`config.json`)**:
   - `model_type`: `StepGuardPRMNet`
   - `in_features`: 73
   - `hidden_dim`: 32 (intermediate dimension: 16)
   - `dropout`: 0.2 (mid-layer dropout: 0.1)
   - `max_tfidf_features`: 48
   - `include_prompt`: `true`
   - `training_epochs`: 80
   - `final_train_loss`: 0.0007, `final_train_acc`: 1.0
2. **Model Weights (`model_weights.pt`)**:
   - Serialized PyTorch state dictionary (16,357 bytes).
   - Confirmed architecture: 3-layer MLP (`Linear(73, 32)` -> `LayerNorm(32)` -> `ReLU` -> `Dropout(0.2)` -> `Linear(32, 16)` -> `LayerNorm(16)` -> `ReLU` -> `Dropout(0.1)` -> `Linear(16, 2)`).
   - Validated weights_only deserialization without tensor degradation or corruption.
3. **Fitted Feature Extractor (`extractor.joblib`)**:
   - Serialized `StepFeatureExtractor` pipeline state (2,876 bytes).
   - Contains fitted TF-IDF vocabulary (48 features), fitted dense feature empirical means and standard deviations for normalization, and prompt caching mappings.

---

### 2.4 73-Dimensional Non-Leaking Feature Decomposition

The feature extractor strictly decomposes candidate step records into an exact 73-dimensional composite vector without data leakage:

```
Total Feature Space: D = 73
├── Textual & Prompt Features (48 dims):
│   └── Fitted TF-IDF (1-2 ngrams, max_features=48) of concatenated problem prompt + step code
└── Dense Numerical & Categorical Features (25 dims):
    ├── AST Geometry & Structural (4 dims): line, column, code char length, code line count
    ├── Step Type One-Hot (3 dims): unified_func_block, func_block, block
    ├── Mutation Family Affordances (5 dims): multiplication_swap, boolean_flip, comparison_swap, off_by_one, identity_swap
    ├── Raw Execution Counts & Ratios (7 dims): num_mutations, num_pass, num_fail, num_runtime_error, pass_ratio, fail_ratio, runtime_error_ratio
    └── Exception Type One-Hot (6 dims): AssertionError, TypeError, IndexError, ZeroDivisionError, KeyError, ValueError
```

**Leakage Prevention Audit**: Verified that forbidden target fields (`label`, `label_rationale`, `split`, `outcome_flip`, `flips_by_type`) are strictly quarantined and never enter the feature extractor.

---

## 3. Gate B Verification: Exact Reproduction of Historical N=37 Evaluation

### 3.1 Held-Out Partition Demographics & Class Balance

The held-out evaluation dataset (`verifier_eval.jsonl`, $N=37$) is strictly partitioned by solution ID from the training split ($N=119$), ensuring zero solution leakage (`train_solutions ∩ eval_solutions = ∅`).

- **Total Held-Out Steps**: $N = 37$
- **Total Underlying Solutions**: 15 distinct candidate programs
- **Ground Truth Class Distribution**:
  - `correct`: 20 steps (54.05%)
  - `uncertain`: 17 steps (45.95%)

---

### 3.2 Evaluation Metric Reproduction Comparison

The reproduced evaluation running against the recovered checkpoint yields **100% exact numerical agreement** with the historical `verifier_metrics.json` recorded in commit `5c59fe7`:

| Metric Category | Specific Metric | Historical Baseline (`5c59fe7`) | Reproduced Result (Isolated Harness) | Match Status |
|:---|:---|:---:|:---:|:---:|
| **Sample Counts** | Total Samples ($N$) | 37 | 37 | **EXACT (100%)** |
| | True Correct / True Uncertain | 20 / 17 | 20 / 17 | **EXACT (100%)** |
| | Predicted Correct / Predicted Uncertain | 20 / 17 | 20 / 17 | **EXACT (100%)** |
| **Overall Performance** | Accuracy | 1.0 (100.0%) | 1.0 (100.0%) | **EXACT (100%)** |
| | Brier Score Loss | 0.0000 | 0.0000 | **EXACT (100%)** |
| **Macro Metrics** | Macro Precision | 1.0000 | 1.0000 | **EXACT (100%)** |
| | Macro Recall | 1.0000 | 1.0000 | **EXACT (100%)** |
| | Macro F1 | 1.0000 | 1.0000 | **EXACT (100%)** |
| **Per-Class: `correct`** | Support | 20 | 20 | **EXACT (100%)** |
| | Precision | 1.0000 | 1.0000 | **EXACT (100%)** |
| | Recall | 1.0000 | 1.0000 | **EXACT (100%)** |
| | F1 Score | 1.0000 | 1.0000 | **EXACT (100%)** |
| **Per-Class: `uncertain`** | Support | 17 | 17 | **EXACT (100%)** |
| | Precision | 1.0000 | 1.0000 | **EXACT (100%)** |
| | Recall | 1.0000 | 1.0000 | **EXACT (100%)** |
| | F1 Score | 1.0000 | 1.0000 | **EXACT (100%)** |

---

### 3.3 Confusion Matrix Exact Match

```
                 Predicted: uncertain   Predicted: correct
True: uncertain           17                     0             (TN=17, FP=0)
True: correct              0                    20             (FN=0,  TP=20)
```
- **True Negatives (`uncertain` -> `uncertain`)**: 17 / 17
- **False Positives (`uncertain` -> `correct`)**: 0 / 17
- **False Negatives (`correct` -> `uncertain`)**: 0 / 20
- **True Positives (`correct` -> `correct`)**: 20 / 20

---

### 3.4 Baseline Comparison Reproduction

To evaluate the strength of the learned signal, the two non-neural reference baselines were also executed on the held-out partition and reproduced exactly:

| System / Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Brier Score | Description / Failure Mode |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **Majority Class Baseline** | 54.05% (20/37) | 0.2703 | 0.5000 | 0.3509 | 0.2680 | Unconditionally predicts `correct`; zero recall on `uncertain` |
| **Execution Heuristic Baseline** | 97.30% (36/37) | 0.9762 | 0.9706 | 0.9727 | 0.0268 | Deterministic rule (`num_fail > 0 and num_pass == 0 -> correct`); 1 False Positive |
| **StepGuard PRM (Recovered Neural)** | **100.0% (37/37)** | **1.0000** | **1.0000** | **1.0000** | **0.0000** | Full composite synergy resolving multi-operator crashes |

#### Crucial Disagreement Case Study: Step #33
The single disagreement between the execution heuristic baseline and the ground truth occurs on Step #33 (`eval_004` / `eval_004_sol_004` / `block_06`):
- **Gold Label**: `uncertain`
- **Execution Heuristic**: `correct` (False Positive)
- **StepGuard PRM**: `uncertain` ($P(\text{correct}) = 0.0002$)
- **Root Cause**: The step had two applicable mutations (`comparison_swap` and `off_by_one`). The `comparison_swap` produced a standard `AssertionError` (`FAIL`), while `off_by_one` caused an unhandled `IndexError` (`RUNTIME_ERROR`). Under Stage 1.3 derivation rules, an unhandled exception does not constitute a valid semantic test failure, requiring an assignment of `uncertain`. The heuristic baseline failed to distinguish an exception crash from a test assertion failure. The neural PRM, leveraging its exception and mutation affordance features, correctly identified the step as `uncertain`.

---

## 4. Scientific Significance: Heuristic Agreement vs. Semantic Correctness

> [!CAUTION]
> **CRITICAL SCIENTIFIC DISTINCTION**:
> The reproduced 100.0% accuracy and 1.0000 macro F1 metrics represent **exact agreement with the historical mutation-derived heuristic labels**, **NOT semantic correctness**.

1. **Origin of Ground-Truth Labels**: The labels in `verifier_labels.jsonl` were produced by the automated derivation script `partner_a/evidence/derive_verifier_labels.py` operating on dynamic execution mutation records. They reflect mechanical reconciliation rules ($\ge 2$ test flips for multi-operator steps, 1/1 flip for single-operator steps, survivor classification).
2. **Absence of Independent Semantic Verification**: The ground-truth labels were **not** verified through exhaustive formal methods, proof assistants, or independent semantic audits.
3. **Semantics of `uncertain`**: Steps labeled `uncertain` do not necessarily contain buggy code. Rather, they designate steps where unit tests failed to kill all mutants (survivors) or where mutation tests caused runtime crashes. Many `uncertain` steps represent functionally sound code paired with weak or non-discriminative test assertions.
4. **Conclusion**: The neural PRM has successfully learned the empirical mutation-survival decision boundary with perfect fidelity on this partition. It must not be cited as a guarantee of true mathematical or semantic program correctness.

---

## 5. Preservation of Task F1 Findings: 101-Label Provenance Gap

This closeout report explicitly preserves and re-affirms all conclusions established in [`data/validation/f1_provenance_gap_closeout.md`](file:///c:/Users/balin/Desktop/StepGuard/data/validation/f1_provenance_gap_closeout.md) (commit `0a5877f`):

1. **The 101-Label Cohort Remains UNRESOLVED / PROVENANCE-GAPPED**: An authoritative specification, manifest, or list of record IDs defining a historical 101-sample cohort does not exist anywhere in the repository or its Git history.
2. **Emergent Dynamic Tally**: The number 101 was an emergent tally of steps assigned the `correct` label across the full dataset ($N=156$, with 101 `correct` and 55 `uncertain`), which was subsequently split into:
   - **81 `correct` steps** in the training partition (`verifier_train.jsonl`, $N=119$)
   - **20 `correct` steps** in the held-out evaluation partition (`verifier_eval.jsonl`, $N=37$)
3. **Prohibition on Reconstructive Engineering**: In compliance with scientific governance rules, no attempt was made to artificially construct a 101-item evaluation set by backfilling records, filtering files, or altering partition boundaries.

---

## 6. Gate C Scope & Governance Boundary

> [!IMPORTANT]
> **GATE C INVESTIGATION WAS NOT AUTHORIZED AND WAS NOT EXECUTED.**

- **Definition of Gate C**: A formal semantic-validity investigation analyzing whether the underlying StepGuard heuristic labels or PRM predictions represent genuine program semantics, AST validity, or true execution soundness.
- **Operational Status**: Gate C was explicitly excluded from the Task F2 recovery scope by Partner A review directives.
- **Governance Action**: Zero semantic re-annotations, zero human reviews of code logic, zero prompt modifications, and zero alternative labeling experiments were authorized, initiated, or executed.

---

## 7. Working-Tree Safety & Git Cleanliness Audit

In accordance with strict read-only governance instructions:

- **Active Working-Tree Status**: Completely clean. Zero active working-tree files or protected repo files were modified.
- **Protected Files**: All existing frozen artifacts in `data/`, `partner_a/`, `partner_b/`, and `tests/` remain untouched byte-for-byte.
- **Git State**:
  - Current branch: `partner-b-evaluation` (HEAD: `0a5877f`)
  - No commits were created (`git commit` was not run).
  - No pushes occurred (`git push` was not run).
  - Untracked files remain strictly quarantined to documentation records.

---

## 8. Isolated Recovery & Evaluation Environment Specification

To enable absolute reproducibility by third-party auditors or Partner A, the exact execution environment utilized during the Gate A and Gate B verification is specified below:

### 8.1 Runtime Specifications
- **Operating System**: Windows 11 Enterprise AMD64 (`MSC v.1943 64 bit`)
- **Python Version**: `3.12.10` (`tags/v3.12.10:0cc8128`, Apr 8 2025)
- **PyTorch**: `2.14.0+cpu`
- **Scikit-learn**: `1.9.1`
- **Joblib**: `1.6.0`
- **NumPy**: `2.5.2`
- **Execution Target**: Deterministic CPU execution (`torch.device("cpu")`, `torch.manual_seed(42)`, `np.random.seed(42)`)

### 8.2 Standalone Reproduction Procedure

To reproduce Gate A and Gate B without checking out branch `master` or modifying the current working tree, execute the following isolated Python invocation:

```powershell
# In PowerShell from repository root:
.\.venv\Scripts\python -c "
import json, subprocess, tempfile, sys
from pathlib import Path

# 1. Verify commit 5c59fe7 existence
commit = '5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1'
eval_raw = subprocess.check_output(['git', 'show', f'{commit}:data/evaluation/stage_1/verifier_eval.jsonl']).decode('utf-8')
eval_records = [json.loads(line) for line in eval_raw.strip().splitlines() if line.strip()]

with tempfile.TemporaryDirectory() as tmpdir:
    tmp = Path(tmpdir)
    ckpt = tmp / 'ckpt'
    ckpt.mkdir()
    (ckpt / 'config.json').write_bytes(subprocess.check_output(['git', 'show', f'{commit}:data/evaluation/stage_2/checkpoint/config.json']))
    (ckpt / 'model_weights.pt').write_bytes(subprocess.check_output(['git', 'show', f'{commit}:data/evaluation/stage_2/checkpoint/model_weights.pt']))
    (ckpt / 'extractor.joblib').write_bytes(subprocess.check_output(['git', 'show', f'{commit}:data/evaluation/stage_2/checkpoint/extractor.joblib']))

    pkg = tmp / 'partner_a' / 'verifier'
    pkg.mkdir(parents=True)
    (tmp / 'partner_a' / '__init__.py').write_text('', encoding='utf-8')
    (pkg / '__init__.py').write_text('', encoding='utf-8')
    for m in ['features.py', 'model.py', 'baselines.py', 'metrics.py']:
        (pkg / m).write_text(subprocess.check_output(['git', 'show', f'{commit}:partner_a/verifier/{m}']).decode('utf-8'), encoding='utf-8')

    sys.path.insert(0, str(tmp))
    from partner_a.verifier.model import StepGuardPRM
    from partner_a.verifier.metrics import evaluate_predictions

    prm = StepGuardPRM.load_checkpoint(ckpt, device='cpu')
    probs = prm.predict_proba(eval_records)
    preds = prm.predict(eval_records)
    metrics = evaluate_predictions([r['label'] for r in eval_records], preds, probs)

    print(f'Gate B Reproduction Verified: N={metrics[\"total_samples\"]}, Acc={metrics[\"accuracy_pct\"]}%, Macro F1={metrics[\"macro_metrics\"][\"f1\"]}, Brier={metrics[\"brier_score\"]}')
"
```

**Expected CLI Output**:
```
Gate B Reproduction Verified: N=37, Acc=100.0%, Macro F1=1.0, Brier=0.0
```

---

## 9. Conclusion & Release Authorization Request

Task F2 has achieved complete resolution:
- **Gate A**: Passed and verified across all 18 artifacts, checkpoint weights, and the 73-dimensional extractor.
- **Gate B**: Passed with exact reproduction of all evaluation metrics and class distributions.
- **Governance**: Provenance firmly tied to commit `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1`; F1 101-label provenance gap preserved; Gate C explicitly noted as unauthorized and not executed; working-tree integrity strictly maintained with zero commits or pushes.

**Action Required**:
This report is hereby submitted to **Partner A for final review and release authorization**.
