import ast
from datasets import load_dataset


def analyze_code(code: str) -> dict:
    """Extract structural features from a Python solution."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {
            "functions": -1,
            "ifs": -1,
            "loops": -1,
            "max_depth": -1,
            "lines": len(code.splitlines()),
            "parse_error": True,
        }

    functions = sum(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )

    ifs = sum(
        isinstance(node, ast.If)
        for node in ast.walk(tree)
    )

    loops = sum(
        isinstance(node, (ast.For, ast.While))
        for node in ast.walk(tree)
    )

    def depth(node, current=0):
        children = list(ast.iter_child_nodes(node))
        if not children:
            return current
        return max(depth(child, current + 1) for child in children)

    return {
        "functions": functions,
        "ifs": ifs,
        "loops": loops,
        "max_depth": depth(tree),
        "lines": len(code.splitlines()),
        "parse_error": False,
    }


def main():
    print("Loading sanitized MBPP...")
    dataset = load_dataset(
        "google-research-datasets/mbpp",
        "sanitized",
    )

    train = dataset["train"]

    print(f"Loaded {len(train)} training problems.\n")

    results = []

    for item in train:
        features = analyze_code(item["code"])

        results.append({
            "task_id": item["task_id"],
            "prompt": item["prompt"],
            "code": item["code"],
            **features,
        })

    # Sort by structural complexity.
    results.sort(
        key=lambda x: (
            x["functions"],
            x["ifs"],
            x["loops"],
            x["max_depth"],
        )
    )

    print("=" * 80)
    print("MBPP STRUCTURAL INSPECTION")
    print("=" * 80)

    for item in results:
        print(
            f"\nTask ID: {item['task_id']}"
            f"\nFunctions: {item['functions']}"
            f"\nIfs: {item['ifs']}"
            f"\nLoops: {item['loops']}"
            f"\nDepth: {item['max_depth']}"
            f"\nLines: {item['lines']}"
            f"\nPrompt: {item['prompt'][:150]}"
            f"\nCode:\n{item['code']}"
        )


if __name__ == "__main__":
    main()