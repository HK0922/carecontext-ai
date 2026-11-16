# Portfolio talking points

## Thirty second introduction

I built CareContext, a clinical evidence-review prototype using entirely synthetic records. A reviewer asks a question, inspects dated source excerpts, compares differing entries, and exports a reviewed brief. The local mode uses an inspectable BM25 baseline, with an optional model selector constrained to source IDs. I used AI-assisted development and tested the retrieval boundaries, source checks, and review lifecycle.

## Resume bullets

- Built a FastAPI and SQLite evidence-review application with case-scoped retrieval, dated citations, differing-value notices, and human-reviewed exports.
- Implemented exact-excerpt validation and a constrained model selector that rejects unavailable source IDs; tested wrong-case citations, missing evidence, date boundaries, and provider failures.
- Added 68 passing Python tests, five frontend utility tests, and a reproducible 24-case synthetic evaluation; documented untested live-model, container, and browser paths.

## Questions to prepare for

Why use BM25? It is transparent and proportionate to a small corpus; a comparison against embeddings remains future work.

Does a citation prevent hallucinations? It limits unsupported generated prose by construction, but quoted evidence can still be irrelevant or wrong. This is not clinical truth verification.

Who uses it? It is a portfolio prototype for demonstrating record review, with no verified external adoption or clinical deployment.

What is the next step? Finish browser and live-provider validation, add held-out cases, and evaluate answer sufficiency before expanding functionality.
