import sys
from pathlib import Path

from .base import AuditResult, BaseAuditor

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class TestingAuditor(BaseAuditor):
    category = "Testing"
    weight = 0.20

    def audit(self) -> AuditResult:
        result = AuditResult(category=self.category, score=0)
        score = 0

        # test directory
        test_dirs = ["tests", "test", "__tests__", "spec"]
        found_test_dir = next((self.path / d for d in test_dirs if (self.path / d).is_dir()), None)
        if found_test_dir:
            result.add_pass(f"Test directory found: {found_test_dir.name}/")
            score += 30

            # count test files
            test_files = list(found_test_dir.rglob("test_*.py")) + \
                         list(found_test_dir.rglob("*_test.py")) + \
                         list(found_test_dir.rglob("*.test.js")) + \
                         list(found_test_dir.rglob("*.spec.js")) + \
                         list(found_test_dir.rglob("*.test.ts")) + \
                         list(found_test_dir.rglob("*.spec.ts"))
            if test_files:
                result.add_pass(f"{len(test_files)} test file(s) found")
                score += 20
            else:
                result.add_issue("warning", "Test directory exists but no test files found inside")
        else:
            result.add_issue("error", "No test directory found (tests/, test/, __tests__/)")

        # pytest config
        has_pytest_config = False
        pytest_ini = self.path / "pytest.ini"
        setup_cfg = self.path / "setup.cfg"
        pyproject = self.path / "pyproject.toml"

        if pytest_ini.exists():
            result.add_pass("pytest.ini found")
            has_pytest_config = True
        elif setup_cfg.exists() and "[tool:pytest]" in setup_cfg.read_text():
            result.add_pass("pytest config found in setup.cfg")
            has_pytest_config = True
        elif pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text())
                if "pytest" in data.get("tool", {}):
                    result.add_pass("pytest config found in pyproject.toml")
                    has_pytest_config = True
            except Exception:
                pass

        if has_pytest_config:
            score += 15
        else:
            result.add_issue("warning", "No pytest configuration found")

        # coverage config
        has_coverage = False
        coveragerc = self.path / ".coveragerc"
        if coveragerc.exists():
            has_coverage = True
        elif pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text())
                if "coverage" in data.get("tool", {}):
                    has_coverage = True
                # check addopts for --cov
                addopts = data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("addopts", "")
                if "--cov" in addopts:
                    has_coverage = True
            except Exception:
                pass

        if has_coverage:
            result.add_pass("Coverage configuration found")
            score += 20
        else:
            result.add_issue("info", "No coverage configuration found — consider adding pytest-cov")

        # CI workflow
        ci_dirs = [self.path / ".github" / "workflows", self.path / ".gitlab-ci.yml", self.path / ".circleci"]
        has_ci = False
        for ci in ci_dirs:
            if ci.exists():
                has_ci = True
                break

        if has_ci:
            result.add_pass("CI configuration found")
            score += 15
        else:
            result.add_issue("warning", "No CI/CD configuration found (.github/workflows, .gitlab-ci.yml, etc.)")

        result.score = min(100, score)
        return result
