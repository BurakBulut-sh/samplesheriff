"""Pytest configuration and fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from samplesheriff.schema import (
    ColumnSchema,
    ColumnType,
    Constraint,
    ConstraintType,
    FileCheckMode,
    Schema,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def simple_schema():
    """Create a simple schema for testing."""
    return Schema(
        name="test_schema",
        description="Test schema",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
            ),
            ColumnSchema(
                name="file",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.OPTIONAL,
            ),
        ],
    )


@pytest.fixture
def fastq_schema():
    """Create a FASTQ schema for testing."""
    return Schema(
        name="fastq_test",
        description="FASTQ test schema",
        columns=[
            ColumnSchema(
                name="sample",
                type=ColumnType.STRING,
                required=True,
            ),
            ColumnSchema(
                name="fastq_1",
                type=ColumnType.PATH,
                required=True,
                file_check=FileCheckMode.OPTIONAL,
            ),
            ColumnSchema(
                name="fastq_2",
                type=ColumnType.PATH,
                required=False,
                file_check=FileCheckMode.OPTIONAL,
            ),
        ],
        constraints=[
            Constraint(
                type=ConstraintType.UNIQUE,
                columns=["sample"],
            ),
        ],
    )


@pytest.fixture
def valid_tsv_file(temp_dir):
    """Create a valid TSV file."""
    path = temp_dir / "valid.tsv"
    path.write_text("sample\tfile\ns1\t/path/to/file1\ns2\t/path/to/file2\n")
    return path


@pytest.fixture
def valid_csv_file(temp_dir):
    """Create a valid CSV file."""
    path = temp_dir / "valid.csv"
    path.write_text("sample,file\ns1,/path/to/file1\ns2,/path/to/file2\n")
    return path


@pytest.fixture
def missing_column_file(temp_dir):
    """Create a file with missing required column."""
    path = temp_dir / "missing_col.tsv"
    path.write_text("file\n/path/to/file1\n")
    return path


@pytest.fixture
def empty_cell_file(temp_dir):
    """Create a file with empty required cell."""
    path = temp_dir / "empty_cell.tsv"
    path.write_text("sample\tfile\ns1\t\n")
    return path


@pytest.fixture
def gzipped_file(temp_dir):
    """Create a gzipped file."""
    import gzip

    path = temp_dir / "test.fastq.gz"
    with gzip.open(path, "wt") as f:
        f.write("@read1\nACGT\n+\n!!!!\n")
    return path
