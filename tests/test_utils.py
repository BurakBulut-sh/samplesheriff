"""Tests for utils module."""

from __future__ import annotations

from pathlib import Path

from samplesheriff.utils import (
    FileType,
    check_index_exists,
    deep_merge,
    detect_file_type,
    format_file_size,
    normalize_path,
    parse_bam_rg_headers,
    parse_vcf_samples,
)


class TestDetectFileType:
    """Tests for file type detection."""

    def test_detect_fastq(self):
        """Test FASTQ detection."""
        assert detect_file_type(Path("sample.fastq")) == FileType.FASTQ
        assert detect_file_type(Path("sample.fq")) == FileType.FASTQ
        assert detect_file_type(Path("sample.fastq.gz")) == FileType.FASTQ
        assert detect_file_type(Path("sample.fq.gz")) == FileType.FASTQ

    def test_detect_bam(self):
        """Test BAM detection."""
        assert detect_file_type(Path("sample.bam")) == FileType.BAM

    def test_detect_cram(self):
        """Test CRAM detection."""
        assert detect_file_type(Path("sample.cram")) == FileType.CRAM

    def test_detect_sam(self):
        """Test SAM detection."""
        assert detect_file_type(Path("sample.sam")) == FileType.SAM

    def test_detect_vcf(self):
        """Test VCF detection."""
        assert detect_file_type(Path("sample.vcf")) == FileType.VCF
        assert detect_file_type(Path("sample.vcf.gz")) == FileType.VCF

    def test_detect_bcf(self):
        """Test BCF detection."""
        assert detect_file_type(Path("sample.bcf")) == FileType.BCF

    def test_detect_unknown(self):
        """Test unknown file type."""
        assert detect_file_type(Path("sample.txt")) == FileType.UNKNOWN
        assert detect_file_type(Path("sample")) == FileType.UNKNOWN


class TestCheckIndexExists:
    """Tests for index existence checking."""

    def test_bam_bai_exists(self, temp_dir):
        """Test BAM BAI detection."""
        bam = temp_dir / "sample.bam"
        bam.write_text("fake bam")
        bai = temp_dir / "sample.bam.bai"
        bai.write_text("fake bai")

        assert check_index_exists(bam) is True

    def test_bam_csi_exists(self, temp_dir):
        """Test BAM CSI detection."""
        bam = temp_dir / "sample.bam"
        bam.write_text("fake bam")
        csi = temp_dir / "sample.bam.csi"
        csi.write_text("fake csi")

        assert check_index_exists(bam, "csi") is True

    def test_bam_no_index(self, temp_dir):
        """Test BAM without index."""
        bam = temp_dir / "sample.bam"
        bam.write_text("fake bam")

        assert check_index_exists(bam) is False

    def test_vcf_tbi_exists(self, temp_dir):
        """Test VCF TBI detection."""
        vcf = temp_dir / "sample.vcf.gz"
        vcf.write_text("fake vcf")
        tbi = temp_dir / "sample.vcf.gz.tbi"
        tbi.write_text("fake tbi")

        assert check_index_exists(vcf) is True


class TestNormalizePath:
    """Tests for path normalization."""

    def test_absolute_path(self, temp_dir):
        """Test absolute path is unchanged."""
        path = temp_dir / "file.txt"
        normalized = normalize_path(path)
        assert normalized == path.resolve()

    def test_relative_path_with_base(self, temp_dir):
        """Test relative path with base directory."""
        rel_path = Path("subdir/file.txt")
        normalized = normalize_path(rel_path, temp_dir)
        assert normalized == (temp_dir / "subdir/file.txt").resolve()

    def test_relative_path_without_base(self):
        """Test relative path without base directory."""
        rel_path = Path("file.txt")
        normalized = normalize_path(rel_path)
        assert normalized.is_absolute()


class TestFormatFileSize:
    """Tests for file size formatting."""

    def test_bytes(self):
        """Test byte formatting."""
        assert format_file_size(512) == "512.0 B"

    def test_kilobytes(self):
        """Test KB formatting."""
        assert format_file_size(1536) == "1.5 KB"

    def test_megabytes(self):
        """Test MB formatting."""
        assert format_file_size(1572864) == "1.5 MB"

    def test_gigabytes(self):
        """Test GB formatting."""
        assert format_file_size(1610612736) == "1.5 GB"


class TestParseBamRgHeaders:
    """Tests for BAM RG header parsing."""

    def test_parse_single_rg(self):
        """Test parsing single RG header."""
        header = "@RG\tID:rg1\tSM:sample1\tLB:lib1\tPL:ILLUMINA"
        rgs = parse_bam_rg_headers(header)

        assert len(rgs) == 1
        assert rgs[0]["ID"] == "rg1"
        assert rgs[0]["SM"] == "sample1"
        assert rgs[0]["LB"] == "lib1"
        assert rgs[0]["PL"] == "ILLUMINA"

    def test_parse_multiple_rg(self):
        """Test parsing multiple RG headers."""
        header = """@RG\tID:rg1\tSM:sample1
@RG\tID:rg2\tSM:sample2
@SQ\tSN:chr1\tLN:1000"""
        rgs = parse_bam_rg_headers(header)

        assert len(rgs) == 2
        assert rgs[0]["ID"] == "rg1"
        assert rgs[1]["ID"] == "rg2"

    def test_no_rg_headers(self):
        """Test parsing header without RG."""
        header = "@SQ\tSN:chr1\tLN:1000"
        rgs = parse_bam_rg_headers(header)

        assert len(rgs) == 0


class TestParseVcfSamples:
    """Tests for VCF sample parsing."""

    def test_parse_samples(self):
        """Test parsing sample names from header."""
        header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tsample1\tsample2\tsample3"
        samples = parse_vcf_samples(header)

        assert samples == ["sample1", "sample2", "sample3"]

    def test_no_samples(self):
        """Test parsing header without samples."""
        header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"
        samples = parse_vcf_samples(header)

        assert samples == []

    def test_header_not_found(self):
        """Test parsing header without #CHROM line."""
        header = "##fileformat=VCFv4.2\n#COMMENT"
        samples = parse_vcf_samples(header)

        assert samples == []


class TestDeepMerge:
    """Tests for deep dictionary merging."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dictionary merge."""
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": {"y": 3, "z": 4}}
        result = deep_merge(base, override)

        assert result == {"a": {"x": 1, "y": 3, "z": 4}}

    def test_does_not_mutate_base(self):
        """Test that base dict is not mutated."""
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        result = deep_merge(base, override)

        assert base == {"a": {"x": 1}}
        assert result == {"a": {"x": 1, "y": 2}}
