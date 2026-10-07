"""
StepGuard -> PRM Dataset Generator Module (Phase 2).

Implements deterministic dataset generation conforming strictly to the
StepGuard -> PRM Data Contract approved in Phase 1.

Supervision Terminology:
- POSITIVE_PROXY: High-confidence mutation/test-derived empirical supervision proxy
  (baseline PASS + mutation sensitivity + zero surviving mutations).
- NEGATIVE_PROXY: Mutation/test-derived empirical supervision proxy
  (synthetically mutated step causing test FAIL / killed mutant).
- SURVIVED: Ambiguous (equivalent mutants / weak tests), excluded from binary dataset.
- RUNTIME_ERROR: Quarantined mutation-induced execution crash, excluded from binary dataset.

Neither POSITIVE_PROXY nor NEGATIVE_PROXY represents universal semantic ground truth.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ProvenanceRecord:
    """Lineage and provenance metadata for a generated PRM record."""
    source_artifact: str
    source_split: str
    problem_id: str
    solution_id: str
    step_id: str
    line: Optional[int] = None
    column: Optional[int] = None
    mutation_type: Optional[str] = None
    execution_returncode: Optional[int] = None
    mutation_record_identity: str = ""


@dataclass
class PRMDatasetRecord:
    """
    Standardized Process Reward Model (PRM) dataset record.
    Conforms strictly to the Phase 1 StepGuard -> PRM Data Contract.
    """
    dataset_record_id: str
    problem_id: str
    solution_id: str
    step_id: str
    step_type: str
    prompt: str
    previous_context: str
    current_step_code: str
    binary_proxy_label: Optional[int]
    evidence_type: str
    provenance: ProvenanceRecord

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to JSON-serializable dictionary."""
        d = asdict(self)
        return d


@dataclass
class PRMDatasetConfig:
    """Configuration for deterministic dataset generation."""
    problems_dir: str = "data/evaluation/problems"
    pilot_problems_dir: str = "data/problems"
    eval_candidates_file: str = "data/evaluation/solutions/candidates.jsonl"
    eval_baseline_file: str = "data/evaluation/solutions/baseline_results.jsonl"
    eval_mutations_file: str = "data/evaluation/mutations/mutation_execution_results.jsonl"
    pilot_candidates_file: str = "data/solutions/candidates.jsonl"
    pilot_baseline_file: str = "data/solutions/baseline_results.jsonl"
    pilot_mutations_file: str = "data/mutations/mutation_execution_results.jsonl"
    random_seed: int = 42
    train_ratio: float = 0.68  # 17 of 25 problems
    val_ratio: float = 0.16    # 4 of 25 problems
    test_ratio: float = 0.16   # 4 of 25 problems
    include_pilot: bool = True


class PRMDatasetGenerator:
    """
    Deterministic StepGuard -> PRM Dataset Generator.
    
    Enforces:
    1. Problem-level split isolation (zero candidate/step/mutation row crossing).
    2. Zero future-step leakage in previous_context.
    3. Zero execution/mutation metadata leakage in model context.
    4. Deterministic record and mutation identities.
    5. Conservative SURVIVED exclusion and RUNTIME_ERROR quarantine.
    """

    def __init__(self, config: Optional[PRMDatasetConfig] = None, base_dir: Optional[str] = None):
        self.config = config or PRMDatasetConfig()
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def _resolve_path(self, rel_path: str) -> Path:
        p = Path(rel_path)
        if p.is_absolute():
            return p
        return self.base_dir / p

    def load_problems(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all problem definitions, normalizing schema discrepancies
        (e.g., pilot_id -> problem_id).
        """
        problems: Dict[str, Dict[str, Any]] = {}
        
        # 1. Evaluation problems
        eval_dir = self._resolve_path(self.config.problems_dir)
        if eval_dir.exists():
            for p_file in sorted(eval_dir.glob("*.json")):
                with open(p_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pid = data.get("problem_id") or data.get("pilot_id")
                    if pid:
                        problems[pid] = {
                            "problem_id": pid,
                            "prompt": data.get("prompt", ""),
                            "code": data.get("code", ""),
                            "test_list": data.get("test_list", []),
                            "test_imports": data.get("test_imports", []),
                            "source_file": data.get("source_file", str(p_file.name)),
                            "source_split": data.get("source_split", "evaluation"),
                            "source_artifact": str(p_file.relative_to(self.base_dir) if p_file.is_relative_to(self.base_dir) else p_file)
                        }

        # 2. Pilot problems (if enabled)
        if self.config.include_pilot:
            pilot_dir = self._resolve_path(self.config.pilot_problems_dir)
            if pilot_dir.exists():
                for p_file in sorted(pilot_dir.glob("*.json")):
                    with open(p_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        pid = data.get("problem_id") or data.get("pilot_id")
                        if pid and pid not in problems:
                            problems[pid] = {
                                "problem_id": pid,
                                "prompt": data.get("prompt", ""),
                                "code": data.get("code", ""),
                                "test_list": data.get("test_list", []),
                                "test_imports": data.get("test_imports", []),
                                "source_file": data.get("source_file", str(p_file.name)),
                                "source_split": data.get("source_split", "pilot"),
                                "source_artifact": str(p_file.relative_to(self.base_dir) if p_file.is_relative_to(self.base_dir) else p_file)
                            }

        return problems

    def load_candidates(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Load candidate solutions keyed by (problem_id, solution_id)."""
        candidates: Dict[Tuple[str, str], Dict[str, Any]] = {}

        candidate_files = [self.config.eval_candidates_file]
        if self.config.include_pilot:
            candidate_files.append(self.config.pilot_candidates_file)

        for c_rel in candidate_files:
            c_path = self._resolve_path(c_rel)
            if not c_path.exists():
                continue
            with open(c_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line.strip())
                    pid = rec.get("problem_id")
                    sid = rec.get("solution_id")
                    if pid and sid:
                        candidates[(pid, sid)] = rec

        return candidates

    def load_baselines(self) -> Dict[Tuple[str, str], str]:
        """Load baseline execution results: (problem_id, solution_id) -> baseline_result."""
        baselines: Dict[Tuple[str, str], str] = {}

        baseline_files = [self.config.eval_baseline_file]
        if self.config.include_pilot:
            baseline_files.append(self.config.pilot_baseline_file)

        for b_rel in baseline_files:
            b_path = self._resolve_path(b_rel)
            if not b_path.exists():
                continue
            with open(b_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line.strip())
                    pid = rec.get("problem_id")
                    sid = rec.get("solution_id")
                    res = rec.get("baseline_result")
                    if pid and sid and res:
                        baselines[(pid, sid)] = res

        return baselines

    def load_canonical_mutations(self) -> List[Dict[str, Any]]:
        """
        Load mutation execution telemetry strictly from canonical sources.
        Guarantees experimental sidecars and duplicate step_evidence are ignored.
        """
        mutation_records: List[Dict[str, Any]] = []

        mutation_files = [self.config.eval_mutations_file]
        if self.config.include_pilot:
            mutation_files.append(self.config.pilot_mutations_file)

        for m_rel in mutation_files:
            m_path = self._resolve_path(m_rel)
            if not m_path.exists():
                continue
            with open(m_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    rec = json.loads(line.strip())
                    rec["_source_artifact"] = m_rel
                    mutation_records.append(rec)

        return mutation_records

    def partition_problems(self, problem_ids: List[str]) -> Dict[str, str]:
        """
        Deterministically partition unique problem IDs into train, validation, and test.
        Enforces strict problem-level isolation.
        """
        sorted_pids = sorted(list(set(problem_ids)))
        rng = random.Random(self.config.random_seed)
        shuffled = sorted_pids.copy()
        rng.shuffle(shuffled)

        n = len(shuffled)
        n_train = max(1, int(round(n * self.config.train_ratio)))
        n_val = max(1, int(round(n * self.config.val_ratio)))
        
        # Ensure at least 1 problem per split if n >= 3
        if n >= 3 and n_train + n_val >= n:
            n_train = n - 2
            n_val = 1

        train_pids = set(shuffled[:n_train])
        val_pids = set(shuffled[n_train:n_train + n_val])
        test_pids = set(shuffled[n_train + n_val:])

        # Fallback if rounding left test empty
        if not test_pids and len(val_pids) > 1:
            moved = val_pids.pop()
            test_pids.add(moved)

        split_map: Dict[str, str] = {}
        for pid in train_pids:
            split_map[pid] = "train"
        for pid in val_pids:
            split_map[pid] = "validation"
        for pid in test_pids:
            split_map[pid] = "test"

        return split_map

    @staticmethod
    def construct_previous_context(solution_code: str, line_num: Optional[int]) -> str:
        """
        Construct previous context containing strictly lines 1 .. line_num - 1.
        Guarantees zero future-step leakage.
        """
        if not solution_code or line_num is None or line_num <= 1:
            return ""
        lines = solution_code.splitlines()
        # line_num is 1-indexed; lines before line_num are 0 .. line_num - 2
        prev_lines = lines[:line_num - 1]
        return "\n".join(prev_lines)

    @staticmethod
    def format_model_input_context(prompt: str, previous_context: str, current_step_code: str) -> str:
        """
        Format clean model context without any execution/mutation metadata.
        """
        parts = []
        if prompt:
            parts.append(f"[PROBLEM]\n{prompt.strip()}")
        if previous_context:
            parts.append(f"[PREVIOUS_CONTEXT]\n{previous_context.strip()}")
        if current_step_code:
            parts.append(f"[CURRENT_STEP]\n{current_step_code.strip()}")
        return "\n\n".join(parts)

    def generate_records(self) -> Tuple[List[PRMDatasetRecord], List[PRMDatasetRecord], List[PRMDatasetRecord], Dict[str, Any]]:
        """
        Generate all PRM dataset records partitioned by problem.
        
        Returns:
            Tuple of:
            - binary_dataset_records: List[PRMDatasetRecord] (POSITIVE_PROXY + NEGATIVE_PROXY)
            - survived_records: List[PRMDatasetRecord] (SURVIVED / Ambiguous excluded)
            - error_records: List[PRMDatasetRecord] (RUNTIME_ERROR quarantined)
            - generation_metadata: Dict[str, Any]
        """
        problems = self.load_problems()
        candidates = self.load_candidates()
        baselines = self.load_baselines()
        mutations = self.load_canonical_mutations()

        split_map = self.partition_problems(list(problems.keys()))

        # Group mutations by (problem_id, solution_id, step_id)
        step_mutations: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        for m in mutations:
            key = (m["problem_id"], m["solution_id"], m["step_id"])
            step_mutations.setdefault(key, []).append(m)

        binary_records: List[PRMDatasetRecord] = []
        survived_records: List[PRMDatasetRecord] = []
        error_records: List[PRMDatasetRecord] = []

        # Track positive steps generated to avoid duplicates
        positive_step_keys: Set[Tuple[str, str, str]] = set()

        rec_counter = 1

        # 1. Process Negative, Survived, and Runtime Error Records from Mutation Telemetry
        for m in mutations:
            pid = m["problem_id"]
            sid = m["solution_id"]
            step_id = m["step_id"]
            m_res = m.get("mutation_result")
            retcode = m.get("returncode")
            m_type = m.get("mutation_type")
            line = m.get("line")
            col = m.get("column")
            mutated_code = m.get("mutated_code", "")
            orig_code = m.get("original_code", "")

            prob_info = problems.get(pid, {})
            prompt = prob_info.get("prompt", "")
            cand_info = candidates.get((pid, sid), {})
            sol_code = cand_info.get("code") or orig_code
            prev_context = self.construct_previous_context(sol_code, line)

            split_name = split_map.get(pid, "train")
            mut_identity = f"{pid}:{sid}:{step_id}:L{line}:C{col}:{m_type}"

            if m_res == "FAIL" and retcode == 1:
                # NEGATIVE_PROXY Record
                rec_id = f"SG-PRM-{split_name.upper()}-{rec_counter:05d}-NEG"
                rec_counter += 1
                prov = ProvenanceRecord(
                    source_artifact=m.get("_source_artifact", ""),
                    source_split=split_name,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    line=line,
                    column=col,
                    mutation_type=m_type,
                    execution_returncode=retcode,
                    mutation_record_identity=mut_identity
                )
                record = PRMDatasetRecord(
                    dataset_record_id=rec_id,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    step_type="block" if "block" in step_id else "function",
                    prompt=prompt,
                    previous_context=prev_context,
                    current_step_code=mutated_code,
                    binary_proxy_label=0,
                    evidence_type="mutation_killed_fail",
                    provenance=prov
                )
                binary_records.append(record)

            elif m_res == "PASS":
                # SURVIVED / Ambiguous (Excluded from binary dataset)
                rec_id = f"SG-PRM-SURVIVED-{len(survived_records) + 1:05d}"
                prov = ProvenanceRecord(
                    source_artifact=m.get("_source_artifact", ""),
                    source_split=split_name,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    line=line,
                    column=col,
                    mutation_type=m_type,
                    execution_returncode=retcode,
                    mutation_record_identity=mut_identity
                )
                record = PRMDatasetRecord(
                    dataset_record_id=rec_id,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    step_type="block" if "block" in step_id else "function",
                    prompt=prompt,
                    previous_context=prev_context,
                    current_step_code=mutated_code,
                    binary_proxy_label=None,
                    evidence_type="survived_ambiguous",
                    provenance=prov
                )
                survived_records.append(record)

            elif m_res == "RUNTIME_ERROR":
                # RUNTIME_ERROR (Quarantined for robustness analysis)
                rec_id = f"SG-PRM-ERROR-{len(error_records) + 1:05d}"
                prov = ProvenanceRecord(
                    source_artifact=m.get("_source_artifact", ""),
                    source_split=split_name,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    line=line,
                    column=col,
                    mutation_type=m_type,
                    execution_returncode=retcode,
                    mutation_record_identity=mut_identity
                )
                record = PRMDatasetRecord(
                    dataset_record_id=rec_id,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    step_type="block" if "block" in step_id else "function",
                    prompt=prompt,
                    previous_context=prev_context,
                    current_step_code=mutated_code,
                    binary_proxy_label=None,
                    evidence_type="runtime_error_quarantine",
                    provenance=prov
                )
                error_records.append(record)

        # 2. Process Positive Proxy Records from Baseline PASS & Clean Mutation Steps
        for (pid, sid, step_id), mut_list in sorted(step_mutations.items()):
            base_res = baselines.get((pid, sid))
            num_fail = sum(1 for m in mut_list if m.get("mutation_result") == "FAIL")
            num_pass = sum(1 for m in mut_list if m.get("mutation_result") == "PASS")

            # Contract Condition: baseline PASS + >=1 killed mutation + 0 surviving mutations
            if base_res == "PASS" and num_fail >= 1 and num_pass == 0:
                first_mut = mut_list[0]
                line = first_mut.get("line")
                col = first_mut.get("column")
                orig_code = first_mut.get("original_code", "")

                prob_info = problems.get(pid, {})
                prompt = prob_info.get("prompt", "")
                cand_info = candidates.get((pid, sid), {})
                sol_code = cand_info.get("code") or orig_code
                prev_context = self.construct_previous_context(sol_code, line)

                split_name = split_map.get(pid, "train")
                rec_id = f"SG-PRM-{split_name.upper()}-{rec_counter:05d}-POS"
                rec_counter += 1

                mut_identity = f"{pid}:{sid}:{step_id}:baseline"
                prov = ProvenanceRecord(
                    source_artifact=prob_info.get("source_artifact", ""),
                    source_split=split_name,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    line=line,
                    column=col,
                    mutation_type=None,
                    execution_returncode=0,
                    mutation_record_identity=mut_identity
                )
                record = PRMDatasetRecord(
                    dataset_record_id=rec_id,
                    problem_id=pid,
                    solution_id=sid,
                    step_id=step_id,
                    step_type="block" if "block" in step_id else "function",
                    prompt=prompt,
                    previous_context=prev_context,
                    current_step_code=orig_code,
                    binary_proxy_label=1,
                    evidence_type="baseline_clean_pass",
                    provenance=prov
                )
                binary_records.append(record)
                positive_step_keys.add((pid, sid, step_id))

        metadata = {
            "random_seed": self.config.random_seed,
            "total_problems": len(problems),
            "split_assignment": split_map,
            "counts": {
                "positive_proxy_count": len(positive_step_keys),
                "negative_proxy_count": len([r for r in binary_records if r.binary_proxy_label == 0]),
                "total_binary_records": len(binary_records),
                "survived_excluded_count": len(survived_records),
                "runtime_error_quarantined_count": len(error_records)
            }
        }

        return binary_records, survived_records, error_records, metadata
