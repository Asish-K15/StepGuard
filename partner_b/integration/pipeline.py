
"""
StepGuard Stage 0A - Partner B integration pipeline.
Supports custom input and output paths.
"""

import argparse
import json
from pathlib import Path

from partner_b.decomposition.function import decompose_functions
from partner_b.decomposition.block import decompose_blocks
from partner_b.mutation.mutator import (
    mutate_comparison,
    mutate_boolean,
    mutate_off_by_one,
)

ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CANDIDATES_FILE = ROOT / "data" / "solutions" / "candidates.jsonl"
DEFAULT_OUTPUT_FILE = ROOT / "data" / "mutations" / "mutation_records.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at {path}, line {line_number}"
                ) from exc

    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def mutation_result_to_record(result) -> dict | None:
    if not result.changed:
        return None

    return {
        "problem_id": result.problem_id,
        "solution_id": result.solution_id,
        "step_id": result.step_id,
        "mutation_type": result.mutation_type,
        "original_code": result.original_code,
        "mutated_code": result.mutated_code,
        "changed": result.changed,
        "original_operator": result.original_operator,
        "mutated_operator": result.mutated_operator,
        "line": result.line,
        "column": result.column,
    }


def generate_mutations_for_step(solution_code: str, step) -> list[dict]:
    records = []

    for mutation_function in (
        mutate_comparison,
        mutate_boolean,
        mutate_off_by_one,
    ):
        result = mutation_function(solution_code, step)
        record = mutation_result_to_record(result)

        if record is not None:
            records.append(record)

    return records


def process_candidate(candidate: dict) -> list[dict]:
    problem_id = candidate["problem_id"]
    solution_id = candidate["solution_id"]
    solution_code = candidate["code"]

    records = []

    function_steps = decompose_functions(
        problem_id,
        solution_id,
        solution_code,
    )

    for step in function_steps:
        records.extend(
            generate_mutations_for_step(solution_code, step)
        )

    block_steps = decompose_blocks(
        problem_id,
        solution_id,
        solution_code,
    )

    for step in block_steps:
        records.extend(
            generate_mutations_for_step(solution_code, step)
        )

    return records


def run_pipeline(
    candidates_file: Path,
    output_file: Path,
) -> int:
    candidates = read_jsonl(candidates_file)
    all_records = []

    for candidate in candidates:
        all_records.extend(process_candidate(candidate))

    write_jsonl(output_file, all_records)

    print("=" * 60)
    print("StepGuard Partner B Integration")
    print("=" * 60)
    print(f"Candidates processed : {len(candidates)}")
    print(f"Mutation records     : {len(all_records)}")
    print(f"Output               : {output_file}")
    print("=" * 60)

    return len(all_records)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_CANDIDATES_FILE,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
    )

    args = parser.parse_args()

    run_pipeline(
        args.input,
        args.output,
    )


if __name__ == "__main__":
    main()