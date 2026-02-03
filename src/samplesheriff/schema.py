"""Schema definition and validation system for SampleSheriff.

This module provides a declarative schema system for validating sample sheets
in bioinformatics pipelines. Schemas define required/optional columns, types,
allowed values, regex patterns, and per-row constraints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class ColumnType(Enum):
    """Supported column data types."""

    STRING = auto()
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    PATH = auto()


class Severity(Enum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class FileCheckMode(Enum):
    """Mode for handling file existence checks."""

    REQUIRED = "required"  # File must exist
    OPTIONAL = "optional"  # File may or may not exist
    SKIP = "skip"  # Don't check file existence


@dataclass(frozen=True)
class ValidationIssue:
    """Represents a single validation issue.

    Attributes:
        code: Unique issue code (e.g., "E001", "W003")
        severity: Issue severity level
        row: Row number in the sample sheet (0 for header issues, 1-indexed for data)
        column: Column name where the issue occurred (empty string for general issues)
        message: Human-readable description of the issue
        suggestion: Optional suggestion for how to fix the issue
    """

    code: str
    severity: Severity
    row: int
    column: str
    message: str
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert issue to dictionary representation."""
        return {
            "code": self.code,
            "severity": self.severity.value,
            "row": self.row,
            "column": self.column,
            "message": self.message,
            "suggestion": self.suggestion,
        }


class ColumnSchema(BaseModel):
    """Schema definition for a single column.

    Attributes:
        name: Column name (must match header exactly)
        type: Data type for the column
        required: Whether this column must be present
        allow_empty: Whether empty/null values are allowed
        allowed_values: Optional list of allowed values (enum-style)
        pattern: Optional regex pattern for validation
        file_check: How to handle file existence checks for PATH type
        description: Human-readable description of the column
    """

    name: str
    type: ColumnType = ColumnType.STRING
    required: bool = True
    allow_empty: bool = True  # Empty values are allowed by default for optional columns
    allowed_values: list[str] | None = None
    pattern: str | None = None
    file_check: FileCheckMode = FileCheckMode.OPTIONAL
    description: str = ""

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str | None) -> str | None:
        """Validate that the pattern is a valid regex."""
        if v is not None:
            try:
                re.compile(v)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        return v

    def validate_value(
        self,
        value: Any,
        row: int,
        base_dir: Path | None = None,
    ) -> list[ValidationIssue]:
        """Validate a single value against this column schema.

        Args:
            value: The value to validate
            row: Row number for issue reporting
            base_dir: Optional base directory for relative paths

        Returns:
            List of validation issues found
        """
        issues: list[ValidationIssue] = []

        # Check for empty/null values
        is_empty = value is None or (isinstance(value, str) and value.strip() == "")

        if is_empty:
            # Empty is an error only for required columns
            if self.required:
                issues.append(
                    ValidationIssue(
                        code="E001",
                        severity=Severity.ERROR,
                        row=row,
                        column=self.name,
                        message=f"Required column '{self.name}' has empty value",
                        suggestion="Provide a value for this column or mark it as optional",
                    )
                )
            return issues

        # Type validation and conversion
        converted_value: Any = value
        str_value = str(value).strip()

        match self.type:
            case ColumnType.INTEGER:
                try:
                    converted_value = int(str_value)
                except ValueError:
                    issues.append(
                        ValidationIssue(
                            code="E002",
                            severity=Severity.ERROR,
                            row=row,
                            column=self.name,
                            message=f"Expected integer in column '{self.name}', got '{str_value}'",
                            suggestion="Ensure the value is a valid integer",
                        )
                    )

            case ColumnType.FLOAT:
                try:
                    converted_value = float(str_value)
                except ValueError:
                    issues.append(
                        ValidationIssue(
                            code="E003",
                            severity=Severity.ERROR,
                            row=row,
                            column=self.name,
                            message=f"Expected float in column '{self.name}', got '{str_value}'",
                            suggestion="Ensure the value is a valid number",
                        )
                    )

            case ColumnType.BOOLEAN:
                lower_val = str_value.lower()
                if lower_val not in ("true", "false", "1", "0", "yes", "no", "y", "n"):
                    issues.append(
                        ValidationIssue(
                            code="E004",
                            severity=Severity.ERROR,
                            row=row,
                            column=self.name,
                            message=f"Expected boolean in column '{self.name}', got '{str_value}'",
                            suggestion="Use 'true'/'false', 'yes'/'no', or '1'/'0'",
                        )
                    )

            case ColumnType.PATH:
                # Path validation (existence check happens separately if requested)
                pass

        # Pattern validation
        if self.pattern is not None and str_value:
            if not re.match(self.pattern, str_value):
                issues.append(
                    ValidationIssue(
                        code="E005",
                        severity=Severity.ERROR,
                        row=row,
                        column=self.name,
                        message=f"Value '{str_value}' in column '{self.name}' does not match pattern '{self.pattern}'",
                        suggestion="Check the value format against the required pattern",
                    )
                )

        # Allowed values validation
        if self.allowed_values is not None and str_value:
            if str_value not in self.allowed_values:
                issues.append(
                    ValidationIssue(
                        code="E006",
                        severity=Severity.ERROR,
                        row=row,
                        column=self.name,
                        message=f"Value '{str_value}' in column '{self.name}' is not in allowed values: {self.allowed_values}",
                        suggestion=f"Use one of: {', '.join(self.allowed_values)}",
                    )
                )

        # File existence check for PATH type
        if self.type == ColumnType.PATH and str_value and self.file_check == FileCheckMode.REQUIRED:
            path = Path(str_value)
            if base_dir is not None:
                path = base_dir / path

            if not path.exists():
                issues.append(
                    ValidationIssue(
                        code="E007",
                        severity=Severity.ERROR,
                        row=row,
                        column=self.name,
                        message=f"File not found: {path}",
                        suggestion="Check the file path and ensure the file exists",
                    )
                )
            elif not path.is_file():
                issues.append(
                    ValidationIssue(
                        code="E008",
                        severity=Severity.ERROR,
                        row=row,
                        column=self.name,
                        message=f"Path exists but is not a file: {path}",
                        suggestion="Ensure the path points to a regular file",
                    )
                )

        return issues


class ConstraintType(Enum):
    """Types of cross-column/cross-row constraints."""

    UNIQUE = "unique"  # Column values must be unique
    REQUIRED_GROUP = "required_group"  # At least one of these columns must be non-empty
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"  # Only one of these columns can be non-empty
    PAIRED = "paired"  # These columns must both be present or both empty


class Constraint(BaseModel):
    """A constraint that applies across columns or rows.

    Attributes:
        type: Type of constraint
        columns: Column names involved in the constraint
        message: Custom error message
    """

    type: ConstraintType
    columns: list[str]
    message: str | None = None


class Schema(BaseModel):
    """Complete schema definition for a sample sheet.

    Attributes:
        name: Schema identifier name
        description: Human-readable description
        delimiter: Expected delimiter (auto-detect if None)
        columns: List of column schemas
        constraints: List of cross-column constraints
        allow_extra_columns: How to handle columns not in schema
        version: Schema version string
    """

    name: str
    description: str = ""
    delimiter: str | None = None
    columns: list[ColumnSchema]
    constraints: list[Constraint] = Field(default_factory=list)
    allow_extra_columns: bool = True
    version: str = "1.0.0"

    @field_validator("columns")
    @classmethod
    def validate_unique_column_names(cls, v: list[ColumnSchema]) -> list[ColumnSchema]:
        """Ensure column names are unique."""
        names = [col.name for col in v]
        if len(names) != len(set(names)):
            from collections import Counter

            duplicates = [name for name, count in Counter(names).items() if count > 1]
            raise ValueError(f"Duplicate column names: {duplicates}")
        return v

    def get_required_columns(self) -> list[str]:
        """Return list of required column names."""
        return [col.name for col in self.columns if col.required]

    def get_optional_columns(self) -> list[str]:
        """Return list of optional column names."""
        return [col.name for col in self.columns if not col.required]

    def get_column(self, name: str) -> ColumnSchema | None:
        """Get column schema by name."""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def to_yaml(self) -> str:
        """Serialize schema to YAML string."""
        # Convert to dict first for better YAML representation
        data = self.model_dump()
        # Convert enums to strings
        for col in data.get("columns", []):
            if "type" in col:
                col["type"] = (
                    col["type"].name if isinstance(col["type"], ColumnType) else col["type"]
                )
            if "file_check" in col:
                col["file_check"] = (
                    col["file_check"].name
                    if isinstance(col["file_check"], FileCheckMode)
                    else col["file_check"]
                )
        for constraint in data.get("constraints", []):
            if "type" in constraint:
                constraint["type"] = (
                    constraint["type"].name
                    if isinstance(constraint["type"], ConstraintType)
                    else constraint["type"]
                )
        return yaml.dump(data, sort_keys=False, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> Schema:
        """Deserialize schema from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls._from_dict(data)

    @classmethod
    def from_file(cls, path: Path) -> Schema:
        """Load schema from a YAML file."""
        with open(path) as f:
            return cls.from_yaml(f.read())

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> Schema:
        """Create Schema from dictionary, handling enum conversions."""
        # Convert string enums back to enum types
        for col in data.get("columns", []):
            if "type" in col and isinstance(col["type"], str):
                col["type"] = ColumnType[col["type"].upper()]
            if "file_check" in col and isinstance(col["file_check"], str):
                col["file_check"] = FileCheckMode[col["file_check"].upper()]

        for constraint in data.get("constraints", []):
            if "type" in constraint and isinstance(constraint["type"], str):
                constraint["type"] = ConstraintType[constraint["type"].upper()]

        return cls.model_validate(data)

    def save(self, path: Path) -> None:
        """Save schema to a YAML file."""
        with open(path, "w") as f:
            f.write(self.to_yaml())


def get_builtin_schemas_dir() -> Path:
    """Get the directory containing built-in schemas."""
    return Path(__file__).parent / "schemas"


def list_builtin_schemas() -> dict[str, str]:
    """List available built-in schemas.

    Returns:
        Dictionary mapping schema names to descriptions.
    """
    schemas_dir = get_builtin_schemas_dir()
    schemas: dict[str, str] = {}

    if schemas_dir.exists():
        for schema_file in schemas_dir.glob("*.yaml"):
            try:
                schema = Schema.from_file(schema_file)
                schemas[schema.name] = schema.description or "No description"
            except Exception:
                # Skip invalid schema files
                continue

    return schemas


def load_builtin_schema(name: str) -> Schema:
    """Load a built-in schema by name.

    Args:
        name: Schema name (with or without .yaml extension)

    Returns:
        Loaded Schema object

    Raises:
        FileNotFoundError: If schema doesn't exist
    """
    schemas_dir = get_builtin_schemas_dir()

    # Handle builtin: prefix
    if name.startswith("builtin:"):
        name = name[8:]

    # Try with and without .yaml extension
    schema_file = schemas_dir / name
    if not schema_file.exists():
        schema_file = schemas_dir / f"{name}.yaml"

    if not schema_file.exists():
        available = list(list_builtin_schemas().keys())
        raise FileNotFoundError(f"Built-in schema '{name}' not found. Available: {available}")

    return Schema.from_file(schema_file)
