import re
from pathlib import Path

from .base import AuditResult, BaseAuditor

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", "dist", "build"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}

DEBT_PATTERNS = [
    (r"\bTODO\b", "TODO"),
    (r"\bFIXME\b", "FIXME"),
    (r"\bHACK\b", "HACK"),
    (r"\bXXX\b", "XXX"),
    (r"\bNOTE:\s*this is broken\b", "broken note"),
    (r"\btemporary\b.*\bfix\b", "temp fix"),
]

LINTERS = {
    ".flake8": "flake8 config",
    ".pylintrc": "pylint config",
    "pyproject.toml": "ruff/black/isort (check separately)",
    ".eslintrc.js": "ESLint config",
    ".eslintrc.json": "ESLint config",
    ".eslintrc.yml": "ESLint config",
    ".prettierrc": "Prettier config",
    ".prettierrc.json": "Prettier config",
}


class QualityAuditor(BaseAuditor):
    category = "Code Quality"
    weight = 0.10

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=100)
        deductions = 0

        # tech debt scan
        debt_by_type: dict[str, list[tuple[str, int]]] = {}
        for f in self._iter_code_files():
            try:
                for line_no, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                    for pattern, label in DEBT_PATTERNS:
                        if re.search(pattern, line, re.IGNORECASE):
                            debt_by_type.setdefault(label, []).append(
                                (str(f.relative_to(self.path)), line_no)
                            )
            except Exception:
                continue

        total_debt = sum(len(v) for v in debt_by_type.values())
        if total_debt == 0:
            result.add_pass("No TODO/FIXME/HACK comments found")
        elif total_debt <= 5:
            result.add_issue("info", f"{total_debt} tech debt comment(s) found — manageable")
            deductions += 5
        elif total_debt <= 15:
            result.add_issue("warning", f"{total_debt} tech debt comments across codebase")
            deductions += 15
        else:
            result.add_issue("error", f"{total_debt} tech debt comments — high debt load")
            deductions += 25

        for label, locations in debt_by_type.items():
            files = list({loc[0] for loc in locations})
            result.add_issue("info", f"  {label}: {len(locations)} occurrence(s) in {len(files)} file(s)")

        # linter config
        found_linters = [name for f, name in LINTERS.items() if (self.path / f).exists()]
        if found_linters:
            result.add_pass(f"Linter config found: {', '.join(set(found_linters[:2]))}")
        else:
            result.add_issue("warning", "No linter configuration found (flake8, pylint, ESLint, etc.)")
            deductions += 15

        # .editorconfig
        if (self.path / ".editorconfig").exists():
            result.add_pass(".editorconfig present — consistent formatting across editors")
        else:
            result.add_issue("info", "No .editorconfig — consider adding for consistent formatting")
            deductions += 5

        # large files (>300 lines) — sign of poor modularization
        large_files = []
        for f in self._iter_code_files():
            try:
                lines = f.read_text(errors="ignore").count("\n")
                if lines > 300:
                    large_files.append((str(f.relative_to(self.path)), lines))
            except Exception:
                continue

        if large_files:
            result.add_issue("info", f"{len(large_files)} file(s) exceed 300 lines — consider splitting")
            deductions += min(10, len(large_files) * 3)
        else:
            result.add_pass("No excessively large files detected")

        result.score = max(0, 100 - deductions)
        return result

    def _iter_code_files(self):
        for f in self.path.rglob("*"):
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                yield f
