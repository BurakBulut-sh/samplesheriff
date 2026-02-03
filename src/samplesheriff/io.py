"""I/O utilities for reading and parsing sample sheets.

This module provides efficient streaming readers for various sample sheet
formats (TSV, CSV) with support for large files and auto-detection of
delimiters and compression formats.
"""

from __future__ import annotations

import csv
import gzip
import io
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from samplesheriff.schema import Schema


def detect_delimiter(content: str, candidates: list[str] | None = None) -> str:
    """Detect the most likely delimiter from content.

    Args:
        content: Sample content to analyze
        candidates: List of delimiter candidates to try

    Returns:
        The detected delimiter
    """
    if candidates is None:
        candidates = ["\t", ",", ";", "|"]

    # Count occurrences of each candidate in the first few lines
    lines = content.split("\n")[:10]
    scores: dict[str, int] = {}

    for delim in candidates:
        counts = [line.count(delim) for line in lines if line.strip()]
        if counts and all(c == counts[0] for c in counts) and counts[0] > 0:
            # Consistent count across lines
            scores[delim] = counts[0] * len(counts)

    if scores:
        # Prefer tab over comma if counts are equal (nf-core convention)
        if "\t" in scores:
            return "\t"
        return max(scores, key=scores.get)

    # Default to tab for bioinformatics
    return "\t"


def open_file(path: Path | str, mode: str = "rt") -> io.IOBase:
    """Open a file, handling gzip compression automatically.

    Args:
        path: Path to the file
        mode: File open mode

    Returns:
        File-like object
    """
    path = Path(path)

    # Only add encoding for text mode
    is_binary = "b" in mode

    if path.suffix == ".gz" or str(path).endswith(".gz"):
        if is_binary:
            return gzip.open(path, mode)
        else:
            return gzip.open(path, mode, encoding="utf-8")
    else:
        if is_binary:
            return open(path, mode)
        else:
            return open(path, mode, encoding="utf-8")


def peek_file(path: Path | str, n_bytes: int = 8192) -> str:
    """Read the beginning of a file for inspection.

    Args:
        path: Path to the file
        n_bytes: Number of bytes to read

    Returns:
        String content from the beginning of the file
    """
    with open_file(path, "rb") as f:
        content = f.read(n_bytes)
        # Try to decode as UTF-8, fallback to latin-1
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")


def read_sample_sheet(
    path: Path | str,
    schema: Schema | None = None,
    delimiter: str | None = None,
) -> SampleSheetReader:
    """Create a reader for a sample sheet file.

    Args:
        path: Path to the sample sheet
        schema: Optional schema for validation hints
        delimiter: Optional delimiter override

    Returns:
        SampleSheetReader instance
    """
    return SampleSheetReader(path, schema, delimiter)


class SampleSheetReader:
    """Streaming reader for sample sheet files.

    This class provides memory-efficient reading of sample sheets,
    supporting both header validation and row-by-row iteration.
    """

    def __init__(
        self,
        path: Path | str,
        schema: Schema | None = None,
        delimiter: str | None = None,
    ):
        """Initialize the reader.

        Args:
            path: Path to the sample sheet
            schema: Optional schema for validation hints
            delimiter: Optional delimiter override
        """
        self.path = Path(path)
        self.schema = schema
        self._delimiter_override = delimiter
        self._detected_delimiter: str | None = None
        self._headers: list[str] | None = None
        self._row_count: int | None = None

    @property
    def delimiter(self) -> str:
        """Get the detected or specified delimiter."""
        if self._delimiter_override:
            return self._delimiter_override
        if self.schema and self.schema.delimiter:
            return self.schema.delimiter
        if self._detected_delimiter is None:
            # Auto-detect from file content
            sample = peek_file(self.path, 4096)
            self._detected_delimiter = detect_delimiter(sample)
        return self._detected_delimiter

    def read_headers(self) -> list[str]:
        """Read and return the header row.

        Skips comment lines (starting with #) to find the actual header.

        Returns:
            List of column names
        """
        if self._headers is None:
            with open_file(self.path) as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                try:
                    # Skip comment lines
                    for row in reader:
                        if row and not row[0].startswith("#"):
                            self._headers = row
                            break
                    else:
                        self._headers = []
                except StopIteration:
                    self._headers = []
        return self._headers

    def iter_rows(self) -> Iterator[dict[str, Any]]:
        """Iterate over data rows as dictionaries.

        Skips comment lines (starting with #).

        Yields:
            Dictionary mapping column names to values
        """
        headers = self.read_headers()
        if not headers:
            return

        with open_file(self.path) as f:
            reader = csv.DictReader(f, fieldnames=headers, delimiter=self.delimiter)
            # Skip comment lines and header row
            header_found = False
            for row in reader:
                # Check if this is the header row (first non-comment row)
                if not header_found:
                    if row and list(row.values())[0] and not list(row.values())[0].startswith("#"):
                        header_found = True
                    continue

                # Filter out None keys and comment lines (from DictReader internals)
                if row:
                    first_value = list(row.values())[0] if row else ""
                    if first_value and not str(first_value).startswith("#"):
                        yield {k: v for k, v in row.items() if k is not None}

    def iter_rows_raw(self) -> Iterator[list[str]]:
        """Iterate over data rows as raw string lists.

        Yields:
            List of string values
        """
        headers = self.read_headers()
        if not headers:
            return

        with open_file(self.path) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            # Skip the header row
            try:
                next(reader)
            except StopIteration:
                return

            for row in reader:
                yield row

    def count_rows(self) -> int:
        """Count total data rows (excluding header).

        Returns:
            Number of data rows
        """
        if self._row_count is None:
            count = 0
            with open_file(self.path) as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                # Skip header
                try:
                    next(reader)
                except StopIteration:
                    self._row_count = 0
                    return 0
                # Count remaining rows
                for _ in reader:
                    count += 1
            self._row_count = count
        return self._row_count

    def get_column_index(self, column_name: str) -> int:
        """Get the index of a column by name.

        Args:
            column_name: Name of the column

        Returns:
            Zero-based column index

        Raises:
            ValueError: If column not found
        """
        headers = self.read_headers()
        try:
            return headers.index(column_name)
        except ValueError:
            raise ValueError(f"Column '{column_name}' not found in headers: {headers}")


def validate_file_readable(path: Path) -> tuple[bool, str]:
    """Check if a file exists and is readable.

    Args:
        path: Path to check

    Returns:
        Tuple of (is_readable, error_message)
    """
    if not path.exists():
        return False, f"File does not exist: {path}"
    if not path.is_file():
        return False, f"Path exists but is not a file: {path}"
    try:
        with open(path, "rb") as f:
            f.read(1)
        return True, ""
    except PermissionError:
        return False, f"Permission denied: {path}"
    except OSError as e:
        return False, f"Cannot read file {path}: {e}"


def is_gzipped(path: Path) -> bool:
    """Check if a file is gzip compressed by examining magic bytes.

    Args:
        path: Path to the file

    Returns:
        True if file appears to be gzip compressed
    """
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
            return magic == b"\x1f\x8b"
    except OSError:
        return False


def check_file_non_empty(path: Path) -> bool:
    """Check if a file is non-empty.

    Args:
        path: Path to the file

    Returns:
        True if file has content
    """
    try:
        return path.stat().st_size > 0
    except OSError:
        return False


def read_fastq_headers(path: Path, n_reads: int = 100) -> list[str]:
    """Read headers from a FASTQ file (supports .gz).

    Args:
        path: Path to the FASTQ file
        n_reads: Maximum number of read headers to extract

    Returns:
        List of read headers (without @ prefix)
    """
    headers: list[str] = []

    try:
        with open_file(path) as f:
            line_num = 0
            for line in f:
                line_num += 1
                # FASTQ: header every 4th line starting at line 1
                if (line_num - 1) % 4 == 0:
                    line = line.strip()
                    if line.startswith("@"):
                        headers.append(line[1:])  # Remove @ prefix
                        if len(headers) >= n_reads:
                            break
    except Exception:
        pass

    return headers


def extract_read_name(header: str) -> str:
    """Extract read name from FASTQ header, handling paired-end suffixes.

    Args:
        header: FASTQ header line (without @)

    Returns:
        Read name without pair indicators
    """
    # Remove trailing /1 or /2 or space-separated pair info
    parts = header.split()
    if parts:
        name = parts[0]
        if name.endswith("/1") or name.endswith("/2"):
            return name[:-2]
    return parts[0] if parts else header
