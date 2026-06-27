from stackaudit.auditors.security import SecurityAuditor


def test_no_issues_clean_project(healthy_project):
    result = SecurityAuditor(healthy_project).audit()
    assert result.score >= 70
    errors = [i for i in result.issues if i.severity == "error"]
    assert len(errors) == 0


def test_detects_hardcoded_api_key(bad_project):
    result = SecurityAuditor(bad_project).audit()
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("hardcoded" in i.message.lower() or "api key" in i.message.lower() for i in errors)
    assert result.score < 70


def test_detects_env_not_in_gitignore(tmp_project):
    (tmp_project / ".env").write_text("SECRET=abc123\n")
    # no .gitignore
    result = SecurityAuditor(tmp_project).audit()
    errors = [i for i in result.issues if i.severity == "error"]
    assert any(".env" in i.message for i in errors)


def test_env_in_gitignore_passes(tmp_project):
    (tmp_project / ".env").write_text("SECRET=abc123\n")
    (tmp_project / ".gitignore").write_text(".env\n")
    result = SecurityAuditor(tmp_project).audit()
    passed = result.passed
    assert any(".env" in p for p in passed)


def test_no_gitignore_deduction(tmp_project):
    result = SecurityAuditor(tmp_project).audit()
    assert result.score < 100
    warnings = [i for i in result.issues if i.severity == "warning"]
    assert any("gitignore" in i.message.lower() for i in warnings)
