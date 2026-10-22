"""Utility functions for SampleSheriff.

This module provides common utilities used across the package.
"""

from __future__ import annotations

import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any


class FileType(Enum):
    """Supported bioinformatics file types."""

    FASTQ = "fastq"
    BAM = "bam"
    CRAM = "cram"
    SAM = "sam"
    VCF = "vcf"
    BCF = "bcf"
    UNKNOWN = "unknown"


def detect_file_type(path: Path) -> FileType:
    """Detect the type of a bioinformatics file from extension.

    Args:
        path: Path to the file

    Returns:
        Detected file type
    """
    name = path.name.lower()

    # Handle .gz suffix
    if name.endswith(".gz"):
        name = name[:-3]

    if name.endswith(".fastq") or name.endswith(".fq"):
        return FileType.FASTQ
    elif name.endswith(".bam"):
        return FileType.BAM
    elif name.endswith(".cram"):
        return FileType.CRAM
    elif name.endswith(".sam"):
        return FileType.SAM
    elif name.endswith(".vcf"):
        return FileType.VCF
    elif name.endswith(".bcf"):
        return FileType.BCF

    return FileType.UNKNOWN


def which(command: str) -> Path | None:
    """Find the path to an executable command.

    Args:
        command: Command name to find

    Returns:
        Path to the executable, or None if not found
    """
    path = shutil.which(command)
    return Path(path) if path else None


def run_command(
    cmd: list[str],
    check: bool = False,
    capture_output: bool = True,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    """Run a shell command safely.

    Args:
        cmd: Command and arguments as list
        check: Whether to raise on non-zero exit
        capture_output: Whether to capture stdout/stderr
        timeout: Timeout in seconds

    Returns:
        CompletedProcess instance

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
        subprocess.TimeoutExpired: If command times out
    """
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=True,
        timeout=timeout,
    )


def has_samtools() -> bool:
    """Check if samtools is available.

    Returns:
        True if samtools is in PATH
    """
    return which("samtools") is not None


def has_bcftools() -> bool:
    """Check if bcftools is available.

    Returns:
        True if bcftools is in PATH
    """
    return which("bcftools") is not None


def get_bam_header(bam_path: Path) -> str:
    """Extract BAM header using samtools.

    Args:
        bam_path: Path to BAM file

    Returns:
        Header content as string

    Raises:
        RuntimeError: If samtools is not available or fails
    """
    samtools = which("samtools")
    if not samtools:
        raise RuntimeError("samtools not found in PATH")

    result = run_command(
        [str(samtools), "view", "-H", str(bam_path)],
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"samtools failed: {result.stderr}")

    return result.stdout


def parse_bam_rg_headers(header: str) -> list[dict[str, str]]:
    """Parse @RG (read group) headers from BAM header text.

    Args:
        header: BAM header content

    Returns:
        List of read group dictionaries
    """
    read_groups: list[dict[str, str]] = []

    for line in header.split("\n"):
        if line.startswith("@RG"):
            # Parse tab-separated key:value pairs
            rg: dict[str, str] = {}
            parts = line.split("\t")
            for part in parts[1:]:  # Skip @RG itself
                if ":" in part:
                    key, value = part.split(":", 1)
                    rg[key] = value
            read_groups.append(rg)

    return read_groups


def get_vcf_header(vcf_path: Path) -> str:
    """Extract VCF header using bcftools or direct reading.

    Args:
        vcf_path: Path to VCF file

    Returns:
        Header content as string
    """
    bcftools = which("bcftools")

    if bcftools:
        result = run_command(
            [str(bcftools), "head", str(vcf_path)],
            check=False,
        )
        if result.returncode == 0:
            return result.stdout

    # Fallback: read directly (works for uncompressed and gzipped)
    from samplesheriff.io import open_file

    headers: list[str] = []
    with open_file(vcf_path) as f:
        for line in f:
            if line.startswith("#"):
                headers.append(line.rstrip("\n"))
            else:
                break
    return "\n".join(headers)


def parse_vcf_samples(header: str) -> list[str]:
    """Extract sample names from VCF header.

    Args:
        header: VCF header content

    Returns:
        List of sample names
    """
    for line in header.split("\n"):
        if line.startswith("#CHROM"):
            # Format: #CHROM POS ID REF ALT QUAL FILTER INFO FORMAT SAMPLE1 SAMPLE2 ...
            parts = line.split("\t")
            # Samples start after FORMAT (column 9, index 8)
            if len(parts) > 9:
                return parts[9:]
            return []
    return []


def check_index_exists(file_path: Path, index_type: str | None = None) -> bool:
    """Check if an index file exists for a given file.

    Args:
        file_path: Path to the data file
        index_type: Specific index type to check, or None for auto-detect

    Returns:
        True if corresponding index file exists
    """
    path = Path(file_path)

    # Determine expected index extensions based on file type and specified index_type
    if index_type:
        # Use specified index type
        if index_type == "bai":
            index_extensions = [".bai"]
        elif index_type == "csi":
            index_extensions = [".csi"]
        elif index_type == "tbi":
            index_extensions = [".tbi"]
        elif index_type == "idx":
            index_extensions = [".idx"]
        else:
            index_extensions = [f".{index_type}"]
    elif path.suffix == ".bam":
        index_extensions = [".bai", ".csi"]
    elif path.suffix == ".cram":
        index_extensions = [".crai"]
    elif path.suffix in (".vcf", ".bcf") or str(path).endswith(".vcf.gz"):
        index_extensions = [".tbi", ".csi"]
    else:
        # Default: try common index extensions
        index_extensions = [".bai", ".csi", ".tbi", ".crai", ".idx"]

    # Check for index file
    for ext in index_extensions:
        # Index can be file.bam.bai or file.bai
        index_path = path.parent / f"{path.name}{ext}"
        if index_path.exists():
            return True

        # Also check without double extension (file.bai for file.bam)
        if path.suffix:
            index_path = path.with_suffix(ext)
            if index_path.exists():
                return True

    return False


def normalize_path(path: Path, base_dir: Path | None = None) -> Path:
    """Normalize a path, optionally resolving against a base directory.

    Args:
        path: Path to normalize
        base_dir: Optional base directory for relative paths

    Returns:
        Normalized absolute path
    """
    if base_dir is not None and not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
