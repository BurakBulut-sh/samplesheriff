"""Schema-based validation rules.

This module provides rules for validating sample sheets against a declarative
schema, including column presence, type checking, and constraint validation.
"""

from __future__ import annotations

from samplesheriff.rules.engine import ValidationContext, ValidationRule, get_column_value
from samplesheriff.schema import (
    ConstraintType,
    Schema,
    Severity,
    ValidationIssue,
)


class SchemaRule(ValidationRule):
    """Validates sample sheets against a declarative schema."""

    def __init__(self, schema: Schema | None = None):
        """Initialize the schema rule.

        Args:
            schema: Schema to validate against
        """
        self.schema = schema
        self._found_columns: set[str] = set()
        self._column_values: dict[str, list[tuple[int, str]]] = {}

    def validate(
        self,
        context: ValidationContext,
        row: dict[str, str],
        row_number: int,
    ) -> list[ValidationIssue]:
        """Validate a row against the schema."""
        issues: list[ValidationIssue] = []
        schema = self.schema or context.schema

        # Track found columns (for extra column detection)
        if row_number == 1:
            self._found_columns = set(row.keys())

        # Validate each schema column
        for col_schema in schema.columns:
            value = get_column_value(row, col_schema.name)

            # Track values for constraint checking
            if col_schema.name not in self._column_values:
                self._column_values[col_schema.name] = []
            self._column_values[col_schema.name].append((row_number, value or ""))

            # Skip column-level validation if column is missing from row
            # (missing required columns will be caught in finalize)
            if col_schema.name not in row and col_schema.name.lower() not in (
                k.lower() for k in row
            ):
                continue

            # Column-level validation
            col_issues = col_schema.validate_value(
                value,
                row_number,
                context.base_dir,
            )
            issues.extend(col_issues)

        return issues

    def finalize(self, context: ValidationContext) -> list[ValidationIssue]:
        """Perform final schema-level checks."""
        issues: list[ValidationIssue] = []
        schema = self.schema or context.schema

        # Check for missing required columns
        schema_columns = {col.name for col in schema.columns}
        required_columns = {col.name for col in schema.columns if col.required}

        missing_required = required_columns - self._found_columns
        for col in missing_required:
            issues.append(
                ValidationIssue(
                    code="E010",
                    severity=Severity.ERROR,
                    row=0,
                    column=col,
                    message=f"Required column '{col}' not found in sample sheet",
                    suggestion=f"Add the '{col}' column to your sample sheet",
                )
            )

        # Check for extra columns
        if not schema.allow_extra_columns:
            extra_columns = self._found_columns - schema_columns
            for col in extra_columns:
                issues.append(
                    ValidationIssue(
                        code="E011" if context.strict else "W001",
                        severity=Severity.ERROR if context.strict else Severity.WARNING,
                        row=0,
                        column=col,
                        message=f"Extra column '{col}' not defined in schema",
                        suggestion="Remove this column or update schema to allow_extra_columns",
                    )
                )

        # Check constraints
        for constraint in schema.constraints:
            constraint_issues = self._check_constraint(
                constraint,
                context,
            )
            issues.extend(constraint_issues)

        return issues

    def _check_constraint(
        self,
        constraint,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Check a single constraint."""
        issues: list[ValidationIssue] = []

        match constraint.type:
            case ConstraintType.UNIQUE:
                issues.extend(self._check_unique(constraint))

            case ConstraintType.REQUIRED_GROUP:
                issues.extend(self._check_required_group(constraint))

            case ConstraintType.MUTUALLY_EXCLUSIVE:
                issues.extend(self._check_mutually_exclusive(constraint))

            case ConstraintType.PAIRED:
                issues.extend(self._check_paired(constraint))

        return issues

    def _check_unique(self, constraint) -> list[ValidationIssue]:
        """Check that column values are unique."""
        issues: list[ValidationIssue] = []

        for col in constraint.columns:
            if col not in self._column_values:
                continue

            seen: dict[str, int] = {}
            for row_num, value in self._column_values[col]:
                if not value:  # Skip empty values
                    continue
                if value in seen:
                    issues.append(
                        ValidationIssue(
                            code="E012",
                            severity=Severity.ERROR,
                            row=row_num,
                            column=col,
                            message=f"Duplicate value '{value}' in column '{col}'",
                            suggestion=f"Values in '{col}' must be unique (first seen at row {seen[value]})",
                        )
                    )
                else:
                    seen[value] = row_num

        return issues

    def _check_required_group(self, constraint) -> list[ValidationIssue]:
        """Check that at least one column in group has a value."""
        issues: list[ValidationIssue] = []

        # Get all row numbers
        all_rows: set[int] = set()
        for col in constraint.columns:
            if col in self._column_values:
                all_rows.update(row_num for row_num, _ in self._column_values[col])

        for row_num in sorted(all_rows):
            has_value = False
            for col in constraint.columns:
                if col in self._column_values:
                    values = [v for r, v in self._column_values[col] if r == row_num and v]
                    if values:
                        has_value = True
                        break

            if not has_value:
                cols_str = ", ".join(constraint.columns)
                msg = constraint.message or f"At least one of [{cols_str}] must have a value"
                issues.append(
                    ValidationIssue(
                        code="E013",
                        severity=Severity.ERROR,
                        row=row_num,
                        column=constraint.columns[0],
                        message=msg,
                        suggestion=f"Provide a value for one of: {cols_str}",
                    )
                )

        return issues

    def _check_mutually_exclusive(self, constraint) -> list[ValidationIssue]:
        """Check that only one column in group has a value."""
        issues: list[ValidationIssue] = []

        # Get all row numbers
        all_rows: set[int] = set()
        for col in constraint.columns:
            if col in self._column_values:
                all_rows.update(row_num for row_num, _ in self._column_values[col])

        for row_num in sorted(all_rows):
            non_empty: list[str] = []
            for col in constraint.columns:
                if col in self._column_values:
                    values = [v for r, v in self._column_values[col] if r == row_num and v]
                    if values:
                        non_empty.append(col)

            if len(non_empty) > 1:
                cols_str = ", ".join(constraint.columns)
                msg = constraint.message or f"Columns [{cols_str}] are mutually exclusive"
                issues.append(
                    ValidationIssue(
                        code="E014",
                        severity=Severity.ERROR,
                        row=row_num,
                        column=non_empty[0],
                        message=f"{msg} - multiple provided: {', '.join(non_empty)}",
                        suggestion=f"Provide only one of: {cols_str}",
                    )
                )

        return issues

    def _check_paired(self, constraint) -> list[ValidationIssue]:
        """Check that paired columns are both present or both empty."""
        issues: list[ValidationIssue] = []

        if len(constraint.columns) != 2:
            return issues

        col1, col2 = constraint.columns[:2]

        # Get all row numbers
        all_rows: set[int] = set()
        for col in constraint.columns:
            if col in self._column_values:
                all_rows.update(row_num for row_num, _ in self._column_values[col])

        for row_num in sorted(all_rows):
            val1 = None
            val2 = None

            if col1 in self._column_values:
                vals = [v for r, v in self._column_values[col1] if r == row_num]
                val1 = vals[0] if vals else None

            if col2 in self._column_values:
                vals = [v for r, v in self._column_values[col2] if r == row_num]
                val2 = vals[0] if vals else None

            has1 = bool(val1 and val1.strip())
            has2 = bool(val2 and val2.strip())

            if has1 != has2:
                issues.append(
                    ValidationIssue(
                        code="E015",
                        severity=Severity.ERROR,
                        row=row_num,
                        column=col1,
                        message=f"Columns '{col1}' and '{col2}' must both be present or both empty",
                        suggestion="Provide values for both columns or neither",
                    )
                )

        return issues
