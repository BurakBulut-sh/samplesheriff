"""Tests for schema module."""

from __future__ import annotations

import pytest

from samplesheriff.schema import (
    ColumnSchema,
    ColumnType,
    Schema,
    Severity,
    ValidationIssue,
    list_builtin_schemas,
    load_builtin_schema,
)


class TestColumnType:
    """Tests for ColumnType enum."""

    def test_column_type_values(self):
        """Test column type enum values."""
        assert ColumnType.STRING.name == "STRING"
        assert ColumnType.INTEGER.name == "INTEGER"
        assert ColumnType.FLOAT.name == "FLOAT"
        assert ColumnType.BOOLEAN.name == "BOOLEAN"
        assert ColumnType.PATH.name == "PATH"


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Test severity enum values."""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_issue_creation(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            code="E001",
            severity=Severity.ERROR,
            row=1,
            column="sample",
            message="Test message",
            suggestion="Fix it",
        )
        assert issue.code == "E001"
        assert issue.severity == Severity.ERROR
        assert issue.row == 1
        assert issue.column == "sample"

    def test_issue_to_dict(self):
        """Test converting issue to dictionary."""
        issue = ValidationIssue(
            code="E001",
            severity=Severity.WARNING,
            row=2,
            column="file",
            message="Warning message",
        )
        d = issue.to_dict()
        assert d["code"] == "E001"
        assert d["severity"] == "warning"
        assert d["row"] == 2


class TestColumnSchema:
    """Tests for ColumnSchema."""

    def test_basic_column(self):
        """Test basic column creation."""
        col = ColumnSchema(name="sample", type=ColumnType.STRING, required=True)
        assert col.name == "sample"
        assert col.type == ColumnType.STRING
        assert col.required is True

    def test_column_with_pattern(self):
        """Test column with regex pattern."""
        col = ColumnSchema(
            name="md5",
            type=ColumnType.STRING,
            pattern="^[a-f0-9]{32}$",
        )
        assert col.pattern == "^[a-f0-9]{32}$"

    def test_invalid_pattern(self):
        """Test that invalid regex raises error."""
        with pytest.raises(ValueError, match="Invalid regex"):
            ColumnSchema(name="test", pattern="[invalid")

    def test_validate_string_value(self):
        """Test validating a string value."""
        col = ColumnSchema(name="sample", type=ColumnType.STRING, required=True)
        issues = col.validate_value("test", 1)
        assert len(issues) == 0

    def test_validate_empty_required(self):
        """Test validating empty required value."""
        col = ColumnSchema(name="sample", type=ColumnType.STRING, required=True)
        issues = col.validate_value("", 1)
        assert len(issues) == 1
        assert issues[0].severity == Severity.ERROR

    def test_validate_empty_optional(self):
        """Test validating empty optional value."""
        col = ColumnSchema(name="sample", type=ColumnType.STRING, required=False)
        issues = col.validate_value("", 1)
        assert len(issues) == 0

    def test_validate_integer(self):
        """Test validating integer values."""
        col = ColumnSchema(name="count", type=ColumnType.INTEGER)
        issues = col.validate_value("42", 1)
        assert len(issues) == 0

        issues = col.validate_value("not_a_number", 1)
        assert len(issues) == 1
        assert issues[0].code == "E002"

    def test_validate_float(self):
        """Test validating float values."""
        col = ColumnSchema(name="score", type=ColumnType.FLOAT)
        issues = col.validate_value("3.14", 1)
        assert len(issues) == 0

        issues = col.validate_value("not_a_float", 1)
        assert len(issues) == 1
        assert issues[0].code == "E003"

    def test_validate_boolean(self):
        """Test validating boolean values."""
        col = ColumnSchema(name="flag", type=ColumnType.BOOLEAN)

        for valid in ["true", "false", "True", "False", "1", "0", "yes", "no", "Y", "N"]:
            issues = col.validate_value(valid, 1)
            assert len(issues) == 0, f"Should accept '{valid}'"

        issues = col.validate_value("maybe", 1)
        assert len(issues) == 1

    def test_validate_pattern(self):
        """Test pattern validation."""
        col = ColumnSchema(
            name="md5",
            type=ColumnType.STRING,
            pattern="^[a-f0-9]{32}$",
        )
        issues = col.validate_value("d41d8cd98f00b204e9800998ecf8427e", 1)
        assert len(issues) == 0

        issues = col.validate_value("invalid_md5", 1)
        assert len(issues) == 1
        assert issues[0].code == "E005"

    def test_validate_allowed_values(self):
        """Test allowed values validation."""
        col = ColumnSchema(
            name="status",
            type=ColumnType.STRING,
            allowed_values=["active", "inactive"],
        )
        issues = col.validate_value("active", 1)
        assert len(issues) == 0

        issues = col.validate_value("unknown", 1)
        assert len(issues) == 1
        assert issues[0].code == "E006"


class TestSchema:
    """Tests for Schema class."""

    def test_basic_schema(self):
        """Test basic schema creation."""
        schema = Schema(
            name="test",
            description="Test schema",
            columns=[
                ColumnSchema(name="sample", type=ColumnType.STRING, required=True),
            ],
        )
        assert schema.name == "test"
        assert len(schema.columns) == 1

    def test_duplicate_column_names(self):
        """Test that duplicate column names raise error."""
        with pytest.raises(ValueError, match="Duplicate column"):
            Schema(
                name="test",
                columns=[
                    ColumnSchema(name="sample", required=True),
                    ColumnSchema(name="sample", required=True),
                ],
            )

    def test_get_required_columns(self):
        """Test getting required columns."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="sample", required=True),
                ColumnSchema(name="optional", required=False),
                ColumnSchema(name="another_required", required=True),
            ],
        )
        required = schema.get_required_columns()
        assert required == ["sample", "another_required"]

    def test_get_column(self):
        """Test getting column by name."""
        col = ColumnSchema(name="sample", required=True)
        schema = Schema(name="test", columns=[col])

        found = schema.get_column("sample")
        assert found is not None
        assert found.name == "sample"

        not_found = schema.get_column("missing")
        assert not_found is None

    def test_schema_yaml_roundtrip(self, temp_dir):
        """Test YAML serialization and deserialization."""
        schema = Schema(
            name="test",
            description="Test",
            columns=[
                ColumnSchema(name="sample", type=ColumnType.STRING, required=True),
                ColumnSchema(name="count", type=ColumnType.INTEGER),
            ],
        )

        path = temp_dir / "schema.yaml"
        schema.save(path)

        loaded = Schema.from_file(path)
        assert loaded.name == schema.name
        assert len(loaded.columns) == len(schema.columns)


class TestBuiltinSchemas:
    """Tests for built-in schema loading."""

    def test_list_builtin_schemas(self):
        """Test listing built-in schemas."""
        schemas = list_builtin_schemas()
        assert "nfcore_like" in schemas
        assert "fastq_only" in schemas
        assert "bam_only" in schemas
        assert "vcf_only" in schemas
        assert "minimal" in schemas

    def test_load_nfcore_like_schema(self):
        """Test loading nfcore_like schema."""
        schema = load_builtin_schema("nfcore_like")
        assert schema.name == "nfcore_like"
        assert len(schema.columns) > 0

        # Check for expected columns
        column_names = {col.name for col in schema.columns}
        assert "sample" in column_names
        assert "fastq_1" in column_names
        assert "bam" in column_names
        assert "vcf" in column_names

    def test_load_with_builtin_prefix(self):
        """Test loading with 'builtin:' prefix."""
        schema = load_builtin_schema("builtin:minimal")
        assert schema.name == "minimal"

    def test_load_nonexistent_schema(self):
        """Test loading non-existent schema raises error."""
        with pytest.raises(FileNotFoundError):
            load_builtin_schema("nonexistent")
