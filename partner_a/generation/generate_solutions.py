import ast
import json
from pathlib import Path

import requests


MODEL = "qwen2.5-coder:7b"
OLLAMA_URL = "http://localhost:11434/api/generate"

TEMPERATURES = [0.2, 0.6, 1.0]

PROBLEMS_DIR = Path("data/problems")
OUTPUT_FILE = Path("data/solutions/candidates.jsonl")


def load_problem(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_required_function(problem: dict) -> str:
    """Find the top-level function called by the MBPP tests."""

    tree = ast.parse(problem["code"])

    top_level_functions = {
        node.name
        for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    called_functions = set()

    for test in problem["test_list"]:
        try:
            test_tree = ast.parse(test)
        except SyntaxError:
            continue

        for node in ast.walk(test_tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_functions.add(node.func.id)

    matching_functions = (
        top_level_functions & called_functions
    )

    if not matching_functions:
        raise ValueError(
            f"Could not identify benchmark entry function "
            f"for {problem['pilot_id']}. "
            f"Top-level functions: {sorted(top_level_functions)}"
        )

    if len(matching_functions) > 1:
        raise ValueError(
            f"Multiple benchmark entry functions found for "
            f"{problem['pilot_id']}: "
            f"{sorted(matching_functions)}"
        )

    return next(iter(matching_functions))


def build_prompt(problem: dict, function_name: str) -> str:
    return f"""You are generating a candidate solution for a Python programming benchmark.

Problem:
{problem["prompt"]}

Required function:
{function_name}

Requirements:
- Return only Python code.
- You MUST define the function exactly as: {function_name}
- Do not rename the function.
- Do not include markdown fences.
- Do not include explanations.
- Do not include test code.

Generate one correct candidate solution.
"""


def generate(prompt: str, temperature: float) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=180,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"].strip()


def clean_code(text: str) -> str:
    """Remove accidental Markdown code fences."""
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return text


def is_valid_python(code: str) -> bool:
    try:
        compile(code, "<generated>", "exec")
        return True
    except SyntaxError:
        return False


def has_required_function(code: str, function_name: str) -> bool:
    """Check that the generated code defines the required function."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
        for node in tree.body
    )


def generate_for_problem(problem: dict, count: int = 3) -> list[dict]:
    records = []

    function_name = get_required_function(problem)

    print(f"Required function: {function_name}")

    for index in range(count):
        temperature = TEMPERATURES[index % len(TEMPERATURES)]

        print(
            f"Generating {problem['pilot_id']} "
            f"candidate {index + 1}/{count} "
            f"(temperature={temperature})..."
        )

        prompt = build_prompt(problem, function_name)

        raw_output = generate(prompt, temperature)
        code = clean_code(raw_output)

        parse_valid = is_valid_python(code)

        record = {
            "problem_id": problem["pilot_id"],
            "task_id": problem["task_id"],
            "solution_id": (
                f"{problem['pilot_id']}_sol_{index + 1:03d}"
            ),
            "temperature": temperature,
            "required_function": function_name,
            "code": code,
            "parse_valid": parse_valid,
            "required_function_present": (
                has_required_function(code, function_name)
                if parse_valid
                else False
            ),
        }

        records.append(record)

    return records


def main():
    problem_paths = sorted(PROBLEMS_DIR.glob("mbpp_*.json"))

    if not problem_paths:
        raise FileNotFoundError(
            f"No MBPP problems found in {PROBLEMS_DIR}"
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    all_records = []

    for problem_path in problem_paths:
        problem = load_problem(problem_path)

        print(
            f"\nProcessing {problem['pilot_id']} "
            f"(task {problem['task_id']})"
        )

        records = generate_for_problem(
            problem,
            count=5,
        )

        all_records.extend(records)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(
                json.dumps(record, ensure_ascii=False)
                + "\n"
            )

    print(
        f"\nWrote {len(all_records)} candidates "
        f"to {OUTPUT_FILE}"
    )

    expected_problem_count = 5
    expected_candidates_per_problem = 5

    assert len(all_records) == expected_problem_count * expected_candidates_per_problem, (
       f"Expected 25 candidates, found {len(all_records)}"
    )

    counts = {}
    for record in all_records:
      problem_id = record["problem_id"]
      counts[problem_id] = counts.get(problem_id, 0) + 1

    assert len(counts) == expected_problem_count, (
    f"Expected {expected_problem_count} problems, found {len(counts)}"
    )

    assert all(
      count == expected_candidates_per_problem
      for count in counts.values()
    ), f"Expected 5 candidates per problem, got {counts}"

    print("Validated 5 problems x 5 candidates = 25 candidates.")
if __name__ == "__main__":
    main()