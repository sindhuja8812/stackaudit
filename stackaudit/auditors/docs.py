import re
from pathlib import Path

from .base import AuditResult, BaseAuditor

IMPORTANT_SECTIONS = [
    ("installation", ["install", "installation", "getting started", "setup", "quick start"]),
    ("usage", ["usage", "how to use", "examples", "example"]),
    ("contributing", ["contributing", "contribute", "how to contribute"]),
    ("license", ["license", "licence"]),
]


class DocsAuditor(BaseAuditor):
    category = "Documentation"
    weight = 0.15

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=0)
        score = 0

        # README exists?
        readme_names = ["README.md", "README.rst", "README.txt", "README"]
        readme = next((self.path / r for r in readme_names if (self.path / r).exists()), None)

        if not readme:
            result.add_issue("error", "No README file found")
            result.score = 0
            return result

        result.add_pass(f"{readme.name} found")
        score += 20

        content = readme.read_text(errors="ignore")
        lines = content.splitlines()
        words = len(content.split())

        # length check
        if words >= 200:
            result.add_pass(f"README is substantial ({words} words)")
            score += 15
        elif words >= 80:
            result.add_issue("info", f"README is short ({words} words) — consider expanding")
            score += 8
        else:
            result.add_issue("warning", f"README is very short ({words} words)")

        # section checks
        headings = " ".join(l.lower().lstrip("#").strip() for l in lines if l.startswith("#"))
        for section_name, keywords in IMPORTANT_SECTIONS:
            found = any(kw in headings for kw in keywords)
            if found:
                result.add_pass(f"README has {section_name} section")
                score += 10
            else:
                result.add_issue("info", f"README missing '{section_name}' section")

        # badges (shows CI/coverage awareness)
        if "![" in content and "badge" in content.lower() or "shields.io" in content or "actions/workflows" in content:
            result.add_pass("README includes badges")
            score += 5

        # code blocks (shows usage examples)
        if "```" in content or "    " in content:
            result.add_pass("README includes code examples")
            score += 5

        # CHANGELOG
        changelog = self.path / "CHANGELOG.md"
        if changelog.exists():
            result.add_pass("CHANGELOG.md present")
            score += 5
        else:
            result.add_issue("info", "No CHANGELOG.md found")

        # CONTRIBUTING guide
        contributing = self.path / "CONTRIBUTING.md"
        if contributing.exists():
            result.add_pass("CONTRIBUTING.md present")
            score += 5

        result.score = min(100, score)
        return result
