# Setting Up Your GitHub Repository

Follow these steps to create a new GitHub repository and push the code:

## 1. Create a New Repository on GitHub

1. Go to [GitHub](https://github.com)
2. Click on the "+" icon in the top right corner and select "New repository"
3. Name your repository `k8s-python-app`
4. Add a description: "A Python Flask application designed to run in Kubernetes or as a standalone container using Podman on macOS."
5. Choose "Public" or "Private" visibility as desired
6. Do NOT initialize with a README, .gitignore, or license file
7. Click "Create repository"

## 2. Initialize Git and Push Code

Run these commands in your terminal from the `k8s-python-app-new` directory:

```bash
# Make app_manager.sh executable
chmod +x app_manager.sh

# Initialize git repository
git init

# Add all files
git add .

# Commit the files
git commit -m "Initial commit"

# Add remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/k8s-python-app.git

# Push to GitHub
git push -u origin main
```

If you're using the `master` branch instead of `main`, use this command instead:
```bash
git push -u origin master
```

## 3. Verify Your Repository

1. Visit your repository on GitHub to make sure all files were pushed correctly
2. Check that the architecture diagrams are properly displayed in the README

## 4. Enable GitHub Pages (Optional)

If you want to showcase the architecture diagrams:

1. Go to repository Settings > Pages
2. Select the branch (main or master) and folder (/root)
3. Click "Save"
4. Your site will be published to `https://YOUR_USERNAME.github.io/k8s-python-app/`
