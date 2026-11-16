# Publish CareContext on GitHub

This package contains the application source, assets, tests, evaluation results, and documentation. It is ready for you to upload. No GitHub repository or public deployment was created for you.

## Publish to your existing repository

1. Extract `CareContext_GitHub_Ready.zip`. Open the inner `carecontext` folder, which contains `README.md` and `pyproject.toml`.
2. Use the already-created public repository `HK0922/carecontext-ai`.
3. This upload targets the empty repository already verified on GitHub. All required files are included.
4. Run the commands below from the extracted project folder after signing into GitHub.

```bash
git init -b main
git add .
git status --short
git commit -m "Add CareContext clinical evidence prototype"
git remote add origin https://github.com/HK0922/carecontext-ai.git
git push -u origin main
```

Before committing, confirm the staged files contain no `.env`, `.venv`, `.data`, SQLite files, or API keys. The supplied `.gitignore` excludes these, including `.DS_Store`.

## GitHub profile details

Description:

> Clinical evidence review prototype with synthetic records, dated citations, scoped retrieval, and human review.

Suggested topics: `healthtech`, `clinical-informatics`, `information-retrieval`, `fastapi`, `python`, `llm`, `ai-agents`, `evaluation`, `synthetic-data`.

Pin the repository to your profile. Add a screenshot of the running app after opening it locally. Do not claim a live public demo unless you have deployed one.

## If the remote already has a commit

The clean-start instructions assume an empty remote. If you initialized GitHub with a README or license, preserve that history:

```bash
git pull --no-rebase origin main --allow-unrelated-histories --no-edit
```

If only `README.md` conflicts and you intend to keep the supplied project README:

```bash
git checkout --ours README.md
git add README.md
git commit --no-edit
git push -u origin main
```

If other files conflict, resolve each one and inspect `git status` before committing. Do not force-push to remove the remote history. If `origin` already exists, use `git remote set-url origin https://github.com/HK0922/carecontext-ai.git` instead of adding it again.

## Verify after upload

- README banner loads from `docs/assets/carecontext-banner.png`.
- The repository includes `carecontext/data`, `carecontext/web`, `tests`, `docs`, and `.github`.
- GitHub Actions completes. The configured CI workflow has not run until you push it.
- The local app starts from a fresh clone using README instructions.
- GitHub Pages alone will not run the Python backend.

The archive includes a SHA-256 manifest. To recreate a clean source ZIP, run `python scripts/package_release.py --output ../CareContext_GitHub_Ready.zip`.
