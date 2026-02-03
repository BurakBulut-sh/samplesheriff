# 🧬 SampleSheriff - Explained Like You're 5

> **TL;DR:** SampleSheriff is like a proofreader for your science homework. It checks your list of DNA samples BEFORE you start analyzing them, so you don't waste hours because of a silly typo.

---

## 🤔 What Is This Thing?

Imagine you're organizing a birthday party and you have a list:
- Alice is bringing cake
- Bob is bringing balloons  
- Charlie is bringing ice cream

But wait! You gave the list to your mom, and she notices:
- Alice's name is spelled "Aliec" 
- Bob's phone number is wrong
- Charlie is listed TWICE

**Your mom just saved the party!** 🎉

**SampleSheriff does the same thing for scientists.** Scientists work with huge lists of DNA/RNA samples. One tiny typo can ruin weeks of work. SampleSheriff catches those mistakes in seconds.

---

## 🎬 A Real Story

### The Sad Scientist (Without SampleSheriff)

> Dr. Maria starts an experiment. She has 100 patient samples. She types up a list and starts her computer analysis. It runs for **3 days**. Then it crashes: *"Error: Cannot find file patient_57_R1.fastq.gz"*
> 
> She checks... yep, typo in the list. Should be "patient_57" not "patinet_57". 
> 
> **3 days wasted.** 😭

### The Happy Scientist (With SampleSheriff)

> Dr. Maria starts an experiment. She types up her list. **Before** running anything, she types:
> ```bash
> samplesheriff validate -i my_samples.tsv -s builtin:fastq_only
> ```
> 
> SampleSheriff says: *"Error: 'patinet_57' not found. Did you mean 'patient_57'?"*
> 
> She fixes the typo in 10 seconds. Runs her analysis. It works perfectly.
> 
> **3 days saved!** 😊

---

## 🎒 What You Need (The "Ingredients")

### 1. Your Data Files 📁

These are the actual results from your experiment. Like photos from a trip, but for DNA.

| File Type | What It Looks Like | What's Inside |
|-----------|-------------------|---------------|
| **FASTQ** | `sample_R1.fastq.gz` | DNA letters (A, T, C, G) |
| **BAM** | `patient_tumor.bam` | Aligned DNA sequences |
| **VCF** | `variants.vcf.gz` | Genetic mutations found |

Think of these like:
- FASTQ = Raw photos from your camera
- BAM = Photos organized into albums  
- VCF = List of "interesting things" you found in the photos

### 2. Your Sample Sheet 📝

This is just a **spreadsheet** (like Excel) that lists:
- Who/what you studied (sample name)
- Where the data files are (file paths)
- Extra info (tumor vs normal, treatment vs control, etc.)

**Example:**
```
sample_name    file_1                    file_2                    type
patient_1      data/p1_DNA_R1.fastq      data/p1_DNA_R2.fastq      tumor
patient_2      data/p2_DNA_R1.fastq      data/p2_DNA_R2.fastq      normal
```

It's like a **mailing list** - name + address + maybe a note.

### 3. A Schema (The Rule Book) 📖

This tells SampleSheriff: *"Here's what a correct spreadsheet should look like."*

It's like a teacher's rubric:
- ✓ Must have: Name, Date, Assignment
- ✗ Optional: Drawing, Stickers
- ✗ Not allowed: Gum on the paper

**We give you pre-made rule books:**
- `builtin:fastq_only` - For DNA/RNA sequencing
- `builtin:bam_only` - For aligned data
- `builtin:vcf_only` - For genetic variants
- `builtin:minimal` - Super simple, just checking files exist

---

## 🎯 How to Use It (Step by Step)

### Step 1: Make Your List

Create a spreadsheet with your samples. You can use:
- **Excel** (save as .tsv or .csv)
- **Google Sheets** (download as .tsv)
- **Notepad/TextEdit** (type with TABS between columns)

**Minimum you need:**
```
sample    file
mouse_1   data/mouse1.fastq
mouse_2   data/mouse2.fastq
```

### Step 2: Install SampleSheriff

```bash
# Copy-paste this into your terminal
cd /Users/burakbulut/projects/samplesheriff
source venv/bin/activate
```

### Step 3: Check Your Work

```bash
# The magic command:
samplesheriff validate -i your_file.tsv -s builtin:minimal
```

**What happens:**
- ✅ **PASSED** = Everything looks good! Start your real work!
- ❌ **FAILED** = Fix the errors listed, then try again

---

## 🔍 What It Checks

### The "Mailman Check" 📬
- Does this address exist?
- Can the mailman reach it?
- Is the house actually there?

**Translation:**
- Does the file exist?
- Can we read it?
- Is it actually a file (not a folder)?

### The "Attendance Check" ✏️
- Is everyone on the list?
- Did anyone get counted twice?
- Is anyone missing?

**Translation:**
- Are all sample names filled in?
- Any duplicates?
- Any empty cells that should have data?

### The "File Type Check" 🏷️
- Is this actually a photo file?
- Or did someone rename a Word document to ".jpg"?

**Translation:**
- Does the file extension match what we expect?
- Is a FASTQ file actually gzipped if it says ".gz"?

---

## 🚦 Understanding the Results

### Green Light (PASSED) ✅
```
╭──────────── ✓ PASSED ────────────╮
│ Total Issues │ 0                 │
│ Errors       │ 0                 │
│ Warnings     │ 0                 │
```

**Means:** Perfect! Your list is good to go!

### Yellow Light (Warnings) ⚠️
```
╭──────────── ✓ PASSED ────────────╮
│ Total Issues │ 2                 │
│ Errors       │ 0                 │
│ Warnings     │ 2                 │
```

**Means:** Probably fine, but double-check. Use `--strict` if you want to be extra careful.

### Red Light (FAILED) ❌
```
╭──────────── ✗ FAILED ────────────╮
│ Total Issues │ 3                 │
│ Errors       │ 3                 │
│ Warnings     │ 0                 │

Error: File not found: /data/missing.fastq
Error: Duplicate sample name: "patient_1"
Error: Empty value in column "condition"
```

**Means:** Stop! Fix these problems first!

---

## 🎓 Real Examples

### Example 1: The RNA Scientist

**Sarah is studying cancer.** She has tumor samples and normal samples.

**Her list:**
```
sample          fastq_1              fastq_2              type
tumor_01        t01_R1.fastq.gz     t01_R2.fastq.gz     tumor
normal_01       n01_R1.fastq.gz     n01_R2.fastq.gz     normal
tumor_02        t02_R1.fastq.gz     t02_R2.fastq.gz     tumor
```

**She runs:**
```bash
samplesheriff validate -i sarah_list.tsv -s builtin:fastq_only
```

**Result:** ✅ PASSED!

**She starts her analysis with confidence.**

---

### Example 2: The Typo Detective

**Mike made a mistake.** He typed:
```
sample          fastq_1              fastq_2
cancer_01       c01_R1.fastq.gz     c01_R2.fastq.gz
cancer_01       c02_R1.fastq.gz     c02_R2.fastq.gz  ← DUPLICATE!
cancer_03       /wrong/path/file    c03_R2.fastq.gz  ← WRONG PATH!
```

**He runs:**
```bash
samplesheriff validate -i mike_list.tsv -s builtin:fastq_only
```

**Result:** ❌ FAILED!
```
Error: Duplicate value 'cancer_01' in column 'sample'
Error: File not found: /wrong/path/file
```

**Mike fixes the typos, runs again:** ✅ PASSED!

**His 2-day analysis completes successfully.**

---

## 🛠️ Common Commands (Copy-Paste These!)

### Check if it works:
```bash
samplesheriff --version
```

### See what rule books (schemas) are available:
```bash
samplesheriff schema list
```

### Check your list:
```bash
samplesheriff validate -i my_samples.tsv -s builtin:fastq_only
```

### Make a template to fill in:
```bash
samplesheriff init --type fastq --name my_study
```
(This creates `my_study.tsv` - edit it with your data!)

### Save a report to show your boss:
```bash
samplesheriff validate -i my_samples.tsv -s builtin:fastq_only --report proof.json
```

---

## 🎮 Try the Demo Data

We made practice files so you can test without risking your real work!

```bash
# Good data (should pass):
samplesheriff validate -i demo_data/rnaseq_samplesheet.tsv -s builtin:fastq_only

# Bad data (should fail):
samplesheriff validate -i demo_data/broken_samplesheet.tsv -s builtin:fastq_only
```

---

## 🤷 FAQ (Frequently Asked Questions)

### Q: Do I need to be a programmer?
**A:** Nope! If you can use Excel and copy-paste commands, you're good!

### Q: What if I use CSV instead of TSV?
**A:** No problem! SampleSheriff auto-detects the format.

### Q: Can I have extra columns?
**A:** Usually yes! Most schemas allow extra info (like "notes", "date", etc.)

### Q: What if my file paths are really long?
**A:** You can use `--base-dir` to set a starting folder, then use shorter paths.

### Q: Does it change my files?
**A:** NO! It only READS. Your data is 100% safe.

### Q: Can I use this for non-biology stuff?
**A:** Absolutely! It's just checking lists against files. Works for photos, documents, anything!

---

## 💡 Pro Tips

1. **Always validate before starting long analyses** - It takes 5 seconds and saves hours
2. **Use relative paths** - Makes your list portable to other computers
3. **Keep backups** - Save your original list before making changes
4. **Use comments** - Start lines with `#` to add notes that get ignored
5. **Check the suggestions** - SampleSheriff often tells you exactly how to fix errors

---

## 📝 The Glossary (Simple Definitions)

| Word | Simple Meaning |
|------|----------------|
| **Sample** | One thing you studied (one patient, one mouse, one test tube) |
| **FASTQ** | File with DNA letters (A, T, C, G) |
| **BAM** | File with DNA aligned to a reference genome |
| **VCF** | File listing genetic differences/mutations |
| **Schema** | Rule book saying what your list should look like |
| **Validate** | Check for mistakes |
| **TSV** | "Tab-separated values" - spreadsheet format with tabs |
| **CSV** | "Comma-separated values" - spreadsheet format with commas |

---

## 🚀 Ready to Start?

1. Find your list of samples (or make one)
2. Open a terminal
3. Type:
   ```bash
   cd /Users/burakbulut/projects/samplesheriff
   source venv/bin/activate
   samplesheriff validate -i YOUR_FILE.tsv -s builtin:minimal
   ```
4. Fix any errors
5. Start your real work with confidence!

---

## 🆘 Need Help?

**Error messages confusing?** 
- Look for the "Suggestion:" line - it tells you how to fix it!

**Not sure which schema to use?**
- Start with `builtin:minimal` - it's very forgiving

**Files not found?**
- Check your paths
- Use absolute paths (starting with /) or set `--base-dir`

---

**Remember:** SampleSheriff is like spell-check for your sample list. It's not scary - it's helpful! 😊

---

*Made with ❤️ for scientists who just want their analyses to work the first time.*
