import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "evidence" / "survivor_classification.json"


result = {
    "classifications": [
        {
            "problem_id": "mbpp_003",
            "mutation_type": "comparison_swap",
            "operator_change": "==->!=",
            "location": "block_08",
            "line": 12,
            "solution_count": 5,
            "observation": (
                "The mutation changes the final RGB branch condition "
                "from equality to inequality and remains undetected "
                "by the pilot tests."
            ),
        },
        {
            "problem_id": "mbpp_004",
            "mutation_type": "boolean_flip",
            "operator_change": "or->and",
            "locations": ["block_05", "func_01"],
            "lines": [9, 10, 11],
            "solution_count": 4,
            "observation": (
                "The mutation changes the LCS boundary condition from "
                "an OR chain to a mixed AND/OR condition and remains "
                "undetected by the pilot tests."
            ),
        },
    ]
}


OUTPUT.write_text(
    json.dumps(result, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Wrote {OUTPUT}")
print("Classifications:", len(result["classifications"]))
