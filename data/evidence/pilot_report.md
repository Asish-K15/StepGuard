# StepGuard Pilot Report

## Pilot scope

- Problems: 5
- Generated candidates: 25
- Baseline-passing candidates: 25
- Baseline pass rate: 100.00%

## Mutation results

- Mutations evaluated: 99
- Detected mutations: 86
- Undetected mutations: 13
- Overall mutation detection rate: 86.87%

## Mutation-type results

| Mutation type | Count | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| boolean_flip | 11 | 3 | 8 | 27.27% |
| comparison_swap | 74 | 69 | 5 | 93.24% |
| off_by_one | 14 | 14 | 0 | 100.00% |

## Step-level analysis

- Step groups analyzed: 77
- Fully detected: 64
- Partially detected: 8
- Undetected: 5

## Undetected survivor patterns

- **mbpp_003**: comparison_swap `==->!=`; location(s): block_08; line(s): 12; 5 solution(s). The mutation changes the final RGB branch condition from equality to inequality and remains undetected by the pilot tests.
- **mbpp_004**: boolean_flip `or->and`; location(s): block_05, func_01; line(s): 9, 10, 11; 4 solution(s). The mutation changes the LCS boundary condition from an OR chain to a mixed AND/OR condition and remains undetected by the pilot tests.

## Interpretation

The pilot establishes a baseline mutation-detection result for the current five-problem, 25-candidate dataset. The results show that most generated mutations were detected, while a smaller set of survivors remained behaviorally equivalent under the current test suite. The survivor patterns identify concrete areas where stronger tests could provide additional discrimination.

This pilot is exploratory and should not be treated as a general estimate of StepGuard performance beyond the evaluated dataset.
