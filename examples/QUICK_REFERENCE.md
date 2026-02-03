# SampleSheriff Quick Reference Card

## Installation (in new terminal)

```bash
cd /Users/burakbulut/projects/samplesheriff
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Basic Commands

```bash
# Show version
samplesheriff --version

# List available schemas
samplesheriff schema list

# Show schema details
samplesheriff schema show nfcore_like

# Generate a template
samplesheriff init --type fastq --name my_study

# Validate a sample sheet
samplesheriff validate -i samples.tsv -s builtin:fastq_only
```

## File Formats

### Format 1: Standard RNA-seq (TSV)
```
sample  fastq_1  fastq_2  condition
ctrl_1  ctrl_1_R1.fastq.gz  ctrl_1_R2.fastq.gz  control
ctrl_2  ctrl_2_R1.fastq.gz  ctrl_2_R2.fastq.gz  control
```

### Format 2: Single-End (no fastq_2)
```
sample  fastq_1  condition
S1  S1.fastq.gz  treatment
S2  S2.fastq.gz  control
```

### Format 3: Old School Minimal
```
ID  FilePath  Notes
T1  tumor.bam  Primary
N1  normal.bam  Blood
```

### Format 4: CSV (auto-detected)
```csv
sample,fastq_1,fastq_2
S1,file_R1.fastq.gz,file_R2.fastq.gz
```

## Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `-i, --input` | Sample sheet file | `-i samples.tsv` |
| `-s, --schema` | Schema to use | `-s builtin:fastq_only` |
| `-b, --base-dir` | Base directory for paths | `-b /data/project` |
| `--strict` | Treat warnings as errors | `--strict` |
| `--report` | Save JSON report | `--report out.json` |
| `-f, --format` | Output format (text/json) | `-f json` |
| `--fail-on` | Fail on warnings | `--fail-on warnings` |
| `--require-index` | Require BAM/VCF index | `--require-index` |

## Built-in Schemas

| Schema | Use For |
|--------|---------|
| `builtin:nfcore_like` | General purpose (FASTQ/BAM/VCF) |
| `builtin:fastq_only` | RNA-seq, ChIP-seq, ATAC-seq |
| `builtin:bam_only` | Alignment files |
| `builtin:vcf_only` | Variant calling |
| `builtin:minimal` | Simple validation |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation errors |
| 2 | Runtime/IO errors |

## Error Codes

| Code | Issue | Fix |
|------|-------|-----|
| E001 | Empty required value | Fill in the missing value |
| E010 | Missing column | Add the required column |
| E012 | Duplicate sample ID | Make sample IDs unique |
| E020 | File not found | Check file path exists |
| E030 | Multiple file types | Use only FASTQ OR BAM OR VCF |
| W010 | Not gzip compressed | Compress with gzip or rename |
| W011 | Wrong file extension | Use correct extension |

## Tips

1. **Start simple**: Use `builtin:minimal` first
2. **Comments OK**: Lines starting with `#` are ignored
3. **Auto-detection**: Delimiter (tab/comma) is auto-detected
4. **Case insensitive**: Column names are case-insensitive
5. **Absolute paths**: Use `--base-dir` for relative paths

## Example Workflows

### RNA-seq Analysis
```bash
# 1. Create template
samplesheriff init --type fastq --name rnaseq

# 2. Edit rnaseq.tsv with your samples

# 3. Validate
samplesheriff validate -i rnaseq.tsv -s builtin:fastq_only

# 4. Run your pipeline
nextflow run nf-core/rnaseq --input rnaseq.tsv
```

### Somatic Variant Calling
```bash
# Validate tumor/normal pairs
samplesheriff validate -i tumor_normal.tsv -s builtin:bam_only --require-index
```

### Custom Schema
```bash
# Create custom schema
cat > my_schema.yaml << 'EOF'
name: my_lab
columns:
  - name: sample_id
    type: STRING
    required: true
  - name: bam_file
    type: PATH
    required: true
    file_check: REQUIRED
constraints:
  - type: UNIQUE
    columns: [sample_id]
EOF

# Use it
samplesheriff validate -i data.tsv -s my_schema.yaml
```

## Getting Help

```bash
samplesheriff --help
samplesheriff validate --help
samplesheriff schema --help
```

---
*Print this page and keep it handy!*
