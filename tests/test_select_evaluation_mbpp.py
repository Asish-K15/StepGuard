import json
import random
from pathlib import Path


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


def test_selection_protocol_is_deterministic():
    dataset = {
        "train": [
            {"task_id": task_id}
            for task_id in range(602, 717)
            if task_id not in PILOT_TASK_IDS
        ],
        "test": [
            {"task_id": task_id}
            for task_id in range(11, 268)
            if task_id not in PILOT_TASK_IDS
        ],
        "validation": [
            {"task_id": task_id}
            for task_id in range(554, 597)
            if task_id not in PILOT_TASK_IDS
        ],
    }

    rng = random.Random(SEED)
    selected = []

    for split_name, count in SPLIT_COUNTS.items():
        candidates = sorted(
            dataset[split_name],
            key=lambda item: int(item["task_id"]),
        )
        chosen = rng.sample(candidates, count)

        selected.extend(
            (split_name, int(item["task_id"]))
            for item in chosen
        )

    assert len(selected) == 20
    assert len({task_id for _, task_id in selected}) == 20

    counts = {}
    for split_name, _ in selected:
        counts[split_name] = counts.get(split_name, 0) + 1

    assert counts == {
        "train": 7,
        "test": 9,
        "validation": 4,
    }

    assert all(
        task_id not in PILOT_TASK_IDS
        for _, task_id in selected
    )


def test_selection_manifest_structure():
    manifest_path = Path("data/evaluation/selection_manifest.json")

    if not manifest_path.exists():
        return

    with manifest_path.open("r", encoding="utf-8-sig") as f:
        manifest = json.load(f)

    assert manifest["project"] == "StepGuard"
    assert manifest["experiment"] == "larger_evaluation"
    assert manifest["selection"]["seed"] == SEED
    assert manifest["selection"]["total_problem_count"] == 20
