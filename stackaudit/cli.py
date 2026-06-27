from pathlib import Path
from typing import Optional
import sys

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .auditors import (
    DepsAuditor, SecurityAuditor, TestingAuditor,
    DocsAuditor, QualityAuditor, StructureAuditor,
)
from .scorer import compute_summary
from .reporter import print_report, print_json

app = typer.Typer(
    name="stackaudit",
    help="Audit your project's health and generate a scored report card.",
    add_completion=False,
)
console = Console()

ALL_AUDITORS = {
    "deps": DepsAuditor,
    "security": SecurityAuditor,
    "testing": TestingAuditor,
    "docs": DocsAuditor,
    "quality": QualityAuditor,
    "structure": StructureAuditor,
}


def version_callback(value: bool):
    if value:
        console.print(f"stackaudit v{__version__}")
        raise typer.Exit()


@app.command()
def audit(
    path: str = typer.Argument(".", help="Path to the project directory"),
    output: str = typer.Option("rich", "--output", "-o", help="Output format: rich | json"),
    skip: Optional[str] = typer.Option(None, "--skip", "-s", help="Comma-separated auditors to skip (deps,security,testing,docs,quality,structure)"),
    version: Optional[bool] = typer.Option(None, "--version", "-v", callback=version_callback, is_eager=True),
):
    """
    Audit a project directory and generate a health report card.

    Examples:\n
      stackaudit .\n
      stackaudit /path/to/project\n
      stackaudit . --output json\n
      stackaudit . --skip security,deps
    """
    project_path = Path(path).resolve()

    if not project_path.exists():
        console.print(f"[red]Error:[/] Path does not exist: {project_path}")
        raise typer.Exit(1)

    if not project_path.is_dir():
        console.print(f"[red]Error:[/] Path is not a directory: {project_path}")
        raise typer.Exit(1)

    # parse skips
    skipped = set()
    if skip:
        skipped = {s.strip().lower() for s in skip.split(",")}
        invalid = skipped - set(ALL_AUDITORS.keys())
        if invalid:
            console.print(f"[yellow]Warning:[/] Unknown auditor(s) to skip: {', '.join(invalid)}")
            console.print(f"  Valid options: {', '.join(ALL_AUDITORS.keys())}")

    active_auditors = {k: v for k, v in ALL_AUDITORS.items() if k not in skipped}

    if output == "rich":
        console.print(f"\n[bold cyan]Auditing[/] [white]{project_path}[/]\n")

    results = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
        disable=(output == "json"),
    ) as progress:
        for key, AuditorClass in active_auditors.items():
            task = progress.add_task(f"Running {AuditorClass.category} audit...", total=None)
            auditor = AuditorClass(project_path)
            result = auditor.audit()
            results.append(result)
            progress.remove_task(task)

    summary = compute_summary(results)

    if output == "json":
        print_json(summary, project_path)
    else:
        print_report(summary, project_path)

    # exit code reflects health
    if summary.overall_score < 60:
        raise typer.Exit(2)
    elif summary.overall_score < 80:
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
