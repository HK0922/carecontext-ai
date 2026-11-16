# Literature workspace

Version 0.2 adds an original research interface inspired by the question-and-sources workflow of medical evidence products. It does not use OpenEvidence branding, content, credentials, private APIs, or a licensed full-text corpus. OpenEvidence's public page returned 403 during this build, so no claim of feature parity is made.

## Using it

1. Start CareContext normally and open the Literature tab.
2. Enter general medical research keywords or PubMed Boolean syntax. The input is passed as a search query, not rewritten by an LLM.
3. Optionally filter to systematic reviews, randomized controlled trials, or guidelines, and select a starting publication year.
4. Search, open an abstract, and follow the PubMed or publisher link for the full context.
5. Export the citation list as Markdown. This export contains metadata and links, not copied abstracts.

The interface displays up to eight relevance-ranked records. Study types are PubMed's indexed labels, not an assessment of evidence quality. An unavailable abstract is explicitly labeled. Correction/retraction-related metadata is flagged for inspection, but absence of a notice is not a guarantee that a paper remains valid.

## Retrieval and data flow

The backend calls NCBI ESearch for IDs, then EFetch for XML records. It extracts title, journal, publication date, author names, study types, abstract sections, DOI, and linked publication notices. Returned IDs must belong to the search results. HTML is escaped in the interface. Outbound hosts are fixed in code.

The entered query is transmitted to NCBI. Do not include patient details. Abstracts are displayed for source inspection; rights remain with the original authors/publishers. No live abstracts are committed to the repository. A bounded in-memory cache holds 32 searches for up to ten minutes; restarting the server clears it. Requests are spaced at least 0.4 seconds apart within one process.

API: `POST /api/literature/search`. See [API.md](API.md). Official service documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/

## Validation

Nine new mocked backend tests exercise parsing, filtering, caching, missing abstracts, empty results, unexpected IDs, service errors, and API validation. A live smoke search for `diabetic foot ulcer offloading`, filtered to systematic reviews from 2020, successfully returned source records. See `evaluations/literature_smoke.json` for the recorded run. This proves connectivity and parsing, not search completeness or clinical utility.

## Boundaries

This release provides literature discovery and original abstracts. It does not generate a synthesized clinical answer, offer treatment recommendations, assess evidence quality, or connect a real patient to research. Those require additional design, source licensing where relevant, and qualified clinical evaluation. The existing optional model selector remains limited to synthetic case records.

Browser interaction and visual QA remain unverified because the preview infrastructure is unavailable. Live model generation and Docker runtime also remain unverified.
