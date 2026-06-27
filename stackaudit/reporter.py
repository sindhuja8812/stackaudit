from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.padding import Padding

from .auditors.base import AuditResult
from .scorer import AuditSummary, score_to_grade

console = Console()

SEVERITY_ICONS = {
    "error": "[bold red]✗[/]",
    "warning": "[bold yellow]⚠[/]",
    "info": "[dim]ℹ[/]",
}

GRADE_COLORS = {
    "A+": "bright_green", "A": "bright_green", "A-": "green",
    "B+": "cyan", "B": "cyan", "B-": "blue",
    "C+": "yellow", "C": "yellow", "C-": "dark_orange",
    "D": "red", "F": "bold red",
}


def _score_bar(score: int, width: int = 12) -> str:
    filled = int((score / 100) * width)
    empty = width - filled
    color = "bright_green" if score >= 80 else "yellow" if score >= 60 else "red"
    return f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"


def _grade_styled(grade: str) -> str:
    color = GRADE_COLORS.get(grade, "white")
    return f"[bold {color}]{grade}[/]"


def print_report(summary: AuditSummary, project_path: Path):
    console.print()

    # header
    header = Text()
    header.append("  STACKAUDIT  ", style="bold white on dark_blue")
    header.append(f"  {project_path.resolve().name}", style="bold cyan")
    console.print(Panel(header, box=box.DOUBLE_EDGE, padding=(0, 2)))
    console.print()

    # per-category table
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold white", padding=(0, 1))
    table.add_column("Category", style="bold", min_width=16)
    table.add_column("Score", justify="right", min_width=5)
    table.add_column("Progress", min_width=14)
    table.add_column("Grade", justify="center", min_width=5)

    for r in summary.results:
        grade = score_to_grade(r.score)
        table.add_row(
            r.category,
            str(r.score),
            _score_bar(r.score),
            _grade_styled(grade),
        )

    console.print(table)

    # overall score panel
    grade_color = GRADE_COLORS.get(summary.grade, "white")
    overall_text = Text()
    overall_text.append(f"  Overall Score  ", style="bold white")
    overall_text.append(f"{summary.overall_score}/100  ", style=f"bold {grade_color}")
    overall_text.append(f"{summary.grade}  ", style=f"bold {grade_color}")
    console.print(Panel(overall_text, box=box.HEAVY, border_style=grade_color, padding=(0, 1)))
    console.print()

    # issues
    errors = [(r.category, i) for r in summary.results for i in r.issues if i.severity == "error"]
    warnings = [(r.category, i) for r in summary.results for i in r.issues if i.severity == "warning"]
    infos = [(r.category, i) for r in summary.results for i in r.issues if i.severity == "info"]

    if errors or warnings or infos:
        console.print("[bold white]Issues Found[/]")
        for cat, issue in errors:
            console.print(f"  {SEVERITY_ICONS['error']} [{cat}] {issue.message}")
        for cat, issue in warnings:
            console.print(f"  {SEVERITY_ICONS['warning']} [{cat}] {issue.message}")
        for cat, issue in infos:
            console.print(f"  {SEVERITY_ICONS['info']} [{cat}] {issue.message}")
        console.print()

    # passed checks
    all_passed = [(r.category, p) for r in summary.results for p in r.passed]
    if all_passed:
        console.print("[bold white]Passing Checks[/]")
        for cat, msg in all_passed:
            console.print(f"  [bold green]✓[/] [{cat}] {msg}")
        console.print()

    # summary line
    console.print(
        f"  [green]{summary.total_passed} checks passed[/]  "
        f"[red]{len(errors)} error(s)[/]  "
        f"[yellow]{len(warnings)} warning(s)[/]  "
        f"[dim]{len(infos)} info(s)[/]"
    )
    console.print()


def print_json(summary: AuditSummary, project_path: Path):
    import json
    output = {
        "project": str(project_path.resolve()),
        "overall_score": summary.overall_score,
        "grade": summary.grade,
        "categories": [
            {
                "name": r.category,
                "score": r.score,
                "grade": score_to_grade(r.score),
                "issues": [{"severity": i.severity, "message": i.message} for i in r.issues],
                "passed": r.passed,
            }
            for r in summary.results
        ],
        "summary": {
            "total_issues": summary.total_issues,
            "total_passed": summary.total_passed,
        }
    }
    print(json.dumps(output, indent=2))
