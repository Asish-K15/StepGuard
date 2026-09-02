from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "pilot_limitations.md"


def load_report():
    return REPORT.read_text(encoding="utf-8")


def test_limitations_report_exists():
    assert REPORT.exists()


def test_limitations_report_scope():
    report = load_report()

    assert "five MBPP problems and 25 generated candidate" in report
    assert "99 evaluated mutations" in report
    assert "86 were" in report
    assert "13 remained undetected" in report
    assert "86.87%" in report
    assert "These results describe the current pilot dataset only." in report
    assert "general estimate of StepGuard performance" in report


def test_limitations_report_mutation_types():
    report = load_report()

    assert "| boolean_flip | 11 | 3 | 8 | 27.27% |" in report
    assert "| comparison_swap | 74 | 69 | 5 | 93.24% |" in report
    assert "| off_by_one | 14 | 14 | 0 | 100.00% |" in report


def test_limitations_report_survivors():
    report = load_report()

    assert "mbpp_003" in report
    assert "comparison_swap" in report
    assert "`==` to `!=`" in report

    assert "mbpp_004" in report
    assert "boolean_flip" in report
    assert "`or` to `and`" in report


def test_limitations_report_step_analysis():
    report = load_report()

    assert "77 step-level groups" in report
    assert "64 fully detected" in report
    assert "8 partially detected" in report
    assert "5 undetected" in report


def test_limitations_report_next_steps():
    report = load_report()

    assert "expand the number of MBPP problems" in report
    assert "increase the number of generated candidate solutions" in report
    assert "evaluate additional mutation operators" in report
    assert "strengthen tests around observed survivor patterns" in report


def test_limitations_report_generalization_warning():
    report = load_report()

    assert "These results describe the current pilot dataset only." in report
    assert "general estimate of StepGuard performance" in report
    assert "rather than a final performance characterization" in report
