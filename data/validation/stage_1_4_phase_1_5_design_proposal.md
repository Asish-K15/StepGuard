# StepGuard Stage 1.4 Phase 1.5 Design Proposal: Coverage-Aware Pipeline Integration & Review Gate

> [!IMPORTANT]
> **PLANNING-ONLY PROPOSAL & APPROVAL GATE NOTICE**:
> - **Author**: Partner B (System Architect & Independent Technical Reviewer)
> - **Date**: 2026-09-28
> - **Status**: Pre-Implementation Planning Proposal (Documentation Only)
> - **Repository**: `StepGuard` (`C:\Users\ashis\Desktop\StepGuard`)
> - **Target Path**: `data/validation/stage_1_4_phase_1_5_design_proposal.md`
> - **Commit Gate**: Phase 1 was committed as `ccc7ac1443507b4cdbf9bc761da85e9709323014` on branch `partner-b-evaluation`.
> - **Approval Constraint**: This document constitutes a design proposal. **No Phase 1.5 code, tests, schemas, or pipelines may be implemented, modified, staged, committed, or pushed until Partner A and Partner B explicitly approve the scope.**

---

## 1. Executive Summary & Review Gate Context

Stage 1.4 Phase 1 successfully established the non-destructive telemetry foundation:
1. Process-isolated candidate execution tracing with process-level timeout enforcement (`partner_b/execution/tracer.py`).
2. Child-process `sys.settrace` containment ensuring parent test runner isolation.
3. AST statement reachability mapping for both `FunctionStep` and `BlockStep` decompositions (`partner_b/evidence/coverage.py`).
4. Unified 6-outcome execution taxonomy (`shared/schema.py`).
5. Zero regressions across 205 total tests (191 pre-existing + 14 Phase 1 tests).
6. Proven SHA-256 byte-for-byte legacy reproducibility in isolated tempdirs (`tests/test_stage_1_4_legacy_compat.py`).

### The Scope Gap in Prior Planning Materials
In the approved Stage 1.4 master design proposal ([`data/validation/stage_1_4_design_proposal.md`](file:///c:/Users/ashis/Desktop/StepGuard/data/validation/stage_1_4_design_proposal.md)), Section 6 formally specified **Phase 1**, and Sections 2–5 established the broad four-tier architectural vision. However, **the master document did not define an explicitly numbered "Phase 1.5"**.

To maintain rigorous configuration management and avoid ungrounded scope creep, this proposal:
1. Formalizes the review gate for Partner A on Phase 1 closeout.
2. Identifies the architectural gap between raw Phase 1 modules and end-to-end evidence generation.
3. Formulates three bounded, defensible scope options for Phase 1.5, recommending **Option A (Coverage-Aware Mutation Pipeline Integration)** as the most direct dependency.

---

## 2. Partner A Review Checklist for Phase 1 Closeout

Partner A must audit and sign off on the Phase 1 implementation against the following criteria:

| Checklist Item | Implementation File | Verification Standard | Partner B Audit Finding |
|:---|:---|:---|:---:|
| **1. Shared Schema Correctness & Compatibility** | [`shared/schema.py`](file:///c:/Users/ashis/Desktop/StepGuard/shared/schema.py) | Additive-only. `CoverageStatus`, `ExecutionOutcome`, `StepCoverage`, `ExecutionTrace` schemas added. Pre-existing dataclasses (`Evidence`, `MutationInput`, `MutationStatus`, `ExecutionResult`) unaltered. | **VERIFIED** |
| **2. Subprocess Isolation & Timeout Handling** | [`partner_b/execution/tracer.py`](file:///c:/Users/ashis/Desktop/StepGuard/partner_b/execution/tracer.py) | Executes via `subprocess.run([sys.executable, "-m", ...], timeout=...)`. Infinite loops (`while True: pass`) terminate cleanly. `TimeoutExpired` caught; returns `ExecutionOutcome.TIMEOUT` with `returncode=None`. No `proc.kill()` calls on completed objects. | **VERIFIED** |
| **3. Trace Containment & Cleanup** | [`partner_b/execution/tracer.py`](file:///c:/Users/ashis/Desktop/StepGuard/partner_b/execution/tracer.py) | `sys.settrace` executed exclusively in child process wrapped in `try ... finally: sys.settrace(None)`. Parent `sys.gettrace()` verified identical before and after invocation. | **VERIFIED** |
| **4. Outcome Taxonomy & Crash Resilience** | [`partner_b/execution/tracer.py`](file:///c:/Users/ashis/Desktop/StepGuard/partner_b/execution/tracer.py) | Parameterized test validates 6 outcomes: `PASS`, `ASSERTION_FAILURE`, `RUNTIME_EXCEPTION`, `SYNTAX_ERROR`, `TIMEOUT`, and `INFRASTRUCTURE_FAILURE` (resilient to `os._exit(139)`). | **VERIFIED** |
| **5. AST Reachability & Line Attribution** | [`partner_b/evidence/coverage.py`](file:///c:/Users/ashis/Desktop/StepGuard/partner_b/evidence/coverage.py) | Line numbers clamped to candidate code $[1, L_{\text{cand}}]$. Docstrings, blank lines, and comments excluded. Shared lines across nested hierarchies (`func_01` and `block_05`) supported. Intra-block steps verified disjoint. | **VERIFIED** |
| **6. Legacy Compatibility & Baseline Preservation** | [`tests/test_stage_1_4_legacy_compat.py`](file:///c:/Users/ashis/Desktop/StepGuard/tests/test_stage_1_4_legacy_compat.py) | End-to-end legacy pipeline regenerated into isolated tempdir. SHA-256 hashes of `step_evidence.jsonl`, `step_analysis.jsonl`, and `pilot_findings.json` strictly match committed baseline artifacts. | **VERIFIED** |
| **7. Known Limitations Formally Noted** | [`partner_b/evidence/coverage.py`](file:///c:/Users/ashis/Desktop/StepGuard/partner_b/evidence/coverage.py) | Scope is strictly **statement/executed-line reachability, NOT full branch or boolean condition coverage**. Single-statement multi-line AST nodes attribute to statement start line unless sub-expressions emit distinct bytecode events. | **VERIFIED** |

---

## 3. Bounded Scope Options for Phase 1.5

Because Phase 1.5 was not predefined in Stage 1.4 materials, three bounded scope options are presented for joint decision:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
 prospective Phase 1.5 Scope Options
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Option A (Recommended): Coverage-Aware Mutation Pipeline Integration                   │
│   • Connect Phase 1 tracer and coverage mapper to the mutation evaluation runner.       │
│   • Before applying mutations to a step, evaluate baseline reachability.               │
│   • If step is UNEXECUTED (e.g. Task 783 block_08), flag as INSUFFICIENT_COVERAGE      │
│     and bypass redundant mutation runs, recording enriched execution evidence.         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Option B: Task-Level Specification Oracles & Defect Harness (Tier 1 & Tier 2)          │
│   • Author task-level specification test suites in data/problems/augmented/ for       │
│     Task 747 (LCS boundary), Task 783 (HSV blue sector), and Task 790 (even_position). │
│   • Implement candidate defect validator to catch KNOWN_DEFECTIVE solutions            │
│     (specifically reproducing SG-VAL-017 candidate failure on [2, 2, 4]).             │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Option C: Decoupled Four-Tier Label Derivation Engine (Tier 4)                         │
│   • Implement partner_b/evidence/derivation.py implementing the 4-tier truth table     │
│     (TEST_SUPPORTED_CORRECT, INCONCLUSIVE_SURVIVOR, INSUFFICIENT_COVERAGE,             │
│     PIPELINE_FALSE_POSITIVE).                                                          │
│   • Process existing or enriched evidence into decoupled label reports.                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Recommendation
**Partner B recommends Option A (Coverage-Aware Mutation Pipeline Integration)** as the natural next step. Option A connects the standalone Phase 1 execution/coverage modules to the actual evidence dataset generation without yet altering benchmark test inputs or rewriting the label derivation formulas. Option B can subsequently provide the augmented test inputs that Option A's pipeline executes.

---

## 4. Detailed Specification for Phase 1.5 (Option A: Coverage-Aware Pipeline)

### 4.1 Objectives & Rationale
1. **Bridge the Telemetry Gap**: Currently, `partner_b/execution/tracer.py` and `partner_b/evidence/coverage.py` exist as standalone library modules verified by unit tests. They are not yet invoked during batch mutation execution.
2. **Prevent Wastage on Unreached Steps**: In Stage 0A–1.3, mutations were blind; 4 mutations were executed on `block_08` of Task 783 even though `block_08` was never reached by the test suite, generating 4 false "survivor" records. Phase 1.5 evaluates baseline reachability *before* mutation, immediately classifying unreached steps as `INSUFFICIENT_COVERAGE`.
3. **Generate Enriched Evidence**: Emit an opt-in enriched evidence schema that records step reachability status alongside mutation pass/fail outcomes.

### 4.2 In-Scope Work
1. **Module Creation**:
   - `partner_b/execution/coverage_runner.py`: Orchestrates candidate execution, computes step-level coverage for all steps of a solution, and runs mutations conditionally based on reachability.
   - `partner_b/evidence/enriched_evidence.py`: Serializes enriched evidence records containing:
     - `problem_id`, `solution_id`, `step_id`, `decomposition_type`
     - `coverage_status`: `COVERED`, `PARTIALLY_COVERED`, `UNEXECUTED`
     - `executable_lines`, `executed_lines`, `line_coverage_ratio`
     - `baseline_outcome`: `ExecutionOutcome` of original unmutated candidate
     - `mutation_records`: List of mutation execution outcomes (only evaluated if step is executed)
2. **Opt-in Pipeline CLI**:
   - Add CLI interface or runner script `partner_b/evaluation/run_coverage_mutations.py` gated behind `--enable-coverage-tracing`.
3. **Unit & Integration Tests**:
   - Verify unreached steps bypass mutation execution and receive `INSUFFICIENT_COVERAGE`.
   - Verify executed steps run standard mutations and capture both trace telemetry and mutation outcomes.

### 4.3 Out-of-Scope Work (Strictly Deferred to Later Phases)
- **Modifying Benchmark Problem Files**: `data/problems/mbpp_001.json`–`mbpp_005.json` remain untouched.
- **Authoring Specification Test Augmentations**: Deferred to Phase 2 (or Option B).
- **Altering Legacy Runners**: `partner_a/execution/harness.py`, `partner_a/evaluation/run_mutations.py`, and `partner_b/evidence/build_evidence.py` remain untouched.
- **Model Inference or PRM Training**: No PRM scoring or training.
- **Overwriting Frozen Evidence**: Baseline files in `data/evidence/*` remain immutable. Enriched evidence will be written to a distinct directory (`data/evidence_stage_1_4/` or test tempdirs).

---

## 5. Architecture & Data Flow (Phase 1.5 Option A)

```
                    Candidate Source Code + Benchmark Tests
                                      │
                                      ▼
                        [ tracer.py: Subprocess ]
                                      │
                         ExecutionTrace (Baseline)
                                      │
                                      ▼
                        [ coverage.py: AST Map ]
                                      │
                       StepCoverage (per step in AST)
                                      │
             ┌────────────────────────┴────────────────────────┐
             ▼                                                 ▼
[ coverage_status == UNEXECUTED ]              [ coverage_status != UNEXECUTED ]
             │                                                 │
   Skip Mutation Execution                            Execute Targeted Mutations
   Status: INSUFFICIENT_COVERAGE                      via tracer.py
             │                                                 │
             └────────────────────────┬────────────────────────┘
                                      │
                                      ▼
                     [ enriched_evidence.py ]
                                      │
                      enriched_step_evidence.jsonl
```

---

## 6. Proposed Test Matrix & Acceptance Criteria

### 6.1 Test Matrix

| Test ID | Target File / Function | Input Scenario | Expected Outcome |
|:---|:---|:---|:---|
| **TC-1.5-01** | `test_coverage_runner.py::test_unexecuted_step_bypasses_mutations` | MBPP Task 783 (`mbpp_003_sol_001`), `block_08` (`elif mx == b:`) under original tests | 1. Baseline trace records `block_08` as `UNEXECUTED`.<br>2. Zero child mutation subprocesses spawned for `block_08`.<br>3. Enriched record records `coverage_status == UNEXECUTED`. |
| **TC-1.5-02** | `test_coverage_runner.py::test_covered_step_executes_mutations` | MBPP Task 783, `block_05` (`if mx == mn:`) under original tests | 1. Baseline trace records `block_05` as `COVERED`.<br>2. Mutations for `block_05` execute in child subprocesses.<br>3. Mutation pass/fail captured alongside coverage ratio `1.0`. |
| **TC-1.5-03** | `test_coverage_runner.py::test_baseline_crash_aborts_mutations` | Candidate with syntax or runtime error in baseline | 1. Baseline trace records `SYNTAX_ERROR` or `RUNTIME_EXCEPTION`.<br>2. All downstream step mutations aborted.<br>3. Solution marked `BASELINE_FAILED`. |
| **TC-1.5-04** | `test_enriched_evidence.py::test_schema_serialization` | Diverse step coverage and mutation outcomes | Validates JSON serialization, field completeness, and deserialization into dataclasses. |
| **TC-1.5-05** | `test_stage_1_4_legacy_compat.py` | Full test suite regression check | All 205 existing tests continue to pass with 0 regressions. |

### 6.2 Acceptance Criteria
1. **Selective Mutation Execution**: The runner executes zero mutations on steps whose baseline coverage is `UNEXECUTED`.
2. **Opt-In Safety**: Executing the pipeline without `--enable-coverage-tracing` or running legacy scripts (`partner_a/evaluation/run_mutations.py`) invokes legacy Stage 1.3 behavior verbatim.
3. **Artifact Immutability**: All files in `data/evidence/` remain byte-for-byte identical.
4. **Zero Test Regressions**: The entire test suite passes ($205 + N_{\text{new}}$ tests).

---

## 7. Open Questions & Decision Items for Partner A

Before implementation of Phase 1.5 can begin, Partner A must review and decide:

1. **Scope Selection**:
   - Does Partner A approve **Option A** (Coverage-Aware Mutation Pipeline Integration)?
   - Or does Partner A prefer **Option B** (Task-Level Specification Oracles & Defect Harness) or **Option C** (Decoupled Derivation Engine) first?
2. **Storage Location for Enriched Telemetry**:
   - Should Phase 1.5 output be written to `data/evidence_stage_1_4/enriched_step_evidence.jsonl`, or kept strictly inside test tempdirs until Stage 1.4 is finalized?
3. **Mutation Execution Granularity**:
   - Should `PARTIALLY_COVERED` steps execute mutations on all statements, or only on the statements whose line numbers were dispatched (`step.executed_lines`)?

---

## 8. Approval Gate

> [!CAUTION]
> **GATE REQUIREMENT**:
> Partner B will remain in a **holding state**. No source code files will be created or modified, no tests will be added, and no git staging or commits will be performed until Partner A formally responds with:
> 1. Approval of Phase 1 closeout.
> 2. Selected scope for Phase 1.5 (Option A, B, or C).
> 3. Resolution of the open decision items in Section 7.
