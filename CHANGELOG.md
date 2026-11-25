## 0.4 alpha — Synthea medication-history parsing and display patch (2026-11-25)

- Preserve concentrations, device volume and combination-product ingredients in the supplied simulated medication-history format.
- Retain exact source links for recorded dates and simulated reasons without treating them as confirmed clinical facts.
- Distinguish product strength from administration dose and replace internal warning codes with plain-language limitations.
- Fix the false complex/weight-based warning for `mg/mL` product concentrations.
- Keep local research restrictions, attribution and current project version unchanged. This patch is not clinical validation.

## 0.4.0a1 — Local Clinical Intelligence Research Alpha (2026-11-24)

- Added separate loopback-only, opt-in de-identified research API and Editorial workbench.
- Added source-offset-preserving medication, symptom, and lab extraction candidates; no inferred diagnoses.
- Added opt-in term-only RxNorm and DailyMed metadata adapters and mock transport tests.
- Added research data registry with permissions, dataset restrictions and SHA-256 checks.
- Added independent-test-ready field evaluation script; bundled samples are author-written only.
- Added experimental local BM25/dense reciprocal-rank fusion infrastructure; disabled for patient-facing answers.
- Kept 0.3.1 Editorial Studio and classic research fixture functionality.
- **No claim of clinical accuracy, HIPAA compliance, live NLM connectivity, OCR validation or safe real-patient upload.**

# Changelog

## 0.3.1 - Modern Python / VS Code compatibility (2026-11-24)

- Make Python 3.14 (installed on the contributor Mac) and Python 3.15 eligible runtimes.
- Refresh direct Python dependencies to November 2026 published releases and let pip resolve platform-specific transitive wheels.
- Replace the Python 3.12-specific legacy lockfile with `requirements.txt` and an editable install.
- Add `RUN_ON_MAC.command`, `.python-version`, and practical VS Code setup notes.
- Expand the GitHub Actions Python matrix and update Docker to Python 3.14.
- Preserve the v0.3 off-white Editorial interface, fictional data safeguards, `/classic` workspace, and existing features.
- Limitations: tests were run here with Python 3.13 and preinstalled dependencies; fresh Python 3.14/3.15 and refreshed dependency integration need CI verification.


## 0.3.0 — Document Intelligence Studio

- New dark-navy/cyan Studio homepage with separate patient, clinician and researcher perspectives.
- In-memory intake of fictional PDF, DOCX, TXT and Markdown files; optional local image OCR using Tesseract.
- Source-addressed excerpts with page numbers, lexical retrieval traces, highlighted source inspector and local JSON session export.
- Optional schema-constrained model explanations with validated citation IDs; never mislabeled as clinically verified.
- Existing v0.2 clinical evidence demo preserved at `/classic`, including PubMed, evaluations and source review.
- New synthetic PDF test document, expanded test suite and upload limits.
- Explicit experimental boundaries: no authentication, no PHI processing authorization and no durable user storage.


## 0.2.0 — 2026-10-30

Added a public-literature research workspace backed by PubMed E-utilities, study/year filters, structured abstracts, publication notices, source links, citation export, and nine backend tests. The original synthetic record review remains separate. No free-form clinical recommendation or OpenEvidence integration.


## 0.1.0 — 2026-10-30

Initial synthetic evidence-review prototype: case queue, BM25 retrieval, dated citations, source inspection, date filtering, differing-field notices, exact-excerpt checker, optional model selection, review persistence, exports, evaluation lab, tests, and GitHub documentation.

Known verification limits: no live model request, no Docker runtime execution, no browser or accessibility QA. The local API and utility tests passed on Python 3.12.14 and Node 24.22.1.

## v0.3 editorial design revision
- Replaced the previous dark laboratory shell with the user-provided off-white/ink editorial token system.
- Reworked the navigation into a sticky masthead and rehomed the patient/clinician/researcher controls in the document studio.
- Added decorative-only pastel atmospheric orbs, restrained transitions, and mobile menu behavior.
- Preserved the FastAPI ingestion, evidence retrieval, conversation, citation inspector, and original `/classic` workspace.
- Added `docs/EDITORIAL_DESIGN_SYSTEM.md` and responsive visual QA.
