# SampleSheriff Example Files

This directory contains example sample sheets demonstrating various real-world bioinformatics use cases. These examples show different file formats, naming conventions, and data types.

## Quick Reference

| File | Use Case | Format | Schema to Use |
|------|----------|--------|---------------|
| `01_simple_rnaseq.tsv` | Standard RNA-seq | TSV | `builtin:fastq_only` |
| `02_single_end_atacseq.tsv` | Single-end ATAC-seq | TSV | `builtin:nfcore_like` |
| `03_tumor_normal_somatic.tsv` | Somatic variant calling | TSV | `builtin:bam_only` |
| `04_variant_calling_results.tsv` | Germline variants | TSV | `builtin:vcf_only` |
| `05_with_lanes_multiplexed.tsv` | Multiplexed sequencing | TSV | `builtin:nfcore_like` |
| `06_old_school_style.tsv` | Simple minimal format | TSV | `builtin:minimal` |
| `07_with_md5_checksums.tsv` | With checksums | TSV | `builtin:nfcore_like` |
| `08_csv_format.csv` | CSV format | CSV | `builtin:fastq_only` |

## Detailed Examples

### 1. Simple RNA-seq (`01_simple_rnaseq.tsv`)

Standard paired-end RNA-seq experiment with treatment vs control design.

```bash
# Validate with FASTQ-only schema
samplesheriff validate -i 01_simple_rnaseq.tsv -s builtin:fastq_only

# Or use the more permissive nfcore schema
samplesheriff validate -i 01_simple_rnaseq.tsv -s builtin:nfcore_like
```

**Columns:**
- `sample` - Unique sample identifier
- `fastq_1` - Forward read file (R1)
- `fastq_2` - Reverse read file (R2)
- `condition` - Experimental condition (control/treatment)
- `replicate` - Biological replicate number

### 2. Single-End ATAC-seq (`02_single_end_atacseq.tsv`)

Single-end sequencing (no fastq_2 column). Note how the `fastq_2` column is simply omitted.

```bash
samplesheriff validate -i 02_single_end_atacseq.tsv -s builtin:nfcore_like
```

**Key Point:** For single-end data, just don't include the `fastq_2` column, or leave it empty.

### 3. Tumor-Normal Pairs (`03_tumor_normal_somatic.tsv`)

Somatic variant calling workflow with matched tumor and normal samples per patient.

```bash
samplesheriff validate -i 03_tumor_normal_somatic.tsv -s builtin:bam_only
```

**Columns:**
- `sample` - Sample identifier
- `bam` - Path to BAM alignment file
- `sample_type` - tumor/normal classification
- `patient_id` - Links tumor/normal pairs
- `sequencing_platform` - Platform used (ILLUMINA, etc.)

### 4. Variant Calling Results (`04_variant_calling_results.tsv`)

VCF files from germline variant calling.

```bash
samplesheriff validate -i 04_variant_calling_results.tsv -s builtin:vcf_only
```

### 5. Multiplexed Sequencing (`05_with_lanes_multiplexed.tsv`)

Same sample sequenced across multiple lanes. The same sample ID appears multiple times with different lane numbers.

```bash
samplesheriff validate -i 05_with_lanes_multiplexed.tsv -s builtin:nfcore_like
```

**Note:** This will produce an INFO message about duplicate sample IDs, which is expected and correct for this use case.

### 6. Old School Style (`06_old_school_style.tsv`)

Simple format for traditional bioinformaticians who just want sample IDs and file paths.

```bash
# Use the minimal schema
samplesheriff validate -i 06_old_school_style.tsv -s builtin:minimal

# Or create a custom schema for this exact format
cat > dr_smith_schema.yaml << 'EOF'
name: dr_smith_lab
description: Dr. Smith's lab format since 2010
columns:
  - name: ID
    type: STRING
    required: true
  - name: FilePath
    type: PATH
    required: true
    file_check: REQUIRED
  - name: Notes
    type: STRING
    required: false
constraints:
  - type: UNIQUE
    columns: [ID]
EOF

samplesheriff validate -i 06_old_school_style.tsv -s dr_smith_schema.yaml
```

### 7. With MD5 Checksums (`07_with_md5_checksums.tsv`)

Sample sheet with MD5 checksums for file integrity verification.

```bash
samplesheriff validate -i 07_with_md5_checksums.tsv -s builtin:nfcore_like
```

**Note:** The validator will verify MD5 checksums if the files exist and the `md5_1`, `md5_2` columns are present.

### 8. CSV Format (`08_csv_format.csv`)

Comma-separated format instead of tab-separated.

```bash
# Auto-detects CSV format
samplesheriff validate -i 08_csv_format.csv -s builtin:fastq_only
```

**Key Point:** SampleSheriff auto-detects delimiters! It handles TSV, CSV, semicolon, and pipe-delimited files.

## Invalid Examples (For Testing Error Detection)

### `invalid_missing_column.tsv`
Missing required `sample` column - should fail with E010 error.

### `invalid_empty_required.tsv`
Empty values in required columns - should fail with E001 error.

### `invalid_mixed_modes.tsv`
Both FASTQ and BAM specified for same sample - should fail with E030 error (mutually exclusive).

## Testing Commands

```bash
# Test all valid examples
for file in 0*.tsv 0*.csv; do
    echo "Testing: $file"
    samplesheriff validate -i "$file" -s builtin:nfcore_like --quiet
done

# Test invalid examples (expect failures)
samplesheriff validate -i invalid_missing_column.tsv -s builtin:nfcore_like || echo "Correctly detected error"

# Generate a report
samplesheriff validate -i 01_simple_rnaseq.tsv -s builtin:fastq_only --report validation_report.json
```

## Creating Your Own

Start with a template:

```bash
# Generate a template for your project
samplesheriff init --type fastq --name my_rnaseq_study

# Edit the generated files
# - my_rnaseq_study.tsv        (your sample data)
# - my_rnaseq_study_schema.yaml (validation rules)

# Validate your data
samplesheriff validate -i my_rnaseq_study.tsv -s my_rnaseq_study_schema.yaml
```

## Tips

1. **Start Simple:** Use `builtin:minimal` for basic validation
2. **Use Comments:** Lines starting with `#` are ignored in TSV/CSV files
3. **Be Consistent:** Use the same naming convention throughout
4. **Absolute Paths:** Use absolute paths or set `--base-dir` for relative paths
5. **Test Early:** Validate your sample sheet before starting your pipeline
