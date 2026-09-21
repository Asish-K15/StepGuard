# StepGuard Phase 4 Final Research Synthesis

## 1. Study Scope

StepGuard evaluates generated program solutions using step-level decomposition
and mutation-based evidence.

The study consists of an initial five-problem pilot and a larger 20-problem
evaluation. The larger evaluation contains 100 generated candidate solutions,
with five candidates per problem.

The final synthesis distinguishes frozen evaluation evidence from subsequent
exploratory Phase 3 coverage experiments.

## 2. Baseline Evaluation

The larger evaluation produced:

| Result | Count |
|---|---:|
| PASS | 60 |
| FAIL | 39 |
| RUNTIME_ERROR | 1 |
| Total | 100 |

The baseline pass rate was therefore 60.0%.

The five-problem pilot had a 100.0% baseline candidate pass rate. The larger
evaluation therefore did not reproduce the pilot's baseline result.

## 3. Frozen Mutation Evaluation

Among the 60 baseline-passing candidates in the larger evaluation:

- 20 were eligible under the frozen mutation-generation rules.
- 40 were ineligible.
- Mutation-generation coverage among baseline-passing candidates was 33.3%.
- 76 mutation records were generated and executed.

All 76 generated mutations were detected:

| Mutation type | Total | Detected | Undetected |
|---|---:|---:|---:|
| boolean_flip | 10 | 10 | 0 |
| comparison_swap | 44 | 44 | 0 |
| off_by_one | 22 | 22 | 0 |
| **Total** | **76** | **76** | **0** |

At the raw-record level, mutation execution produced 68 FAIL results and
8 RUNTIME_ERROR results. The 76 raw records corresponded to 56 unique
mutation identities because 20 identities appeared at both function and block
decomposition levels. After deduplication, the outcomes were 48 FAIL and
8 RUNTIME_ERROR.

The 8 runtime errors occurred in `eval_004` and were associated with
`off_by_one` mutations producing `IndexError`. No harness issue was observed.

The 20 mutation-producing candidates exactly matched the candidates
identified as eligible by the independent eligibility analysis.

## 4. Interpretation of Frozen Detection Results

The frozen Phase 2.2 result supports the bounded conclusion that all mutations
generated and executed under the current mutation-generation rules were
detected in the 20-problem evaluation.

The 100.0% detection rate does not establish complete mutation coverage,
complete defect detection, or detection of all possible mutations.

Mutation-generation coverage is an important qualification: only 20 of the
60 baseline-passing candidates produced mutations under the current rules.

Mutation generation was also concentrated in five evaluation problems:
`eval_004`, `eval_007`, `eval_016`, `eval_017`, and `eval_020`.

## 5. Pilot Survivor Evidence

The five-problem pilot contained 99 mutations, of which 86 were detected and
13 were undetected.

The 13 surviving mutations were concentrated in two problems:

- `mbpp_003`: five `comparison_swap` survivors.
- `mbpp_004`: eight `boolean_flip` survivors.

Independent review classified these survivor patterns as legitimate
non-equivalent mutants associated with specific gaps in the available tests.

These survivors are important qualification evidence because they demonstrate
that the supplied tests can leave non-equivalent mutations undetected.

The larger evaluation used a different problem set and therefore did not
contain these two pilot survivor cases.

## 6. Phase 3 Exploratory Coverage

After the frozen Phase 2.2 evaluation, controlled exploratory experiments
examined additional mutation operators without modifying the frozen mutation
pipeline or frozen evaluation artifacts.

### `is -> is not`

The experimental eligibility analysis increased from 20/60 to 25/60 eligible
baseline-passing candidates when `is` and `is not` comparisons were included.

The resulting experiment produced 10 additional mutation records from
`eval_013`:

- 10 FAIL
- 0 PASS
- 10/10 detected

This is controlled evidence for the tested `is` mutation case, not a general
claim about all identity mutations.

### `* -> /`

Multiplication experiments covered all 22 previously identified ineligible
baseline-passing candidates containing multiplication.

Across the experiments:

- 32 mutation executions
- 10 FAIL
- 22 RUNTIME_ERROR
- 0 PASS
- 32/32 detected

The runtime-error outcomes were observed mutation outcomes rather than
evidence of a harness failure.

These experiments provide coverage evidence for the tested multiplication
mutation and candidate test suites; they do not establish general mutation
effectiveness.

### `in -> not in`

Two previously ineligible `eval_007` candidates were tested:

- 2 mutation executions
- 2 RUNTIME_ERROR
- 0 FAIL
- 0 PASS
- 2/2 detected

Both mutations changed only the intended membership operator and produced
`KeyError: 60` at `return memo[n]`.

This is controlled evidence for the tested membership case and its specific
tests.

### `** -> *`

Seven previously identified baseline-passing candidates containing `Pow`
were tested:

- 7 mutation executions
- 7 RUNTIME_ERROR
- 0 FAIL
- 0 PASS
- 7/7 detected

All seven mutations changed the intended `**` operator. `AssertionError`
appeared in stderr for the runtime-error outcomes.

This is controlled evidence for the tested power-mutation cases and their
specific test suites.

## 7. Phase 3 Interpretation

The Phase 3 experiments demonstrate that additional operator families can be
executed and detected in selected candidates that were excluded by the
frozen Phase 2.2 eligibility rules.

They should not be combined with the frozen 76-mutation detection rate as
though they were part of the same evaluation population.

The experiments remain limited to the specific operators, candidates, and
test suites examined. They therefore provide exploratory coverage evidence,
not a general estimate of mutation-operator effectiveness.

## 8. Overall Limitations

- The study evaluates 20 selected MBPP problems and 100 generated candidates;
  it is not representative of all programming problems or generated programs.
- Only 60 of the 100 candidates passed the baseline tests.
- Only 20 of those 60 passing candidates were eligible under the frozen
  mutation rules.
- The frozen mutation population contains only `comparison_swap`,
  `boolean_flip`, and `off_by_one`.
- Detection is measured against the supplied MBPP tests.
- An undetected mutation can therefore reflect insufficient test coverage.
- Runtime errors are counted as detected mutation outcomes.
- The pilot and larger evaluation contain different mutation populations and
  different problem sets.
- Phase 3 additional-operator experiments are exploratory and were not part
  of the frozen evaluation.
- The evidence does not establish universal mutation coverage or complete
  defect detection.

## 9. Overall Conclusion

The StepGuard evaluation demonstrates a reproducible pipeline for generating
candidate solutions, executing baseline tests, decomposing passing solutions,
generating mutations under explicit eligibility rules, and evaluating mutated
programs.

In the frozen 20-problem evaluation, 60 of 100 candidates passed the baseline
tests. Twenty of those 60 candidates were eligible for the current mutation
operators and produced 76 mutations. All 76 generated mutations were
detected.

The pilot provides an important complementary result: 13 mutations survived
the available tests, including recurring survivor patterns that were reviewed
as legitimate non-equivalent mutants. This shows why the larger evaluation's
100.0% detection result must remain conditional on its generated mutation
population and test suites.

Phase 3 exploratory experiments provide additional evidence that selected
unsupported operator families can also be exercised and detected. These
experiments expand the evidence about mutation-generation coverage but do
not alter the frozen Phase 2.2 result.

The resulting evidence supports continued investigation of step-level
mutation-based evaluation while keeping mutation-generation coverage,
operator scope, test adequacy, and broader generalization as explicit
limitations.
