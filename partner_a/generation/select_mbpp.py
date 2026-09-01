import json
from pathlib import Path

from datasets import load_dataset


# Pilot mapping:
# Our local pilot ID -> original MBPP task ID
SELECTED_TASKS = {
    "mbpp_001": 790,
    "mbpp_002": 797,
    "mbpp_003": 783,
    "mbpp_004": 747,
    "mbpp_005": 807,
}


def main():
    print("Loading sanitized MBPP...")
    dataset = load_dataset(
        "google-research-datasets/mbpp",
        "sanitized",
    )

    # Search all available splits so we don't accidentally assume
    # that a selected task is in train.
    selected = {}

    for split_name, split in dataset.items():
        for item in split:
            task_id = item["task_id"]

            for pilot_id, wanted_id in SELECTED_TASKS.items():
                if task_id == wanted_id:
                    selected[pilot_id] = {
                        "pilot_id": pilot_id,
                        "task_id": task_id,
                        "prompt": item["prompt"],
                        "code": item["code"],
                        "test_imports": item["test_imports"],
                        "test_list": item["test_list"],
                        "source_file": item["source_file"],
                        "source_split": split_name,
                    }

    missing = set(SELECTED_TASKS) - set(selected)

    if missing:
        raise RuntimeError(
            f"Could not find selected tasks: {sorted(missing)}"
        )

    output_dir = Path("data/problems")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pilot_id, record in selected.items():
        output_path = output_dir / f"{pilot_id}.json"

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        print(f"Wrote {output_path}")

    print("\nSelected MBPP problems:")
    for pilot_id, record in selected.items():
        print(
            f"{pilot_id}: "
            f"MBPP task {record['task_id']} "
            f"({record['source_split']})"
        )


if __name__ == "__main__":
    main()