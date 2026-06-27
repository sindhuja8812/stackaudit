from stackaudit.auditors.quality import QualityAuditor


def test_clean_project_high_score(healthy_project):
    result = QualityAuditor(healthy_project).audit()
    assert result.score >= 60


def test_detects_todo_fixme(bad_project):
    result = QualityAuditor(bad_project).audit()
    issues = [i for i in result.issues if "todo" in i.message.lower() or "fixme" in i.message.lower() or "hack" in i.message.lower() or "debt" in i.message.lower()]
    assert len(issues) > 0


def test_no_debt_passes(tmp_project):
    (tmp_project / "main.py").write_text("def hello():\n    return 'world'\n")
    result = QualityAuditor(tmp_project).audit()
    passed = result.passed
    assert any("todo" in p.lower() or "fixme" in p.lower() for p in passed)


def test_large_file_flagged(tmp_project):
    big_code = "\n".join(f"x_{i} = {i}" for i in range(350))
    (tmp_project / "big_file.py").write_text(big_code)
    result = QualityAuditor(tmp_project).audit()
    infos = [i for i in result.issues if "300" in i.message or "large" in i.message.lower()]
    assert len(infos) > 0


def test_linter_config_detected(healthy_project):
    result = QualityAuditor(healthy_project).audit()
    passed = result.passed
    assert any("linter" in p.lower() or "config" in p.lower() for p in passed)
