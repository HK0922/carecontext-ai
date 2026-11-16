# Scope and safety

CareContext is a local synthetic research prototype. Its outputs are evidence excerpts for inspection, not clinical judgments or recommendations.

## Implemented controls

- Fixed fictional corpus and no record-upload endpoint.
- Patient and date filtering before retrieval; independent source-ID membership check after selection.
- Complete exact excerpts rather than model-authored clinical claims.
- Explicit missing-evidence and outside-scope statuses.
- Visible dates, source titles, and differing annotated values.
- Server-side model credential, bounded candidate list, limited output, and no automatic retries.
- Typed input limits, actual streamed request-body cap, same-origin mutation header, restrictive CSP, escaped dynamic UI text, and parameterized SQL.
- Human review notes clearly separate from source evidence.

## What these controls do not establish

A source match does not prove truth, completeness, current applicability, or correct interpretation. BM25 can return an irrelevant passage that shares a keyword. Advice and injection regexes are incomplete heuristics. The latest entry may still be incorrect. A source can contain an erroneous or malicious statement even if quoted exactly.

There is no clinical validation, authorization system, multi-tenant isolation, managed key service, production observability, or compliance certification. Local database contents are not encrypted by the application. The nonce is a cross-site request control, not a login system.

## Data handling

Local mode keeps queries and review notes in the local SQLite database. Model mode sends the question and retrieved fictional passages to the configured OpenAI service. Only configure it for synthetic data. API `store: false` does not override provider retention policies.

Do not enter real patient identifiers or clinical information in any field. Do not use public hosting for real data. Production use would require a separate design, qualified clinical evaluation, privacy/security review, appropriate contracts, authentication and access controls, incident handling, and applicable legal review.
