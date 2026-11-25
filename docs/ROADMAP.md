# Roadmap

## Delivered in v0.1

Local evidence workspace, three synthetic cases, 12 documents, BM25 retrieval, dated citations, record changes, source checker, human reviews, Markdown/JSON export, optional model selector, tests, fixture evaluation, and GitHub packaging.

## Next engineering steps

1. Complete desktop/mobile browser interaction and accessibility checks in an available environment.
2. Exercise Docker and a selected live model; record actual results and costs.
3. Add independently authored evaluation cases and multi-part question handling.
4. Compare an embedding retriever against the lexical baseline rather than assuming it performs better.
5. Add explicit evidence sufficiency and temporal-intent evaluation, with qualified domain review.

## Separate production track

Real data ingestion, EHR/FHIR connections, identity and access controls, tenancy, encrypted storage management, audit retention, operational monitoring, clinical evaluation, and compliance work are outside v0.1. They require their own design and validation before any clinical deployment.
