from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def load_readme():
    return README.read_text(encoding="utf-8-sig")


def test_readme_exists():
    assert README.exists()


def test_readme_contains_pilot_scope():
    readme = load_readme()

    assert "# StepGuard" in readme
    assert "5 MBPP problems" in readme
    assert "25 generated candidate solutions" in readme
    assert "25 baseline-passing candidates" in readme
    assert "99 evaluated mutations" in readme


def test_readme_contains_pilot_results():
    readme = load_readme()

    assert "86 were detected" in readme
    assert "13 were undetected" in readme
    assert "86.87%" in readme


def test_readme_contains_mutation_types():
    readme = load_readme()

    assert "| boolean_flip | 11 | 3 | 8 | 27.27% |" in readme
    assert "| comparison_swap | 74 | 69 | 5 | 93.24% |" in readme
    assert "| off_by_one | 14 | 14 | 0 | 100.00% |" in readme


def test_readme_contains_reproducibility():
    readme = load_readme()

    assert "python -m pytest -q" in readme
    assert "python partner_a\\evidence\\validate_pilot_reproducibility.py" in readme
    assert "Pilot reproducibility validation: PASS" in readme


def test_readme_contains_limitations():
    readme = load_readme()

    assert "exploratory pilot" in readme
    assert "should not be treated as a general estimate" in readme


def test_readme_contains_generation_setup():
    readme = load_readme()

    assert "Qwen qwen2.5-coder:7b" in readme
