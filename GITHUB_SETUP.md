# GitHub Setup Instructions

Follow these steps to push your code to GitHub and deploy to Render.

## Step 1: Initialize Git Repository

```bash
# Navigate to project directory
cd "/Users/varshasaravanan/Downloads/cs221-tripcompass-new copy"

# Initialize git repository
git init

# Add all files (respecting .gitignore)
git add .

# Check what will be committed (verify large files are excluded)
git status

# Make initial commit
git commit -m "Initial commit: TripCompass deployment ready"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (name it `tripcompass` or similar)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)
4. Copy the repository URL (e.g., `https://github.com/yourusername/tripcompass.git`)

## Step 3: Push to GitHub

```bash
# Add remote (replace with your actual GitHub URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 4: Verify Repository Size

After pushing, check your repository on GitHub. It should be relatively small (under 50MB) because:
- Large raw CSV files are excluded via `.gitignore`
- Only essential runtime files are included

## Step 5: Deploy to Render

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub account (if not already connected)
4. Select your repository
5. Render will auto-detect the `render.yaml` configuration
6. Click "Create Web Service"
7. Wait for deployment (5-10 minutes)
8. Your app will be live at `https://tripcompass.onrender.com` (or your custom name)

## Troubleshooting

### If GitHub says files are too large:
- Check `.gitignore` is working: `git status` should not show large CSV files
- If a large file was already committed, remove it:
  ```bash
  git rm --cached tripcompass/data/pois_sf.csv
  git commit -m "Remove large data files"
  ```

### If Render build fails:
- Check build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify model files (`main_nn_model.npz`, `main_scaler.joblib`) are committed

### Essential Files Checklist

Before pushing, verify these files exist and are committed:
- [ ] `tripcompass/data/pois_sf_enriched.csv`
- [ ] `tripcompass/data/user_profiles.csv`
- [ ] `tripcompass/main_nn_model.npz`
- [ ] `tripcompass/main_scaler.joblib`
- [ ] All Python code files
- [ ] `requirements.txt`
- [ ] `render.yaml`
- [ ] `ui/` directory with all frontend files

## Need Help?

If you need to share your GitHub credentials or repository URL, I can help you set up the remote and push the code.

