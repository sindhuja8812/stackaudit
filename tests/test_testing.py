from stackaudit.auditors.testing import TestingAuditor


def test_healthy_project_high_score(healthy_project):
    result = TestingAuditor(healthy_project).audit()
    assert result.score >= 60


def test_no_tests_low_score(bad_project):
    result = TestingAuditor(bad_project).audit()
    assert result.score < 40
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("test" in i.message.lower() for i in errors)


def test_detects_test_directory(healthy_project):
    result = TestingAuditor(healthy_project).audit()
    passed = result.passed
    assert any("test" in p.lower() for p in passed)


def test_detects_ci_config(healthy_project):
    result = TestingAuditor(healthy_project).audit()
    passed = result.passed
    assert any("ci" in p.lower() for p in passed)


def test_missing_ci_flagged(tmp_project):
    tests = tmp_project / "tests"
    tests.mkdir()
    (tests / "test_x.py").write_text("def test_x(): assert True")
    result = TestingAuditor(tmp_project).audit()
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("ci" in i.message.lower() for i in warnings)
