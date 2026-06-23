import json
import sys
from pathlib import Path

import httpx

from .base import AuditResult, BaseAuditor

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class DepsAuditor(BaseAuditor):
    category = "Dependencies"
    weight = 0.20

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=100)
        checks = []

        # detect project type and dep files
        dep_files = {
            "requirements.txt": self.path / "requirements.txt",
            "pyproject.toml": self.path / "pyproject.toml",
            "package.json": self.path / "package.json",
            "Pipfile": self.path / "Pipfile",
        }
        found = {k: v for k, v in dep_files.items() if v.exists()}

        if not found:
            result.add_issue("error", "No dependency file found (requirements.txt / package.json / pyproject.toml)")
            result.score = 20
            return result

        result.add_pass(f"Dependency file(s) found: {', '.join(found.keys())}")
        checks.append(True)

        # lockfile check
        lockfiles = ["requirements.txt", "package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock", "uv.lock"]
        has_lock = any((self.path / lf).exists() for lf in lockfiles)
        if has_lock:
            result.add_pass("Lockfile present")
            checks.append(True)
        else:
            result.add_issue("warning", "No lockfile detected — reproducible installs not guaranteed")
            checks.append(False)

        # outdated check via PyPI (requirements.txt)
        req_file = self.path / "requirements.txt"
        if req_file.exists():
            outdated = self._check_outdated_pypi(req_file)
            if outdated:
                result.add_issue("warning", f"{len(outdated)} potentially outdated package(s): {', '.join(outdated[:3])}{'...' if len(outdated) > 3 else ''}")
                checks.append(False)
            else:
                result.add_pass("All PyPI packages appear up to date")
                checks.append(True)

        # pyproject.toml has version pinning?
        if "pyproject.toml" in found:
            try:
                data = tomllib.loads((self.path / "pyproject.toml").read_text())
                deps = data.get("project", {}).get("dependencies", [])
                unpinned = [d for d in deps if not any(op in d for op in [">=", "==", "~=", "<="])]
                if unpinned:
                    result.add_issue("info", f"{len(unpinned)} dep(s) have no version constraint in pyproject.toml")
                else:
                    result.add_pass("All pyproject.toml dependencies have version constraints")
            except Exception:
                pass

        passed = sum(1 for c in checks if c)
        result.score = max(20, int((passed / max(len(checks), 1)) * 100))
        return result

    def _check_outdated_pypi(self, req_file: Path) -> list[str]:
        outdated = []
        try:
            lines = [l.strip() for l in req_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
            for line in lines[:8]:  # limit API calls
                pkg = line.split("==")[0].split(">=")[0].split("~=")[0].strip()
                try:
                    r = httpx.get(f"https://pypi.org/pypi/{pkg}/json", timeout=3)
                    if r.status_code == 200:
                        latest = r.json()["info"]["version"]
                        pinned = line.split("==")[1].strip() if "==" in line else None
                        if pinned and pinned != latest:
                            outdated.append(f"{pkg} ({pinned} → {latest})")
                except Exception:
                    continue
        except Exception:
            pass
        return outdated
