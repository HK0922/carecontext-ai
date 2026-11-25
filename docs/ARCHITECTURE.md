# Architecture and project flow

Each displayed statement is a complete passage from a fixed synthetic corpus. Optional model output can select passages but cannot introduce clinical prose.

| Component | Responsibility |
| --- | --- |
| Catalog | Source IDs, patient boundaries, date filters, annotated field changes. |
| Retriever | Token aliases, BM25, at most six candidates. |
| Selector | Local top four, or model-selected candidate IDs. |
| Engine | Scope checks, selection validation, original excerpts, warnings. |
| Store | Immutable answer snapshots and separate mutable annotations. |
| API | Typed inputs, session and size checks, exports, evaluations. |
| Interface | Case queue, evidence brief, source library, timeline, review history. |

## Flow

1. Load session nonce and synthetic case list.
2. Choose case, question, date cutoff, reference inclusion, and mode.
3. Reject explicit advice and injection patterns. These are limited heuristics, not a complete safety classifier.
4. Filter by case and date before ranking.
5. Score passage text and human-authored tags with BM25 (`k1=1.2`, `b=0.75`).
6. Select local top four or send six candidates to the optional model.
7. Validate candidate membership independently and construct exact excerpts from the catalog.
8. Surface differing values for relevant annotated fields. Preserve all dated entries without automatic reconciliation.
9. Save the answer snapshot and corpus SHA-256 in SQLite.
10. Add a separate human annotation, then export the snapshot and annotation.

## Important distinctions

- Ranking scores are uncalibrated relevance values, not confidence percentages.
- The baseline can miss paraphrases, negation, and multi-part intent. A shared term does not establish full answer sufficiency.
- Date is a tie-breaker for tied scores; a latest-fact question may return both older and newer records. Dates remain visible.
- Changes can be normal progression or corrections, not necessarily contradictions.
- Exact quotation checks provenance, not truth or current applicability.

## Persistence

SQLite table `runs`: `id`, `patient_id`, `created_at`, `payload`, `review`. Queries use SQL parameters. New queries create immutable answer snapshots. Review decisions and notes are mutable, human-authored annotations. History returns 30 runs and the UI displays seven. Clearing history deletes all runs for that case, including older hidden entries.

The corpus loads at startup. Restart after editing fixtures. The export fingerprint identifies the corpus used for a saved answer, even if current source data changes later.

## Tradeoffs

A small lexical baseline is transparent and needs no vector service. No free-form answer generation makes provenance enforceable. Fixed synthetic fixtures keep the project reproducible. Browser-native modules avoid a frontend build chain. These are deliberate prototype constraints, not a claim of production readiness.
