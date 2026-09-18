# StepGuard Phase 2.2 Evaluation Synthesis

## 1. Evaluation Scope

The larger evaluation covers 20 selected MBPP problems and 100 generated candidate solutions, with five candidates per problem.

- Problems: 20
- Candidates: 100
- Baseline-passing candidates: 60
- Baseline pass rate: 60.0%

## 2. Baseline Result

The larger evaluation produced:

| Result | Count |
|---|---:|
| PASS | 60 |
| FAIL | 39 |
| RUNTIME_ERROR | 1 |
| Total | 100 |

The 60.0% baseline pass rate is lower than the 100.0% pass rate observed in the five-problem pilot.

## 3. Mutation Generation Coverage

Mutation generation was applied to the 60 baseline-passing candidates.

- Passing candidates with mutations: 20
- Passing candidates without mutations: 40
- Mutation-generation coverage: 33.3%
- Generated mutation records: 76

The eligibility analysis found that the 20 mutation-producing candidates exactly matched the 20 candidates containing targets recognized by the current mutation rules.

Therefore, the 100.0% mutation detection result applies only to the mutations that were eligible and actually generated.

## 4. Mutation Detection

The larger evaluation generated and executed 76 mutations.

| Result | Count |
|---|---:|
| Detected | 76 |
| Undetected | 0 |
| Detection rate | 100.0% |

Mutation execution produced 68 FAIL results and 8 RUNTIME_ERROR results. Runtime errors are counted as detected because the mutated program did not pass the test execution.

## 5. Detection by Mutation Type

| Mutation type | Total | Detected | Undetected |
|---|---:|---:|---:|
| boolean_flip | 10 | 10 | 0 |
| comparison_swap | 44 | 44 | 0 |
| off_by_one | 22 | 22 | 0 |
| Total | 76 | 76 | 0 |

Every generated mutation was detected across all three mutation types represented in the larger evaluation.

## 6. Detection by Problem

| Problem | Total | Detected | Undetected |
|---|---:|---:|---:|
| eval_004 | 41 | 41 | 0 |
| eval_007 | 4 | 4 | 0 |
| eval_016 | 15 | 15 | 0 |
| eval_017 | 6 | 6 | 0 |
| eval_020 | 10 | 10 | 0 |
| Total | 76 | 76 | 0 |

The 76 mutations were concentrated in five of the 20 evaluated problems.

## 7. Pilot Comparison

The pilot contained 99 mutations, of which 86 were detected and 13 were undetected.

| Scope | Mutations | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| Pilot | 99 | 86 | 13 | 86.87% |
| Larger evaluation | 76 | 76 | 0 | 100.0% |

The pilot's 13 undetected mutations were concentrated entirely in two problems:

| Pilot problem | Mutation type | Detected | Undetected |
|---|---|---:|---:|
| mbpp_003 | comparison_swap | 25 | 5 |
| mbpp_004 | boolean_flip | 0 | 8 |

All other pilot problem/type combinations had zero undetected mutations.

The larger evaluation used a different set of five problems for mutation generation and therefore did not include these two pilot survivor cases.

## 8. Interpretation

The larger evaluation provides broader validation of the StepGuard pipeline than the five-problem pilot. It shows that, within this 20-problem evaluation and under the current mutation-generation rules, all 76 generated mutations were detected.

However, the 100.0% detection rate should not be interpreted as evidence of universally adequate test coverage. Only 20 of the 60 baseline-passing candidates were mutation-eligible under the current rules, and those candidates generated the 76 evaluated mutations.

The difference between the pilot's 86.87% detection rate and the larger evaluation's 100.0% rate also cannot be attributed to evaluation scale alone. The mutation populations differ, and the larger evaluation does not contain the two pilot problems responsible for the 13 surviving mutants.

The pilot survivors remain relevant evidence of test-adequacy limitations. Prior review found the five MBPP-003 comparison-swap survivors and eight MBPP-004 boolean-flip survivors to be legitimate non-equivalent mutants associated with specific gaps in the existing tests.

## 9. Phase 2.2 Conclusion

The Phase 2.2 results support the following bounded conclusion:

> The larger 20-problem evaluation successfully exercised the StepGuard pipeline beyond the initial five-problem pilot. Among the 60 baseline-passing candidates, 20 were eligible for the current mutation operators and produced 76 mutations. All 76 generated mutations were detected. This demonstrates successful mutation generation and detection for the evaluated mutation population, but does not establish that all possible mutations, all candidate solutions, or all program defects would be detected. The pilot's 13 legitimate surviving mutants remain an important qualification because they demonstrate that the supplied tests can leave non-equivalent mutations undetected.

## 10. Limitations

- The evaluation contains 20 selected MBPP problems and 100 generated candidates and is not representative of all programming problems or generated programs.
- Only 60 of the 100 candidates passed the baseline tests.
- Only 20 of those 60 passing candidates were eligible under the current mutation rules.
- Mutation detection was evaluated only for the 76 mutations actually generated.
- The mutation population differs between the pilot and larger evaluation.
- The larger evaluation does not include the two pilot problems containing the 13 surviving mutants.
- Detection is measured against the supplied MBPP tests; surviving mutations can therefore reflect test-coverage limitations.
- Runtime errors are treated as detected mutation outcomes.
