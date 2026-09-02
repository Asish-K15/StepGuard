"""
StepGuard Stage 0A - Partner B integration pipeline.

Pipeline:
    Partner A candidates.jsonl
        -> function decomposition
        -> block decomposition
        -> targeted mutations
        -> mutation_records.jsonl

Mutation types:
    B3.1 comparison_swap
    B3.2 boolean_flip
    B3.3 off_by_one
"""

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

CANDIDATES_FILE = (
    ROOT / "data" / "solutions" / "candidates.jsonl"
)

OUTPUT_FILE = (
    ROOT / "data" / "mutations" / "mutation_records.jsonl"
)


def read_jsonl(path: Path) -> list[dict]:
    """Read JSON Lines file."""

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
    """Write records as JSON Lines."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )


def mutation_result_to_record(result) -> dict | None:
    """
    Convert MutationResult into the shared JSONL representation.

    Only actual mutations are emitted.
    """

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


def generate_mutations_for_step(
    solution_code: str,
    step,
) -> list[dict]:
    """
    Generate all supported mutation types for one decomposition step.

    At most one mutation is produced for each mutation type.
    """

    mutation_functions = (
        mutate_comparison,
        mutate_boolean,
        mutate_off_by_one,
    )

    records = []

    for mutation_function in mutation_functions:
        result = mutation_function(
            solution_code,
            step,
        )

        record = mutation_result_to_record(result)

        if record is not None:
            records.append(record)

    return records


def process_candidate(candidate: dict) -> list[dict]:
    """Decompose and mutate one Partner A candidate."""

    problem_id = candidate["problem_id"]
    solution_id = candidate["solution_id"]
    solution_code = candidate["code"]

    records = []

    # ---------------------------------------------------------
    # Function-level decomposition
    # ---------------------------------------------------------

    function_steps = decompose_functions(
        problem_id,
        solution_id,
        solution_code,
    )

    for step in function_steps:
        records.extend(
            generate_mutations_for_step(
                solution_code,
                step,
            )
        )

    # ---------------------------------------------------------
    # Block-level decomposition
    # ---------------------------------------------------------

    block_steps = decompose_blocks(
        problem_id,
        solution_id,
        solution_code,
    )

    for step in block_steps:
        records.extend(
            generate_mutations_for_step(
                solution_code,
                step,
            )
        )

    return records


def main() -> None:
    candidates = read_jsonl(CANDIDATES_FILE)

    all_records = []

    for candidate in candidates:
        candidate_records = process_candidate(candidate)
        all_records.extend(candidate_records)

    write_jsonl(
        OUTPUT_FILE,
        all_records,
    )

    print("=" * 60)
    print("StepGuard Partner B Integration")
    print("=" * 60)
    print(f"Candidates processed : {len(candidates)}")
    print(f"Mutation records     : {len(all_records)}")
    print(f"Output               : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()