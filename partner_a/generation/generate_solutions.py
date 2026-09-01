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
    """Extract the required function name from the MBPP reference code."""
    tree = ast.parse(problem["code"])

    functions = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

    if not functions:
        raise ValueError(
            f"No top-level function found for {problem['pilot_id']}"
        )

    if len(functions) > 1:
        raise ValueError(
            f"Multiple top-level functions found for "
            f"{problem['pilot_id']}: {functions}"
        )

    return functions[0]


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
    problem_path = PROBLEMS_DIR / "mbpp_001.json"

    if not problem_path.exists():
        raise FileNotFoundError(problem_path)

    problem = load_problem(problem_path)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    records = generate_for_problem(problem, count=3)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(records)} candidates to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()