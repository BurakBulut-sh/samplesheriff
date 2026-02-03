"""Domain-specific validation rules for bioinformatics files.

This module provides validation rules specific to FASTQ, BAM, and VCF files,
including header checks, pairing validation, and cross-file consistency.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from samplesheriff.io import extract_read_name, open_file, read_fastq_headers
from samplesheriff.rules.engine import ValidationContext, ValidationRule, get_column_value
from samplesheriff.schema import Severity, ValidationIssue
from samplesheriff.utils import (
    check_index_exists,
    get_bam_header,
    get_vcf_header,
    has_samtools,
    normalize_path,
    parse_bam_rg_headers,
    parse_vcf_samples,
)


class DomainRule(ValidationRule):
    """Validates domain-specific constraints for bioinformatics files."""

    def __init__(
        self,
        require_index: bool = False,
        peek_fastq: int = 0,
        check_md5: bool = True,
    ):
        """Initialize domain rule.

        Args:
            require_index: Whether to require index files for BAM/CRAM/VCF
            peek_fastq: Number of FASTQ reads to peek at for pairing validation
            check_md5: Whether to verify MD5 checksums if provided
        """
        self.require_index = require_index
        self.peek_fastq = peek_fastq
        self.check_md5 = check_md5

        # State for cross-row validation
        self._sample_files: dict[str, dict[str, Any]] = {}
        self._fastq_pairs: dict[str, list[tuple[str, str, int]]] = {}  # sample -> [(r1, r2, row)]

    def validate(
        self,
        context: ValidationContext,
        row: dict[str, str],
        row_number: int,
    ) -> list[ValidationIssue]:
        """Validate domain-specific constraints for a row."""
        issues: list[ValidationIssue] = []

        # Get sample identifier
        sample_id = get_column_value(row, "sample") or get_column_value(row, "sample_id")
        lane = get_column_value(row, "lane")

        # Track sample for uniqueness check
        if sample_id:
            if sample_id not in self._sample_files:
                self._sample_files[sample_id] = {
                    "rows": [],
                    "files": {},
                }
            self._sample_files[sample_id]["rows"].append(row_number)

        # Determine file mode and validate accordingly
        fastq_1 = get_column_value(row, "fastq_1") or get_column_value(row, "fastq1")
        fastq_2 = get_column_value(row, "fastq_2") or get_column_value(row, "fastq2")
        bam = get_column_value(row, "bam")
        cram = get_column_value(row, "cram")
        vcf = get_column_value(row, "vcf")

        # File mode detection and mutual exclusivity
        modes = []
        if fastq_1 or fastq_2:
            modes.append("fastq")
        if bam:
            modes.append("bam")
        if cram:
            modes.append("cram")
        if vcf:
            modes.append("vcf")

        if len(modes) > 1:
            issues.append(
                ValidationIssue(
                    code="E030",
                    severity=Severity.ERROR,
                    row=row_number,
                    column="",
                    message=f"Multiple file modes specified: {', '.join(modes)}",
                    suggestion="Specify only one file type per sample (FASTQ, BAM, CRAM, or VCF)",
                )
            )

        # Validate FASTQ
        if fastq_1 or fastq_2:
            fq_issues = self._validate_fastq(
                fastq_1, fastq_2, sample_id, lane, row, row_number, context
            )
            issues.extend(fq_issues)

        # Validate BAM
        if bam:
            bam_issues = self._validate_bam(bam, sample_id, row, row_number, context)
            issues.extend(bam_issues)

        # Validate CRAM
        if cram:
            cram_issues = self._validate_cram(cram, sample_id, row, row_number, context)
            issues.extend(cram_issues)

        # Validate VCF
        if vcf:
            vcf_issues = self._validate_vcf(vcf, sample_id, row, row_number, context)
            issues.extend(vcf_issues)

        # Validate MD5 if present
        if self.check_md5:
            md5_issues = self._validate_md5(row, row_number, context)
            issues.extend(md5_issues)

        return issues

    def _validate_fastq(
        self,
        fastq_1: str | None,
        fastq_2: str | None,
        sample_id: str | None,
        lane: str | None,
        row: dict[str, str],
        row_number: int,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Validate FASTQ-specific constraints."""
        issues: list[ValidationIssue] = []

        # FASTQ_1 is required for FASTQ mode
        if not fastq_1:
            issues.append(
                ValidationIssue(
                    code="E031",
                    severity=Severity.ERROR,
                    row=row_number,
                    column="fastq_1",
                    message="FASTQ mode requires fastq_1",
                    suggestion="Provide a valid fastq_1 file path",
                )
            )
            return issues

        # Track pair for validation
        if sample_id:
            if sample_id not in self._fastq_pairs:
                self._fastq_pairs[sample_id] = []
            self._fastq_pairs[sample_id].append((fastq_1, fastq_2 or "", row_number))

        # R1/R2 naming check
        if fastq_2:
            # Check for consistent naming patterns
            r1_pattern = r"[._-][Rr]?1(\.\w+)?\.((fastq|fq)(\.gz)?)$"
            r2_pattern = r"[._-][Rr]?2(\.\w+)?\.((fastq|fq)(\.gz)?)$"

            if not re.search(r1_pattern, fastq_1):
                issues.append(
                    ValidationIssue(
                        code="W020",
                        severity=Severity.WARNING,
                        row=row_number,
                        column="fastq_1",
                        message=f"fastq_1 doesn't follow R1 naming convention: {fastq_1}",
                        suggestion="Use _R1. or _1. naming pattern for read 1",
                    )
                )

            if not re.search(r2_pattern, fastq_2):
                issues.append(
                    ValidationIssue(
                        code="W021",
                        severity=Severity.WARNING,
                        row=row_number,
                        column="fastq_2",
                        message=f"fastq_2 doesn't follow R2 naming convention: {fastq_2}",
                        suggestion="Use _R2. or _2. naming pattern for read 2",
                    )
                )

            # Peek at FASTQ headers if requested
            peek = context.peek_fastq if context.peek_fastq > 0 else self.peek_fastq
            if peek > 0:
                peek_issues = self._peek_fastq_pair(fastq_1, fastq_2, row_number, context, peek)
                issues.extend(peek_issues)

        return issues

    def _peek_fastq_pair(
        self,
        fastq_1: str,
        fastq_2: str,
        row_number: int,
        context: ValidationContext,
        n_reads: int,
    ) -> list[ValidationIssue]:
        """Peek at FASTQ headers to validate pairing."""
        issues: list[ValidationIssue] = []

        try:
            path1 = normalize_path(Path(fastq_1), context.base_dir)
            path2 = normalize_path(Path(fastq_2), context.base_dir)

            headers1 = read_fastq_headers(path1, n_reads)
            headers2 = read_fastq_headers(path2, n_reads)

            if not headers1:
                issues.append(
                    ValidationIssue(
                        code="E032",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="fastq_1",
                        message=f"Could not read headers from {fastq_1}",
                        suggestion="Check the file format and compression",
                    )
                )
                return issues

            if not headers2:
                issues.append(
                    ValidationIssue(
                        code="E033",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="fastq_2",
                        message=f"Could not read headers from {fastq_2}",
                        suggestion="Check the file format and compression",
                    )
                )
                return issues

            # Compare read names
            min_reads = min(len(headers1), len(headers2))
            mismatches = 0
            for i in range(min_reads):
                name1 = extract_read_name(headers1[i])
                name2 = extract_read_name(headers2[i])
                if name1 != name2:
                    mismatches += 1

            if mismatches > 0:
                issues.append(
                    ValidationIssue(
                        code="W022",
                        severity=Severity.WARNING,
                        row=row_number,
                        column="",
                        message=f"FASTQ pair has {mismatches}/{min_reads} mismatched read names",
                        suggestion="Ensure fastq_1 and fastq_2 are properly paired",
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    code="W023",
                    severity=Severity.WARNING,
                    row=row_number,
                    column="",
                    message=f"Could not validate FASTQ pairing: {e}",
                    suggestion="Check file permissions and format",
                )
            )

        return issues

    def _validate_bam(
        self,
        bam: str,
        sample_id: str | None,
        row: dict[str, str],
        row_number: int,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Validate BAM-specific constraints."""
        issues: list[ValidationIssue] = []

        bam_path = normalize_path(Path(bam), context.base_dir)

        # Check index if required
        if self.require_index or context.require_index:
            if not check_index_exists(bam_path, "bai") and not check_index_exists(bam_path, "csi"):
                issues.append(
                    ValidationIssue(
                        code="E034",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="bam",
                        message=f"BAM index not found for {bam}",
                        suggestion="Create index with 'samtools index' or disable --require-index",
                    )
                )

        # Check header if samtools available
        if has_samtools():
            try:
                header = get_bam_header(bam_path)
                read_groups = parse_bam_rg_headers(header)

                if not read_groups:
                    issues.append(
                        ValidationIssue(
                            code="E035",
                            severity=Severity.ERROR,
                            row=row_number,
                            column="bam",
                            message=f"BAM file missing @RG header: {bam}",
                            suggestion="Add read group information with 'samtools addreplacerg'",
                        )
                    )
                else:
                    # Check SM tag matches sample_id if provided
                    if sample_id:
                        sm_tags = {rg.get("SM") for rg in read_groups if rg.get("SM")}
                        if sm_tags and sample_id not in sm_tags:
                            issues.append(
                                ValidationIssue(
                                    code="W024",
                                    severity=Severity.WARNING,
                                    row=row_number,
                                    column="bam",
                                    message=f"BAM SM tag ({sm_tags}) doesn't match sample ID ({sample_id})",
                                    suggestion="Ensure @RG SM tag matches the sample sheet sample ID",
                                )
                            )

            except Exception as e:
                issues.append(
                    ValidationIssue(
                        code="E036",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="bam",
                        message=f"Could not read BAM header: {e}",
                        suggestion="Check the BAM file is valid and not corrupted",
                    )
                )

        return issues

    def _validate_cram(
        self,
        cram: str,
        sample_id: str | None,
        row: dict[str, str],
        row_number: int,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Validate CRAM-specific constraints."""
        issues: list[ValidationIssue] = []

        cram_path = normalize_path(Path(cram), context.base_dir)

        # Check index if required
        if self.require_index or context.require_index:
            if not check_index_exists(cram_path, "crai"):
                issues.append(
                    ValidationIssue(
                        code="E037",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="cram",
                        message=f"CRAM index not found for {cram}",
                        suggestion="Create index with 'samtools index' or disable --require-index",
                    )
                )

        # Similar header checks as BAM
        if has_samtools():
            try:
                header = get_bam_header(cram_path)
                read_groups = parse_bam_rg_headers(header)

                if not read_groups:
                    issues.append(
                        ValidationIssue(
                            code="E038",
                            severity=Severity.ERROR,
                            row=row_number,
                            column="cram",
                            message=f"CRAM file missing @RG header: {cram}",
                            suggestion="Add read group information",
                        )
                    )

            except Exception as e:
                issues.append(
                    ValidationIssue(
                        code="E039",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="cram",
                        message=f"Could not read CRAM header: {e}",
                        suggestion="Check the CRAM file is valid",
                    )
                )

        return issues

    def _validate_vcf(
        self,
        vcf: str,
        sample_id: str | None,
        row: dict[str, str],
        row_number: int,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Validate VCF-specific constraints."""
        issues: list[ValidationIssue] = []

        vcf_path = normalize_path(Path(vcf), context.base_dir)

        # Check index if required
        if self.require_index or context.require_index:
            if not check_index_exists(vcf_path):
                issues.append(
                    ValidationIssue(
                        code="E040",
                        severity=Severity.ERROR,
                        row=row_number,
                        column="vcf",
                        message=f"VCF index not found for {vcf}",
                        suggestion="Create index with 'bcftools index' or 'tabix'",
                    )
                )

        # Check header
        try:
            header = get_vcf_header(vcf_path)
            vcf_samples = parse_vcf_samples(header)

            if not vcf_samples:
                issues.append(
                    ValidationIssue(
                        code="W025",
                        severity=Severity.WARNING,
                        row=row_number,
                        column="vcf",
                        message=f"VCF file has no sample columns: {vcf}",
                        suggestion="Ensure the VCF contains genotype data",
                    )
                )
            elif sample_id and sample_id not in vcf_samples:
                issues.append(
                    ValidationIssue(
                        code="W026",
                        severity=Severity.WARNING,
                        row=row_number,
                        column="vcf",
                        message=f"Sample ID ({sample_id}) not found in VCF samples: {vcf_samples}",
                        suggestion="Ensure the sample ID matches a VCF sample column",
                    )
                )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    code="E041",
                    severity=Severity.ERROR,
                    row=row_number,
                    column="vcf",
                    message=f"Could not read VCF header: {e}",
                    suggestion="Check the VCF file is valid",
                )
            )

        return issues

    def _validate_md5(
        self,
        row: dict[str, str],
        row_number: int,
        context: ValidationContext,
    ) -> list[ValidationIssue]:
        """Validate MD5 checksums if provided."""
        issues: list[ValidationIssue] = []

        # Look for md5 columns
        md5_columns = [col for col in row if "md5" in col.lower()]

        for md5_col in md5_columns:
            md5_value = get_column_value(row, md5_col)
            if not md5_value:
                continue

            # Find corresponding file column
            file_col = md5_col.replace("_md5", "").replace("md5_", "")
            file_path = get_column_value(row, file_col)

            if not file_path:
                # Try common mappings
                for candidate in ["fastq_1", "fastq1", "fastq_2", "fastq2", "bam", "vcf"]:
                    if candidate in row:
                        file_path = get_column_value(row, candidate)
                        if file_path:
                            break

            if not file_path:
                continue

            # Validate MD5
            try:
                path = normalize_path(Path(file_path), context.base_dir)
                computed_md5 = compute_md5(path)

                if computed_md5.lower() != md5_value.lower():
                    issues.append(
                        ValidationIssue(
                            code="E042",
                            severity=Severity.ERROR,
                            row=row_number,
                            column=md5_col,
                            message=f"MD5 mismatch for {file_path}",
                            suggestion=f"Expected {md5_value}, computed {computed_md5}",
                        )
                    )

            except Exception as e:
                issues.append(
                    ValidationIssue(
                        code="W027",
                        severity=Severity.WARNING,
                        row=row_number,
                        column=md5_col,
                        message=f"Could not verify MD5: {e}",
                        suggestion="Check file permissions",
                    )
                )

        return issues

    def finalize(self, context: ValidationContext) -> list[ValidationIssue]:
        """Perform final domain-level checks."""
        issues: list[ValidationIssue] = []

        # Check for duplicate sample IDs with different lanes
        for sample_id, data in self._sample_files.items():
            rows = data["rows"]
            if len(rows) > 1:
                # This could be valid if different lanes
                issues.append(
                    ValidationIssue(
                        code="I010",
                        severity=Severity.INFO,
                        row=0,
                        column="sample",
                        message=f"Sample '{sample_id}' appears in {len(rows)} rows",
                        suggestion="Ensure this is intentional (e.g., multiple lanes)",
                    )
                )

        return issues


def compute_md5(file_path: Path, block_size: int = 8192) -> str:
    """Compute MD5 hash of a file.

    Args:
        file_path: Path to the file
        block_size: Size of blocks to read

    Returns:
        Hexadecimal MD5 digest
    """
    md5 = hashlib.md5()
    with open_file(file_path, "rb") as f:
        while block := f.read(block_size):
            md5.update(block)
    return md5.hexdigest()
