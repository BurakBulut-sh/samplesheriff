"""File-level validation rules.

This module provides rules for validating file existence, readability,
extensions, and integrity for bioinformatics files.
"""

from __future__ import annotations

from pathlib import Path

from samplesheriff.io import check_file_non_empty, is_gzipped, validate_file_readable
from samplesheriff.rules.engine import ValidationContext, ValidationRule, get_column_value
from samplesheriff.schema import Severity, ValidationIssue


class FileRule(ValidationRule):
    """Validates file existence, readability, and basic integrity."""

    # Columns that typically contain file paths
    FILE_COLUMNS = [
        "fastq_1",
        "fastq_2",
        "fastq1",
        "fastq2",
        "fq1",
        "fq2",
        "r1",
        "r2",
        "read1",
        "read2",
        "bam",
        "cram",
        "sam",
        "vcf",
        "bcf",
        "gvcf",
        "crai",
        "bai",
        "tbi",
        "csi",
        "idx",
        "md5",
        "md5sum",
    ]

    def __init__(
        self,
        check_extensions: bool = True,
        check_readability: bool = True,
        check_non_empty: bool = True,
    ):
        """Initialize the file rule.

        Args:
            check_extensions: Whether to validate file extensions
            check_readability: Whether to check file readability
            check_non_empty: Whether to check file is non-empty
        """
        self.check_extensions = check_extensions
        self.check_readability = check_readability
        self.check_non_empty = check_non_empty

    def validate(
        self,
        context: ValidationContext,
        row: dict[str, str],
        row_number: int,
    ) -> list[ValidationIssue]:
        """Validate file paths in a row."""
        issues: list[ValidationIssue] = []

        for col in row:
            col_lower = col.lower()
            is_file_col = any(
                col_lower == fc or col_lower.startswith(fc + "_") or col_lower.endswith("_" + fc)
                for fc in self.FILE_COLUMNS
            )

            if not is_file_col:
                continue

            value = get_column_value(row, col)
            if not value:
                continue

            # Normalize path
            path = Path(value)
            if context.base_dir is not None and not path.is_absolute():
                path = context.base_dir / path

            # File existence and readability
            if self.check_readability:
                readable, error = validate_file_readable(path)
                if not readable:
                    issues.append(
                        ValidationIssue(
                            code="E020",
                            severity=Severity.ERROR,
                            row=row_number,
                            column=col,
                            message=error,
                            suggestion="Check the file path exists and is readable",
                        )
                    )
                    continue

            # Non-empty check
            if self.check_readability and self.check_non_empty:
                if not check_file_non_empty(path):
                    issues.append(
                        ValidationIssue(
                            code="E021",
                            severity=Severity.ERROR,
                            row=row_number,
                            column=col,
                            message=f"File is empty: {path}",
                            suggestion="Provide a non-empty file",
                        )
                    )

            # Extension sanity check
            if self.check_extensions:
                ext_issues = self._check_extension(path, col, row_number)
                issues.extend(ext_issues)

            # Gzip integrity check
            if self.check_readability and path.suffix == ".gz":
                if not is_gzipped(path):
                    issues.append(
                        ValidationIssue(
                            code="W010",
                            severity=Severity.WARNING,
                            row=row_number,
                            column=col,
                            message=f"File has .gz extension but is not gzip compressed: {path}",
                            suggestion="Remove .gz extension or compress with gzip",
                        )
                    )

        return issues

    def _check_extension(
        self,
        path: Path,
        column: str,
        row_number: int,
    ) -> list[ValidationIssue]:
        """Check file extension matches column semantics."""
        issues: list[ValidationIssue] = []
        col_lower = column.lower()

        # Determine expected extensions based on column name
        expected: list[str] = []

        if "fastq" in col_lower or "fq" in col_lower or col_lower in ("r1", "r2"):
            expected = [".fastq", ".fq", ".fastq.gz", ".fq.gz"]
        elif col_lower == "bam":
            expected = [".bam"]
        elif col_lower == "cram":
            expected = [".cram"]
        elif col_lower == "sam":
            expected = [".sam"]
        elif col_lower in ("vcf", "gvcf"):
            expected = [".vcf", ".vcf.gz"]
        elif col_lower == "bcf":
            expected = [".bcf"]
        elif col_lower in ("bai", "crai"):
            expected = [".bai", ".crai"]
        elif col_lower in ("tbi", "csi"):
            expected = [".tbi", ".csi"]

        if not expected:
            return issues

        # Check if path ends with any expected extension
        name_lower = path.name.lower()
        matches = any(name_lower.endswith(ext) for ext in expected)

        if not matches:
            issues.append(
                ValidationIssue(
                    code="W011",
                    severity=Severity.WARNING,
                    row=row_number,
                    column=column,
                    message=f"File extension for '{path}' doesn't match expected for column '{column}'",
                    suggestion=f"Expected one of: {', '.join(expected)}",
                )
            )

        return issues
