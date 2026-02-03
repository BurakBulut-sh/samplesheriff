"""Tests for validation rules."""

from __future__ import annotations

from pathlib import Path

from samplesheriff.rules import RuleEngine, ValidationContext
from samplesheriff.rules.domain_rules import DomainRule
from samplesheriff.rules.engine import get_column_value
from samplesheriff.rules.file_rules import FileRule
from samplesheriff.rules.schema_rules import SchemaRule
from samplesheriff.schema import (
    ColumnSchema,
    ColumnType,
    Constraint,
    ConstraintType,
    Schema,
)


class TestGetColumnValue:
    """Tests for column value extraction."""

    def test_exact_match(self):
        """Test exact column match."""
        row = {"sample": "s1", "file": "/path"}
        assert get_column_value(row, "sample") == "s1"

    def test_case_insensitive_match(self):
        """Test case-insensitive column match."""
        row = {"Sample": "s1", "FILE": "/path"}
        assert get_column_value(row, "sample") == "s1"
        assert get_column_value(row, "file") == "/path"

    def test_empty_value(self):
        """Test empty value returns None."""
        row = {"sample": "", "file": "   "}
        assert get_column_value(row, "sample") is None
        assert get_column_value(row, "file") is None

    def test_missing_column(self):
        """Test missing column returns None."""
        row = {"sample": "s1"}
        assert get_column_value(row, "missing") is None


class TestSchemaRule:
    """Tests for SchemaRule."""

    def test_valid_row(self, simple_schema):
        """Test validation of valid row."""
        rule = SchemaRule(simple_schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        issues = rule.validate(context, {"sample": "s1", "file": "/path"}, 1)
        assert len(issues) == 0

    def test_empty_required_field(self, simple_schema):
        """Test validation catches empty required field."""
        rule = SchemaRule(simple_schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        issues = rule.validate(context, {"sample": "", "file": "/path"}, 1)
        assert len(issues) == 1
        assert issues[0].code == "E001"

    def test_type_validation(self):
        """Test type validation."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="count", type=ColumnType.INTEGER, required=True),
            ],
        )
        rule = SchemaRule(schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        issues = rule.validate(context, {"count": "not_a_number"}, 1)
        assert len(issues) == 1
        assert issues[0].code == "E002"

    def test_missing_required_column(self, simple_schema):
        """Test finalization catches missing required columns."""
        rule = SchemaRule(simple_schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        # Process one row (to trigger header detection)
        rule.validate(context, {"sample": "s1"}, 1)

        issues = rule.finalize(context)
        assert len(issues) == 1
        assert issues[0].code == "E010"  # Missing required column

    def test_unique_constraint(self):
        """Test unique constraint validation."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="sample", type=ColumnType.STRING, required=True),
            ],
            constraints=[
                Constraint(type=ConstraintType.UNIQUE, columns=["sample"]),
            ],
        )
        rule = SchemaRule(schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        rule.validate(context, {"sample": "s1"}, 1)
        rule.validate(context, {"sample": "s2"}, 2)
        rule.validate(context, {"sample": "s1"}, 3)  # Duplicate

        issues = rule.finalize(context)
        assert len(issues) == 1
        assert issues[0].code == "E012"

    def test_required_group_constraint(self):
        """Test required group constraint."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="a", required=False),
                ColumnSchema(name="b", required=False),
            ],
            constraints=[
                Constraint(type=ConstraintType.REQUIRED_GROUP, columns=["a", "b"]),
            ],
        )
        rule = SchemaRule(schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        rule.validate(context, {"a": "", "b": ""}, 1)

        issues = rule.finalize(context)
        assert len(issues) == 1
        assert issues[0].code == "E013"

    def test_mutually_exclusive_constraint(self):
        """Test mutually exclusive constraint."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="a", required=False),
                ColumnSchema(name="b", required=False),
            ],
            constraints=[
                Constraint(type=ConstraintType.MUTUALLY_EXCLUSIVE, columns=["a", "b"]),
            ],
        )
        rule = SchemaRule(schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        rule.validate(context, {"a": "value1", "b": "value2"}, 1)

        issues = rule.finalize(context)
        assert len(issues) == 1
        assert issues[0].code == "E014"

    def test_paired_constraint(self):
        """Test paired constraint."""
        schema = Schema(
            name="test",
            columns=[
                ColumnSchema(name="a", required=False),
                ColumnSchema(name="b", required=False),
            ],
            constraints=[
                Constraint(type=ConstraintType.PAIRED, columns=["a", "b"]),
            ],
        )
        rule = SchemaRule(schema)
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        rule.validate(context, {"a": "value", "b": ""}, 1)

        issues = rule.finalize(context)
        assert len(issues) == 1
        assert issues[0].code == "E015"


class TestFileRule:
    """Tests for FileRule."""

    def test_missing_file(self, temp_dir):
        """Test detection of missing file."""
        rule = FileRule()
        schema = Schema(name="test", columns=[])
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        issues = rule.validate(context, {"fastq_1": str(temp_dir / "nonexistent.fastq")}, 1)
        assert len(issues) == 1
        assert issues[0].code == "E020"

    def test_extension_warning(self, temp_dir):
        """Test extension sanity check warning."""
        rule = FileRule()
        schema = Schema(name="test", columns=[])
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        # Create a file with wrong extension
        path = temp_dir / "data.txt"
        path.write_text("content")

        issues = rule.validate(context, {"fastq_1": str(path)}, 1)
        assert len(issues) == 1
        assert issues[0].code == "W011"

    def test_gzip_warning(self, temp_dir):
        """Test gzip extension warning for non-gzipped file."""
        rule = FileRule()
        schema = Schema(name="test", columns=[])
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        # Create a non-gzipped file with .gz extension
        path = temp_dir / "data.fastq.gz"
        path.write_text("plain text, not gzipped")

        issues = rule.validate(context, {"fastq_1": str(path)}, 1)
        assert len(issues) == 1
        assert issues[0].code == "W010"


class TestDomainRule:
    """Tests for DomainRule."""

    def test_mutually_exclusive_modes(self):
        """Test mutually exclusive file mode detection."""
        rule = DomainRule()
        schema = Schema(name="test", columns=[])
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        issues = rule.validate(
            context,
            {"sample": "s1", "fastq_1": "/path/to/file.fastq", "bam": "/path/to/file.bam"},
            1,
        )
        assert len(issues) == 1
        assert issues[0].code == "E030"

    def test_fastq_requires_fastq1(self):
        """Test FASTQ mode requires fastq_1."""
        rule = DomainRule()
        schema = Schema(name="test", columns=[])
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=schema,
        )

        issues = rule.validate(context, {"sample": "s1", "fastq_2": "/path/to/file.fastq"}, 1)
        assert len(issues) == 1
        assert issues[0].code == "E031"


class TestRuleEngine:
    """Tests for RuleEngine."""

    def test_engine_initialization(self, simple_schema):
        """Test engine initialization."""
        engine = RuleEngine()
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        issues = engine.initialize(context)
        assert len(issues) == 0

    def test_add_and_run_rules(self, simple_schema):
        """Test adding and running rules."""
        engine = RuleEngine()
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        engine.initialize(context)
        engine.add_rule(SchemaRule(simple_schema))

        issues = engine.validate_row({"sample": "s1", "file": "/path"}, 1)
        assert len(issues) == 0

    def test_finalize(self, simple_schema):
        """Test rule finalization."""
        engine = RuleEngine()
        context = ValidationContext(
            input_path=Path("test.tsv"),
            schema=simple_schema,
        )

        engine.initialize(context)
        engine.add_rule(SchemaRule(simple_schema))

        # Validate one row
        engine.validate_row({"sample": "s1"}, 1)

        # Finalize should catch missing required column
        issues = engine.finalize()
        assert len(issues) == 1
