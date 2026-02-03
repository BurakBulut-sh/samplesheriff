# SampleSheriff Demo Data

This directory contains realistic demo data for testing SampleSheriff.

## Directory Structure

```
demo_data/
├── rnaseq/                    # RNA-seq FASTQ files
│   ├── control_1_R1.fastq
│   ├── control_1_R2.fastq
│   ├── control_2_R1.fastq
│   ├── control_2_R2.fastq
│   ├── treatment_1_R1.fastq
│   ├── treatment_1_R2.fastq
│   ├── treatment_2_R1.fastq
│   └── treatment_2_R2.fastq
├── somatic/                   # BAM files for somatic calling
│   ├── patient_01_tumor.bam
│   ├── patient_01_normal.bam
│   ├── patient_02_tumor.bam
│   └── patient_02_normal.bam
├── variants/                  # VCF files
│   ├── sample_A.vcf
│   ├── sample_B.vcf
│   └── sample_C.vcf
├── rnaseq_samplesheet.tsv     # Sample sheets
├── somatic_samplesheet.tsv
└── variants_samplesheet.tsv
```

## Quick Test Commands

### Test 1: RNA-seq Validation (Should PASS ✅)

```bash
cd /Users/burakbulut/projects/samplesheriff
source venv/bin/activate

samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only
```

Expected: **PASSED** with 0 errors

### Test 2: Somatic Validation (Should PASS ✅)

```bash
samplesheriff validate -i demo_data/somatic_samplesheet.tsv -s builtin:bam_only
```

Expected: **PASSED** with 0 errors

### Test 3: Variants Validation (Should PASS ✅)

```bash
samplesheriff validate -i demo_data/variants_samplesheet.tsv -s builtin:vcf_only
```

Expected: **PASSED** with 0 errors

### Test 4: Generate JSON Report

```bash
samplesheriff validate \
  -i demo_data/rnaseq_samplesheet.tsv \
  -s builtin:fastq_only \
  --report demo_report.json

cat demo_report.json | jq .
```

### Test 5: Test with Strict Mode

```bash
samplesheriff validate \
  -i demo_data/rnaseq_samplesheet.tsv \
  -s builtin:fastq_only \
  --strict
```

## Expected Results

All three sample sheets should validate successfully with:
- **0 errors**
- **0 warnings**
- **PASSED** status

## What the Files Contain

### FASTQ Files (rnaseq/)
Realistic FASTQ format with:
- `@SEQ_ID` read headers
- DNA sequences (40bp each)
- `+` separator
- Quality scores (Phred scale 'I')
- 2-3 reads per file for quick testing

### BAM Files (somatic/)
Mock BAM files with placeholder content.
In real use, these would be binary alignment files from tools like BWA or STAR.

### VCF Files (variants/)
Proper VCF v4.2 format with:
- Header lines (`##fileformat`, `##source`, etc.)
- Column header (`#CHROM`, `POS`, `ID`, etc.)
- Actual variant calls
- Sample genotypes (`GT` field)

## Make a Deliberate Error

Want to see error detection? Create a bad sample sheet:

```bash
# Create a sample sheet with duplicate sample
cat > /tmp/bad_samplesheet.tsv << 'EOF'
sample	fastq_1	fastq_2
control_1	demo_data/rnaseq/control_1_R1.fastq	demo_data/rnaseq/control_1_R2.fastq
control_1	demo_data/rnaseq/control_2_R1.fastq	demo_data/rnaseq/control_2_R2.fastq
EOF

# Validate (should FAIL with duplicate error)
samplesheriff validate -i /tmp/bad_samplesheet.tsv -s builtin:fastq_only
```

Expected: **FAILED** with E012 duplicate sample error

## All Tests at Once

Run this to test everything:

```bash
cd /Users/burakbulut/projects/samplesheriff
source venv/bin/activate

echo "=== Test 1: RNA-seq ==="
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only --quiet && echo "✅ PASS" || echo "❌ FAIL"

echo "=== Test 2: Somatic ==="
samplesheriff validate -i demo_data/somatic_samplesheet.tsv -s builtin:bam_only --quiet && echo "✅ PASS" || echo "❌ FAIL"

echo "=== Test 3: Variants ==="
samplesheriff validate -i demo_data/variants_samplesheet.tsv -s builtin:vcf_only --quiet && echo "✅ PASS" || echo "❌ FAIL"

echo "=== All tests complete ==="
```

## Tips

1. **Relative paths**: The sample sheets use relative paths (`demo_data/...`) so they work from the project root
2. **Base directory**: You can use `--base-dir` if running from elsewhere:
   ```bash
   samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only --base-dir /Users/burakbulut/projects/samplesheriff
   ```
3. **Custom schema**: Create your own schema for specific validation rules

## Next Steps

1. Try editing a sample sheet to introduce errors
2. See how the validator responds
3. Create your own sample sheet based on these templates
