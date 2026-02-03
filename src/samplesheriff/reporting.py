"""Reporting utilities for SampleSheriff validation results.

This module provides formatted output generation for validation results,
including rich terminal output and JSON reports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from samplesheriff.schema import Severity, ValidationIssue


class ReportFormat(Enum):
    """Supported report output formats."""

    TEXT = "text"
    JSON = "json"
    TSV = "tsv"


@dataclass
class ValidationSummary:
    """Summary of validation results."""

    total_rows: int = 0
    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    files_checked: set[str] = field(default_factory=set)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Update summary counts from an issue."""
        self.total_issues += 1
        match issue.severity:
            case Severity.ERROR:
                self.error_count += 1
            case Severity.WARNING:
                self.warning_count += 1
            case Severity.INFO:
                self.info_count += 1


@dataclass
class ValidationReport:
    """Complete validation report."""

    input_file: str
    schema_name: str
    success: bool
    issues: list[ValidationIssue]
    summary: ValidationSummary
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "input_file": self.input_file,
            "schema_name": self.schema_name,
            "success": self.success,
            "summary": {
                "total_rows": self.summary.total_rows,
                "total_issues": self.summary.total_issues,
                "errors": self.summary.error_count,
                "warnings": self.summary.warning_count,
                "info": self.summary.info_count,
            },
            "issues": [issue.to_dict() for issue in self.issues],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class Reporter:
    """Generates formatted validation reports."""

    def __init__(self, console: Console | None = None):
        """Initialize the reporter.

        Args:
            console: Rich console for output (creates default if None)
        """
        self.console = console or Console()

    def print_report(
        self,
        report: ValidationReport,
        format: ReportFormat = ReportFormat.TEXT,
        fail_on_warnings: bool = False,
    ) -> int:
        """Print a validation report.

        Args:
            report: The validation report to print
            format: Output format
            fail_on_warnings: Whether warnings count as failure

        Returns:
            Exit code (0 for success, 1 for validation errors)
        """
        match format:
            case ReportFormat.TEXT:
                return self._print_text_report(report, fail_on_warnings)
            case ReportFormat.JSON:
                return self._print_json_report(report, fail_on_warnings)
            case ReportFormat.TSV:
                return self._print_tsv_report(report, fail_on_warnings)
            case _:
                raise ValueError(f"Unknown format: {format}")

    def _print_text_report(
        self,
        report: ValidationReport,
        fail_on_warnings: bool,
    ) -> int:
        """Print a rich text report."""
        # Title panel
        title = Text("SampleSheriff Validation Report", style="bold blue")
        if report.success:
            status = Text("✓ PASSED", style="bold green")
        else:
            status = Text("✗ FAILED", style="bold red")

        self.console.print(
            Panel.fit(
                f"{title}\n{report.input_file}",
                title=status,
                border_style="green" if report.success else "red",
            )
        )

        # Summary table
        summary_table = Table(title="Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="white")

        summary_table.add_row("Input File", report.input_file)
        summary_table.add_row("Schema", report.schema_name)
        summary_table.add_row("Total Rows", str(report.summary.total_rows))
        summary_table.add_row("Total Issues", str(report.summary.total_issues))
        summary_table.add_row(
            "Errors",
            f"[red]{report.summary.error_count}[/red]" if report.summary.error_count else "0",
        )
        summary_table.add_row(
            "Warnings",
            f"[yellow]{report.summary.warning_count}[/yellow]"
            if report.summary.warning_count
            else "0",
        )
        summary_table.add_row(
            "Info",
            f"[blue]{report.summary.info_count}[/blue]" if report.summary.info_count else "0",
        )

        self.console.print(summary_table)

        # Issues table (if any)
        if report.issues:
            self.console.print()
            issues_table = Table(title="Validation Issues")
            issues_table.add_column("Code", style="cyan", width=6)
            issues_table.add_column("Severity", width=10)
            issues_table.add_column("Row", width=6)
            issues_table.add_column("Column", style="magenta")
            issues_table.add_column("Message", style="white")

            for issue in report.issues:
                severity_style = self._severity_style(issue.severity)
                row_num = str(issue.row) if issue.row > 0 else "-"
                col_name = issue.column or "-"

                issues_table.add_row(
                    issue.code,
                    f"[{severity_style}]{issue.severity.value}[/{severity_style}]",
                    row_num,
                    col_name,
                    issue.message,
                )

            self.console.print(issues_table)

            # Suggestions (for errors)
            errors = [i for i in report.issues if i.severity == Severity.ERROR]
            if errors:
                self.console.print()
                self.console.print("[bold red]Suggestions:[/bold red]")
                for issue in errors[:10]:  # Show first 10
                    if issue.suggestion:
                        self.console.print(f"  • [{issue.code}] {issue.suggestion}")
                if len(errors) > 10:
                    self.console.print(f"  ... and {len(errors) - 10} more errors")

        # Determine exit code
        if report.summary.error_count > 0:
            return 1
        if fail_on_warnings and report.summary.warning_count > 0:
            return 1
        return 0

    def _print_json_report(
        self,
        report: ValidationReport,
        fail_on_warnings: bool,
    ) -> int:
        """Print a JSON report."""
        self.console.print(report.to_json())

        if report.summary.error_count > 0:
            return 1
        if fail_on_warnings and report.summary.warning_count > 0:
            return 1
        return 0

    def _print_tsv_report(
        self,
        report: ValidationReport,
        fail_on_warnings: bool,
    ) -> int:
        """Print a TSV report."""
        # Header
        print("code\tseverity\trow\tcolumn\tmessage\tsuggestion")

        # Issues
        for issue in report.issues:
            print(
                f"{issue.code}\t{issue.severity.value}\t{issue.row}\t{issue.column}\t{issue.message}\t{issue.suggestion}"
            )

        if report.summary.error_count > 0:
            return 1
        if fail_on_warnings and report.summary.warning_count > 0:
            return 1
        return 0

    def _severity_style(self, severity: Severity) -> str:
        """Get Rich style for a severity level."""
        match severity:
            case Severity.ERROR:
                return "red"
            case Severity.WARNING:
                return "yellow"
            case Severity.INFO:
                return "blue"
            case _:
                return "white"

    def save_report(self, report: ValidationReport, path: Path) -> None:
        """Save a JSON report to file.

        Args:
            report: Report to save
            path: Output file path
        """
        with open(path, "w") as f:
            f.write(report.to_json())


class ProgressReporter:
    """Reports progress during validation."""

    def __init__(self, console: Console | None = None, quiet: bool = False):
        """Initialize the progress reporter.

        Args:
            console: Rich console for output
            quiet: Suppress progress output
        """
        self.console = console or Console()
        self.quiet = quiet

    def info(self, message: str) -> None:
        """Print an info message."""
        if not self.quiet:
            self.console.print(f"[blue]ℹ[/blue] {message}")

    def success(self, message: str) -> None:
        """Print a success message."""
        if not self.quiet:
            self.console.print(f"[green]✓[/green] {message}")

    def warning(self, message: str) -> None:
        """Print a warning message."""
        if not self.quiet:
            self.console.print(f"[yellow]⚠[/yellow] {message}")

    def error(self, message: str) -> None:
        """Print an error message."""
        if not self.quiet:
            self.console.print(f"[red]✗[/red] {message}")

    def progress(self, current: int, total: int, message: str = "") -> None:
        """Print a progress update."""
        if not self.quiet:
            pct = (current / total * 100) if total > 0 else 0
            self.console.print(f"[cyan]→[/cyan] {message} ({current}/{total}, {pct:.1f}%)")


def create_report_from_issues(
    input_file: str,
    schema_name: str,
    issues: list[ValidationIssue],
    total_rows: int = 0,
    metadata: dict[str, Any] | None = None,
) -> ValidationReport:
    """Create a validation report from a list of issues.

    Args:
        input_file: Path to the validated sample sheet
        schema_name: Name of the schema used
        issues: List of validation issues
        total_rows: Total number of rows validated
        metadata: Optional metadata dictionary

    Returns:
        ValidationReport instance
    """
    summary = ValidationSummary(total_rows=total_rows)
    for issue in issues:
        summary.add_issue(issue)

    success = summary.error_count == 0

    # Sort issues for deterministic output
    sorted_issues = sorted(
        issues,
        key=lambda i: (
            0 if i.severity == Severity.ERROR else 1 if i.severity == Severity.WARNING else 2,
            i.row,
            i.column or "",
            i.code,
        ),
    )

    return ValidationReport(
        input_file=input_file,
        schema_name=schema_name,
        success=success,
        issues=sorted_issues,
        summary=summary,
        metadata=metadata or {},
    )
