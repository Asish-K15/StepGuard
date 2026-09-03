import json
from pathlib import Path

import pytest

from partner_a.generation import generate_solutions


def write_problem(path, problem_id_key, problem_id):
    record = {
        problem_id_key: problem_id,
        "task_id": 1,
        "prompt": "Return the input value.",
        "code": "def echo(x):\n    return x\n",
        "test_imports": [],
        "test_list": ["assert echo(1) == 1"],
        "source_file": "test.json",
        "source_split": "test",
    }

    path.write_text(
        json.dumps(record),
        encoding="utf-8",
    )


def test_get_problem_id_supports_pilot_schema():
    assert generate_solutions.get_problem_id(
        {"pilot_id": "mbpp_001"}
    ) == "mbpp_001"


def test_get_problem_id_supports_evaluation_schema():
    assert generate_solutions.get_problem_id(
        {"problem_id": "eval_001"}
    ) == "eval_001"


def test_main_scales_to_arbitrary_problem_count(
    tmp_path,
    monkeypatch,
):
    problems_dir = tmp_path / "problems"
    output_file = tmp_path / "solutions.jsonl"
    problems_dir.mkdir()

    for index in range(4):
        write_problem(
            problems_dir / f"mbpp_{index:03d}.json",
            "problem_id",
            f"eval_{index + 1:03d}",
        )

    def fake_generate(prompt, temperature):
        return "def echo(x):\n    return x\n"

    monkeypatch.setattr(
        generate_solutions,
        "generate",
        fake_generate,
    )

    generate_solutions.main(
        problems_dir=problems_dir,
        output_file=output_file,
        candidates_per_problem=5,
    )

    records = [
        json.loads(line)
        for line in output_file.read_text(
            encoding="utf-8"
        ).splitlines()
    ]

    assert len(records) == 20

    counts = {}
    for record in records:
        counts[record["problem_id"]] = (
            counts.get(record["problem_id"], 0) + 1
        )

    assert counts == {
        "eval_001": 5,
        "eval_002": 5,
        "eval_003": 5,
        "eval_004": 5,
    }


def test_main_rejects_zero_candidates(tmp_path):
    problems_dir = tmp_path / "problems"
    output_file = tmp_path / "solutions.jsonl"
    problems_dir.mkdir()

    write_problem(
        problems_dir / "mbpp_001.json",
        "pilot_id",
        "mbpp_001",
    )

    with pytest.raises(ValueError, match="at least 1"):
        generate_solutions.main(
            problems_dir=problems_dir,
            output_file=output_file,
            candidates_per_problem=0,
        )
