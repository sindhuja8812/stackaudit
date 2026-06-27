from stackaudit.auditors.docs import DocsAuditor


def test_healthy_readme_high_score(healthy_project):
    result = DocsAuditor(healthy_project).audit()
    assert result.score >= 60


def test_no_readme_zero_score(bad_project):
    result = DocsAuditor(bad_project).audit()
    assert result.score == 0
    errors = [i for i in result.issues if i.severity == "error"]
    assert any("readme" in i.message.lower() for i in errors)


def test_short_readme_flagged(tmp_project):
    (tmp_project / "README.md").write_text("# Hello\n\nThis is my project.\n")
    result = DocsAuditor(tmp_project).audit()
    assert result.score < 60
    issues = [i for i in result.issues if "short" in i.message.lower() or "word" in i.message.lower()]
    assert len(issues) > 0


def test_missing_sections_flagged(tmp_project):
    (tmp_project / "README.md").write_text("# MyProject\n\n" + "word " * 100)
    result = DocsAuditor(tmp_project).audit()
    infos = [i for i in result.issues if i.severity == "info"]
    # should flag missing usage/install/etc
    assert len(infos) >= 2


def test_full_readme_detects_sections(healthy_project):
    result = DocsAuditor(healthy_project).audit()
    passed = result.passed
    assert any("installation" in p.lower() or "usage" in p.lower() for p in passed)
