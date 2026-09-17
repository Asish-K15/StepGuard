import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

BASELINE_INPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "solutions"
    / "baseline_results.jsonl"
)

MUTATION_INPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "mutations"
    / "mutation_records.jsonl"
)

EXECUTION_INPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "mutations"
    / "mutation_execution_results.jsonl"
)

OUTPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "evaluation_summary.json"
)


ALLOWED_BASELINE_RESULTS = {
    "PASS",
    "FAIL",
    "RUNTIME_ERROR",
    "SYNTAX_ERROR",
    "TIMEOUT",
    "HARNESS_ERROR",
}

ALLOWED_MUTATION_RESULTS = {
    "PASS",
    "FAIL",
    "RUNTIME_ERROR",
}


def read_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open(encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {path}"
                ) from exc

    return records


def rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def build_summary(
    baseline: list[dict],
    mutations: list[dict],
    executions: list[dict],
) -> dict:
    """
    Build the larger-evaluation evidence summary.

    Baseline records describe candidate execution against the original
    MBPP tests.

    Mutation records describe mutations generated from baseline-passing
    candidates.

    Execution records describe the result of running each generated
    mutation against the corresponding tests.
    """

    baseline_results = Counter(
        record["baseline_result"]
        for record in baseline
    )

    unexpected_baseline = (
        set(baseline_results)
        - ALLOWED_BASELINE_RESULTS
    )

    if unexpected_baseline:
        raise ValueError(
            "Unexpected baseline results: "
            f"{sorted(unexpected_baseline)}"
        )

    mutation_results = Counter(
        record["mutation_result"]
        for record in executions
    )

    unexpected_mutation = (
        set(mutation_results)
        - ALLOWED_MUTATION_RESULTS
    )

    if unexpected_mutation:
        raise ValueError(
            "Unexpected mutation results: "
            f"{sorted(unexpected_mutation)}"
        )

    candidate_ids = {
        record["solution_id"]
        for record in baseline
    }

    passing_candidate_ids = {
        record["solution_id"]
        for record in baseline
        if record["baseline_result"] == "PASS"
    }

    mutated_candidate_ids = {
        record["solution_id"]
        for record in mutations
    }

    problems = {
        record["problem_id"]
        for record in baseline
    }

    passing_problems = {
        record["problem_id"]
        for record in baseline
        if record["baseline_result"] == "PASS"
    }

    problems_with_mutations = {
        record["problem_id"]
        for record in mutations
    }

    passing_candidates_with_mutations = (
        passing_candidate_ids
        & mutated_candidate_ids
    )

    passing_candidates_without_mutations = (
        passing_candidate_ids
        - mutated_candidate_ids
    )

    detected_count = sum(
        1
        for record in executions
        if record["detected"]
    )

    undetected_count = (
        len(executions)
        - detected_count
    )

    by_type = {}

    mutation_types = sorted(
        {
            record["mutation_type"]
            for record in executions
        }
    )

    for mutation_type in mutation_types:
        rows = [
            record
            for record in executions
            if record["mutation_type"] == mutation_type
        ]

        results = Counter(
            record["mutation_result"]
            for record in rows
        )

        detected = sum(
            1
            for record in rows
            if record["detected"]
        )

        by_type[mutation_type] = {
            "mutation_count": len(rows),
            "results": dict(
                sorted(results.items())
            ),
            "detected_count": detected,
            "undetected_count": (
                len(rows) - detected
            ),
            "detection_rate": rate(
                detected,
                len(rows),
            ),
        }

    by_problem = {}

    mutation_problem_ids = sorted(
        {
            record["problem_id"]
            for record in executions
        }
    )

    for problem_id in mutation_problem_ids:
        rows = [
            record
            for record in executions
            if record["problem_id"] == problem_id
        ]

        results = Counter(
            record["mutation_result"]
            for record in rows
        )

        detected = sum(
            1
            for record in rows
            if record["detected"]
        )

        by_problem[problem_id] = {
            "mutation_count": len(rows),
            "results": dict(
                sorted(results.items())
            ),
            "detected_count": detected,
            "undetected_count": (
                len(rows) - detected
            ),
            "detection_rate": rate(
                detected,
                len(rows),
            ),
        }

    summary = {
        "scope": {
            "problem_count": len(problems),
            "candidate_count": len(candidate_ids),
            "baseline_pass_count": len(
                passing_candidate_ids
            ),
            "baseline_pass_rate": rate(
                len(passing_candidate_ids),
                len(candidate_ids),
            ),
        },
        "baseline_results": dict(
            sorted(baseline_results.items())
        ),
        "mutation_coverage": {
            "passing_candidate_count": len(
                passing_candidate_ids
            ),
            "passing_candidates_with_mutations": len(
                passing_candidates_with_mutations
            ),
            "passing_candidates_without_mutations": len(
                passing_candidates_without_mutations
            ),
            "coverage_rate": rate(
                len(passing_candidates_with_mutations),
                len(passing_candidate_ids),
            ),
            "problems_with_mutations": len(
                problems_with_mutations
            ),
            "passing_problems": len(
                passing_problems
            ),
        },
        "mutations": {
            "mutation_record_count": len(
                mutations
            ),
            "execution_count": len(
                executions
            ),
            "detected_count": detected_count,
            "undetected_count": undetected_count,
            "detection_rate": rate(
                detected_count,
                len(executions),
            ),
            "execution_results": dict(
                sorted(mutation_results.items())
            ),
            "by_mutation_type": by_type,
            "by_problem": by_problem,
        },
    }

    return summary


def main() -> None:
    baseline = read_jsonl(
        BASELINE_INPUT
    )

    mutations = read_jsonl(
        MUTATION_INPUT
    )

    executions = read_jsonl(
        EXECUTION_INPUT
    )

    summary = build_summary(
        baseline,
        mutations,
        executions,
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            summary,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {OUTPUT}")

    print(
        "Problems:",
        summary["scope"]["problem_count"],
    )

    print(
        "Candidates:",
        summary["scope"]["candidate_count"],
    )

    print(
        "Baseline PASS:",
        summary["scope"]["baseline_pass_count"],
    )

    print(
        "Baseline pass rate:",
        f"{summary['scope']['baseline_pass_rate']:.4f}",
    )

    print(
        "Passing candidates with mutations:",
        summary[
            "mutation_coverage"
        ][
            "passing_candidates_with_mutations"
        ],
    )

    print(
        "Passing candidates without mutations:",
        summary[
            "mutation_coverage"
        ][
            "passing_candidates_without_mutations"
        ],
    )

    print(
        "Mutation coverage:",
        f"{summary['mutation_coverage']['coverage_rate']:.4f}",
    )

    print(
        "Problems with mutations:",
        summary[
            "mutation_coverage"
        ][
            "problems_with_mutations"
        ],
    )

    print(
        "Passing problems:",
        summary[
            "mutation_coverage"
        ][
            "passing_problems"
        ],
    )

    print(
        "Mutations:",
        summary["mutations"]["execution_count"],
    )

    print(
        "Detected:",
        summary["mutations"]["detected_count"],
    )

    print(
        "Undetected:",
        summary["mutations"]["undetected_count"],
    )

    print(
        "Detection rate:",
        f"{summary['mutations']['detection_rate']:.4f}",
    )


if __name__ == "__main__":
    main()