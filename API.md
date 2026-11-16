# API contract

Base: http://127.0.0.1:8000. OpenAPI: `/openapi.json`. Self-contained reference page: `/docs`.

Mutations require `X-CareContext-Session` from `GET /api/config`. This is a cross-site request control, not authentication. Use the following client example for mutations.

```python
import httpx
with httpx.Client(base_url="http://127.0.0.1:8000") as client:
    client.headers["X-CareContext-Session"] = client.get("/api/config").json()["session"]
    r = client.post("/api/query", json={
        "patient_id": "demo-001", "question": "What allergy information changed?",
        "mode": "local", "include_reference": False, "as_of": None,
    })
    r.raise_for_status()
    print(r.json())
```

| Method and route | Result |
| --- | --- |
| GET /api/health | Version and service status. |
| GET /api/config | Session, model availability, corpus hash and counts; no API key. |
| GET /api/patients | Case metadata. |
| GET /api/patients/{id} | Metadata, timeline, differing annotated values. |
| GET /api/sources?patient_id=...&include_reference=true | Case-scoped passages and optional shared references. |
| POST /api/query | Saved evidence snapshot. |
| POST /api/verify | Exact-excerpt checks. |
| GET /api/history/{patient_id} | Most recent 30 runs. |
| DELETE /api/history/{patient_id} | Delete every run and annotation for that case. |
| GET /api/runs/{run_id} | Stored answer and current review. |
| POST /api/runs/{run_id}/review | Save decision and note. |
| GET /api/runs/{run_id}/export?format=markdown | Markdown attachment; `format=json` also supported. |
| POST /api/evaluations | Run 24 local fixture checks; no model calls. |

## Inputs

Questions: 4–600 trimmed characters. Mode: `local` or `model`. Optional `as_of`: ISO date. Extra fields are rejected. Successful pipeline outcomes are `evidence_found`, `insufficient_evidence`, or `outside_scope`. Provider/contract failures are not stored.

Review body: `{"decision":"needs_followup","note":"Reconcile the allergy entries."}`. Decisions: `reviewed`, `needs_followup`. Note maximum: 2,000 characters.

Verification body:

```json
{"patient_id":"demo-001","claims":[{"source_id":"MC-01:2","text":"The intake allergy field lists no known drug allergies."}]}
```

The verifier compares complete text after Unicode NFKC and whitespace normalization. It returns `source_match` or `unverified`. Paraphrases and partial excerpts require human review. A match against another patient's source is rejected. Fictional workflow references are shared.

## Errors

403: missing session or rejected origin. 404: unknown case or run. 409: model not configured. 413: actual mutation body exceeds 16 KB. 422: invalid typed input. 502: failed model request, schema, or source selection.

Responses use no-store, nosniff, no-referrer, and restrictive CSP. No wildcard CORS. Session tokens change on restart; one worker is required because nonces are held in memory.

## Public literature search

`POST /api/literature/search` uses the same session header. Body: `{"query":"diabetic foot ulcer offloading","study_type":"review","since":2020}`. Query length 3–500; study type `all`, `review`, `trial`, or `guideline`; optional year 1900–2100. Returns up to eight ranked PubMed records with abstract sections, identifiers, publication types, correction links metadata, executed query, translation, and retrieval time. 502 means an upstream failure. No source substitutes are generated.
