# CLAUDE.md

This file provides context and guidance for AI assistants working in this repository.

## Repository Overview

**Hello_world** is a minimal educational repository created to learn and demonstrate basic Git and GitHub workflows. It is not a software application — it contains no source code, no build system, no dependencies, and no tests.

- **Owner**: AntoineMoulet
- **Purpose**: Git/GitHub tutorial and workflow experimentation
- **Language**: None (documentation only)

## Repository Structure

```
Hello_world/
├── README.md        # Project title and short description
├── explanation.txt  # Placeholder text file
├── what.md          # Placeholder markdown file
└── CLAUDE.md        # This file
```

All files are simple text/markdown placeholders with minimal content. There is no application logic.

## Git Workflow

This repository demonstrates a standard feature-branch workflow:

1. Create a feature branch from `master`
2. Make changes on the feature branch
3. Open a pull request targeting `master`
4. Merge the pull request

**Default branch**: `master`

**Historical branches** (all merged via PRs):
- `feat` — merged via PR #1
- `test-1` — merged via PR #2
- `another-test` — merged via PR #3

## Development Commands

There are no build, test, or lint commands. This is a documentation-only repository.

```bash
# Clone the repository
git clone <repo-url>

# Create a feature branch
git checkout -b my-feature-branch

# Stage and commit changes
git add <file>
git commit -m "Describe the change"

# Push and open a PR
git push -u origin my-feature-branch
```

## Conventions

- **Commit messages**: Short, descriptive imperative sentences (e.g., `Create explanation.txt`, `Update README.md`)
- **Branch names**: Lowercase, hyphen-separated (e.g., `feat`, `test-1`, `another-test`)
- **No force pushes** to `master`
- All changes to `master` go through pull requests

## Notes for AI Assistants

- There is no code to analyze, refactor, or test.
- Changes in this repository are limited to documentation files (`.md`, `.txt`).
- When creating new files, prefer markdown (`.md`) for documentation.
- Do not introduce build systems, dependency files, or source code unless explicitly requested.
- Commit and push to the designated feature branch; never push directly to `master`.
