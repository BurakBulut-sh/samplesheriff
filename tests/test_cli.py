"""Tests for CLI module."""

from __future__ import annotations

import re

from typer.testing import CliRunner

from samplesheriff.cli import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    return re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)


class TestValidateCommand:
    """Tests for validate command."""

    def test_help(self):
        """Test validate command help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        clean_output = strip_ansi(result.output)
        assert "--input" in clean_output
        assert "--schema" in clean_output

    def test_missing_input(self):
        """Test validate fails without input."""
        result = runner.invoke(app, ["validate"])
        assert result.exit_code != 0

    def test_valid_samplesheet(self, temp_dir):
        """Test validate with valid samplesheet."""
        # Create an actual file that exists
        data_file = temp_dir / "data.txt"
        data_file.write_text("test data")

        # Create a valid TSV file
        sheet = temp_dir / "samples.tsv"
        sheet.write_text(f"sample\tfile\ns1\t{data_file}\n")

        result = runner.invoke(
            app,
            [
                "validate",
                "--input",
                str(sheet),
                "--schema",
                "builtin:minimal",
            ],
        )
        # Should succeed (exit code 0) since file exists
        assert result.exit_code == 0

    def test_missing_column(self, temp_dir):
        """Test validate catches missing column."""
        sheet = temp_dir / "samples.tsv"
        sheet.write_text("file\n/path/to/file\n")

        result = runner.invoke(
            app,
            [
                "validate",
                "--input",
                str(sheet),
                "--schema",
                "builtin:minimal",
            ],
        )
        # Should fail due to missing required column
        assert result.exit_code == 1
        assert "sample" in result.output.lower()

    def test_json_output(self, temp_dir):
        """Test validate with JSON output."""
        # Create an actual file that exists
        data_file = temp_dir / "data.txt"
        data_file.write_text("test data")

        sheet = temp_dir / "samples.tsv"
        sheet.write_text(f"sample\tfile\ns1\t{data_file}\n")

        result = runner.invoke(
            app,
            [
                "validate",
                "--input",
                str(sheet),
                "--schema",
                "builtin:minimal",
                "--format",
                "json",
            ],
        )
        assert result.exit_code == 0
        assert '"success"' in result.output

    def test_report_output(self, temp_dir):
        """Test validate saves JSON report."""
        # Create an actual file that exists
        data_file = temp_dir / "data.txt"
        data_file.write_text("test data")

        sheet = temp_dir / "samples.tsv"
        sheet.write_text(f"sample\tfile\ns1\t{data_file}\n")
        report = temp_dir / "report.json"

        result = runner.invoke(
            app,
            [
                "validate",
                "--input",
                str(sheet),
                "--schema",
                "builtin:minimal",
                "--report",
                str(report),
            ],
        )
        assert result.exit_code == 0
        assert report.exists()


class TestSchemaCommands:
    """Tests for schema subcommands."""

    def test_schema_list(self):
        """Test schema list command."""
        result = runner.invoke(app, ["schema", "list"])
        assert result.exit_code == 0
        assert "nfcore_like" in result.output
        assert "minimal" in result.output

    def test_schema_show(self):
        """Test schema show command."""
        result = runner.invoke(app, ["schema", "show", "minimal"])
        assert result.exit_code == 0
        assert "minimal" in result.output
        assert "sample" in result.output

    def test_schema_show_not_found(self):
        """Test schema show with non-existent schema."""
        result = runner.invoke(app, ["schema", "show", "nonexistent"])
        assert result.exit_code == 1


class TestInitCommand:
    """Tests for init command."""

    def test_init_fastq(self, temp_dir):
        """Test init with FASTQ template."""
        result = runner.invoke(
            app,
            [
                "init",
                str(temp_dir),
                "--type",
                "fastq",
                "--name",
                "test",
            ],
        )
        assert result.exit_code == 0

        sheet = temp_dir / "test.tsv"
        schema = temp_dir / "test_schema.yaml"

        assert sheet.exists()
        assert schema.exists()
        assert "fastq_1" in sheet.read_text()

    def test_init_bam(self, temp_dir):
        """Test init with BAM template."""
        result = runner.invoke(
            app,
            [
                "init",
                str(temp_dir),
                "--type",
                "bam",
                "--name",
                "test",
            ],
        )
        assert result.exit_code == 0

        sheet = temp_dir / "test.tsv"
        assert "bam" in sheet.read_text()

    def test_init_vcf(self, temp_dir):
        """Test init with VCF template."""
        result = runner.invoke(
            app,
            [
                "init",
                str(temp_dir),
                "--type",
                "vcf",
                "--name",
                "test",
            ],
        )
        assert result.exit_code == 0

        sheet = temp_dir / "test.tsv"
        assert "vcf" in sheet.read_text()

    def test_init_unknown_type(self, temp_dir):
        """Test init with unknown template type."""
        result = runner.invoke(
            app,
            [
                "init",
                str(temp_dir),
                "--type",
                "unknown",
            ],
        )
        assert result.exit_code == 1


class TestVersion:
    """Tests for version flag."""

    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "SampleSheriff" in result.output

    def test_version_short(self):
        """Test -v flag."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "SampleSheriff" in result.output
