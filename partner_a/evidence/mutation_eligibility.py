import ast
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

OUTPUT = (
    ROOT
    / "data"
    / "evaluation"
    / "mutation_eligibility.json"
)


SUPPORTED_COMPARISONS = {
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
}

SUPPORTED_BOOLEAN_OPERATORS = {
    ast.And,
    ast.Or,
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


def _build_parent_map(tree: ast.AST) -> dict:
    parent_map = {}

    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent

    return parent_map


def _is_direct_subscript_index(
    node: ast.BinOp,
    parent_map: dict,
) -> bool:
    parent = parent_map.get(node)

    if not isinstance(parent, ast.Subscript):
        return False

    return parent.slice is node


def _is_direct_range_argument(
    node: ast.BinOp,
    parent_map: dict,
) -> bool:
    parent = parent_map.get(node)

    if not isinstance(parent, ast.Call):
        return False

    if not isinstance(parent.func, ast.Name):
        return False

    if parent.func.id != "range":
        return False

    return node in parent.args


def analyze_code(code: str) -> dict:
    tree = ast.parse(code)
    parent_map = _build_parent_map(tree)

    comparison_targets = 0
    boolean_targets = 0
    off_by_one_targets = 0

    comparison_operators = Counter()
    boolean_operators = Counter()
    off_by_one_contexts = Counter()

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operator in node.ops:
                if type(operator) in SUPPORTED_COMPARISONS:
                    comparison_targets += 1
                    comparison_operators[type(operator).__name__] += 1

        elif isinstance(node, ast.BoolOp):
            if type(node.op) in SUPPORTED_BOOLEAN_OPERATORS:
                boolean_targets += 1
                boolean_operators[type(node.op).__name__] += 1

        elif isinstance(node, ast.Constant):
            if type(node.value) is bool:
                boolean_targets += 1
                boolean_operators[
                    "True" if node.value else "False"
                ] += 1

        elif isinstance(node, ast.BinOp):
            if not (
                isinstance(node.right, ast.Constant)
                and type(node.right.value) is int
                and node.right.value == 1
            ):
                continue

            if not isinstance(node.op, (ast.Add, ast.Sub)):
                continue

            is_index = _is_direct_subscript_index(
                node,
                parent_map,
            )

            is_range = _is_direct_range_argument(
                node,
                parent_map,
            )

            if is_index:
                off_by_one_targets += 1
                off_by_one_contexts["subscript"] += 1

            elif is_range:
                off_by_one_targets += 1
                off_by_one_contexts["range"] += 1

    return {
        "comparison_targets": comparison_targets,
        "boolean_targets": boolean_targets,
        "off_by_one_targets": off_by_one_targets,
        "comparison_operators": dict(sorted(comparison_operators.items())),
        "boolean_operators": dict(sorted(boolean_operators.items())),
        "off_by_one_contexts": dict(sorted(off_by_one_contexts.items())),
        "eligible": (
            comparison_targets > 0
            or boolean_targets > 0
            or off_by_one_targets > 0
        ),
    }


def build_eligibility(baseline: list[dict]) -> dict:
    passing = [
        record
        for record in baseline
        if record["baseline_result"] == "PASS"
    ]

    candidates = []
    by_problem = {}

    for record in sorted(
        passing,
        key=lambda item: (
            item["problem_id"],
            item["solution_id"],
        ),
    ):
        analysis = analyze_code(record["solution_code"])

        candidate = {
            "problem_id": record["problem_id"],
            "solution_id": record["solution_id"],
            **analysis,
        }

        candidates.append(candidate)

        by_problem.setdefault(
            record["problem_id"],
            {
                "candidate_count": 0,
                "eligible_candidate_count": 0,
                "ineligible_candidate_count": 0,
                "comparison_target_count": 0,
                "boolean_target_count": 0,
                "off_by_one_target_count": 0,
            },
        )

        problem = by_problem[record["problem_id"]]

        problem["candidate_count"] += 1

        if analysis["eligible"]:
            problem["eligible_candidate_count"] += 1
        else:
            problem["ineligible_candidate_count"] += 1

        problem["comparison_target_count"] += analysis[
            "comparison_targets"
        ]

        problem["boolean_target_count"] += analysis[
            "boolean_targets"
        ]

        problem["off_by_one_target_count"] += analysis[
            "off_by_one_targets"
        ]

    eligible_count = sum(
        1
        for candidate in candidates
        if candidate["eligible"]
    )

    ineligible_count = len(candidates) - eligible_count

    summary = {
        "scope": {
            "baseline_passing_candidates": len(candidates),
        },
        "candidate_eligibility": {
            "eligible_candidates": eligible_count,
            "ineligible_candidates": ineligible_count,
            "eligibility_rate": (
                eligible_count / len(candidates)
                if candidates
                else 0.0
            ),
        },
        "by_problem": dict(sorted(by_problem.items())),
        "candidates": candidates,
    }

    return summary


def main() -> None:
    baseline = read_jsonl(BASELINE_INPUT)

    summary = build_eligibility(baseline)

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
        "Baseline-passing candidates:",
        summary["scope"]["baseline_passing_candidates"],
    )
    print(
        "Eligible candidates:",
        summary["candidate_eligibility"]["eligible_candidates"],
    )
    print(
        "Ineligible candidates:",
        summary["candidate_eligibility"]["ineligible_candidates"],
    )
    print(
        "Eligibility rate:",
        f"{summary['candidate_eligibility']['eligibility_rate']:.4f}",
    )


if __name__ == "__main__":
    main()