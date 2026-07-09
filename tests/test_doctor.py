from trueform.doctor import format_doctor_report, run_doctor


def test_doctor_runs_and_includes_core_checks():
    report = run_doctor()
    names = {c.name for c in report.checks}
    assert "Python" in names
    assert "httpx" in names
    assert "mock provider" in names
    assert "recommended now" in names


def test_doctor_mock_provider_passes():
    report = run_doctor()
    mock = next(c for c in report.checks if c.name == "mock provider")
    assert mock.ok is True


def test_doctor_format_is_plain_text():
    text = format_doctor_report(run_doctor())
    assert "trueform doctor" in text
    assert "[ok]" in text or "[!!]" in text
