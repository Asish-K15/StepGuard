# StepGuard Stage 1.3 Independent Semantic Review — Partner B

## 1. Review Scope & Identity

- **Review Date**: 2026-09-26
- **Reviewer**: Partner B Pipeline & Decomposition Specialist (Independent Second Reviewer)
- **Review Objective**: Independent verification of Stage 1.3 mutation targeting, AST decomposition boundaries, semantic validity, and verifier-label suitability across formal Stage 1.3 evidence.
- **Input Artifacts**:
  - `data/evaluation/mutations/step_evidence_is.jsonl` (158 records)
  - `data/evaluation/mutations/mutation_execution_results_is.jsonl` (158 records)
  - `data/evaluation/mutations/mutation_records_is.jsonl` (158 records)
  - `data/evaluation/stage_1/mutation_eligibility_is.json` (49 eligible / 60 baseline-passing)
  - `partner_b/mutation/mutator.py` & `partner_b/integration/pipeline.py`

---

## 2. Independent Audit Methodology & Sample Selection

To ensure genuine independent verification rather than mirroring Partner A's sample, Partner B drew an independent audit sample of **35 distinct `(problem_id, solution_id, step_id)` identities** (comprising 41 raw mutation execution records).

The sample intentionally focuses on:
1. **100% of Stage 1.3 Identity Mutations**: All 10 `identity_swap` identities in `eval_013` (solutions `sol_001` through `sol_005`, across both `func_01` and `block_01`) to inspect AST token offset targeting and predicate inversion.
2. **Alternative LLM Solution Variants**: Solutions `sol_002`, `sol_003`, `sol_004`, and `sol_005` across `eval_001`, `eval_002`, `eval_004`, `eval_007`, `eval_012`, `eval_014`, `eval_016`, `eval_017`, `eval_020` to verify structural variance across LLM outputs.
3. **Multi-Mutation Steps vs. Single-Mutation Steps**: Steps with multiple concurrent operators (`eval_004` `func_01`, `block_05`, `block_06`) versus steps with exactly one operator.
4. **All Exception Modes**: Examining the 38 runtime crashes (`TypeError`, `IndexError`, `KeyError`, `ZeroDivisionError`) versus assertion failures (`FAIL`).

---

## 3. Audited Step Identities (35 Distinct Identities / 41 Records)

| # | Problem | Solution | Step ID | Mutation Family | Operator Change | Outcome | Diagnostic / Stderr | Decomposition Assessment |
|---|---|---|---|---|---|---|---|---|
| 1 | `eval_013` | `eval_013_sol_001` | `func_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Single-expr function body |
| 2 | `eval_013` | `eval_013_sol_001` | `block_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 3 | `eval_013` | `eval_013_sol_002` | `func_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Single-expr function body |
| 4 | `eval_013` | `eval_013_sol_002` | `block_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 5 | `eval_013` | `eval_013_sol_003` | `func_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Single-expr function body |
| 6 | `eval_013` | `eval_013_sol_003` | `block_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 7 | `eval_013` | `eval_013_sol_004` | `func_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Single-expr function body |
| 8 | `eval_013` | `eval_013_sol_004` | `block_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 9 | `eval_013` | `eval_013_sol_005` | `func_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Single-expr function body |
| 10 | `eval_013` | `eval_013_sol_005` | `block_01` | `identity_swap` | `is` -> `is not` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 11 | `eval_004` | `eval_004_sol_002` | `func_01` | `comparison_swap`<br>`boolean_flip`<br>`off_by_one`<br>`multiplication_swap` | `==` -> `!=`<br>`and` -> `or`<br>`+` -> `-`<br>`*` -> `/` | FAIL<br>FAIL<br>FAIL<br>RUNTIME_ERROR | `AssertionError`<br>`AssertionError`<br>`AssertionError`<br>`TypeError: unsupported operand /: 'list', 'int'` | Compound function step (4 mutations generated) |
| 12 | `eval_004` | `eval_004_sol_002` | `block_02` | `multiplication_swap` | `*` -> `/` | RUNTIME_ERROR | `TypeError: unsupported operand /: 'list', 'int'` | DP table allocation: `[0] * n` |
| 13 | `eval_004` | `eval_004_sol_002` | `block_05` | `comparison_swap`<br>`boolean_flip` | `==` -> `!=`<br>`and` -> `or` | FAIL<br>FAIL | `AssertionError`<br>`AssertionError` | Length-2 base match block |
| 14 | `eval_004` | `eval_004_sol_002` | `block_06` | `comparison_swap`<br>`off_by_one` | `==` -> `!=`<br>`+` -> `-` | FAIL<br>FAIL | `AssertionError`<br>`AssertionError` | Match transition block |
| 15 | `eval_004` | `eval_004_sol_003` | `block_07` | `off_by_one` | `-` -> `+` | RUNTIME_ERROR | `IndexError: list index out of range` | Boundary array indexing |
| 16 | `eval_004` | `eval_004_sol_004` | `block_07` | `off_by_one` | `-` -> `+` | RUNTIME_ERROR | `IndexError: list index out of range` | Boundary array indexing |
| 17 | `eval_007` | `eval_007_sol_002` | `func_01` | `comparison_swap` | `in` -> `not in` | RUNTIME_ERROR | `KeyError: 60` | Full recurrence function |
| 18 | `eval_007` | `eval_007_sol_002` | `block_01` | `comparison_swap` | `in` -> `not in` | RUNTIME_ERROR | `KeyError: 60` | Cache membership test |
| 19 | `eval_007` | `eval_007_sol_004` | `block_01` | `comparison_swap` | `in` -> `not in` | RUNTIME_ERROR | `KeyError: 60` | Cache membership test |
| 20 | `eval_007` | `eval_007_sol_005` | `block_01` | `comparison_swap` | `in` -> `not in` | RUNTIME_ERROR | `KeyError: 60` | Cache membership test |
| 21 | `eval_001` | `eval_001_sol_002` | `func_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Full tuple product function |
| 22 | `eval_001` | `eval_001_sol_002` | `block_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 23 | `eval_002` | `eval_002_sol_003` | `func_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Full multiply function |
| 24 | `eval_002` | `eval_002_sol_003` | `block_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 25 | `eval_012` | `eval_012_sol_004` | `func_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Full nonagonal formula |
| 26 | `eval_012` | `eval_012_sol_004` | `block_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Duplicate of func_01 span |
| 27 | `eval_014` | `eval_014_sol_003` | `func_01` | `multiplication_swap` | `*` -> `/` | RUNTIME_ERROR | `ZeroDivisionError: division by zero` | Full 4th power sum func |
| 28 | `eval_014` | `eval_014_sol_003` | `block_01` | `multiplication_swap` | `*` -> `/` | RUNTIME_ERROR | `ZeroDivisionError: division by zero` | Duplicate of func_01 span |
| 29 | `eval_016` | `eval_016_sol_002` | `func_01` | `comparison_swap` | `<=` -> `>` | FAIL | `AssertionError` | Full binary search func |
| 30 | `eval_016` | `eval_016_sol_002` | `block_04` | `comparison_swap` | `==` -> `!=` | FAIL | `AssertionError` | Mid-element equality check |
| 31 | `eval_016` | `eval_016_sol_002` | `block_05` | `comparison_swap` | `<` -> `>=` | FAIL | `AssertionError` | Partition boundary check |
| 32 | `eval_017` | `eval_017_sol_003` | `func_01` | `off_by_one`<br>`multiplication_swap` | `+` -> `-`<br>`*` -> `/` | FAIL<br>FAIL | `AssertionError`<br>`AssertionError` | Full difference function |
| 33 | `eval_017` | `eval_017_sol_003` | `block_01` | `multiplication_swap` | `*` -> `/` | FAIL | `AssertionError` | Linear sum formula step |
| 34 | `eval_020` | `eval_020_sol_004` | `func_01` | `comparison_swap` | `==` -> `!=` | FAIL | `AssertionError` | Full parity function |
| 35 | `eval_020` | `eval_020_sol_004` | `block_01` | `comparison_swap` | `==` -> `!=` | FAIL | `AssertionError` | Duplicate of func_01 span |

---

## 4. Independent Technical Observations & Findings

### Observation 1: AST Token Targeting in `mutate_identity`
Partner B specifically verified `partner_b/mutation/mutator.py`:
- `_find_identity_mutation` utilizes `tokenize.generate_tokens` bounded by AST `ast.Compare` coordinates.
- In `eval_013_sol_001` through `eval_013_sol_005`:
  `return any(item is None for item in tup)`
  The tokenizer accurately isolated token `is` at Line 2, Column 20, replacing it with `is not`.
- The mutated code parses cleanly through `ast.parse` and produces valid Python bytecode.
- **Targeting Verdict**: 100% verified. No variable names, string literals, or docstrings are misidentified as operators.

### Observation 2: Semantic Significance of `identity_swap`
- In Python, `is None` checks pointer equality against the unique singleton `NoneType`.
- Swapping `is` to `is not` flips the truth table for every item in the input tuple.
- The unit test `assert check_none((7, 8, 9, 11, 14)) == False` fails immediately because `any(item is not None ...)` evaluates to `True`.
- **Semantic Verdict**: Genuine, high-value semantic perturbation testing exact specification conformity.

### Observation 3: Execution Runtime Errors (38 Total Records)
Partner B investigated the 38 runtime errors:
1. `TypeError` (10 records in `eval_004`):
   Target: `dp = [[0] * n for _ in range(n)]` mutated to `[[0] / n ...]`.
   *Analysis*: While syntactically valid in Python AST (`ast.BinOp(op=ast.Div())`), division is illegal for sequence replication. This causes an immediate type exception.
2. `IndexError` (10 records in `eval_004`):
   Target: `dp[i][j - 1]` mutated to `dp[i][j + 1]`.
   *Analysis*: When `j = n - 1`, index `j + 1` exceeds allocated matrix dimensions. Direct consequence of off-by-one error.
3. `KeyError` (8 records in `eval_007`):
   Target: `if n in memo:` mutated to `if n not in memo:`.
   *Analysis*: Skips recursive computation and attempts to fetch an unmemoized key. Valid semantic invariant breakdown.
4. `ZeroDivisionError` (10 records in `eval_014`):
   Target: `2*i` mutated to `2/i` inside generator `for i in range(n)`.
   *Analysis*: At `i = 0`, evaluation raises zero division. Valid arithmetic domain violation.
- **Runtime Error Verdict**: All 38 runtime errors are legitimate execution-grounded failure signals arising directly from mutated operations, with zero harness or execution harness anomalies.

### Observation 4: The Function/Block Duplication Issue
- In 6 evaluation problems (`eval_001`, `eval_002`, `eval_012`, `eval_013`, `eval_014`, `eval_020`), the generated candidate solutions are one-line or single-expression functions.
- For these solutions, `func_01` (lines 1..2) and `block_01` (lines 1..2) represent the exact same AST node span.
- Naively treating `func_01` and `block_01` as independent step entities inflates record counts (e.g. 10 records for 5 solutions in `eval_013`).
- **Partner B Directive**: For downstream verifier label generation, steps where `func_01` and `block_01` have identical line spans MUST be deduplicated by `(solution_id, mutation_type, mutated_code)` or mapped to a unified step representation.

---

## 5. Critical Verification of PRD Label Derivation Compatibility

Partner B independently evaluated whether the planned PRD label derivation rule can be applied to the current evidence:

> **PRD Rule**:
> - `outcome_flip` true across >=2 mutation types on the same step => `correct`
> - `outcome_flip` false across all applicable mutations => `uncertain`
> - `RUNTIME_ERROR` dominant => `uncertain`

### Critical Structural Finding:
- In `step_evidence_is.jsonl`, out of 130 distinct `(problem_id, solution_id, step_id)` identities:
  - **112 steps have exactly 1 mutation type applicable**;
  - **13 steps have 2 mutation types applicable**;
  - **5 steps have 4 mutation types applicable**.
- **Why?** `partner_b/integration/pipeline.py` attempts all 5 mutation functions on each step, but most simple steps syntactically contain only ONE operator category (e.g. only `is`, only `*`, or only `==`).
- **Consequence**: If ">=2 mutation types" is interpreted as requiring 2 distinct mutation types to exist on that specific step, **112 out of 130 steps would be disqualified from receiving a `correct` label**, regardless of how definitively the single mutation killed the mutant!
- **Resolution**:
  - The PRD rule must be interpreted contextually: for steps that support multiple operators, >=2 mutation types must flip outcome.
  - For single-operator steps (where only 1 mutation type is syntactically possible), a verified outcome flip across all applicable mutation types (1/1) must be recognized as valid evidence of correctness for that operator, OR the step must be marked according to single-operator flip criteria.
  - This nuance must be formally documented in the joint reconciliation.

---

## 6. Disagreements / Additions to Partner A Review

1. **Agreement on Core Execution**: Partner B fully agrees with Partner A that targeting is 100% accurate, detection is 158/158, and `identity_swap` is a valid semantic operator.
2. **Disagreement / Clarification on Label Derivation**:
   Partner A noted that evidence is sufficient for labeling. Partner B clarifies: **Evidence is sufficient, BUT the labeling derivation engine must handle steps where only 1 mutation type is applicable**, rather than naively demanding >=2 mutation types for code steps that contain only one operator.
3. **Deduplication Enforcement**:
   Partner B mandates that deduplication of single-statement `func_01`/`block_01` pairs must occur during dataset compilation so that verifier training loss is not skewed by identical duplicates.

---

## 7. Independent Partner B Decision

### **DECISION: GO (CONDITIONAL)**

Partner B approves the Stage 1.3 semantic validity review with the following binding conditions for downstream label derivation:

1. **Condition 1 (Deduplication)**: Identical `func_01`/`block_01` step representations in single-statement functions must be deduplicated before verifier training.
2. **Condition 2 (Operator Applicability Rule)**: Step correctness labeling must account for steps with only 1 applicable operator family, preventing artificial disqualification of 112 valid step identities.
3. **Condition 3 (Type Exception Awareness)**: `TypeError` resulting from `[0] * n` -> `[0] / n` in `eval_004` must be explicitly tagged as a type error rather than an algorithmic assertion failure in verifier metadata.

With these conditions recorded, the semantic validity gate is **PASSED**.
