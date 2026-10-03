"""StepGuard Task F3 Slice 1: Canonical Identity Module.

Provides:
- Universal serialized sg:// URI specification, builders, parsers, and validators.
- Canonical candidate identity contract preserving Phase 1.5 semantics.
- Explicit solution_id -> candidate_id legacy mapping adapter (never infer equivalence from string equality).
- Deterministic AST code normalization and 12-character SHA-256 step hashing.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

# Allowed canonical entity types in the sg:// URI hierarchy
VALID_ENTITY_TYPES = {
    "problem",
    "candidate",
    "step",
    "mutation",
    "trace",
    "label",
    "prediction",
    "cohort",
}

CANONICAL_URI_PATTERN = re.compile(
    r"^sg://(?P<entity_type>[a-z_]+)/(?P<key>[A-Za-z0-9_:\.\-]+)$"
)

# Canonical step ID format: sg://step/{candidate_id}::{ast_hash}
STEP_ID_PATTERN = re.compile(
    r"^sg://step/(?P<candidate_id>[a-z0-9_]+)::(?P<ast_hash>[a-f0-9]{12})$"
)

# Canonical label ID format: sg://label/{candidate_id}::{ast_hash}::{ruleset}
LABEL_ID_PATTERN = re.compile(
    r"^sg://label/(?P<candidate_id>[a-z0-9_]+)::(?P<ast_hash>[a-f0-9]{12})::(?P<ruleset>[a-z0-9_]+)$"
)

# Canonical cohort ID format: sg://cohort/{cohort_name}::{version}
COHORT_ID_PATTERN = re.compile(
    r"^sg://cohort/(?P<cohort_name>[a-z0-9_]+)::(?P<version>v[0-9]+.*)$"
)


# ---------------------------------------------------------------------------
# Phase 1.5 Canonical Candidate Identity Contract & Legacy Mapping Adapter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateIdentityMapping:
    """Explicit, deterministic mapping from legacy solution_id to canonical candidate_id.

    Guarantees that equivalence is NEVER inferred merely because string values match.
    """

    mapping: Dict[str, str]

    def map_solution_to_candidate(self, legacy_solution_id: str) -> str:
        if not legacy_solution_id or not isinstance(legacy_solution_id, str):
            raise ValueError("Legacy solution_id must be a non-empty string.")
        clean_sol = legacy_solution_id.strip()
        if clean_sol not in self.mapping:
            raise KeyError(
                f"Legacy solution_id '{clean_sol}' is not in the explicit candidate identity mapping."
            )
        return self.mapping[clean_sol]

    def get_canonical_id(self, legacy_solution_id: str) -> str:
        return self.map_solution_to_candidate(legacy_solution_id)


def resolve_candidate_identity(
    candidate_id: Optional[str] = None,
    solution_id: Optional[str] = None,
    mapping: Optional[Union[Dict[str, str], CandidateIdentityMapping]] = None,
) -> Tuple[str, Optional[str], bool]:
    """Resolve and validate candidate identity under the Phase 1.5 identity contract.

    Rules:
    - candidate_id is the canonical identity.
    - Legacy solution_id is supported ONLY via an explicit, deterministic mapping.
    - Equivalence is NEVER inferred merely because solution_id and candidate_id strings match.
    - Ambiguous or conflicting combinations fail fast with ValueError.

    Returns:
        (canonical_candidate_id, legacy_solution_id, is_mapped)
    """
    clean_candidate = (
        candidate_id.strip()
        if candidate_id and isinstance(candidate_id, str) and candidate_id.strip()
        else None
    )
    clean_solution = (
        solution_id.strip()
        if solution_id and isinstance(solution_id, str) and solution_id.strip()
        else None
    )

    mapper: Optional[CandidateIdentityMapping] = None
    if mapping is not None:
        if isinstance(mapping, CandidateIdentityMapping):
            mapper = mapping
        elif isinstance(mapping, dict):
            mapper = CandidateIdentityMapping(mapping=mapping)
        else:
            raise TypeError("mapping must be a dict or CandidateIdentityMapping instance.")

    if clean_candidate:
        if clean_solution:
            if mapper is None:
                raise ValueError(
                    "Ambiguous identity: both canonical candidate_id and legacy solution_id were provided "
                    "without an explicit mapping. Equivalence cannot be silently inferred."
                )
            expected_candidate = mapper.map_solution_to_candidate(clean_solution)
            if clean_candidate != expected_candidate:
                raise ValueError(
                    f"Conflicting identity: provided candidate_id '{clean_candidate}' does not match "
                    f"mapped solution_id '{clean_solution}' -> '{expected_candidate}'."
                )
            return (clean_candidate, clean_solution, True)
        return (clean_candidate, None, False)

    if clean_solution:
        if mapper is None:
            raise ValueError(
                f"Legacy solution_id '{clean_solution}' provided without an explicit mapping. "
                "Direct string equivalence is strictly forbidden."
            )
        mapped_candidate = mapper.map_solution_to_candidate(clean_solution)
        return (mapped_candidate, clean_solution, True)

    raise ValueError("Neither candidate_id nor solution_id was provided.")


# ---------------------------------------------------------------------------
# AST Normalization & Step Code Hashing
# ---------------------------------------------------------------------------

def normalize_ast_code(code_str: str) -> str:
    """Normalize Python step code deterministically.

    Parses the AST, formats via ast.unparse if valid, or falls back to
    standardized whitespace stripping to eliminate formatting-only divergence.
    """
    if not code_str or not isinstance(code_str, str):
        return ""
    code_clean = code_str.strip()
    try:
        parsed = ast.parse(code_clean)
        return ast.unparse(parsed).strip()
    except Exception:
        lines = [line.rstrip() for line in code_clean.splitlines() if line.strip()]
        return "\n".join(lines)


def compute_ast_hash(code_str: str) -> str:
    """Compute the 12-character hexadecimal SHA-256 hash of normalized AST code."""
    normalized = normalize_ast_code(code_str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Universal Serialized sg:// Canonical ID Builders & Parsers
# ---------------------------------------------------------------------------

def build_canonical_id(entity_type: str, hierarchical_key: str) -> str:
    """Construct a validated serialized sg:// canonical identifier."""
    clean_type = entity_type.strip().lower()
    if clean_type not in VALID_ENTITY_TYPES:
        raise ValueError(
            f"Invalid entity type '{entity_type}'. Must be one of: {sorted(VALID_ENTITY_TYPES)}"
        )
    clean_key = hierarchical_key.strip()
    if not clean_key:
        raise ValueError("hierarchical_key cannot be empty.")
    uri = f"sg://{clean_type}/{clean_key}"
    if not CANONICAL_URI_PATTERN.match(uri):
        raise ValueError(f"Constructed URI '{uri}' does not match canonical URI pattern.")
    return uri


def parse_canonical_id(uri: str) -> Tuple[str, str]:
    """Parse and validate a serialized sg:// canonical identifier.

    Returns:
        (entity_type, hierarchical_key)
    """
    if not uri or not isinstance(uri, str):
        raise ValueError("Canonical ID must be a non-empty string.")
    match = CANONICAL_URI_PATTERN.match(uri.strip())
    if not match:
        raise ValueError(f"String '{uri}' is not a valid canonical sg:// URI.")
    entity_type = match.group("entity_type")
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Entity type '{entity_type}' in URI '{uri}' is not supported.")
    return (entity_type, match.group("key"))


def is_valid_canonical_id(uri: str, expected_entity_type: Optional[str] = None) -> bool:
    """Return True if uri is a syntactically valid sg:// canonical identifier."""
    try:
        etype, _ = parse_canonical_id(uri)
        if expected_entity_type is not None:
            return etype == expected_entity_type.strip().lower()
        return True
    except Exception:
        return False


def build_problem_id(problem_id: str) -> str:
    clean = problem_id.strip().lower()
    return build_canonical_id("problem", clean)


def build_candidate_id(candidate_id: str) -> str:
    clean = candidate_id.strip().lower()
    return build_canonical_id("candidate", clean)


def build_step_id(candidate_id: str, ast_hash_or_code: str) -> str:
    clean_cand = candidate_id.strip().lower()
    if len(ast_hash_or_code) == 12 and all(c in "0123456789abcdef" for c in ast_hash_or_code.lower()):
        ast_hash = ast_hash_or_code.lower()
    else:
        ast_hash = compute_ast_hash(ast_hash_or_code)
    return build_canonical_id("step", f"{clean_cand}::{ast_hash}")


def build_mutation_id(candidate_id: str, ast_hash: str, operator: str, node_index: int) -> str:
    clean_cand = candidate_id.strip().lower()
    clean_hash = ast_hash.strip().lower()
    clean_op = operator.strip().lower()
    key = f"{clean_cand}::{clean_hash}::{clean_op}::{node_index:02d}"
    return build_canonical_id("mutation", key)


def build_trace_id(
    candidate_id: str, ast_hash: str, operator: str, node_index: int, test_hash: str
) -> str:
    clean_cand = candidate_id.strip().lower()
    clean_hash = ast_hash.strip().lower()
    clean_op = operator.strip().lower()
    clean_test = test_hash.strip().lower()[:8]
    key = f"{clean_cand}::{clean_hash}::{clean_op}::{node_index:02d}::{clean_test}"
    return build_canonical_id("trace", key)


def build_label_id(candidate_id: str, ast_hash: str, ruleset_version: str) -> str:
    clean_cand = candidate_id.strip().lower()
    clean_hash = ast_hash.strip().lower()
    clean_rule = ruleset_version.strip().lower()
    key = f"{clean_cand}::{clean_hash}::{clean_rule}"
    return build_canonical_id("label", key)


def build_prediction_id(candidate_id: str, ast_hash: str, checkpoint_hash: str) -> str:
    clean_cand = candidate_id.strip().lower()
    clean_hash = ast_hash.strip().lower()
    clean_ckpt = checkpoint_hash.strip().lower()[:8]
    key = f"{clean_cand}::{clean_hash}::{clean_ckpt}"
    return build_canonical_id("prediction", key)


def build_cohort_id(cohort_name: str, version: str) -> str:
    clean_name = cohort_name.strip().lower()
    clean_ver = version.strip().lower()
    if not clean_ver.startswith("v"):
        clean_ver = f"v{clean_ver}"
    key = f"{clean_name}::{clean_ver}"
    return build_canonical_id("cohort", key)
