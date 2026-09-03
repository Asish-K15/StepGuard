import json
from pathlib import Path

from partner_a.evaluation.run_mutations import main


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_main_executes_mutation_and_marks_failure_detected(tmp_path, monkeypatch):
    problems_dir = tmp_path / "problems"
    mutations_path = tmp_path / "mutations.jsonl"
    output_path = tmp_path / "results.jsonl"

    problems_dir.mkdir()

    (problems_dir / "eval_001.json").write_text(
        json.dumps({"test_list": ["assert f(1) == 1"]}),
        encoding="utf-8",
    )

    write_jsonl(
        mutations_path,
        [
            {
                "problem_id": "eval_001",
                "solution_id": "eval_001_sol_001",
                "step_id": "func_01",
                "mutation_type": "comparison_swap",
                "original_code": "def f(x):\n    return x == 1\n",
                "mutated_code": "def f(x):\n    return x != 1\n",
                "changed": True,
                "original_operator": "==",
                "mutated_operator": "!=",
                "line": 2,
                "column": 13,
            }
        ],
    )

    import partner_a.evaluation.run_mutations as module

    monkeypatch.setattr(
        module,
        "run_candidate",
        lambda code, tests: {
            "status": "FAIL",
            "stdout": "",
            "stderr": "AssertionError",
            "returncode": 1,
        },
    )

    main(
        problems_dir=problems_dir,
        mutations_path=mutations_path,
        output_path=output_path,
    )

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(records) == 1
    assert records[0]["mutation_result"] == "FAIL"
    assert records[0]["detected"] is True


def test_main_marks_passing_mutation_undetected(tmp_path, monkeypatch):
    problems_dir = tmp_path / "problems"
    mutations_path = tmp_path / "mutations.jsonl"
    output_path = tmp_path / "results.jsonl"

    problems_dir.mkdir()

    (problems_dir / "eval_001.json").write_text(
        json.dumps({"test_list": ["assert f(1) == 1"]}),
        encoding="utf-8",
    )

    write_jsonl(
        mutations_path,
        [
            {
                "problem_id": "eval_001",
                "solution_id": "eval_001_sol_001",
                "step_id": "func_01",
                "mutation_type": "boolean_flip",
                "original_code": "def f(x):\n    return True\n",
                "mutated_code": "def f(x):\n    return False\n",
                "changed": True,
                "original_operator": "True",
                "mutated_operator": "False",
                "line": 2,
                "column": 11,
            }
        ],
    )

    import partner_a.evaluation.run_mutations as module

    monkeypatch.setattr(
        module,
        "run_candidate",
        lambda code, tests: {
            "status": "PASS",
            "stdout": "__STEPGUARD_PASS__",
            "stderr": "",
            "returncode": 0,
        },
    )

    main(
        problems_dir=problems_dir,
        mutations_path=mutations_path,
        output_path=output_path,
    )

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(records) == 1
    assert records[0]["mutation_result"] == "PASS"
    assert records[0]["detected"] is False