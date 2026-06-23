from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Issue:
    severity: str  # "error", "warning", "info"
    message: str


@dataclass
class AuditResult:
    category: str
    score: int          # 0-100
    issues: list[Issue] = field(default_factory=list)
    passed: list[str] = field(default_factory=list)

    def add_issue(self, severity: str, message: str):
        self.issues.append(Issue(severity=severity, message=message))

    def add_pass(self, message: str):
        self.passed.append(message)


class BaseAuditor:
    category = "base"
    weight = 1.0

    def __init__(self, path: Path):
        self.path = path

    def audit(self) -> AuditResult:
        raise NotImplementedError
