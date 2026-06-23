import re
from pathlib import Path

from .base import AuditResult, BaseAuditor

# patterns that suggest hardcoded secrets
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*=\s*["\']?[A-Za-z0-9_\-]{16,}', "Possible hardcoded API key"),
    (r'(?i)(secret[_-]?key|secret)\s*=\s*["\']?[A-Za-z0-9_\-]{16,}', "Possible hardcoded secret"),
    (r'(?i)(password|passwd|pwd)\s*=\s*["\']?[^\s\$\{]{6,}', "Possible hardcoded password"),
    (r'(?i)(token|access[_-]?token|auth[_-]?token)\s*=\s*["\']?[A-Za-z0-9_\-\.]{20,}', "Possible hardcoded token"),
    (r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*=\s*["\']?[A-Z0-9]{20}', "Possible AWS Access Key"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID pattern detected"),
    (r'(?i)private[_-]?key\s*=\s*["\']?-----BEGIN', "Private key detected"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "env", ".env", "dist", "build"}
CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini", ".sh"}


class SecurityAuditor(BaseAuditor):
    category = "Security"
    weight = 0.25

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=100)
        deductions = 0

        # .env committed to git?
        env_file = self.path / ".env"
        gitignore = self.path / ".gitignore"

        if env_file.exists():
            if gitignore.exists() and ".env" in gitignore.read_text():
                result.add_pass(".env file exists and is in .gitignore")
            else:
                result.add_issue("error", ".env file exists but is NOT in .gitignore — secrets may be exposed")
                deductions += 30
        else:
            result.add_pass("No .env file committed")

        # .gitignore present?
        if gitignore.exists():
            result.add_pass(".gitignore present")
        else:
            result.add_issue("warning", "No .gitignore found — sensitive files may be tracked")
            deductions += 15

        # scan source files for secret patterns
        hits = self._scan_secrets()
        if hits:
            for filepath, pattern_msg, line_no in hits[:5]:
                result.add_issue("error", f"{pattern_msg} in {filepath}:{line_no}")
            deductions += min(40, len(hits) * 10)
        else:
            result.add_pass("No hardcoded secrets detected in source files")

        # check for .env.example (good practice)
        env_example = self.path / ".env.example"
        if env_example.exists():
            result.add_pass(".env.example present — good practice")
        else:
            result.add_issue("info", "No .env.example found — consider adding one for collaborators")
            deductions += 5

        result.score = max(0, 100 - deductions)
        return result

    def _scan_secrets(self) -> list[tuple[str, str, int]]:
        hits = []
        for file in self._iter_files():
            try:
                text = file.read_text(errors="ignore")
                for line_no, line in enumerate(text.splitlines(), 1):
                    # skip comments
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue
                    for pattern, msg in SECRET_PATTERNS:
                        if re.search(pattern, line):
                            rel = str(file.relative_to(self.path))
                            hits.append((rel, msg, line_no))
                            break
            except Exception:
                continue
        return hits

    def _iter_files(self):
        for f in self.path.rglob("*"):
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                yield f
