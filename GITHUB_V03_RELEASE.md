# Publishing the v0.3 branch — without disturbing v0.2

The GitHub repository `HK0922/carecontext-ai` currently contains some originally nested files at the repository root because of the original drag-and-drop upload. The v0.3 ZIP restores the canonical Python project directory hierarchy.

**The package has not been pushed to GitHub. Do not overwrite `main` until the new branch has passed CI and been inspected.**

## Recommended: Codespaces or a local terminal

1. Open your GitHub repository: https://github.com/HK0922/carecontext-ai
2. Choose **Code → Codespaces → Create codespace on main**. A terminal appears in the browser-based VS Code editor. Alternatively, use a terminal on your own computer after cloning the repository.
3. Open the terminal, ensure you are at the repository root, and run:

```bash
git switch -c feature/carecontext-v0.3.1
```

4. Upload this ZIP into the Codespace Explorer (drag and drop the ZIP), then unzip it to a temporary folder. Assuming the archive is named `CareContext_v0_3_1_Modern_Python.zip`:

```bash
mkdir -p /tmp/carecontext-v03
unzip CareContext_v0_3_1_Modern_Python.zip -d /tmp/carecontext-v03
cp -a /tmp/carecontext-v03/carecontext/. .
```

5. **Review before committing**. Your previously flattened v0.2 files at the root may still be present. Their removal is a separate cleanup; do not run broad delete commands until you verify the entire tree. Confirm these paths exist: `carecontext/api.py`, `carecontext/web/studio.html`, `carecontext/data/cases.json`, `tests/test_studio.py`, `docs/V0_3.md`.

```bash
git status --short
python -m pip install -r requirements.txt
python -m pytest
npm run check
npm test
python scripts/check_release.py
```

6. Inspect the diff, then stage and commit. Avoid committing `.env`, actual patient information, `.data`, or virtual environments.

```bash
git add -A
git diff --cached --stat
git commit -m "CareContext v0.3.1: synthetic document intelligence studio"
git push -u origin feature/carecontext-v0.3.1
```

7. Create a PR to `main`; review GitHub Actions, source structure, privacy boundaries, and preview behavior before merge. Keep the public v0.2 deployment as-is until v0.3 is ready.

**Do not upload the ZIP as a repository file** expecting GitHub to extract it. GitHub's website does not unpack archives. For a multi-folder project, Git or Codespaces is more reliable than dragging individual flattened files into GitHub's web uploader.
