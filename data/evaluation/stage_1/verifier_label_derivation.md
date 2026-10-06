# StepGuard Verifier Label Derivation Report

## 1. Executive Summary

- **Derivation Stage**: Stage 1.3 Joint Reconciled Pipeline
- **Target Status**: **PASS** (>= 150 labeled steps)
- **Total Canonical Labeled Steps**: **156**
- **Raw Evidence Records Aggregated**: 257 (Pilot: 99, Evaluation: 158)
- **Single-Statement Duplicates Collapsed**: 51
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
| **`correct`** | **101** | **64.7%** |
| **`uncertain`** | **55** | **35.3%** |
| **Total Canonical Steps** | **156** | **100.0%** |

### Evidence Contribution
| Source | Raw Records | Canonical Steps | Correct | Uncertain |
|---|---:|---:|---:|---:|
| **Evaluation (`eval_*`)** | 158 | 94 | 70 | 24 |
| **Pilot (`mbpp_*`)** | 99 | 62 | 31 | 31 |
| **Total** | **257** | **156** | **101** | **55** |

### 80/20 Solution-Grouped Split
| Split | Canonical Steps | Solutions | Correct | Uncertain | Leakage |
|---|---:|---:|---:|---:|---:|
| **Train (80%)** | 119 (76.3%) | 59 | 81 | 38 | 0 |
| **Eval (20%)** | 37 (23.7%) | 15 | 20 | 17 | 0 |
| **Total** | **156** | **74** | **101** | **55** | **0** |

---

## 4. Mutation Families Covered

| Mutation Family | Canonical Step Occurrences |
|---|---:|
| `comparison_swap` | 100 |
| `multiplication_swap` | 40 |
| `off_by_one` | 35 |
| `boolean_flip` | 20 |
| `identity_swap` | 5 |

---

## 5. Artifact Preservation & Reproducibility

The following verified artifacts were produced without modifying frozen historical datasets:
- `data\evaluation\stage_1\verifier_labels.jsonl`
- `data\evaluation\stage_1\verifier_train.jsonl`
- `data\evaluation\stage_1\verifier_eval.jsonl`
- `data\evaluation\stage_1\verifier_label_summary.json`

Regenerate at any time using:
```powershell
.\.venv\Scripts\python partner_a/evidence/derive_verifier_labels.py
```
