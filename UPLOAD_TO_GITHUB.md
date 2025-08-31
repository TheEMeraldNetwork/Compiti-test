# 📤 How to Upload Files to GitHub Pages

**You need to manually upload these files to your GitHub repository to create the web interface.**

## 🎯 Files to Upload

From the `github_pages/` folder, upload these files to your **TheEMeraldNetwork/Compiti-test** repository:

### 1. **index.html** 
- Upload to: **ROOT** of your repository
- This creates the GitHub Pages website

### 2. **README.md**
- Upload to: **ROOT** of your repository  
- This replaces the default README

## 📋 Step-by-Step Upload Process

### Step 1: Go to Your Repository
Visit: [https://github.com/TheEMeraldNetwork/Compiti-test](https://github.com/TheEMeraldNetwork/Compiti-test)

### Step 2: Upload index.html
1. Click **"Add file"** → **"Upload files"**
2. Drag and drop `github_pages/index.html`
3. Commit message: `Add GitHub Pages interface for math solver`
4. Click **"Commit changes"**

### Step 3: Upload README.md
1. If README.md already exists, click on it and then **"Edit this file"**
2. Replace content with the content from `github_pages/README.md`
3. Or upload as new file if it doesn't exist
4. Commit message: `Update README with math solver instructions`
5. Click **"Commit changes"**

### Step 4: Enable GitHub Pages
1. Go to **Settings** tab in your repository
2. Scroll down to **"Pages"** section
3. Under **"Source"**, select **"Deploy from a branch"**
4. Select **"main"** branch
5. Select **"/ (root)"** folder
6. Click **"Save"**

### Step 5: Access Your Website
After a few minutes, your website will be available at:
**https://theemaraldnetwork.github.io/Compiti-test/**

## 🗂️ Create Folder Structure

Also create these folders in your repository:

### Create "problems" folder:
1. Click **"Add file"** → **"Create new file"**
2. Type: `problems/README.md`
3. Add content:
   ```markdown
   # Problems Folder
   
   Upload your mathematical problems here!
   
   Supported formats: PDF, JPG, PNG, TXT, MD
   ```
4. Commit changes

### Create "solutions" folder:
1. Click **"Add file"** → **"Create new file"**
2. Type: `solutions/README.md`
3. Add content:
   ```markdown
   # Solutions Folder
   
   Automated solutions will appear here!
   
   Solutions are generated automatically when problems are uploaded to the problems/ folder.
   ```
4. Commit changes

## ✅ Final Repository Structure

After uploading, your repository should look like:

```
TheEMeraldNetwork/Compiti-test/
├── index.html          # GitHub Pages website
├── README.md           # Repository documentation
├── problems/
│   └── README.md       # Upload math problems here
└── solutions/
    └── README.md       # Automated solutions appear here
```

## 🌐 Result

Once uploaded and GitHub Pages is enabled:

- **Website**: https://theemaraldnetwork.github.io/Compiti-test/
- **Upload problems to**: `problems/` folder
- **Solutions appear in**: `solutions/` folder
- **Email notifications**: Sent to davideconsiglio1978@gmail.com

## 🔄 System Workflow

1. **You upload** math problems to `problems/` folder
2. **System detects** new files (every 30 minutes)
3. **System processes** and solves the problems
4. **Solutions uploaded** to `solutions/` folder
5. **Email sent** to notify you
6. **Website updates** automatically

---

**🚀 Once you upload these files, your automated math solver will be fully operational!**
