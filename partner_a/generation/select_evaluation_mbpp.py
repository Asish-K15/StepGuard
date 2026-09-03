import json
import random
from pathlib import Path

from datasets import load_dataset


SEED = 20260903

PILOT_TASK_IDS = {
    790,
    797,
    783,
    747,
    807,
}

SPLIT_COUNTS = {
    "train": 7,
    "test": 9,
    "validation": 4,
}

OUTPUT_DIR = Path("data/evaluation/problems")
MANIFEST_PATH = Path("data/evaluation/selection_manifest.json")


def main():
    print("Loading sanitized MBPP...")
    dataset = load_dataset(
        "google-research-datasets/mbpp",
        "sanitized",
    )

    rng = random.Random(SEED)
    selected = []

    for split_name, count in SPLIT_COUNTS.items():
        candidates = [
            item
            for item in dataset[split_name]
            if int(item["task_id"]) not in PILOT_TASK_IDS
        ]

        candidates = sorted(
            candidates,
            key=lambda item: int(item["task_id"]),
        )

        if len(candidates) < count:
            raise RuntimeError(
                f"Not enough eligible problems in {split_name}: "
                f"need {count}, found {len(candidates)}"
            )

        chosen = rng.sample(candidates, count)

        for item in chosen:
            selected.append(
                {
                    "source_split": split_name,
                    "task_id": int(item["task_id"]),
                    "prompt": item["prompt"],
                    "code": item["code"],
                    "test_imports": item["test_imports"],
                    "test_list": item["test_list"],
                    "source_file": item["source_file"],
                }
            )

    selected.sort(
        key=lambda item: (
            item["source_split"],
            item["task_id"],
        )
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    for index, item in enumerate(selected, start=1):
        problem_id = f"eval_{index:03d}"

        record = {
            "problem_id": problem_id,
            **item,
        }

        output_path = OUTPUT_DIR / f"{problem_id}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                record,
                f,
                indent=2,
                ensure_ascii=False,
            )

        records.append(
            {
                "problem_id": problem_id,
                "task_id": item["task_id"],
                "source_split": item["source_split"],
            }
        )

        print(
            f"Wrote {output_path} "
            f"(task {item['task_id']}, {item['source_split']})"
        )

    manifest = {
        "project": "StepGuard",
        "experiment": "larger_evaluation",
        "selection": {
            "dataset": "google-research-datasets/mbpp",
            "config": "sanitized",
            "seed": SEED,
            "pilot_task_ids_excluded": sorted(PILOT_TASK_IDS),
            "split_counts": SPLIT_COUNTS,
            "total_problem_count": len(selected),
        },
        "problems": records,
    }

    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            manifest,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nWrote {len(selected)} evaluation problems.")
    print(f"Wrote selection manifest to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
