# Phase 3 Coverage Experiments

## Scope

This note records controlled, exploratory mutation experiments conducted after
the frozen Phase 2.2 evaluation. These experiments do not modify the frozen
mutation pipeline, frozen eligibility artifact, or frozen evaluation results.

## Controlled `is` / `is not` experiment

The independent eligibility analysis was temporarily extended to recognize
`is` and `is not` comparisons.

The resulting experimental eligibility set increased from the frozen
20/60 eligible baseline-passing candidates to 25/60.

The corresponding experimental mutation set increased from 76 to 86 raw
mutation records. The 10 additional records came from `eval_013`.

For `eval_013`, all 10 experimental `is -> is not` mutation executions were
detected:

- 10 FAIL
- 0 PASS
- 10/10 detected

The 10 raw records represent two decomposition-level records for each of the
five candidates.

This is controlled evidence for the tested `is` mutation case; it is not a
general claim about all `is` / `is not` mutations.

## Controlled multiplication experiment

A separate exploratory experiment applied `* -> /` to multiplication
expressions in previously ineligible baseline-passing candidates.

The first experiment covered `eval_001` and `eval_002`:

- 10 mutation executions
- 10 FAIL
- 0 PASS
- 10/10 detected

A second experiment covered `eval_014`:

- 5 mutation executions
- 5 RUNTIME_ERROR
- 0 PASS
- 5/5 detected

Combined multiplication experiment:

- 15 mutation executions
- 10 FAIL
- 5 RUNTIME_ERROR
- 0 PASS
- 15/15 detected

The runtime-error outcomes in the `eval_014` experiment were observed
mutation outcomes, not evidence of a harness failure.

## Controlled `in` / `not in` experiment

A separate exploratory experiment applied `in -> not in` to the two
previously ineligible `eval_007` candidates containing a membership test.

The experiment produced:

- 2 mutation executions
- 2 RUNTIME_ERROR
- 0 FAIL
- 0 PASS
- 2/2 detected

Both mutations changed only the intended `in` operator. Both produced
`KeyError: 60` at `return memo[n]` when the mutated condition prevented the
memoization branch from handling the requested key.

This is controlled evidence for the tested `in -> not in` case and the
specific `eval_007` tests; it is not a general claim about membership
mutation effectiveness.

## Interpretation

These experiments show that additional mutation operators can produce
executable and detected mutations in candidates excluded by the frozen
Phase 2.2 eligibility rules.

However, the experiments are limited to the specific operators, candidates,
and test suites examined. They should therefore be treated as coverage
evidence rather than as evidence of general mutation-operator effectiveness.

The frozen Phase 2.2 artifacts remain unchanged. The experimental JSONL files
remain separate from the frozen evaluation artifacts.

## Current Phase 3 coverage inventory

Among the 40 baseline-passing but ineligible candidates in the frozen
eligibility analysis, the independently observed unsupported operator
inventory includes:

- Mult: 22 candidates
- Add: 9 candidates
- FloorDiv: 9 candidates
- Pow: 7 candidates
- Sub: 7 candidates
- Is: 5 candidates
- In: 2 candidates

These categories overlap at the candidate level and therefore must not be
summed.

The multiplication experiments now cover all 22 of the 22 candidates
containing multiplication.

Across these experiments there are 32 mutation targets:

- 10 FAIL
- 22 RUNTIME_ERROR
- 0 PASS
- 32/32 detected

The 22 candidates therefore have experimental coverage, but these results
remain limited to the tested `* -> /` operator and the specific candidate
test suites.

## Status

Phase 3 evidence collection remains exploratory and read-only with respect to
the frozen evaluation. No mutation-pipeline or frozen-artifact change is
proposed by this note.
