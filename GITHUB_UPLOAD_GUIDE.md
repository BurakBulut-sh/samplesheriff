# 📤 How to Upload SampleSheriff to Your GitHub

## Method 1: Using the Web Browser (Easiest)

### Step 1: Create a GitHub Account
1. Go to https://github.com
2. Click "Sign up" 
3. Follow the instructions

### Step 2: Create a New Repository
1. Click the **+** button (top right) → "New repository"
2. Name it: `samplesheriff`
3. Description: `A fast, strict sample sheet validator for bioinformatics`
4. Make it **Public** (or Private if you prefer)
5. **DO NOT** check "Initialize with README" (we already have one)
6. Click **"Create repository"**

### Step 3: Upload Your Files

You'll see instructions on the page. Here's what to do:

**Option A: Using Git (Recommended)**

Open your terminal and run these commands one by one:

```bash
# 1. Go to your project folder
cd /Users/burakbulut/projects/samplesheriff

# 2. Initialize git
git init

# 3. Add all your files
git add .

# 4. Commit (save) your files
git commit -m "Initial commit: SampleSheriff v0.1.0"

# 5. Connect to GitHub (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/samplesheriff.git

# 6. Upload!
git branch -M main
git push -u origin main
```

You'll be asked for your GitHub username and password (or a token).

---

**Option B: Drag & Drop (Super Easy, No Commands!)**

1. On the GitHub page, look for **"uploading an existing file"** link
2. Click it
3. Drag and drop your files from Finder into the browser
4. Add a message: "Initial commit"
5. Click **"Commit changes"**

⚠️ **Note:** This is slower for many files, but very easy!

---

## Method 2: Using GitHub Desktop (User-Friendly)

### Step 1: Download GitHub Desktop
1. Go to https://desktop.github.com
2. Download and install
3. Sign in with your GitHub account

### Step 2: Add Your Repository
1. Open GitHub Desktop
2. Click **File** → **Add Local Repository**
3. Browse to: `/Users/burakbulut/projects/samplesheriff`
4. Click **"Add Repository"**

### Step 3: Publish to GitHub
1. You'll see a "Publish repository" button
2. Click it
3. Name: `samplesheriff`
4. Description: `Sample sheet validator for bioinformatics`
5. Click **"Publish Repository"**

✅ Done! Your code is now on GitHub!

---

## Method 3: Using VS Code (If You Have It)

1. Open VS Code
2. File → Open Folder → Select `samplesheriff`
3. Click the Source Control icon (branch icon on left)
4. Click "Initialize Repository"
5. Stage all changes (+ icon)
6. Type message: "Initial commit"
7. Click checkmark to commit
8. Click "..." → "Remote" → "Add Remote"
9. Enter your GitHub repo URL
10. Click "Publish Branch"

---

## 🎉 After Uploading

### What You'll Have

Your GitHub repo will be at:
```
https://github.com/YOUR_USERNAME/samplesheriff
```

### What to Check

1. ✅ All files uploaded?
2. ✅ README.md displays nicely?
3. ✅ Code is visible?

### Cool Features You'll Get

- **View your code online** from any browser
- **Share the link** with others
- **Download as ZIP** for others to use
- **Track changes** if you update the code
- **Free hosting** of your project

---

## 🔧 If You Get Stuck

### "Permission denied" error?
You need to set up authentication:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a token with "repo" permissions
3. Use that token instead of your password

### "Repository not found" error?
Make sure you created the repository on GitHub first!

### "Not a git repository" error?
Make sure you ran `git init` first!

### Too many files to drag?
Use the git command line method instead.

---

## 📝 One-Time Setup (If Using Terminal)

If this is your first time using git, run these once:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 🎯 Quick Checklist

- [ ] Created GitHub account
- [ ] Created new repository named "samplesheriff"
- [ ] Opened terminal
- [ ] Navigated to `/Users/burakbulut/projects/samplesheriff`
- [ ] Ran `git init`
- [ ] Ran `git add .`
- [ ] Ran `git commit -m "Initial commit"`
- [ ] Ran `git remote add origin YOUR_URL`
- [ ] Ran `git push -u origin main`
- [ ] Checked that files appear on GitHub website

---

## 🆘 Still Need Help?

**GitHub's own guide:** https://docs.github.com/en/get-started/quickstart/hello-world

**Common issues:** https://docs.github.com/en/get-started/quickstart/troubleshooting-connectivity-problems

**Video tutorial:** Search YouTube for "how to upload project to github"

---

## 💡 Pro Tips

1. **Your first push might ask for login** - This is normal!
2. **If you change files later**, just run:
   ```bash
   git add .
   git commit -m "Description of changes"
   git push
   ```
3. **Don't commit the venv folder** - It's in .gitignore already!
4. **Keep your README updated** - It's the first thing people see

---

**You've got this!** 🚀
