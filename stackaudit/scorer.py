from dataclasses import dataclass

from .auditors.base import AuditResult
from .auditors import (
    DepsAuditor, SecurityAuditor, TestingAuditor,
    DocsAuditor, QualityAuditor, StructureAuditor,
)

AUDITOR_WEIGHTS = {
    "Dependencies": 0.20,
    "Security": 0.25,
    "Testing": 0.20,
    "Documentation": 0.15,
    "Code Quality": 0.10,
    "Structure": 0.10,
}


@dataclass
class AuditSummary:
    results: list[AuditResult]
    overall_score: int
    grade: str
    total_issues: int
    total_passed: int


def score_to_grade(score: int) -> str:
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 82: return "B+"
    if score >= 78: return "B"
    if score >= 75: return "B-"
    if score >= 72: return "C+"
    if score >= 68: return "C"
    if score >= 65: return "C-"
    if score >= 60: return "D"
    return "F"


def compute_summary(results: list[AuditResult]) -> AuditSummary:
    weighted_sum = 0.0
    total_weight = 0.0

    for r in results:
        w = AUDITOR_WEIGHTS.get(r.category, 0.10)
        weighted_sum += r.score * w
        total_weight += w

    overall = int(weighted_sum / total_weight) if total_weight > 0 else 0
    grade = score_to_grade(overall)

    total_issues = sum(len(r.issues) for r in results)
    total_passed = sum(len(r.passed) for r in results)

    return AuditSummary(
        results=results,
        overall_score=overall,
        grade=grade,
        total_issues=total_issues,
        total_passed=total_passed,
    )
