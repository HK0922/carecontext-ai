# Evaluation

Recorded results are in `evaluations/results.json`. Regenerate them with `carecontext evaluate`. Each run includes a corpus SHA-256 and actual timestamp.

## What was measured

The 24 labeled cases test expected-source retrieval, missing information, explicit out-of-scope requests, patient boundaries, date cutoffs, and optional workflow references. The labels are in `carecontext/data/eval_cases.json`.

| Metric | Definition | Recorded baseline |
| --- | --- | --- |
| Fixture checks passed | Status, expected sources, scope, date, exact text, and annotated-change checks pass together | 24 / 24 |
| Expected-source recall at 6 | Total labeled required source IDs found among six candidates / total labeled required IDs | 1.00 |
| Cross-case leakage | Returned passages belonging to another case | 0 |
| Exact-source match rate | Returned excerpt text equal to catalog text / returned excerpts | 1.00 |

The exact-source metric is enforced by construction and is not a hallucination benchmark. Retrieval recall is measured at the candidate stage, not solely the four excerpts displayed by local mode. Tests do not establish clinical relevance, completeness, accuracy, or patient benefit.

## Automated checks

68 Python tests cover the labeled cases, API lifecycle, case/date isolation, source verification, invalid model output, provider failures, input validation, session controls, exports, and static-file boundaries. Five Node tests cover safe text escaping, dates, source grouping, question validation, and abstention labels. The 24 labeled cases are a subset of the Python test count.

The model adapter is tested through `httpx.MockTransport`. No paid provider call was made. A Starlette warning notes future migration from HTTPX in its test client; the installed, pinned combination passed the tests.

## Verification limits

- The suite is small, author-written, and bundled with the development corpus. It is not held-out or independently clinically annotated.
- Only Python 3.12.14 was exercised locally. CI is configured for 3.11, 3.12, and 3.13 but has not run on GitHub yet.
- Live model selection and Docker execution were not exercised.
- The managed preview daemon was unavailable. Browser interaction, visual layout, and assistive-technology behavior remain unverified. Node tests are utility checks, not browser tests.
- Rule-based request filtering is incomplete. Exact excerpts can still be outdated, clinically wrong, or irrelevant to part of a question.

## Next evaluation

Add independently written paraphrases, compound questions, negation, incorrect source documents, ambiguous dates, and adversarial cases. Compare lexical and embedding retrieval on a held-out synthetic set. Have qualified reviewers annotate relevance before considering any clinical claims.

## v0.2 research extension

The full Python suite now has 77 passing tests, including nine tests for literature parsing, cache, filters, missing abstracts, source membership, API validation, and upstream failures. These use synthetic XML through mocked HTTP, not clinical efficacy labels. JavaScript syntax and the five existing utility tests also pass. Browser QA remains unverified.
