# 🚀 SampleSheriff Demo - Quick Start

## Test the Demo Data in 30 Seconds

```bash
cd /Users/burakbulut/projects/samplesheriff
source venv/bin/activate

# Test 1: VALID data (should PASS ✅)
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only

# Test 2: BROKEN data (should FAIL ❌)
samplesheriff validate -i demo_data/broken_samplesheet.tsv -s builtin:fastq_only
```

## What You'll See

### ✅ Successful Validation
```
╭──────────── ✓ PASSED ────────────╮
│ Total Issues │ 1                 │
│ Errors       │ 0                 │  ← No errors!
│ Warnings     │ 1                 │
```

### ❌ Failed Validation
```
╭──────────── ✗ FAILED ────────────╮
│ Total Issues │ 6                 │
│ Errors       │ 4                 │  ← Has errors!
│ Warnings     │ 1                 │
```

## All Demo Files

| File | Type | Expected Result |
|------|------|-----------------|
| `rnaseq_samplesheet.tsv` | RNA-seq | ✅ PASS |
| `somatic_samplesheet.tsv` | BAM | ✅ PASS |
| `variants_samplesheet.tsv` | VCF | ✅ PASS |
| `broken_samplesheet.tsv` | Bad data | ❌ FAIL |

## What's in the Demo?

```
demo_data/
├── rnaseq/              ← 8 FASTQ files (real format)
├── somatic/             ← 4 BAM files
├── variants/            ← 3 VCF files (real VCF format)
└── *_samplesheet.tsv    ← Sample sheets
```

## Common Commands

```bash
# List available schemas
samplesheriff schema list

# Validate with different schemas
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:nfcore_like
samplesheriff validate -i demo_data/somatic_samplesheet.tsv -s builtin:bam_only
samplesheriff validate -i demo_data/variants_samplesheet.tsv -s builtin:vcf_only

# Generate JSON report
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only --report report.json

# Test strict mode (warnings become errors)
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only --strict
```

## Try These Experiments

### 1. Introduce a Duplicate Sample
```bash
# Edit rnaseq_samplesheet.tsv and change "control_2" to "control_1"
# Then validate - should fail with E012 (duplicate)
```

### 2. Change a File Path
```bash
# Edit rnaseq_samplesheet.tsv and change a path to /nonexistent/file.fastq
# Then validate - should fail with E020 (file not found)
```

### 3. Remove a Required Column
```bash
# Edit rnaseq_samplesheet.tsv and remove the "fastq_2" column
# Then validate - should fail with E010 (missing column)
```

## Understanding the Output

### Error Codes
- **E001** - Empty value in required column
- **E007** - File not found
- **E010** - Missing required column
- **E012** - Duplicate value (e.g., sample ID)
- **E020** - File not readable

### Severity Levels
- **Error** - Must fix for pipeline to work
- **Warning** - Should review but may work
- **Info** - Just FYI

## Next Steps

1. ✅ Try the demo commands above
2. 📝 Edit the broken_samplesheet.tsv to fix the errors
3. 🔧 Create your own sample sheet based on the examples
4. 📖 Read the full README: `cat demo_data/README.md`

---
**Ready to validate your own data?** Use `samplesheriff init --type fastq` to create a template!
