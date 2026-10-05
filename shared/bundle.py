"""StepGuard Task F3 Slice 4: End-to-End Provenance Bundle Engine.

Provides:
- 10-field canonical payload assembly and SHA-256 bundle hashing.
- Programmatic creation and single-pass verification of ProvenanceBundleManifest.
- Multi-layer composite evaluation across environment, authoritative registry,
  referential lineage, and Merkle tree roots.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from shared.contracts import (
    CANONICAL_REGISTRY_REL_PATH,
    ArtifactRegistryManifest,
    ArtifactStatus,
    AuthoritativeArtifactRecord,
    BundleVerificationReport,
    CohortManifest,
    EnvironmentFingerprintRecord,
    LineageVerificationSummary,
    ProvenanceBundleManifest,
)
from shared.environment import (
    canonical_environment_payload,
    capture_environment_fingerprint,
    derive_git_commit_sha,
    verify_environment_parity,
)
from shared.identity import (
    build_bundle_id,
    is_valid_canonical_id,
)
from shared.registry import verify_artifact_registry
from shared.validator import (
    EvidenceValidator,
    G8BundleHashMismatch,
    G8BundleSchemaMismatch,
    G8EnvironmentMismatch,
    G8LineageCycleDetected,
    G8LineageTraversalDepthExceeded,
    G8RegistryIntegrityFailure,
    G8UnregisteredArtifactViolation,
    ValidationViolation,
)


def canonical_bundle_hash_payload(
    manifest: Union[ProvenanceBundleManifest, Dict[str, Any]]
) -> Dict[str, Any]:
    """Assemble and normalize the exact 10-field canonical bundle payload.

    Excludes volatile 'created_at' and self-referential 'aggregate_bundle_hash'.
    """
    if isinstance(manifest, ProvenanceBundleManifest):
        raw = manifest.to_dict()
    elif isinstance(manifest, dict):
        raw = dict(manifest)
    else:
        raise TypeError(f"Expected ProvenanceBundleManifest or dict, got {type(manifest).__name__}")

    return {
        "bundle_id": str(raw["bundle_id"]).strip(),
        "cohort_manifest_ids": sorted([str(cid).strip() for cid in raw.get("cohort_manifest_ids", [])]),
        "cohort_merkle_roots": sorted([str(cmr).strip().lower() for cmr in raw.get("cohort_merkle_roots", [])]),
        "environment_fingerprint_id": str(raw["environment_fingerprint_id"]).strip(),
        "environment_record": canonical_environment_payload(raw["environment_record"]),
        "git_commit_sha": str(raw.get("git_commit_sha", "unknown")).strip().lower(),
        "lineage_summary": raw["lineage_summary"] if isinstance(raw["lineage_summary"], dict) else raw["lineage_summary"].to_canonical_dict(),
        "registry_manifest_id": str(raw["registry_manifest_id"]).strip(),
        "registry_merkle_root": str(raw["registry_merkle_root"]).strip().lower(),
        "schema_version": str(raw.get("schema_version", "1.0.0")).strip(),
    }


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    """Serialize dictionary using deterministic UTF-8 canonical JSON rules."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_aggregate_bundle_hash(
    manifest: Union[ProvenanceBundleManifest, Dict[str, Any]]
) -> str:
    """Compute deterministic SHA-256 digest over the exact 10-field canonical payload."""
    payload = canonical_bundle_hash_payload(manifest)
    c_bytes = canonical_json_bytes(payload)
    return hashlib.sha256(c_bytes).hexdigest().lower()


def build_lineage_summary(
    candidates: Sequence[Dict[str, Any]],
    steps: Sequence[Dict[str, Any]],
    mutations: Sequence[Dict[str, Any]],
    traces: Sequence[Dict[str, Any]],
    labels: Optional[Sequence[Dict[str, Any]]] = None,
    predictions: Optional[Sequence[Dict[str, Any]]] = None,
    max_depth_budget: int = 10,
) -> Tuple[LineageVerificationSummary, List[ValidationViolation]]:
    """Analyze relational execution DAG, count edges, detect cycles, and enforce max depth budget."""
    violations: List[ValidationViolation] = []

    c_ids = {c.get("candidate_id") for c in candidates if c.get("candidate_id")}
    s_ids = {s.get("canonical_step_id") for s in steps if s.get("canonical_step_id")}
    m_ids = {m.get("mutation_id") for m in mutations if m.get("mutation_id")}
    t_ids = {t.get("trace_id") for t in traces if t.get("trace_id")}
    l_list = list(labels or [])
    p_list = list(predictions or [])

    # Edge counts
    candidate_step_edges = sum(1 for s in steps if s.get("candidate_id") in c_ids)
    step_mutation_edges = sum(1 for m in mutations if (m.get("canonical_step_id") or m.get("step_id")) in s_ids)
    mutation_trace_edges = sum(1 for t in traces if (t.get("mutation_id") or t.get("parent_mutation_id")) in m_ids)
    step_label_edges = sum(1 for l in l_list if l.get("canonical_step_id") in s_ids)
    step_prediction_edges = sum(1 for p in p_list if p.get("canonical_step_id") in s_ids)

    # Build adjacency list for DAG path and cycle checking
    # Graph nodes: candidate -> step -> mutation -> trace -> label/prediction
    adj: Dict[str, List[str]] = {}
    in_degree: Dict[str, int] = {}

    all_nodes: Set[str] = set()
    for c in candidates:
        cid = c.get("candidate_id")
        if cid:
            all_nodes.add(cid)
            adj.setdefault(cid, [])
            in_degree.setdefault(cid, 0)

    for s in steps:
        sid = s.get("canonical_step_id")
        cand = s.get("candidate_id")
        if sid:
            all_nodes.add(sid)
            adj.setdefault(sid, [])
            in_degree.setdefault(sid, 0)
            if cand and cand in all_nodes:
                adj[cand].append(sid)
                in_degree[sid] = in_degree.get(sid, 0) + 1

    for m in mutations:
        mid = m.get("mutation_id")
        ps = m.get("canonical_step_id") or m.get("step_id")
        if mid:
            all_nodes.add(mid)
            adj.setdefault(mid, [])
            in_degree.setdefault(mid, 0)
            if ps and ps in all_nodes:
                adj[ps].append(mid)
                in_degree[mid] = in_degree.get(mid, 0) + 1

    for t in traces:
        tid = t.get("trace_id")
        pm = t.get("mutation_id") or t.get("parent_mutation_id")
        if tid:
            all_nodes.add(tid)
            adj.setdefault(tid, [])
            in_degree.setdefault(tid, 0)
            if pm and pm in all_nodes:
                adj[pm].append(tid)
                in_degree[tid] = in_degree.get(tid, 0) + 1

    for l in l_list:
        lid = l.get("label_id")
        ps = l.get("canonical_step_id")
        if lid:
            all_nodes.add(lid)
            adj.setdefault(lid, [])
            in_degree.setdefault(lid, 0)
            if ps and ps in all_nodes:
                adj[ps].append(lid)
                in_degree[lid] = in_degree.get(lid, 0) + 1

    for p in p_list:
        pid = p.get("prediction_id")
        ps = p.get("canonical_step_id")
        if pid:
            all_nodes.add(pid)
            adj.setdefault(pid, [])
            in_degree.setdefault(pid, 0)
            if ps and ps in all_nodes:
                adj[ps].append(pid)
                in_degree[pid] = in_degree.get(pid, 0) + 1

    # Check for cycles and compute max traversal depth
    visited_global: Set[str] = set()
    has_cycles = False
    cycle_details: List[str] = []
    max_observed_depth = 0
    traversal_completed = True
    depth_exceeded = False
    violating_depth_entity = ""

    roots = [n for n in all_nodes if in_degree.get(n, 0) == 0]
    if not roots and all_nodes:
        # All nodes have in_degree > 0 -> entire graph is a cycle
        has_cycles = True
        cycle_details = sorted(list(all_nodes))
        violations.append(
            ValidationViolation(
                fault_class="G8",
                rule_id="RULE_8_6_LINEAGE_CYCLE_DETECTED",
                entity_id="lineage_graph",
                message=f"Lineage graph contains cycles involving nodes: {cycle_details[:5]}",
                context={"cycle_nodes": cycle_details},
            )
        )
        traversal_completed = False

    def dfs(node: str, current_path: List[str], depth: int) -> None:
        nonlocal has_cycles, max_observed_depth, traversal_completed, depth_exceeded, violating_depth_entity
        if depth > max_observed_depth:
            max_observed_depth = depth

        if depth > max_depth_budget:
            # Reached depth 11
            depth_exceeded = True
            traversal_completed = False
            violating_depth_entity = node
            return

        for child in adj.get(node, []):
            if child in current_path:
                has_cycles = True
                cycle_details.append(f"{node}->{child}")
                traversal_completed = False
            else:
                dfs(child, current_path + [child], depth + 1)

    for r in roots:
        dfs(r, [r], 1)

    if has_cycles:
        cycle_details = sorted(list(set(cycle_details)))
        violations.append(
            ValidationViolation(
                fault_class="G8",
                rule_id="RULE_8_6_LINEAGE_CYCLE_DETECTED",
                entity_id="lineage_graph",
                message=f"Lineage graph contains cycles: {cycle_details[:5]}",
                context={"cycle_details": cycle_details},
            )
        )

    if depth_exceeded:
        violations.append(
            ValidationViolation(
                fault_class="G8",
                rule_id="RULE_8_7_TRAVERSAL_DEPTH_EXCEEDED",
                entity_id=str(violating_depth_entity or "lineage_node"),
                message=f"Lineage traversal exceeded maximum permitted depth budget of {max_depth_budget} (reached depth {max_observed_depth}).",
                context={"max_permitted_depth": max_depth_budget, "reached_depth": max_observed_depth},
            )
        )

    summary = LineageVerificationSummary(
        total_candidates=len(candidates),
        total_steps=len(steps),
        total_mutations=len(mutations),
        total_traces=len(traces),
        total_labels=len(l_list),
        total_predictions=len(p_list),
        candidate_step_edges=candidate_step_edges,
        step_mutation_edges=step_mutation_edges,
        mutation_trace_edges=mutation_trace_edges,
        step_label_edges=step_label_edges,
        step_prediction_edges=step_prediction_edges,
        has_cycles=has_cycles,
        traversal_completed=traversal_completed,
        max_traversal_depth=max_observed_depth,
        cycle_details=cycle_details,
    )
    return (summary, violations)


def create_provenance_bundle(
    cohort_manifests: List[CohortManifest],
    registry_manifest: ArtifactRegistryManifest,
    environment_record: EnvironmentFingerprintRecord,
    git_commit_sha: Optional[str] = None,
    bundle_name: str = "authoritative",
    version: str = "1.0",
    candidates: Optional[Sequence[Dict[str, Any]]] = None,
    steps: Optional[Sequence[Dict[str, Any]]] = None,
    mutations: Optional[Sequence[Dict[str, Any]]] = None,
    traces: Optional[Sequence[Dict[str, Any]]] = None,
    labels: Optional[Sequence[Dict[str, Any]]] = None,
    predictions: Optional[Sequence[Dict[str, Any]]] = None,
) -> ProvenanceBundleManifest:
    """Assemble and seal a ProvenanceBundleManifest with deterministic 10-field hashing."""
    clean_sha = git_commit_sha or derive_git_commit_sha()
    cohort_ids = sorted([c.cohort_id for c in cohort_manifests])
    cohort_roots = sorted([c.aggregate_merkle_root.lower() for c in cohort_manifests])

    lineage_summary, _ = build_lineage_summary(
        candidates=candidates or [],
        steps=steps or [],
        mutations=mutations or [],
        traces=traces or [],
        labels=labels,
        predictions=predictions,
    )

    bundle_id = build_bundle_id(bundle_name, version=version)
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw_manifest_dict = {
        "bundle_id": bundle_id,
        "schema_version": "1.0.0",
        "git_commit_sha": clean_sha,
        "environment_fingerprint_id": environment_record.environment_id,
        "environment_record": environment_record.to_dict(),
        "registry_manifest_id": registry_manifest.registry_id,
        "registry_merkle_root": registry_manifest.aggregate_merkle_root.lower(),
        "cohort_manifest_ids": cohort_ids,
        "cohort_merkle_roots": cohort_roots,
        "lineage_summary": lineage_summary.to_canonical_dict(),
        "created_at": created_at,
    }

    bundle_hash = compute_aggregate_bundle_hash(raw_manifest_dict)

    return ProvenanceBundleManifest(
        bundle_id=bundle_id,
        schema_version="1.0.0",
        git_commit_sha=clean_sha,
        environment_fingerprint_id=environment_record.environment_id,
        environment_record=environment_record.to_dict(),
        registry_manifest_id=registry_manifest.registry_id,
        registry_merkle_root=registry_manifest.aggregate_merkle_root.lower(),
        cohort_manifest_ids=cohort_ids,
        cohort_merkle_roots=cohort_roots,
        lineage_summary=lineage_summary.to_canonical_dict(),
        created_at=created_at,
        aggregate_bundle_hash=bundle_hash,
    )


def verify_provenance_bundle(
    bundle: Union[ProvenanceBundleManifest, Dict[str, Any]],
    repo_root: Optional[Path] = None,
    enforce_environment: bool = True,
    pipeline_referenced_artifacts: Optional[Sequence[str]] = None,
) -> BundleVerificationReport:
    """Execute single-pass composite verification over environment, registry, lineage, and bundle hash."""
    violations: List[ValidationViolation] = []
    total_checks = 0
    merkle_roots: List[str] = []

    root_p = Path(repo_root) if repo_root else Path(".")

    # 1. Parse / Cast Bundle Manifest
    if isinstance(bundle, dict):
        try:
            b_obj = ProvenanceBundleManifest.from_dict(bundle)
        except Exception as e:
            violations.append(
                ValidationViolation(
                    fault_class="G8",
                    rule_id="RULE_8_1_BUNDLE_SCHEMA_MISMATCH",
                    entity_id=str(bundle.get("bundle_id", "bundle")),
                    message=f"Bundle schema mismatch: {e}",
                )
            )
            return BundleVerificationReport(
                is_valid=False,
                total_checks=1,
                violations=violations,
                summary_by_class={"G1": 0, "G2": 0, "G3": 0, "G4": 0, "G5": 0, "G6": 0, "G7": 0, "G8": 1},
                environment_verified=False,
                environment_mismatches=[],
                registry_verified=False,
                registry_violations=[],
                artifacts_verified_count=0,
                unregistered_artifact_count=0,
                lineage_verified=False,
                lineage_summary=None,
                bundle_hash_verified=False,
                computed_bundle_hash="",
                declared_bundle_hash=str(bundle.get("aggregate_bundle_hash", "")),
                historical_artifacts_count=0,
                historical_provenance_gapped=False,
            )
    else:
        b_obj = bundle

    # 2. Verify Bundle Hash
    total_checks += 1
    computed_hash = compute_aggregate_bundle_hash(b_obj)
    declared_hash = b_obj.aggregate_bundle_hash.lower()
    bundle_hash_verified = (computed_hash == declared_hash)

    if not bundle_hash_verified:
        violations.append(
            ValidationViolation(
                fault_class="G8",
                rule_id="RULE_8_5_BUNDLE_HASH_MISMATCH",
                entity_id=b_obj.bundle_id,
                message=f"Bundle hash mismatch: declared '{declared_hash}', computed '{computed_hash}'.",
                context={"declared": declared_hash, "computed": computed_hash},
            )
        )

    # 3. Verify Environment Parity
    total_checks += 1
    env_verified = True
    env_mismatches: List[str] = []
    if enforce_environment:
        current_env = capture_environment_fingerprint(repo_root=root_p)
        baseline_env = EnvironmentFingerprintRecord.from_dict(b_obj.environment_record)
        is_clean, mismatches = verify_environment_parity(
            baseline=baseline_env,
            current=current_env,
            require_exact_commit=True,
        )
        env_verified = is_clean
        env_mismatches = mismatches
        if not is_clean:
            for mm in mismatches:
                violations.append(
                    ValidationViolation(
                        fault_class="G8",
                        rule_id="RULE_8_2_BUNDLE_ENV_MISMATCH",
                        entity_id=b_obj.environment_fingerprint_id,
                        message=f"Environment parity mismatch: {mm}",
                        context={"mismatch": mm},
                    )
                )

    # 4. Verify Authoritative Registry Manifest
    total_checks += 1
    registry_verified = True
    registry_violations: List[str] = []
    historical_count = 0
    historical_gapped = False
    registered_paths: Set[str] = set()

    canonical_reg_path = root_p / CANONICAL_REGISTRY_REL_PATH
    if canonical_reg_path.is_file():
        try:
            reg_dict = json.loads(canonical_reg_path.read_text(encoding="utf-8"))
            reg_manifest = ArtifactRegistryManifest.from_dict(reg_dict)
            registered_paths = {a.relative_path for a in reg_manifest.artifacts}
            
            # Count historical gapped artifacts
            for a in reg_manifest.artifacts:
                if a.status == ArtifactStatus.HISTORICAL_PROVENANCE_GAPPED:
                    historical_count += 1
                    historical_gapped = True

            # Verify registry on-disk
            is_reg_clean, reg_viols = verify_artifact_registry(reg_manifest, repo_root=root_p)
            registry_verified = is_reg_clean
            registry_violations = reg_viols
            if not is_reg_clean:
                for rv in reg_viols:
                    violations.append(
                        ValidationViolation(
                            fault_class="G8",
                            rule_id="RULE_8_3_BUNDLE_REGISTRY_FAILURE",
                            entity_id=b_obj.registry_manifest_id,
                            message=f"Authoritative registry failure: {rv}",
                        )
                    )
            else:
                merkle_roots.append(reg_manifest.aggregate_merkle_root.lower())
        except Exception as e:
            registry_verified = False
            violations.append(
                ValidationViolation(
                    fault_class="G8",
                    rule_id="RULE_8_3_BUNDLE_REGISTRY_FAILURE",
                    entity_id=b_obj.registry_manifest_id,
                    message=f"Error reading authoritative registry manifest: {e}",
                )
            )
    else:
        # Registry file missing
        registry_verified = False
        violations.append(
            ValidationViolation(
                fault_class="G8",
                rule_id="RULE_8_3_BUNDLE_REGISTRY_FAILURE",
                entity_id=b_obj.registry_manifest_id,
                message=f"Canonical registry manifest missing at '{CANONICAL_REGISTRY_REL_PATH}'.",
            )
        )

    # 5. Check Pipeline Referenced Artifacts against Registry Whitelist
    unregistered_count = 0
    if pipeline_referenced_artifacts:
        for art_path in pipeline_referenced_artifacts:
            total_checks += 1
            clean_p = art_path.replace("\\", "/").strip("/").strip()
            if clean_p not in registered_paths:
                unregistered_count += 1
                violations.append(
                    ValidationViolation(
                        fault_class="G8",
                        rule_id="RULE_8_4_UNREGISTERED_ARTIFACT",
                        entity_id=f"sg://artifact/{clean_p}",
                        message=f"Pipeline artifact '{clean_p}' is not registered in authoritative manifest.",
                    )
                )

    # 6. Verify Lineage Summary
    total_checks += 1
    lineage_summary_dict = b_obj.lineage_summary
    lineage_verified = True

    if lineage_summary_dict:
        if lineage_summary_dict.get("has_cycles", False):
            lineage_verified = False
            violations.append(
                ValidationViolation(
                    fault_class="G8",
                    rule_id="RULE_8_6_LINEAGE_CYCLE_DETECTED",
                    entity_id=b_obj.bundle_id,
                    message=f"Lineage summary reports cycles: {lineage_summary_dict.get('cycle_details', [])}",
                )
            )
        if not lineage_summary_dict.get("traversal_completed", True):
            lineage_verified = False
            if lineage_summary_dict.get("max_traversal_depth", 0) > 10:
                violations.append(
                    ValidationViolation(
                        fault_class="G8",
                        rule_id="RULE_8_7_TRAVERSAL_DEPTH_EXCEEDED",
                        entity_id=b_obj.bundle_id,
                        message=f"Lineage summary reports traversal depth exceeded: {lineage_summary_dict.get('max_traversal_depth')}",
                    )
                )

    # Add cohort merkle roots
    for cmr in b_obj.cohort_merkle_roots:
        merkle_roots.append(cmr.lower())

    # Deterministic sorting of violations: by (fault_class, entity_id, rule_id, message)
    sorted_violations = sorted(
        violations,
        key=lambda v: (v.fault_class, v.entity_id, v.rule_id, v.message),
    )

    summary_by_class: Dict[str, int] = {f"G{i}": 0 for i in range(1, 9)}
    for v in sorted_violations:
        summary_by_class[v.fault_class] = summary_by_class.get(v.fault_class, 0) + 1

    return BundleVerificationReport(
        is_valid=(len(sorted_violations) == 0),
        total_checks=total_checks,
        violations=sorted_violations,
        summary_by_class=summary_by_class,
        environment_verified=env_verified,
        environment_mismatches=sorted(env_mismatches),
        registry_verified=registry_verified,
        registry_violations=sorted(registry_violations),
        artifacts_verified_count=len(registered_paths),
        unregistered_artifact_count=unregistered_count,
        lineage_verified=lineage_verified,
        lineage_summary=lineage_summary_dict,
        bundle_hash_verified=bundle_hash_verified,
        computed_bundle_hash=computed_hash,
        declared_bundle_hash=declared_hash,
        historical_artifacts_count=historical_count,
        historical_provenance_gapped=historical_gapped,
        merkle_roots_verified=sorted(list(set(merkle_roots))),
    )
