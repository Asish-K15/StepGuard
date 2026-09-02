# StepGuard Pilot Limitations and Next Steps

## Scope limitations

The current pilot evaluates five MBPP problems and 25 generated candidate
solutions. All 25 baseline candidates passed the available problem tests.

The mutation analysis contains 99 evaluated mutations. Of these, 86 were
detected and 13 remained undetected, giving an overall mutation detection
rate of 86.87%.

These results describe the current pilot dataset only. They should not be
treated as a general estimate of StepGuard performance across larger or
different datasets.

## Mutation-type variation

Detection varied substantially by mutation type:

| Mutation type | Count | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| boolean_flip | 11 | 3 | 8 | 27.27% |
| comparison_swap | 74 | 69 | 5 | 93.24% |
| off_by_one | 14 | 14 | 0 | 100.00% |

The pilot therefore shows that mutation type is an important dimension for
interpreting mutation-detection results.

## Undetected survivors

Thirteen mutations survived the current test suites.

Two recurring survivor patterns were identified:

1. `mbpp_003`: a `comparison_swap` changing `==` to `!=` in `block_08`
   remained undetected across five generated solutions.
2. `mbpp_004`: a `boolean_flip` changing `or` to `and` in the LCS boundary
   condition remained undetected across four generated solutions.

These observations identify concrete cases where the current tests do not
distinguish the original and mutated behavior.

## Step-level observations

The mutation evidence was grouped into 77 step-level groups:

- 64 fully detected
- 8 partially detected
- 5 undetected

The five completely undetected step groups correspond to the surviving
`mbpp_003` mutations identified above.

## Next research steps

The current evidence supports several natural follow-up directions:

- expand the number of MBPP problems,
- increase the number of generated candidate solutions,
- evaluate additional mutation operators,
- strengthen tests around observed survivor patterns,
- and repeat the analysis on a larger dataset before drawing broader
  conclusions.

The present pilot provides an initial empirical baseline for these future
evaluations rather than a final performance characterization.
