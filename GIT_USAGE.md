# Git Version Control for Kubernetes Dashboard

This repository contains the Kubernetes Dashboard and Deployment Control tools. Git has been set up to maintain version control of the codebase.

## Current Repository Status

- **Main Branch**: `master`
- **Feature Branch**: `deployment-control` (for deployment control feature)
- **Current Version**: `v1.0.0` (tagged)

## Common Git Commands

### Checking Status

```bash
# Check current status
git status

# View commit history
git log --oneline --decorate
```

### Working with Branches

```bash
# List all branches
git branch

# Create a new branch
git branch <branch-name>

# Switch to a branch
git checkout <branch-name>

# Create and switch to a new branch
git checkout -b <branch-name>

# Merge a branch into current branch
git merge <branch-name>
```

### Making Changes

```bash
# Stage changes for commit
git add <file-or-directory>

# Commit changes
git commit -m "Descriptive message about the changes"

# Stage all changes and commit
git commit -a -m "Descriptive message about the changes"
```

### Working with Tags

```bash
# List all tags
git tag

# Create a new tag
git tag -a v1.x.x -m "Tag description"

# View tag details
git show v1.x.x
```

### Undoing Changes

```bash
# Discard changes in working directory
git restore <file>

# Unstage a file
git restore --staged <file>

# Revert a commit
git revert <commit-hash>
```

## Workflow for New Features

1. Create a new branch for the feature:
   ```bash
   git checkout -b feature-name
   ```

2. Make changes and commit them:
   ```bash
   git add <changed-files>
   git commit -m "Implement feature X"
   ```

3. When the feature is complete, merge it back to master:
   ```bash
   git checkout master
   git merge feature-name
   ```

4. Tag a new version if appropriate:
   ```bash
   git tag -a v1.x.x -m "Version with feature X"
   ```

## Deployment Control Feature

The deployment control feature is currently in its own branch. To work on it:

```bash
git checkout deployment-control
```

To merge it into the main codebase when ready:

```bash
git checkout master
git merge deployment-control
```
