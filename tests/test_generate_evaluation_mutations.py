import json
from pathlib import Path

from partner_a.evaluation.generate_mutations import main


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_main_only_mutates_baseline_passing_candidates(tmp_path, monkeypatch):
    candidates_path = tmp_path / "candidates.jsonl"
    baseline_path = tmp_path / "baseline.jsonl"
    output_path = tmp_path / "mutations.jsonl"

    candidates = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "code": "def f(x):\n    return x == 1\n",
        },
        {
            "problem_id": "eval_002",
            "solution_id": "eval_002_sol_001",
            "code": "def f(x):\n    return x != 1\n",
        },
    ]

    baseline = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "baseline_result": "PASS",
        },
        {
            "problem_id": "eval_002",
            "solution_id": "eval_002_sol_001",
            "baseline_result": "FAIL",
        },
    ]

    write_jsonl(candidates_path, candidates)
    write_jsonl(baseline_path, baseline)

    import partner_a.evaluation.generate_mutations as module

    monkeypatch.setattr(
        module,
        "process_candidate",
        lambda candidate: [
            {
                "problem_id": candidate["problem_id"],
                "solution_id": candidate["solution_id"],
                "mutation_type": "comparison_swap",
            }
        ],
    )

    main(
        candidates_path=candidates_path,
        baseline_path=baseline_path,
        output_path=output_path,
    )

    records = [
        json.loads(line)
        for line in output_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(records) == 1
    assert records[0]["solution_id"] == "eval_001_sol_001"


def test_main_writes_empty_output_when_no_candidates_pass(tmp_path):
    candidates_path = tmp_path / "candidates.jsonl"
    baseline_path = tmp_path / "baseline.jsonl"
    output_path = tmp_path / "mutations.jsonl"

    candidates = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "code": "def f(x):\n    return x\n",
        }
    ]

    baseline = [
        {
            "problem_id": "eval_001",
            "solution_id": "eval_001_sol_001",
            "baseline_result": "FAIL",
        }
    ]

    write_jsonl(candidates_path, candidates)
    write_jsonl(baseline_path, baseline)

    main(
        candidates_path=candidates_path,
        baseline_path=baseline_path,
        output_path=output_path,
    )

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") == ""