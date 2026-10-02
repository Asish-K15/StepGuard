# StepGuard — F1 Provenance Gap Closeout Report

**Evaluation Task**: F1 (Mutation-Derived Correct Label Verification & Scoring)  
**Investigator**: Partner A  
**Status**: **BLOCKED / UNRESOLVED (Provenance Gap)**  
**Protocol Compliance**: Strict Multi-Agent Governance Protocol. Zero existing files modified, zero files staged/committed, zero reconstructions attempted, zero code/eval executions performed.

---

## 1. Executive Summary & Review Context

Evaluation task F1 relies on an assumed historical cohort of 101 mutation-derived `correct` labels. However, prior audits revealed that an authoritative specification or record-ID manifest for this cohort had not been located.

Pursuant to multi-agent governance protocols, Partner A performed an exhaustive, read-only provenance search across both the current repository working tree and the entire Git history. 

**Conclusion**: The authoritative 101-label cohort specification / record-ID manifest does **not** exist in the repository or Git history. Consequently, F1 evaluation is formally marked **BLOCKED / UNRESOLVED due to provenance gap**.

---

## 2. Exhaustive Search Scope & Provenance Audit

The read-only provenance search covered all branches, commits, reflogs, and trees in the repository:
1. **Repository Scope**:
   - Current working tree on branch `partner-b-evaluation` (HEAD: `66a5d6d`)
   - Branch `master` / `origin/master` (HEAD: `5c59fe7`)
   - Branch `main` / `origin/main` (HEAD: `114526b`)
   - All 50+ intermediate commits, tags, and forks from initial commit `114526b`.
2. **Identifier & Field Scans**:
   - Targeted queries for `"record_id"` and `"label_record_id"` yielded **0 occurrences** across all historical Git commits, trees, blobs, and working tree files.
3. **Query Term & Manifest Tracking**:
   - Exhaustive searches for `"101"`, `"correct"`, `"mutation"`, `"label"`, `"cohort"`, `"manifest"`, `"ground truth"`, `"ground_truth"`, `"mutation-derived"`, and `"correct labels"` identified only high-level summary narrative citations and downstream dynamic execution logs.
4. **Git Deletion History Audit**:
   - `git log --all --diff-filter=D --summary` confirmed that no dataset, manifest, or label file was ever deleted from the repository (the only historical deletions were two internal Python cache files in commit `ae23736`).

---

## 3. Historical Artifact Analysis: `data/evaluation/stage_1/verifier_labels.jsonl`

The search identified the primary historical origin of the "101" count in commit `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1` on branch `master`:

- **File Path**: `data/evaluation/stage_1/verifier_labels.jsonl`
- **Git Commit**: `5c59fe73bf4ddc7590bee61a28e1fc33ec3fa1d1` (Branch `master`; absent from the working tree on `partner-b-evaluation`)
- **Git Blob SHA**: `b433b28e5c6cde70dd28fb4a05591c345ff3984e`
- **SHA-256**: `6b06b4bcffd16d2f301a1ddb033f5b7a7c289af2ed5a625015e26037e6dd54e3`
- **Record Composition**: Exactly **156 total records**:
  - **`correct`**: 101 records (64.74%)
  - **`uncertain`**: 55 records (35.26%)
- **Data Schema**: Records are indexed strictly by AST syntactic location tuples (`problem_id`, `solution_id`, `step_id`, `step_type`, `line`, `column`).
- **Absence of Dedicated Identifiers**: The file contains **no** `record_id`, **no** `label_record_id`, and **no** cohort identifier tags.

---

## 4. Why the 101 Records Are an Emergent Label Count, Not an Authoritative Cohort

The 101 `correct` records in `verifier_labels.jsonl` cannot serve as an authoritative cohort specification for the following reasons:

1. **Emergent Dynamic Tally**: The number 101 was not a pre-registered benchmark cohort. It is the **emergent tally** produced when `partner_a/evidence/derive_verifier_labels.py` dynamically processed 257 raw execution evidence records (99 pilot + 158 evaluation), collapsed 51 duplicate single-statement steps into unified canonical steps, and applied Stage 1.3 reconciliation heuristics ($\ge 2$ flips for multi-operator steps, 1/1 flip for single-operator steps).
2. **Partition Bifurcation**: The 101 `correct` records were never managed as a cohesive, standalone cohort:
   - **81 records** were assigned to the training split (`data/evaluation/stage_1/verifier_train.jsonl`, $N=119$).
   - **20 records** were assigned to the held-out evaluation split (`data/evaluation/stage_1/verifier_eval.jsonl`, $N=37$).
3. **No Authoritative Manifest**: There is no existing specification document, mapping table, or manifest defining an authoritative 101-label cohort.

---

## 5. Why Other Candidate Artifacts Cannot Serve as the Authoritative 101-Label Manifest

| Candidate Artifact | Git Location | Record Count | Why It Cannot Serve as Authoritative 101-Label Manifest |
|:---|:---|:---:|:---|
| `data/evaluation/stage_1/verifier_train.jsonl` | Commit `5c59fe7` (`master`) | 119 | Incomplete subset (contains only 81 of the 101 `correct` records); training split only. |
| `data/evaluation/stage_1/verifier_eval.jsonl` | Commit `5c59fe7` (`master`) | 37 | Frozen held-out evaluation partition ($N=37$, containing 20 `correct` records); strictly forbidden from being accessed to fill provenance gaps. |
| `data/evaluation/stage_1/verifier_label_summary.json` | Commit `5c59fe7` (`master`) | 1 | Metadata tally reporting scalar totals (`"correct": 101`); contains zero record-level identifiers or step keys. |
| `data/evidence/pilot_manifest.json` | Working tree & commits | 1 | Pilot experiment metadata manifest; restricted to 5 problems, 25 candidates, and 99 raw mutation records. |
| `data/evaluation/selection_manifest.json` | Working tree & commits | 20 | Problem selection manifest specifying sanitized MBPP task allocations (`eval_001`–`eval_020`); contains zero step or label data. |
| `data/validation/blind_annotation_sheet.md` | Working tree & commits | 28 | Covers a distinct, fixed 28-sample cohort (`SG-VAL-001`–`SG-VAL-028`) with all mutation-derived labels explicitly stripped for blind human review. |

---

## 6. Formal Conclusion & F1 Operational Status

1. **Exact Cohort Membership Not Established**: The repository lacks an authoritative manifest or specification defining record-level membership for a historical 101-label cohort.
2. **Strict Prohibition on Reconstruction**: Deriving or reconstructing a 101-record cohort by filtering `verifier_labels.jsonl` on `label == "correct"`, re-running derivation scripts, or inferring membership from ordering, naming, or split counts is strictly prohibited by scientific governance rules.
3. **Held-Out Partition Protection**: The $N=37$ held-out evaluation set (`verifier_eval.jsonl`) remains strictly protected and cannot be utilized to backfill missing cohort definitions.
4. **Resulting F1 Status**: **BLOCKED / UNRESOLVED due to provenance gap**.
5. **Preservation of Diagnostics**: All pre-existing F1 diagnostic outputs, test suites, and historical artifacts remain completely untouched and preserved byte-for-byte.
