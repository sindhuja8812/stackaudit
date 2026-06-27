from stackaudit.auditors.base import AuditResult
from stackaudit.scorer import compute_summary, score_to_grade


def make_result(category, score):
    r = AuditResult(category=category, score=score)
    return r


def test_grade_boundaries():
    assert score_to_grade(95) == "A+"
    assert score_to_grade(90) == "A"
    assert score_to_grade(82) == "B+"
    assert score_to_grade(78) == "B"
    assert score_to_grade(68) == "C"
    assert score_to_grade(59) == "F"


def test_summary_overall_score():
    results = [
        make_result("Dependencies", 80),
        make_result("Security", 90),
        make_result("Testing", 70),
        make_result("Documentation", 85),
        make_result("Code Quality", 75),
        make_result("Structure", 80),
    ]
    summary = compute_summary(results)
    assert 70 <= summary.overall_score <= 95
    assert summary.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]


def test_summary_counts_issues():
    r = make_result("Security", 50)
    r.add_issue("error", "bad secret")
    r.add_issue("warning", "no gitignore")
    r.add_pass("something good")
    summary = compute_summary([r])
    assert summary.total_issues == 2
    assert summary.total_passed == 1


def test_perfect_score():
    results = [make_result(cat, 100) for cat in
               ["Dependencies", "Security", "Testing", "Documentation", "Code Quality", "Structure"]]
    summary = compute_summary(results)
    assert summary.overall_score == 100
    assert summary.grade == "A+"
