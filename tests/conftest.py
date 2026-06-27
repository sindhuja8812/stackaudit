import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def tmp_project(tmp_path):
    """Bare minimum project directory."""
    return tmp_path


@pytest.fixture
def healthy_project(tmp_path):
    """A well-structured project with most best practices."""
    (tmp_path / "README.md").write_text(
        "# MyProject\n\n## Installation\n\npip install myproject\n\n"
        "## Usage\n\n```python\nimport myproject\n```\n\n"
        "## Contributing\n\nPRs welcome!\n\n## License\n\nMIT\n\n"
        + "This is a great project. " * 20
    )
    (tmp_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n.venv/\ndist/\n")
    (tmp_path / "requirements.txt").write_text("rich==13.7.0\ntyper==0.12.0\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myproject"\nversion = "0.1.0"\n'
        'dependencies = ["rich>=13.0.0"]\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\naddopts = "--cov=myproject"\n'
    )
    (tmp_path / "LICENSE").write_text("MIT License\n")
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_example():\n    assert True\n")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    )
    pkg = tmp_path / "myproject"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "main.py").write_text("def main():\n    pass\n")
    return tmp_path


@pytest.fixture
def bad_project(tmp_path):
    """A poorly structured project."""
    (tmp_path / "script.py").write_text(
        "API_KEY = 'supersecret123456789abc'\n"
        "# TODO: fix this\n# FIXME: broken\n# HACK: workaround\n"
        "password = 'hunter2abc123'\n"
    )
    return tmp_path
