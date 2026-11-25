# New: CareContext Research Lab (v0.4.0a1)

For the new local-only, de-identified clinical document research workspace, open VS Code Terminal in the extracted `carecontext` folder and run:

```bash
CARECONTEXT_RESEARCH_MODE=1 zsh RUN_ON_MAC.command
```

Open <http://127.0.0.1:8000/research>. **Do not upload identifiable patient information.** This alpha is not HIPAA compliant or medically validated. If you only want the older fictional Studio, simply use `zsh RUN_ON_MAC.command`.

To enable optional public RxNorm/DailyMed medication-name lookup, run `CARECONTEXT_RESEARCH_MODE=1 CARECONTEXT_RESEARCH_NETWORK=1 zsh RUN_ON_MAC.command`. All lookups send only a medication name, never source documents. See [full alpha notes](docs/CLINICAL_INTELLIGENCE_PHASE1.md).

---

# CareContext v0.3.1 - Mac / VS Code

This is the **complete working FastAPI project** with the Editorial UI, not just a mockup.
It is prepared for your Mac's existing **Python 3.14** and aims to support Python 3.15 too.
No real medical records should be uploaded. Use fictional test documents only.

## One-command setup in VS Code

1. Extract `CareContext_v0_3_1_Modern_Python.zip` (do not open the ZIP as a folder).
2. In VS Code choose **File > Open Folder** and select the extracted **carecontext** folder containing `pyproject.toml`.
3. In **Terminal > New Terminal**, run:

```zsh
zsh RUN_ON_MAC.command
```

The launcher detects your installed Python 3.14 or 3.15, creates `.venv`, installs the package, and starts the local server. First install requires internet access.
Then open **http://127.0.0.1:8000**.
Press **Control+C** to stop the server.

## Or run the individual commands

```zsh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m carecontext.cli serve
```

**Important:** The correct command is `python3.14 -m venv .venv` with a **space** between `venv` and `.venv`.
`python` is usually not present globally on Homebrew macOS. It becomes available inside an activated virtual environment.

If your Mac recognizes `python3` but not `python3.14`, replace `python3.14` with `python3` after confirming its version with `python3 --version`.

## What you will see

- **/**: v0.3 Editorial Studio with fictional document intake, local retrieval, optional server-configured AI explanation, source evidence, and patient/clinician/researcher views.
- **/classic**: original synthetic case workspace and PubMed literature tools.
- **/api/health**: version and readiness check.

### Optional AI

The app works locally without API keys. It uses BM25-style document matching for local mode. To enable AI explanation, set `OPENAI_API_KEY` and `CARECONTEXT_MODEL` **in the terminal** before starting the server, never in the source or frontend. The live model integration has not been independently validated for this release.

### Troubleshooting

- `zsh: command not found: python`: create and activate `.venv` first; use `python3.14` for creation.
- `No module named venv.venv`: you missed the space before `.venv`.
- `source: no such file or directory`: create `.venv` successfully before activating it.
- `Port 8000 is in use`: stop the other server, or run `python -m carecontext.cli serve --port 8010`.
- If an old `.venv` used the wrong Python version, `RUN_ON_MAC.command` preserves it under a timestamped `.venv.previous.*` name and creates a fresh one.
- If a dependency install fails, paste the complete error into ChatGPT rather than retrying blindly.

## Verification scope

The package was verified under Python 3.13 in the authoring environment; the refreshed dependency versions and Python 3.14/3.15 must be verified by running the included multi-Python CI matrix on GitHub. This package does not replace the existing GitHub release or Vercel deployment.
