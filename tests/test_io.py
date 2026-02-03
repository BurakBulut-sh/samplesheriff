"""Tests for io module."""

from __future__ import annotations

import gzip

import pytest

from samplesheriff.io import (
    check_file_non_empty,
    detect_delimiter,
    extract_read_name,
    is_gzipped,
    open_file,
    peek_file,
    read_fastq_headers,
    read_sample_sheet,
    validate_file_readable,
)


class TestDetectDelimiter:
    """Tests for delimiter detection."""

    def test_detect_tab(self):
        """Test detecting tab delimiter."""
        content = "col1\tcol2\tcol3\nval1\tval2\tval3\n"
        assert detect_delimiter(content) == "\t"

    def test_detect_comma(self):
        """Test detecting comma delimiter."""
        content = "col1,col2,col3\nval1,val2,val3\n"
        assert detect_delimiter(content) == ","

    def test_detect_semicolon(self):
        """Test detecting semicolon delimiter."""
        content = "col1;col2;col3\nval1;val2;val3\n"
        assert detect_delimiter(content) == ";"

    def test_default_to_tab(self):
        """Test default to tab when no clear delimiter."""
        content = "single column\nmore data\n"
        assert detect_delimiter(content) == "\t"

    def test_tab_preferred_over_comma(self):
        """Test that tab is preferred when both present."""
        # Tab-separated with commas in data
        content = "col1\tcol2\n1,000\t2,000\n"
        assert detect_delimiter(content) == "\t"


class TestOpenFile:
    """Tests for file opening."""

    def test_open_regular_file(self, temp_dir):
        """Test opening regular file."""
        path = temp_dir / "test.txt"
        path.write_text("hello")

        with open_file(path) as f:
            assert f.read() == "hello"

    def test_open_gzipped_file(self, temp_dir):
        """Test opening gzipped file."""
        path = temp_dir / "test.gz"
        with gzip.open(path, "wt") as f:
            f.write("compressed")

        with open_file(path) as f:
            assert f.read() == "compressed"


class TestPeekFile:
    """Tests for file peeking."""

    def test_peek_regular_file(self, temp_dir):
        """Test peeking regular file."""
        path = temp_dir / "test.txt"
        path.write_text("hello world")

        content = peek_file(path, 5)
        assert content == "hello"

    def test_peek_gzipped_file(self, temp_dir):
        """Test peeking gzipped file."""
        path = temp_dir / "test.gz"
        with gzip.open(path, "wt") as f:
            f.write("compressed content")

        content = peek_file(path, 10)
        assert content.startswith("compressed")


class TestIsGzipped:
    """Tests for gzip detection."""

    def test_detect_gzipped(self, temp_dir):
        """Test detecting gzipped file."""
        path = temp_dir / "test.gz"
        with gzip.open(path, "wt") as f:
            f.write("data")

        assert is_gzipped(path) is True

    def test_detect_not_gzipped(self, temp_dir):
        """Test detecting non-gzipped file."""
        path = temp_dir / "test.txt"
        path.write_text("plain text")

        assert is_gzipped(path) is False


class TestCheckFileNonEmpty:
    """Tests for file emptiness check."""

    def test_non_empty_file(self, temp_dir):
        """Test non-empty file detection."""
        path = temp_dir / "test.txt"
        path.write_text("content")

        assert check_file_non_empty(path) is True

    def test_empty_file(self, temp_dir):
        """Test empty file detection."""
        path = temp_dir / "test.txt"
        path.write_text("")

        assert check_file_non_empty(path) is False


class TestValidateFileReadable:
    """Tests for file readability validation."""

    def test_readable_file(self, temp_dir):
        """Test readable file."""
        path = temp_dir / "test.txt"
        path.write_text("content")

        readable, error = validate_file_readable(path)
        assert readable is True
        assert error == ""

    def test_nonexistent_file(self, temp_dir):
        """Test non-existent file."""
        path = temp_dir / "missing.txt"

        readable, error = validate_file_readable(path)
        assert readable is False
        assert "not exist" in error

    def test_directory_not_file(self, temp_dir):
        """Test directory is not a file."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        readable, error = validate_file_readable(subdir)
        assert readable is False
        assert "not a file" in error


class TestReadSampleSheet:
    """Tests for sample sheet reading."""

    def test_read_tsv(self, temp_dir):
        """Test reading TSV file."""
        path = temp_dir / "samples.tsv"
        path.write_text("sample\tfile\ns1\t/path/to/file1\n")

        reader = read_sample_sheet(path)
        headers = reader.read_headers()
        assert headers == ["sample", "file"]

        rows = list(reader.iter_rows())
        assert len(rows) == 1
        assert rows[0]["sample"] == "s1"

    def test_read_csv(self, temp_dir):
        """Test reading CSV file."""
        path = temp_dir / "samples.csv"
        path.write_text("sample,file\ns1,/path/to/file1\n")

        reader = read_sample_sheet(path)
        headers = reader.read_headers()
        assert headers == ["sample", "file"]

    def test_count_rows(self, temp_dir):
        """Test row counting."""
        path = temp_dir / "samples.tsv"
        path.write_text("sample\tfile\ns1\tf1\ns2\tf2\ns3\tf3\n")

        reader = read_sample_sheet(path)
        assert reader.count_rows() == 3

    def test_get_column_index(self, temp_dir):
        """Test getting column index."""
        path = temp_dir / "samples.tsv"
        path.write_text("sample\tfile\ns1\tf1\n")

        reader = read_sample_sheet(path)
        assert reader.get_column_index("sample") == 0
        assert reader.get_column_index("file") == 1

        with pytest.raises(ValueError):
            reader.get_column_index("missing")


class TestReadFastqHeaders:
    """Tests for FASTQ header reading."""

    def test_read_headers(self, temp_dir):
        """Test reading FASTQ headers."""
        path = temp_dir / "test.fastq"
        path.write_text(
            "@read1/1\nACGT\n+\n!!!!\n@read2/1\nTGCA\n+\n!!!!\n@read3/1\nAAAA\n+\n!!!!\n"
        )

        headers = read_fastq_headers(path, 10)
        assert len(headers) == 3
        assert headers[0] == "read1/1"
        assert headers[1] == "read2/1"

    def test_read_gzipped_fastq(self, temp_dir):
        """Test reading gzipped FASTQ headers."""
        path = temp_dir / "test.fastq.gz"
        with gzip.open(path, "wt") as f:
            f.write("@read1\nACGT\n+\n!!!!\n")

        headers = read_fastq_headers(path, 10)
        assert len(headers) == 1
        assert headers[0] == "read1"


class TestExtractReadName:
    """Tests for read name extraction."""

    def test_simple_name(self):
        """Test simple read name."""
        assert extract_read_name("read1") == "read1"

    def test_name_with_space(self):
        """Test name with space (Illumina format)."""
        assert extract_read_name("read1 comment") == "read1"

    def test_name_with_pair_suffix(self):
        """Test name with /1 or /2 suffix."""
        assert extract_read_name("read1/1") == "read1"
        assert extract_read_name("read1/2") == "read1"

    def test_name_with_comment_and_suffix(self):
        """Test name with both comment and suffix."""
        assert extract_read_name("read1/1 comment") == "read1"
