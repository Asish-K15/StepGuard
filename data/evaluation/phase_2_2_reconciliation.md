# Phase 2.2 Joint Reconciliation

## Scope

Phase 2.2 reconciles the independent Partner A and Partner B reviews of the larger-evaluation mutation evidence. Frozen pilot and larger-evaluation artifacts remain unchanged.

## Evidence integrity

- Raw mutation records: 76
- Unique mutation identities: 56
- Function/block duplicate identities: 20
- Raw execution results: 76
- Missing execution results: 0
- Extra execution results: 0
- Raw-record detection: 76/76
- Unique-identity detection: 56/56

The 20 identities represented at both function-level and block-level steps had consistent outcomes.

## Mutation outcomes

At the raw-record level:

- FAIL: 68
- RUNTIME_ERROR: 8
- PASS: 0

After deduplicating mutation identities:

- FAIL: 48
- RUNTIME_ERROR: 8
- PASS: 0

The 8 runtime errors occurred in `eval_004` and were associated with `off_by_one` mutations producing `IndexError`. No harness issue was observed.

## Eligibility coverage

Among the 60 baseline-passing candidates:

- Eligible: 20
- Ineligible: 40
- Eligibility rate: 33.33%

Mutation generation was concentrated in five evaluation problems:

- `eval_004`
- `eval_007`
- `eval_016`
- `eval_017`
- `eval_020`

## Joint assessment

The Partner A and Partner B reviews are consistent on mutation-record integrity, execution consistency, eligibility coverage, targeting, and runtime-error attribution.

Detection results apply to the generated mutation set evaluated in Phase 2.2. They should not be interpreted as a general defect-detection completeness claim.

Mutation coverage remains limited because only 20 of 60 baseline-passing candidates were currently mutation-eligible and generated mutations were concentrated in five problems.

## Artifact preservation

No frozen pilot or larger-evaluation artifacts were changed during reconciliation.

The mutation-generation pipeline remains unchanged.

Any additional mutation operators or controlled experiments should be treated separately from the frozen Phase 2.2 evaluation.
