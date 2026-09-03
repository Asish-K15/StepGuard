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

The pilot evaluated three mutation types:

| Mutation type | Count | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| boolean_flip | 11 | 3 | 8 | 27.27% |
| comparison_swap | 74 | 69 | 5 | 93.24% |
| off_by_one | 14 | 14 | 0 | 100.00% |

## Step-Level Evidence

The pilot mutation evidence was grouped into 77 step-level groups:

- 64 fully detected
- 8 partially detected
- 5 undetected

Two recurring undetected survivor patterns were identified:

1. `mbpp_003`: `comparison_swap` changing `==` to `!=` in `block_08` remained undetected across five generated solutions.
2. `mbpp_004`: `boolean_flip` changing `or` to `and` in the LCS boundary condition remained undetected across four generated solutions.

These survivor patterns motivated closer examination of test adequacy and remain part of the pilot evidence.

## Pilot Evidence Artifacts

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

## Larger Evaluation

The larger evaluation expands the pilot to:

- 20 MBPP problems
- 100 generated candidate solutions
- 60 baseline-passing candidates
- 76 generated and executed mutations

### Baseline Results

- 60 candidates passed
- 39 candidates failed
- 1 candidate produced a runtime error
- Baseline pass rate: 60.0%

The larger evaluation therefore did not reproduce the pilot's 100.0% baseline candidate pass rate.

### Mutation-Generation Coverage

Among the 60 baseline-passing candidates:

- 20 produced at least one mutation
- 40 produced no mutation under the current mutation-generation rules
- Mutation-generation coverage: 33.3%

This means the mutation detection result applies only to candidates for which the current mutation-generation rules produced valid mutations.

### Mutation Detection Results

The larger evaluation generated and executed 76 mutations:

- 76 detected
- 0 undetected
- Detection rate among generated mutations: 100.0%

The 100.0% result should therefore be interpreted as:

> All mutations generated and executed under the current mutation-generation rules were detected by the available tests.

It does not establish complete mutation coverage, complete bug detection, or that all possible mutations would be detected.

## Larger Evaluation Mutation Types

| Mutation type | Count | Detected | Undetected | Detection rate |
|---|---:|---:|---:|---:|
| boolean_flip | 10 | 10 | 0 | 100.00% |
| comparison_swap | 44 | 44 | 0 | 100.00% |
| off_by_one | 22 | 22 | 0 | 100.00% |

## Pilot vs. Larger Evaluation

| Metric | Pilot | Larger evaluation |
|---|---:|---:|
| Problems | 5 | 20 |
| Candidates | 25 | 100 |
| Baseline passes | 25 | 60 |
| Baseline pass rate | 100.0% | 60.0% |
| Mutations | 99 | 76 |
| Detected mutations | 86 | 76 |
| Undetected mutations | 13 | 0 |
| Detection rate | 86.87% | 100.0%* |

\* Detection rate is calculated among mutations actually generated and executed. Mutation-generation coverage among baseline-passing candidates in the larger evaluation was 33.3%.

The larger evaluation increased the problem and candidate scope substantially, while showing that the pilot's perfect baseline candidate pass rate did not persist at larger scale.

The larger evaluation also produced a different mutation profile: fewer mutations were generated overall because only 20 of the 60 baseline-passing candidates produced mutations under the current mutation-generation rules.

## Larger Evaluation Evidence Artifacts

The larger-evaluation evidence is stored under `data/evaluation/`:

- `data/evaluation/selection_manifest.json`
- `data/evaluation/problems/`
- `data/evaluation/solutions/candidates.jsonl`
- `data/evaluation/solutions/baseline_results.jsonl`
- `data/evaluation/mutations/mutation_records.jsonl`
- `data/evaluation/mutations/mutation_execution_results.jsonl`
- `data/evaluation/evaluation_summary.json`
- `data/evaluation/pilot_evaluation_comparison.json`
- `data/evaluation/evaluation_report.md`

The selection manifest records the deterministic selection seed, excluded pilot task IDs, split counts, and selected evaluation problems.

## Reproducibility

From the repository root, run:

    python -m pytest -q

The current test suite contains 170 passing tests.

Pilot reproducibility can be checked with:

    python partner_a\evidence\validate_pilot_reproducibility.py

Pilot reproducibility validation: PASS

The evaluation pipeline consists of:

1. MBPP problem selection
2. Candidate generation
3. Baseline execution
4. Mutation generation for baseline-passing candidates
5. Mutation execution
6. Evidence aggregation
7. Pilot/evaluation comparison
8. Research-facing report generation

The larger evaluation uses deterministic problem selection. The selection configuration and selected task IDs are recorded in:

    data/evaluation/selection_manifest.json

## Generation Setup

Candidate generation used:

`Qwen qwen2.5-coder:7b`

The model was run through the local Ollama generation setup.

## Research Interpretation

The pilot demonstrated that mutation-based evidence can expose weaknesses in the available tests. In particular, recurring mutation survivors were localized to specific decomposed steps and mutation types.

The larger evaluation provides a stronger validation point than the initial five-problem pilot. It shows that the pilot's 100.0% baseline candidate pass rate did not persist when the evaluation was expanded to 20 problems and 100 candidates.

For the mutations actually generated under the current mutation rules, all 76 larger-evaluation mutations were detected.

However, only 20 of the 60 baseline-passing candidates produced mutations. Therefore, the current evidence supports a narrower conclusion:

> StepGuard successfully detected all mutations generated in the larger evaluation under its current mutation-generation rules, while mutation-generation coverage remains an important limitation for broader claims.

The results do not establish that StepGuard detects all possible defects in generated programs.

## Limitations

The overall study remains an exploratory pilot.

Important limitations include:

- The larger evaluation contains 20 selected MBPP problems and 100 generated candidates; it is not a representative sample of all programming problems or generated programs.
- Only 60 of the 100 candidates passed the baseline tests.
- Only 20 of those 60 passing candidates produced mutations under the current mutation-generation rules.
- The evaluation currently uses three mutation operators: `comparison_swap`, `boolean_flip`, and `off_by_one`.
- Mutation-generation coverage is therefore incomplete.
- Detection is measured against the supplied MBPP tests, so an undetected defect may reflect insufficient test coverage rather than program correctness.
- A runtime error is counted as detected because the mutated program did not pass the test execution.
- The 100.0% larger-evaluation mutation detection rate applies only to generated and executed mutations.
- The results should not be treated as a general estimate of bug-detection effectiveness.
- The current evaluation does not establish that the three mutation operators are sufficient to represent the space of meaningful program defects.

## Natural Next Steps

Potential next steps include:

1. Expand the number of evaluation problems.
2. Increase the number and diversity of generated candidates.
3. Improve mutation-generation coverage for baseline-passing candidates.
4. Add additional mutation operators.
5. Strengthen tests for mutation survivors.
6. Investigate whether mutation survivors consistently identify weaknesses in the underlying test suites.
7. Repeat the evaluation on additional datasets or problem distributions.

## Current Status

The StepGuard pilot and larger evaluation pipeline are implemented.

The repository currently contains:

- deterministic evaluation-problem selection
- generated candidate solutions
- baseline execution
- step-level decomposition
- mutation generation
- mutation execution
- pilot evidence
- larger-evaluation evidence
- pilot/evaluation comparison
- research-facing reports
- reproducibility validation
- automated tests covering the implemented pipeline

The current evidence supports continued investigation of step-level mutation-based evaluation while keeping mutation-generation coverage and broader generalization as explicit limitations.