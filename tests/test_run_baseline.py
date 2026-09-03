import json

from partner_a.evaluation.run_baseline import main


def test_main_runs_evaluation_candidates(tmp_path, monkeypatch):
    problems_dir = tmp_path / "problems"
    problems_dir.mkdir()

    problem = {
        "problem_id": "eval_001",
        "task_id": 120,
        "test_list": [
            "assert max_product_tuple([(2, 3), (4, 5)]) == 20",
        ],
    }

    (problems_dir / "eval_001.json").write_text(
        json.dumps(problem),
        encoding="utf-8",
    )

    candidates_path = tmp_path / "candidates.jsonl"
    candidates_path.write_text(
        json.dumps(
            {
                "problem_id": "eval_001",
                "solution_id": "eval_001_sol_001",
                "code": "def max_product_tuple(pairs):\n"
                        "    return max(abs(x * y) for x, y in pairs)",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "baseline_results.jsonl"

    main(
        problems_dir=problems_dir,
        candidates_path=candidates_path,
        output_path=output_path,
    )

    rows = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(rows) == 1
    assert rows[0]["problem_id"] == "eval_001"
    assert rows[0]["solution_id"] == "eval_001_sol_001"
    assert rows[0]["baseline_result"] == "PASS"
    assert rows[0]["returncode"] == 0


def test_main_handles_unknown_problem(tmp_path):
    problems_dir = tmp_path / "problems"
    problems_dir.mkdir()

    candidates_path = tmp_path / "candidates.jsonl"
    candidates_path.write_text(
        json.dumps(
            {
                "problem_id": "missing",
                "solution_id": "missing_sol_001",
                "code": "def foo():\n    return 1",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "baseline_results.jsonl"

    main(
        problems_dir=problems_dir,
        candidates_path=candidates_path,
        output_path=output_path,
    )

    row = json.loads(output_path.read_text(encoding="utf-8").strip())

    assert row["baseline_result"] == "HARNESS_ERROR"
    assert "unknown problem" in row["stderr"]