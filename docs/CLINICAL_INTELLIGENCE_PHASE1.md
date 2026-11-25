# Clinical document intelligence — implementation milestone A/B (0.4.0a1)

**Status:** open-source research alpha; no independent clinical accuracy claim; no identifiable patient intake.

This milestone follows the prior clinical research architecture plan. It **does not** implement the entire multi-phase plan and does not establish 85% clinical accuracy.

## What is running now

1. `carecontext/clinical_extract.py` — conservative rule-based field extraction: medication name, strength, dose, route, frequency, duration, explicitly documented symptom statements, laboratory values and source-labeled context. The `explicit_indication` field is always `null` for medication candidates; a separate `explicit_context` field preserves what is actually documented. No condition or symptom is inferred from a drug.
2. `carecontext/studio_ingest.py` — existing size-limited PDF, DOCX, TXT, Markdown and optional local image OCR; new `extract_pages()` exposes complete page text and cryptographic source fingerprints, while keeping older Studio behavior unchanged. PDF OCR and precise layout bounding boxes remain outstanding.
3. `carecontext/research_privacy.py` — reject-only direct identifier heuristics. **Not an anonymization service or a HIPAA de-identification certificate.** Human screening and authorization remain necessary.
4. `carecontext/medical_references.py` — opt-in **medication-name-only** calls to official NLM RxNorm and DailyMed **metadata** APIs. Ambiguous RxCUIs are not auto-resolved. No label indications or adverse effects are interpreted yet. Network integration is mock-tested, not live-tested here.
5. `carecontext/hybrid_retrieval.py` — experimental BM25 + opt-in local dense-vector retrieval with reciprocal-rank fusion. **Not wired into patient-facing answers** until independently evaluated.
6. `carecontext/web/research.*` — Editorial-theme local research lab with file selection, provenance inspector, candidate cards, optional official source links and JSON export; served at `/research` and disabled by default.
7. `data/registry.json` and `scripts/data_registry.py` — source licenses, acquisition policy and local file checksums. No restricted dataset or journal corpus is bundled.
8. `scripts/evaluate_clinical.py` and author-written fixtures — field-level exact-match metrics and Wilson confidence intervals. This is a **regression suite**, not a clinical benchmark.

## Run locally (macOS)

```bash
cd carecontext
zsh RUN_ON_MAC.command
```

Open `http://127.0.0.1:8000/studio` for the existing fictional-data Studio. The Research Lab is at `/research` but intake is off by default.

To opt in to *authorized de-identified* local research:

```bash
CARECONTEXT_RESEARCH_MODE=1 zsh RUN_ON_MAC.command
```

In a separate terminal with `.venv` active:

```bash
python -m pytest
python scripts/data_registry.py --validate
python scripts/evaluate_clinical.py
npm run check && npm test
```

The server defaults to `127.0.0.1`. When Research Mode is enabled, CLI refuses binding to an external interface. The API additionally checks loopback address, origin/session and document-use attestation. These checks are defense in depth, not a claim of HIPAA compliance, and must not be relied upon behind an internet-facing reverse proxy.

For official reference lookups (sends only the medication term):

```bash
CARECONTEXT_RESEARCH_MODE=1 CARECONTEXT_RESEARCH_NETWORK=1 zsh RUN_ON_MAC.command
```

**No full document, symptom, dates, source text or patient details are transmitted to RxNorm or DailyMed by the reference adapter.** Only format-limited name-shaped strings are permitted. The user must explicitly confirm a term is a medication and contains no identifying information before a live network request. This confirmation is not a clinical or privacy guarantee. The whole research workflow does not use an LLM or any third-party model. Existing Studio's optional LLM mode remains synthetic-only.

## Boundaries

- No storage is created by `/api/research/analyze` or `/api/research/lookup`. Data and source excerpts are returned to the requesting browser and held in tab memory, but users can export a JSON file containing text; exported files can be sensitive.
- No audit trail, authentication, at-rest encryption or multi-tenant isolation is implemented. Never enable the research service on a public host or process identifying patient information.
- Filename/content heuristics catch some identifiers (MRNs, emails, labeled DOB, names) but miss many. De-identify *before* loading, review data rights and access conditions, and do not treat a successful identifier scan as permission to upload PHI.
- OCR confidence is `null`; no fabricated confidence percentages. Extractor returns `manual_review_required` for every candidate, including clean text.
- Medication lookup returns *possible identities*, not a verified prescribed product or indication.
- PubMed/PMC literature is not locally mirrored; publisher licensing varies. The legacy PubMed search remains available in the Studio.
- A prescription is not a basis to assert a patient's diagnosis, symptoms, drug safety, or appropriate treatment.

## Separate data planes

| Plane | Location | Rules |
|---|---|---|
| User inputs | Request memory only | Authorized de-identified data; never embedded in public repo or external API requests |
| Authoritative sources | Live RxNorm and DailyMed API metadata | Terms-only, opt-in, no unlicensed full-text copying |
| Development regression data | `tests/fixtures/` | Author-written synthetic, versioned and openly shipped |
| External gold evaluation | *Not acquired yet* | Credentialed data must remain outside the repo and tuning loop; clinician-adjudicated |

### Research data registry

The registry includes RxNorm, DailyMed, LOINC, UCUM, PubMed, PMC Open Access, RxHandBD, n2c2, MIMIC-IV, BHCP-DOC, MedlinePlus and the bundled fixtures. Entries state purpose, access requirements, allowed acquisition method, redistribution prohibition, local path and optional checksum. Retrieval scripts refuse to fetch restricted content automatically. See official sources:

- [RxNorm API](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html)
- [DailyMed v2 SPL API](https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_api.cfm)
- [PMC OA retrieval conditions](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/)
- [MIMIC-IV access](https://physionet.org/content/mimiciv/)
- [n2c2 datasets and DUA](https://n2c2.dbmi.hms.harvard.edu/data-sets)
- [FDA Clinical Decision Support Software](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software)

## Measurement and the 85% goal

The included 12 *author-written* examples are easy unit/regression examples, and the extractor can overfit by construction. Its observed score and Wilson lower confidence bounds **must not be reported as clinical accuracy or evidence the 85% criterion is satisfied**. Clinical validation must use independent, clinician-adjudicated real-world de-identified documents with no leakage.

Required future evaluations (not completed): OCR word/character error by print/handwriting; medication name span F1; exact strength/dose/route/frequency match; RxCUI accuracy and abstention; negation/temporality; hybrid retrieval Recall@10; medical claim entailment; serious error counts; confidence calibration; external blinded test CI and demographics/institution stratification. The acceptance target must be set per field and risk level, not one aggregate percentage. A low average does not imply safe usage, nor does a high one.

## Next phases (not complete)

- **B continuation:** independent handwritten OCR adapter, page geometry and quality scores; stronger clinical NER trained/evaluated on authorized data; RxNorm/LOINC mapping, temporal and negation validation; explicit human corrections.
- **C:** licensed versioned DailyMed label-section corpus and PMC OA subset; biomedical dense encoders + reranker; benchmark every retrieval variant against BM25; source versions and evidence hierarchy.
- **D:** source-constrained LLM with sentence/claim-level entailment, dose/identity validator, abstention, adversarial document prompt-injection tests; human review first.
- **E:** external independent n2c2/MIMIC/prescription evaluation under their DUAs, annotations by clinicians/pharmacists, locked splits, confidence intervals and model card.
- **F:** privacy/security/regulatory assessment, authentication, encryption, retention, BAA/vendor review as applicable, documented intended use and pilot evaluation **before** any identifiable-document deployment.

**Do not promote this alpha to a clinical deployment, label it HIPAA compliant, accept identifiable clinical data, or claim 85% accuracy.**
