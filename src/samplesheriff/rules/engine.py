"""Core validation rule engine.

This module provides the base infrastructure for defining and executing
validation rules in a composable, extensible manner.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from samplesheriff.schema import Schema, ValidationIssue


@dataclass
class ValidationContext:
    """Context passed to validation rules.

    Contains all information needed for validation, including
    configuration options and accumulated state.
    """

    # Input configuration
    input_path: Path
    schema: Schema
    base_dir: Path | None = None
    strict: bool = False
    require_index: bool = False
    peek_fastq: int = 0

    # Runtime state
    row_data: dict[str, Any] = field(default_factory=dict)
    row_number: int = 0
    headers: list[str] = field(default_factory=list)

    # Accumulated results
    sample_ids: set[str] = field(default_factory=set)
    file_paths: dict[str, list[Path]] = field(default_factory=dict)


def find_column_case_insensitive(headers: list[str], target: str) -> str | None:
    """Find a column name case-insensitively.

    Args:
        headers: List of header column names
        target: Target column name to find

    Returns:
        Actual column name if found, None otherwise
    """
    target_lower = target.lower()
    for header in headers:
        if header.lower() == target_lower:
            return header
    return None


def get_column_value(row: dict[str, str], column: str) -> str | None:
    """Get value from row, handling case-insensitive column matching.

    Args:
        row: Row data dictionary
        column: Target column name

    Returns:
        Column value or None if not found/empty
    """
    # Try exact match first
    if column in row:
        val = row[column]
        return val if val and val.strip() else None

    # Try case-insensitive match
    for key, val in row.items():
        if key.lower() == column.lower():
            return val if val and val.strip() else None

    return None


class ValidationRule(ABC):
    """Abstract base class for validation rules."""

    @abstractmethod
    def validate(
        self,
        context: ValidationContext,
        row: dict[str, str],
        row_number: int,
    ) -> list[ValidationIssue]:
        """Validate a single row.

        Args:
            context: Validation context
            row: Row data as column->value mapping
            row_number: 1-indexed row number

        Returns:
            List of validation issues found
        """
        ...

    def finalize(self, context: ValidationContext) -> list[ValidationIssue]:
        """Perform final validation after all rows processed.

        Args:
            context: Validation context with accumulated state

        Returns:
            List of validation issues found
        """
        return []


class RuleEngine:
    """Engine for executing multiple validation rules."""

    def __init__(self):
        """Initialize the rule engine."""
        self.rules: list[ValidationRule] = []
        self.context: ValidationContext | None = None

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule to the engine.

        Args:
            rule: Rule to add
        """
        self.rules.append(rule)

    def initialize(self, context: ValidationContext) -> list[ValidationIssue]:
        """Initialize validation with the given context.

        Args:
            context: Validation context

        Returns:
            Any issues found during initialization
        """
        self.context = context
        return []

    def validate_row(
        self,
        row: dict[str, str],
        row_number: int,
    ) -> list[ValidationIssue]:
        """Validate a single row against all rules.

        Args:
            row: Row data
            row_number: 1-indexed row number

        Returns:
            Combined list of validation issues
        """
        if self.context is None:
            raise RuntimeError("RuleEngine not initialized")

        self.context.row_data = row
        self.context.row_number = row_number

        all_issues: list[ValidationIssue] = []
        for rule in self.rules:
            issues = rule.validate(self.context, row, row_number)
            all_issues.extend(issues)

        return all_issues

    def finalize(self) -> list[ValidationIssue]:
        """Finalize validation and run any post-processing checks.

        Returns:
            List of validation issues found during finalization
        """
        if self.context is None:
            raise RuntimeError("RuleEngine not initialized")

        all_issues: list[ValidationIssue] = []
        for rule in self.rules:
            issues = rule.finalize(self.context)
            all_issues.extend(issues)

        return all_issues
