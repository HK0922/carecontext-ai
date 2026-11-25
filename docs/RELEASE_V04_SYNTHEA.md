# CareContext v0.4.0a1 — Synthea-aware research release

This release contains a local research-oriented extraction pipeline. It is **not** validated for clinical use.

## Included changes

- Normalization of Synthea medication-history document structures and recorded dates.
- Device/auto-injector and multi-ingredient medication extraction from the named test fixture.
- Distinction between product strength/concentration and a patient administration dose.
- Human-readable missing-field indicators for histories without administration instructions.
- Exact-source citations, source inspection, and optional NLM term lookups in the Research Lab.
- Retains the original evidence-first Studio and classic research views.

## Scope and safety

- Intended for synthetic or appropriately authorized, de-identified research documents only.
- Do not upload real identifiable patient records to public deployments.
- A product listed in a medication history does not establish that a dose was taken or a diagnosis is present.
- The 85% clinical accuracy target has not been independently achieved or validated.
- Research mode stays off by default. Do not enable it in public deployments.

## Tested prior to publishing

- Python pytest suite: 122 tests passed on Python 3.13.5.
- JavaScript frontend suite: 5 tests passed on Node.js 22.16.0.
- Release checks: passed.
- Python 3.14 on user Mac and live NLM network endpoints: not re-tested in this build.

## Source repository and release process

Repository: https://github.com/HK0922/carecontext-ai

The prior repository main branch was a flat upload of the v0.2 source tree. This release restores the proper Python package structure. Changes should first be reviewed on `release/v0.4-synthea-polish` before merging into `main`.
