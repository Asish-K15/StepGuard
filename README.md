# StepGuard

StepGuard is a research project for evaluating generated program solutions through step-level decomposition and mutation-based evidence.

## Current Pilot

The pilot evaluates:

- 5 MBPP problems
- 25 generated candidate solutions
- 25 baseline-passing candidates
- 99 evaluated mutations

All 25 baseline candidates passed the available problem tests.

Of the 99 evaluated mutations:

- 86 were detected
- 13 were undetected
- Overall mutation detection rate: 86.87%

## Mutation Types

| Mutation type | Count | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| boolean_flip | 11 | 3 | 8 | 27.27% |
| comparison_swap | 74 | 69 | 5 | 93.24% |
| off_by_one | 14 | 14 | 0 | 100.00% |

## Step-Level Evidence

The mutation evidence was grouped into 77 step-level groups:

- 64 fully detected
- 8 partially detected
- 5 undetected

Two recurring undetected survivor patterns were identified:

1. `mbpp_003`: `comparison_swap` changing `==` to `!=` in `block_08` remained undetected across five generated solutions.
2. `mbpp_004`: `boolean_flip` changing `or` to `and` in the LCS boundary condition remained undetected across four generated solutions.

## Evidence Artifacts

Pilot evidence is stored under `data/`:

- `data/mutations/mutation_execution_results.jsonl`
- `data/evidence/step_evidence.jsonl`
- `data/evidence/step_analysis.jsonl`
- `data/evidence/pilot_findings.json`
- `data/evidence/mutation_type_analysis.json`
- `data/evidence/undetected_mutation_analysis.json`
- `data/evidence/survivor_classification.json`
- `data/evidence/pilot_summary.json`
- `data/evidence/pilot_report.md`
- `data/evidence/pilot_limitations.md`
- `data/evidence/pilot_manifest.json`

## Reproducibility

From the repository root, run:

    python -m pytest -q

The current test suite contains 127 passing tests.

Run the reproducibility check with:

    python partner_a\evidence\validate_pilot_reproducibility.py

Expected output:

    Pilot reproducibility validation: PASS
    Manifest consistency: PASS
    Evidence paths: PASS

## Generation Setup

The baseline candidate generation used:

`Qwen qwen2.5-coder:7b`

## Limitations

This is an exploratory pilot over a small evaluated dataset. Its results should not be treated as a general estimate of StepGuard performance beyond the evaluated dataset.

Natural next research steps include:

- expanding the number of MBPP problems
- increasing the number of generated candidates
- evaluating additional mutation operators
- strengthening tests around observed survivor patterns
- repeating the analysis on a larger dataset

## Current Status

The pilot evidence, analysis, reporting, manifest, and reproducibility validation layers are implemented and covered by the automated test suite.
