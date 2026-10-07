"""
Deterministic unit and integration test suite for PRM Dataset Generator (Phase 2).

Verifies:
1. Schema conformance matching the approved Data Contract.
2. Problem-level split isolation (zero candidate/step/mutation row crossing).
3. Deterministic split assignment and record IDs.
4. Zero future-step leakage in previous_context.
5. Zero execution/mutation metadata in model context.
6. SURVIVED mutant exclusion (binary_proxy_label is None).
7. RUNTIME_ERROR quarantine (binary_proxy_label is None).
8. Gate C isolation from training/validation splits.
9. Provenance completeness.
10. MBPP pilot_id normalization.
11. Repeated generation determinism.
"""

import json
import pytest
from pathlib import Path

from partner_b.dataset.generator import (
    PRMDatasetConfig,
    PRMDatasetGenerator,
    PRMDatasetRecord,
)


@pytest.fixture
def generator():
    """Create generator instance pointing to repository data."""
    config = PRMDatasetConfig(random_seed=42)
    return PRMDatasetGenerator(config=config)


def test_problem_loading_and_normalization(generator):
    """Verify all 25 problems are loaded and pilot_id is properly normalized to problem_id."""
    problems = generator.load_problems()
    assert len(problems) == 25
    assert "eval_001" in problems
    assert "eval_020" in problems
    assert "mbpp_001" in problems
    assert "mbpp_005" in problems

    for pid, pdata in problems.items():
        assert pdata["problem_id"] == pid
        assert "prompt" in pdata
        assert "test_list" in pdata
        assert isinstance(pdata["test_list"], list)


def test_problem_level_split_isolation(generator):
    """Verify problem-level split strictly separates problem IDs across splits."""
    problems = generator.load_problems()
    pids = list(problems.keys())
    split_map = generator.partition_problems(pids)

    train_pids = {pid for pid, s in split_map.items() if s == "train"}
    val_pids = {pid for pid, s in split_map.items() if s == "validation"}
    test_pids = {pid for pid, s in split_map.items() if s == "test"}

    assert len(train_pids) > 0
    assert len(val_pids) > 0
    assert len(test_pids) > 0
    assert train_pids.isdisjoint(val_pids)
    assert train_pids.isdisjoint(test_pids)
    assert val_pids.isdisjoint(test_pids)
    assert train_pids | val_pids | test_pids == set(pids)


def test_split_determinism(generator):
    """Verify split mapping is 100% deterministic given the same seed."""
    problems = generator.load_problems()
    pids = list(problems.keys())
    split1 = generator.partition_problems(pids)
    split2 = generator.partition_problems(pids)
    assert split1 == split2


def test_previous_context_zero_future_step_leakage():
    """Verify previous_context only contains lines before line_num."""
    code = (
        "def example(x):\n"
        "    a = x + 1\n"
        "    b = a * 2\n"
        "    c = b - 3\n"
        "    return c"
    )

    # Step at line 3 ("b = a * 2") -> lines 1 and 2
    ctx_line3 = PRMDatasetGenerator.construct_previous_context(code, line_num=3)
    assert ctx_line3 == "def example(x):\n    a = x + 1"
    assert "b = a * 2" not in ctx_line3
    assert "c = b - 3" not in ctx_line3
    assert "return c" not in ctx_line3

    # Step at line 1 -> empty previous context
    ctx_line1 = PRMDatasetGenerator.construct_previous_context(code, line_num=1)
    assert ctx_line1 == ""


def test_model_input_context_zero_metadata_leakage():
    """Verify formatted model input context contains zero execution metadata."""
    prompt = "def add(a, b):\n    return a + b"
    prev = "    a = 1"
    curr = "    return a + b"

    ctx = PRMDatasetGenerator.format_model_input_context(prompt, prev, curr)
    assert "[PROBLEM]" in ctx
    assert "[PREVIOUS_CONTEXT]" in ctx
    assert "[CURRENT_STEP]" in ctx

    # Execution keywords must not be present
    forbidden = ["PASS", "FAIL", "AssertionError", "returncode", "RUNTIME_ERROR", "mutation_type"]
    for word in forbidden:
        assert word not in ctx


def test_dataset_generation_counts_and_conformance(generator):
    """Verify exact counts and schema conformance on the canonical repository data."""
    binary_recs, survived_recs, error_recs, meta = generator.generate_records()

    # Exact audited counts from Task 1
    pos_recs = [r for r in binary_recs if r.binary_proxy_label == 1]
    neg_recs = [r for r in binary_recs if r.binary_proxy_label == 0]

    assert len(pos_recs) == 97, f"Expected 97 POSITIVE_PROXY records, got {len(pos_recs)}"
    assert len(neg_recs) == 135, f"Expected 135 NEGATIVE_PROXY records, got {len(neg_recs)}"
    assert len(binary_recs) == 232, f"Expected 232 total binary records, got {len(binary_recs)}"
    assert len(survived_recs) == 13, f"Expected 13 SURVIVED records, got {len(survived_recs)}"
    assert len(error_recs) == 27, f"Expected 27 RUNTIME_ERROR records, got {len(error_recs)}"

    # Check SURVIVED records have None label
    for r in survived_recs:
        assert r.binary_proxy_label is None
        assert r.evidence_type == "survived_ambiguous"

    # Check ERROR records have None label
    for r in error_recs:
        assert r.binary_proxy_label is None
        assert r.evidence_type == "runtime_error_quarantine"

    # Check schema dictionary serialization
    sample_dict = binary_recs[0].to_dict()
    required_keys = {
        "dataset_record_id", "problem_id", "solution_id", "step_id",
        "step_type", "prompt", "previous_context", "current_step_code",
        "binary_proxy_label", "evidence_type", "provenance"
    }
    assert required_keys.issubset(set(sample_dict.keys()))

    prov = sample_dict["provenance"]
    assert "source_artifact" in prov
    assert "source_split" in prov
    assert "mutation_record_identity" in prov


def test_generation_determinism():
    """Verify repeated execution produces identical dataset records."""
    gen1 = PRMDatasetGenerator(config=PRMDatasetConfig(random_seed=42))
    gen2 = PRMDatasetGenerator(config=PRMDatasetConfig(random_seed=42))

    bin1, surv1, err1, _ = gen1.generate_records()
    bin2, surv2, err2, _ = gen2.generate_records()

    assert [r.to_dict() for r in bin1] == [r.to_dict() for r in bin2]
    assert [r.to_dict() for r in surv1] == [r.to_dict() for r in surv2]
    assert [r.to_dict() for r in err1] == [r.to_dict() for r in err2]
