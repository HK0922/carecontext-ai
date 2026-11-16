# Setup and troubleshooting

Use Python 3.11–3.13. Python 3.12.14 was used locally. The CI matrix is configured for all three versions but has not run on GitHub yet.

## macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
carecontext serve
```

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe -m pip install --no-deps -e .
.venv\Scripts\python.exe -m carecontext.cli serve
```

Open http://127.0.0.1:8000. API docs: `/docs`. Opening `index.html` directly or uploading only the frontend to GitHub Pages will not run the backend.

The UI has no CDN fonts, external scripts, analytics, or frontend dependency install. Pip needs internet for the first installation. If the port is occupied, use `carecontext serve --port 8010`.

## Configuration

| Variable | Purpose |
| --- | --- |
| OPENAI_API_KEY | Optional model credential; server only. |
| CARECONTEXT_MODEL | Explicit model supporting Responses API strict structured output. No paid model is selected by default. |
| CARECONTEXT_DB | SQLite path; defaults to `.data/carecontext.sqlite3`. |

Export variables before starting; restart after configuration changes. `.env.example` is documentation, not an automatic loader. Local mode never calls the model. Model mode sends the question and retrieved fictional passages. Requests use HTTPX timeout 25 seconds and output cap 600 tokens, with no automatic retries. Errors do not silently fall back to local mode.

## Docker option

Docker and Compose are supplied but were not runtime-tested here.

```bash
docker compose up --build
```

The host port binds to `127.0.0.1:8000`. The image runs as user 10001. A named volume stores review data. `docker compose down` stops it; adding `--volumes` also deletes saved review data.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Command not found | Activate the venv or use `python -m carecontext.cli serve`. |
| Model option disabled | Set both model variables and restart. |
| POST returns 403 | Reload after restart, or send the nonce from `/api/config` as `X-CareContext-Session`. |
| Evidence gap | Check the selected case, date, and wording; do not interpret it as a negative clinical finding. |
| Source unverified | The checker requires a complete source excerpt, not a substring or paraphrase. |
| API unavailable | Serve with the Python application, not a file URL. |
| Banner missing on GitHub | Upload `docs/assets/carecontext-banner.png` with README.md. |

## Deployment boundary

This version is for one local reviewer and one server process. It has no user authentication, tenancy, managed encryption, rate limiting, EHR integration, or clinical audit system. The session header is a same-origin control, not user authentication. Do not expose it publicly or use real patient data without implementing and independently reviewing these capabilities.
