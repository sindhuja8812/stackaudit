from pathlib import Path

from .base import AuditResult, BaseAuditor

JUNK_FILES = [
    "Thumbs.db", ".DS_Store", "*.pyc", "*.pyo", "desktop.ini",
    ".idea", ".vscode/settings.json",
]

ENTRY_POINTS = [
    "main.py", "app.py", "index.js", "index.ts", "src/index.js",
    "src/index.ts", "src/main.py", "src/app.py", "manage.py",
    "server.py", "run.py",
]

COMMON_STRUCTURE_FILES = [
    (".gitignore", "Version control hygiene"),
    ("LICENSE", "Open source license"),
    ("README.md", "Project documentation"),
]


class StructureAuditor(BaseAuditor):
    category = "Structure"
    weight = 0.10

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=0)
        score = 0

        # entry point
        entry = next((self.path / e for e in ENTRY_POINTS if (self.path / e).exists()), None)
        if entry:
            result.add_pass(f"Entry point detected: {entry.name}")
            score += 25
        else:
            # check for src/ layout
            src = self.path / "src"
            if src.is_dir():
                result.add_pass("src/ directory layout detected")
                score += 20
            else:
                result.add_issue("warning", "No clear entry point detected (main.py, app.py, index.js, etc.)")

        # standard files
        for filename, desc in COMMON_STRUCTURE_FILES:
            exists = (self.path / filename).exists()
            # also accept LICENSE.txt, LICENSE.md
            if filename == "LICENSE":
                exists = exists or (self.path / "LICENSE.txt").exists() or (self.path / "LICENSE.md").exists()
            if exists:
                result.add_pass(f"{filename} present ({desc})")
                score += 15
            else:
                result.add_issue("info", f"No {filename} found")

        # junk files committed
        junk_found = []
        for junk in ["Thumbs.db", ".DS_Store", "desktop.ini"]:
            for f in self.path.rglob(junk):
                if ".git" not in f.parts:
                    junk_found.append(str(f.relative_to(self.path)))

        if junk_found:
            result.add_issue("warning", f"OS junk files committed: {', '.join(junk_found[:3])}")
            score -= 10
        else:
            result.add_pass("No OS junk files detected")
            score += 5

        # src or package directory structure
        has_package = any(
            (self.path / d).is_dir()
            for d in ["src", "lib", "app", "api", "core"]
            if (self.path / d).is_dir()
        )
        # also check for a python package (dir with __init__.py)
        python_pkgs = list(self.path.glob("*/__init__.py"))
        if has_package or python_pkgs:
            result.add_pass("Organized package/module structure detected")
            score += 15
        else:
            result.add_issue("info", "No clear package structure — consider organizing code into modules")

        # pyc / cache files not ignored
        pyc_files = list(self.path.rglob("*.pyc"))
        pyc_files = [f for f in pyc_files if ".git" not in f.parts and ".venv" not in f.parts and "venv" not in f.parts]
        if pyc_files:
            result.add_issue("warning", f"{len(pyc_files)} .pyc file(s) committed — add __pycache__/ to .gitignore")
            score -= 5
        else:
            result.add_pass("No compiled .pyc files committed")
            score += 5

        result.score = max(0, min(100, score))
        return result
