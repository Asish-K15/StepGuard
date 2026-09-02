from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "data" / "evidence" / "pilot_report.md"


def load_report():
    return REPORT.read_text(encoding="utf-8")


def test_report_exists():
    assert REPORT.exists()


def test_report_contains_pilot_scope():
    report = load_report()

    assert "# StepGuard Pilot Report" in report
    assert "- Problems: 5" in report
    assert "- Generated candidates: 25" in report
    assert "- Baseline pass rate: 100.00%" in report


def test_report_contains_mutation_results():
    report = load_report()

    assert "- Mutations evaluated: 99" in report
    assert "- Detected mutations: 86" in report
    assert "- Undetected mutations: 13" in report
    assert "- Overall mutation detection rate: 86.87%" in report


def test_report_contains_mutation_type_results():
    report = load_report()

    assert "| boolean_flip | 11 | 3 | 8 | 27.27% |" in report
    assert "| comparison_swap | 74 | 69 | 5 | 93.24% |" in report
    assert "| off_by_one | 14 | 14 | 0 | 100.00% |" in report


def test_report_contains_step_analysis():
    report = load_report()

    assert "- Step groups analyzed: 77" in report
    assert "- Fully detected: 64" in report
    assert "- Partially detected: 8" in report
    assert "- Undetected: 5" in report


def test_report_contains_survivor_patterns():
    report = load_report()

    assert "mbpp_003" in report
    assert "comparison_swap `==->!=`" in report
    assert "equality to inequality" in report

    assert "mbpp_004" in report
    assert "boolean_flip `or->and`" in report
    assert "OR chain to a mixed AND/OR condition" in report


def test_report_contains_scope_limitation():
    report = load_report()

    assert (
        "This pilot is exploratory and should not be treated as a general "
        "estimate of StepGuard performance beyond the evaluated dataset."
    ) in report
