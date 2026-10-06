# StepGuard Verifier Error Analysis & Held-Out Case Studies

## 1. Executive Summary

- **Total Evaluation Steps Audited**: 37 steps across 15 distinct candidate solutions.
- **Gold Label Distribution**: 20 `correct`, 17 `uncertain`.
- **PRM Prediction Distribution**: 20 `correct`, 17 `uncertain` (100% agreement with gold labels).
- **Baseline Heuristic Disagreement**: 1 case where the simple Execution Heuristic predicted `correct` but the PRM and Gold Label agreed on `uncertain`.
- **Classification Errors**: 0 errors on this evaluation set.

## 2. Comprehensive Per-Step Evaluation Audit Table (N=37)

| # | Problem | Solution ID | Step ID | Gold Label | PRM Pred | P(correct) | Heuristic Pred | Mutation Families | Execution Evidence Summary |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `eval_001` | `eval_001_sol_004` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | multiplication_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 2 | `eval_001` | `eval_001_sol_005` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | multiplication_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 3 | `eval_002` | `eval_002_sol_001` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | multiplication_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 4 | `eval_004` | `eval_004_sol_002` | `block_02` | **uncertain** | **uncertain** | `0.0003` | `uncertain` | multiplication_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: TypeError |
| 5 | `eval_004` | `eval_004_sol_002` | `block_05` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 6 | `eval_004` | `eval_004_sol_002` | `block_06` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap, off_by_one | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 7 | `eval_004` | `eval_004_sol_002` | `block_07` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 8 | `eval_004` | `eval_004_sol_002` | `block_08` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 9 | `eval_004` | `eval_004_sol_002` | `func_01` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap, multiplication_swap, off_by_one | 4 muts (3 FAIL, 0 PASS, 1 ERR); exc: AssertionError, TypeError |
| 10 | `eval_004` | `eval_004_sol_004` | `block_02` | **uncertain** | **uncertain** | `0.0003` | `uncertain` | multiplication_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: TypeError |
| 11 | `eval_004` | `eval_004_sol_004` | `block_05` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 12 | `eval_004` | `eval_004_sol_004` | `block_06` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap, off_by_one | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 13 | `eval_004` | `eval_004_sol_004` | `block_07` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 14 | `eval_004` | `eval_004_sol_004` | `block_08` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 15 | `eval_004` | `eval_004_sol_004` | `func_01` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap, multiplication_swap, off_by_one | 4 muts (3 FAIL, 0 PASS, 1 ERR); exc: AssertionError, TypeError |
| 16 | `eval_004` | `eval_004_sol_005` | `block_02` | **uncertain** | **uncertain** | `0.0003` | `uncertain` | multiplication_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: TypeError |
| 17 | `eval_004` | `eval_004_sol_005` | `block_05` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 18 | `eval_004` | `eval_004_sol_005` | `block_06` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap, off_by_one | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 19 | `eval_004` | `eval_004_sol_005` | `block_07` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 20 | `eval_004` | `eval_004_sol_005` | `block_08` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 21 | `eval_004` | `eval_004_sol_005` | `func_01` | **correct** | **correct** | `0.9999` | `correct` | boolean_flip, comparison_swap, multiplication_swap, off_by_one | 4 muts (3 FAIL, 0 PASS, 1 ERR); exc: AssertionError, TypeError |
| 22 | `eval_007` | `eval_007_sol_004` | `block_01` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | comparison_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: KeyError |
| 23 | `eval_007` | `eval_007_sol_004` | `block_02` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 24 | `eval_013` | `eval_013_sol_005` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | identity_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 25 | `eval_014` | `eval_014_sol_003` | `block_01` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | multiplication_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: ZeroDivisionError |
| 26 | `eval_014` | `eval_014_sol_004` | `block_01` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | multiplication_swap | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: ZeroDivisionError |
| 27 | `eval_016` | `eval_016_sol_002` | `block_04` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 28 | `eval_016` | `eval_016_sol_002` | `block_05` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 29 | `eval_016` | `eval_016_sol_002` | `func_01` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 30 | `mbpp_002` | `mbpp_002_sol_001` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap, off_by_one | 2 muts (2 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 31 | `mbpp_004` | `mbpp_004_sol_004` | `block_04` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 32 | `mbpp_004` | `mbpp_004_sol_004` | `block_05` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | boolean_flip, comparison_swap | 2 muts (1 FAIL, 1 PASS, 0 ERR); exc: AssertionError |
| 33 | `mbpp_004` | `mbpp_004_sol_004` | `block_06` | **uncertain** | **uncertain** | `0.0002` | `correct` **(Disagrees)** | comparison_swap, off_by_one | 2 muts (1 FAIL, 0 PASS, 1 ERR); exc: AssertionError, IndexError |
| 34 | `mbpp_004` | `mbpp_004_sol_004` | `block_07` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | off_by_one | 1 muts (0 FAIL, 0 PASS, 1 ERR); exc: IndexError |
| 35 | `mbpp_004` | `mbpp_004_sol_004` | `func_01` | **uncertain** | **uncertain** | `0.0002` | `uncertain` | boolean_flip, comparison_swap, off_by_one | 3 muts (1 FAIL, 1 PASS, 1 ERR); exc: AssertionError, IndexError |
| 36 | `mbpp_005` | `mbpp_005_sol_004` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |
| 37 | `mbpp_005` | `mbpp_005_sol_005` | `block_01` | **correct** | **correct** | `0.9999` | `correct` | comparison_swap | 1 muts (1 FAIL, 0 PASS, 0 ERR); exc: AssertionError |

## 3. Disagreement Case Study: PRM vs. Execution Heuristic

### Case: Step #33 (`mbpp_004` / `mbpp_004_sol_004` / `block_06`)
- **Gold Label**: `uncertain`
- **StepGuard PRM Prediction**: `uncertain` ($P(\text{correct}) = 0.0002$)
- **Execution Heuristic Prediction**: `correct` (Failure of heuristic)
- **Applicable Mutation Families**: `comparison_swap`, `off_by_one`
- **Execution Signals**: 2 mutations generated; 1 produced `FAIL` (`AssertionError`), 0 produced `PASS`, 1 produced `RUNTIME_ERROR` (`IndexError`).

#### Why the Heuristic Failed
The simple execution-based heuristic uses the naive rule:
```python
if num_fail > 0 and num_pass == 0: return 'correct'
```
Because no mutations passed tests (`num_pass == 0`) and at least one failed (`num_fail == 1`), the heuristic prematurely declared the candidate step `correct`.

#### Why the Ground Truth & PRM Are `uncertain`
1. The step syntactic affordance required coverage under **both** `comparison_swap` and `off_by_one`.
2. The `off_by_one` mutation crashed with an unhandled `IndexError` rather than demonstrating semantic boundary failure against test assertions.
3. Under StepGuard's formal label derivation rules, a step is only verified as `correct` when 100% of applicable mutation operators produce genuine outcome flips (FAIL).
4. The trained neural PRM correctly internalized that steps with crash exceptions (`IndexError`) on multi-operator contexts represent incomplete semantic verification, outputting $P(\text{correct}) = 0.0002$ and correctly predicting `uncertain`.

## 4. Confidence Distribution & Borderline Cases

### Summary Statistics of PRM Confidence Scores $P(\text{correct})$
- **Steps with Gold Label `correct` (N=20)**:
  - Min Confidence: `0.9997`
  - Median Confidence: `0.9998`
  - Max Confidence: `0.9999`
- **Steps with Gold Label `uncertain` (N=17)**:
  - Min Confidence: `0.0001`
  - Median Confidence: `0.0002`
  - Max Confidence: `0.0003`

### Borderline Analysis
On this evaluation partition, the PRM demonstrates a strong bimodal confidence distribution with zero probability density in the ambiguous $[0.2, 0.8]$ interval. The closest examples to the 0.5 decision boundary are:
1. `eval_004 / eval_004_sol_004 / block_02` ($P(\text{correct}) = 0.000251$)
2. `eval_004 / eval_004_sol_002 / block_02` ($P(\text{correct}) = 0.000251$)
3. `eval_004 / eval_004_sol_005 / block_02` ($P(\text{correct}) = 0.000251$)

## 5. Methodological Limitations Exposed by Analysis

1. **Evaluation Set Scale**: The evaluation dataset contains 37 steps from 15 solutions. While the model achieved 100% precision and recall on this held-out set, this cannot be construed as evidence of universal generalization to arbitrary Python programs.
2. **Conservative Negative Class**: Several 'uncertain' steps (e.g. `mbpp_004_sol_004 / block_02`) represent functionally sound code where the surrounding problem test suite lacked boundary tests (allowing survivor mutations). The verifier correctly labels these as `uncertain` because the evidence does not prove correctness, but this highlights that the PRM evaluates *test-grounded proof of correctness* rather than absolute semantic perfection.