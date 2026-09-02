
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MUTATION_FILE = ROOT / "data" / "mutations" / "mutation_records.jsonl"


def load_records():
    with MUTATION_FILE.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_all_mutated_code_is_valid_python():
    records = load_records()

    assert len(records) == 99

    for record in records:
        ast.parse(record["mutated_code"])


def test_every_record_is_actually_changed():
    records = load_records()

    for record in records:
        assert record["changed"] is True
        assert record["original_code"] != record["mutated_code"]


def test_required_metadata_exists():
    records = load_records()

    required = {
        "problem_id",
        "solution_id",
        "step_id",
        "mutation_type",
        "original_code",
        "mutated_code",
        "changed",
    }

    for record in records:
        assert required.issubset(record.keys())


def test_only_expected_mutation_types_exist():
    records = load_records()

    allowed = {
        "comparison_swap",
        "boolean_flip",
        "off_by_one",
    }

    for record in records:
        assert record["mutation_type"] in allowed


def test_mutated_program_preserves_function_indentation():
    records = load_records()

    for record in records:
        original_lines = record["original_code"].splitlines()
        mutated_lines = record["mutated_code"].splitlines()

        assert len(original_lines) == len(mutated_lines)

        for original, mutated in zip(original_lines, mutated_lines):
            if original != mutated:
                original_indent = len(original) - len(original.lstrip())
                mutated_indent = len(mutated) - len(mutated.lstrip())

                assert original_indent == mutated_indent, (
                    f"Unexpected indentation change in "
                    f"{record['solution_id']} / "
                    f"{record['mutation_type']}: "
                    f"{original!r} -> {mutated!r}"
                )