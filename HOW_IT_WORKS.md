# 🎯 How SampleSheriff Works (Visual Guide)

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                    BEFORE SampleSheriff                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  You → Start Analysis → Wait 3 days → CRASH! 💥                  │
│                         ↑                                        │
│                         └ "Error: File not found"                │
│                                                                  │
│  Result: 3 days wasted 😭                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    WITH SampleSheriff                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  You → Validate First → ✅ PASSED → Start Analysis              │
│            ↑                      ↓                              │
│            │                      └ Runs perfectly!              │
│            │                                                     │
│            └ ❌ FAILED (fix typo) → Re-validate → ✅ PASSED      │
│                                                                  │
│  Result: Fixed in 10 seconds! 😊                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Validation Process Step-by-Step

### Step 1: You Create a Sample Sheet

**This is just a spreadsheet with your experiment info:**

```
┌─────────────┬───────────────────────────┬───────────────────────────┬───────────┐
│ sample      │ fastq_1                   │ fastq_2                   │ condition │
├─────────────┼───────────────────────────┼───────────────────────────┼───────────┤
│ patient_1   │ data/p1_R1.fastq.gz       │ data/p1_R2.fastq.gz       │ tumor     │
│ patient_2   │ data/p2_R1.fastq.gz       │ data/p2_R2.fastq.gz       │ normal    │
│ patient_3   │ data/p3_R1.fastq.gz       │ data/p3_R2.fastq.gz       │ tumor     │
└─────────────┴───────────────────────────┴───────────────────────────┴───────────┘
```

Think of it like a **mailing list** for your data files.

---

### Step 2: SampleSheriff Reads Your List

```
┌────────────────────────────────────┐
│  SampleSheriff Opens Your File     │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│  1. Detects format (TSV or CSV)    │
│  2. Finds column headers           │
│  3. Counts total samples           │
└────────────────────────────────────┘
```

---

### Step 3: SampleSheriff Checks Each Row

For EVERY sample in your list, it checks:

```
Sample: patient_1
├─ ✓ Name is not empty
├─ ✓ File exists: data/p1_R1.fastq.gz
├─ ✓ File is readable
├─ ✓ File is not empty
├─ ✓ File extension looks correct (.fastq.gz)
└─ ✓ Not a duplicate name

Sample: patient_2
├─ ✓ Name is not empty
├─ ✓ File exists: data/p2_R1.fastq.gz
├─ ... (etc)
```

---

### Step 4: SampleSheriff Checks Across All Rows

```
┌─────────────────────────────────────────┐
│  Cross-Row Validation                   │
├─────────────────────────────────────────┤
│                                         │
│  ✓ No duplicate sample names?          │
│  ✓ All required columns present?       │
│  ✓ Data types look correct?            │
│  ✓ No conflicting information?         │
│                                         │
└─────────────────────────────────────────┘
```

---

### Step 5: The Report Card

```
┌─────────────────────────────────────────┐
│         VALIDATION COMPLETE             │
├─────────────────────────────────────────┤
│                                         │
│   ╔═══════════════════════════════════╗ │
│   ║    ✓ PASSED (No Errors Found)     ║ │
│   ╚═══════════════════════════════════╝ │
│                                         │
│   Total Samples: 3                      │
│   Total Issues: 0                       │
│   Errors: 0                             │
│   Warnings: 0                           │
│                                         │
│   Status: READY TO RUN! 🚀              │
│                                         │
└─────────────────────────────────────────┘
```

**OR if there are problems:**

```
┌─────────────────────────────────────────┐
│         VALIDATION COMPLETE             │
├─────────────────────────────────────────┤
│                                         │
│   ╔═══════════════════════════════════╗ │
│   ║    ✗ FAILED (Errors Found)        ║ │
│   ╚═══════════════════════════════════╝ │
│                                         │
│   Issues Found:                         │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│   ❌ Row 2: File not found              │
│      → data/p2_R1.fastq.gz              │
│      → Check the file path              │
│                                         │
│   ❌ Row 3: Duplicate sample name       │
│      → "patient_1" appears twice        │
│      → Make names unique                │
│                                         │
│   Status: FIX ERRORS FIRST! ⚠️          │
│                                         │
└─────────────────────────────────────────┘
```

---

## What SampleSheriff Actually Checks

### 1. File Existence (The "Is It There?" Check)

```
You wrote:    /data/sample_1.fastq.gz
Does it exist? ✓ YES → Continue
                ✗ NO  → ERROR!
```

**Real example:**
```
Your list says:  /data/patient_57.fastq.gz
Reality:         File doesn't exist!
SampleSheriff:   "Error: File not found"
You:             "Oops, typo! Should be patient_57"
```

---

### 2. File Readability (The "Can I Open It?" Check)

```
File exists?    ✓ Yes
Can we read it? ✓ Yes → Continue
                ✗ No  → ERROR (permissions?)
```

---

### 3. Empty File Check (The "Is It Real?" Check)

```
File exists?    ✓ Yes
Can read it?    ✓ Yes
Is it empty?    ✓ No  → Continue (good!)
                ✗ Yes → WARNING (0 bytes?)
```

---

### 4. File Type Check (The "Is It What It Says?" Check)

```
File name ends with:  .fastq.gz
Is it actually:       gzip compressed?
                      ✓ Yes → Continue
                      ✗ No  → WARNING
```

**Real example:**
```
You have:        data.txt
You renamed:     data.fastq.gz
Reality:         It's not actually gzipped!
SampleSheriff:   "Warning: File has .gz extension but is not gzip compressed"
```

---

### 5. Duplicate Detection (The "No Twins Allowed" Check)

```
Sample names found:
  - patient_1 ✓ (first occurrence)
  - patient_2 ✓ 
  - patient_1 ✗ DUPLICATE!
```

**Real example:**
```
Your list:
  patient_1, data/p1.fastq
  patient_2, data/p2.fastq
  patient_1, data/p3.fastq  ← WAIT, patient_1 again?!?

SampleSheriff: "Error: Duplicate value 'patient_1' in column 'sample'"
You: "Oops, that third one should be patient_3!"
```

---

## The Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        INPUT                                 │
│  Your Sample Sheet (TSV/CSV file)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   SAMPLE SHERIFF                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Read File    │→ │ Validate     │→ │ Generate     │      │
│  │              │  │ Each Row     │  │ Report       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                │                │
│         ▼                ▼                ▼                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Checks: Headers, Files, Types, Duplicates, etc.     │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│   ✓ PASSED      │      │   ✗ FAILED      │
│                 │      │                 │
│ 0 errors found  │      │ N errors found  │
│ Safe to proceed │      │ Fix and retry   │
└─────────────────┘      └─────────────────┘
```

---

## What You Need vs What SampleSheriff Does

| You Provide | SampleSheriff Does |
|-------------|-------------------|
| Sample sheet (spreadsheet) | Reads and parses it |
| Data files (FASTQ/BAM/VCF) | Verifies they exist |
| Schema choice (rule book) | Applies validation rules |
| | Checks for errors |
| | Reports what needs fixing |
| | Gives suggestions |

**You don't need to:**
- ❌ Write any code
- ❌ Understand the internals
- ❌ Manually check each file
- ❌ Remember complex rules

**You just:**
- ✅ Write your list
- ✅ Run one command
- ✅ Fix any errors reported
- ✅ Start your analysis!

---

## Common Error Messages Explained

### "File not found"
```
What it means:    The path you wrote doesn't point to a real file
How to fix:       Check for typos in the filename or path
Example:          
  Wrong:  /data/samle_1.fastq  (typo: "samle")
  Right:  /data/sample_1.fastq
```

### "Required column 'sample' not found"
```
What it means:    Your spreadsheet is missing a required column
How to fix:       Add the missing column header
Example:
  Wrong:  name, file_1, file_2    (used "name" instead of "sample")
  Right:  sample, file_1, file_2
```

### "Duplicate value 'patient_1' in column 'sample'"
```
What it means:    The same sample name appears twice
How to fix:       Make each sample name unique
Example:
  Wrong:  patient_1, patient_2, patient_1
  Right:  patient_1, patient_2, patient_3
```

### "File is empty"
```
What it means:    The file exists but has 0 bytes
How to fix:       Check if the file downloaded/copied correctly
```

---

## Summary

**SampleSheriff is like a smart assistant that:**

1. 📋 Reads your sample list
2. 🔍 Checks every entry
3. 📁 Verifies all files exist
4. ⚠️ Catches mistakes early
5. 💡 Tells you how to fix them

**You get:**
- ✅ Confidence your data is correct
- ✅ Time saved (catch errors in seconds, not days)
- ✅ Peace of mind before long analyses

**All you do:**
```bash
samplesheriff validate -i your_samples.tsv -s builtin:minimal
```

That's it! 🎉
