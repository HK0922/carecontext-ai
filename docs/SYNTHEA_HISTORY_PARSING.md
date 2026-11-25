# Synthea medication-history display fix

## What was wrong

The Research Lab's original generic medication parser treated `10 MG/ML` as a reason to warn about complex or weight-based dosing, even though it is a product concentration. It also missed the package-code and volume prefix in an epinephrine auto-injector product description and lost `Clavulanate 125 MG` from `Amoxicillin 250 MG / Clavulanate 125 MG`.

The UI exposed raw internal warning codes (`frequency_missing`, `dose_missing`, `complex_or_weight_based_instruction_requires_review`) and called missing administration directions an *unconfirmed dose*. In the test file, those fields are **not present**, because it is a Synthea simulated medication history, not an original prescription or sig.

## Fix

- Detect Synthea simulated-history format only when both exact conversion markers are present inside the document; do not trigger on the filename alone.
- Preserve all eight recorded entries in `SYNTHEA_030.txt`, including repeated products at distinct recorded dates.
- Capture epinephrine product code `NDA020800`, injector volume `0.3 mL`, and concentration `1 mg/mL` without inferring a patient dose.
- Capture both ingredients in `Amoxicillin 250 mg / Clavulanate 125 mg`. Do not collapse this to amoxicillin.
- Preserve `Hydrocortisone 10 mg/mL` as a concentration, not `10 mg` or a weight-based dosage warning.
- Capture source-linked recorded start dates and simulated reasons separately; neither establishes a clinical diagnosis or the actual medication administration.
- Show "Administration directions not recorded in source" for simulated histories, and readable warnings for other document types.
- Preserve conservative generic parsing, source offsets, and the local-only document privacy boundary.

## Expected result for supplied SYNTHEA_030.txt

Eight dated medication entries, six distinct medication/combination product names, zero inferred administration doses or frequencies, and zero unparsed medication lines. This is **one regression case**, not a clinical accuracy benchmark.

## Tests

Run `python -m pytest -q`, `node --test tests/frontend.test.mjs`, `node --check carecontext/web/research.js` and `python scripts/check_release.py`. Additional regression tests in `tests/test_synthea_history_display.py` validate source spans, ingredients, device volume, concentration, dates and preservation of existing generic behavior.

## Limitations

This format-specific patch is not a general clinical NER or medical normalization engine, and does not validate drug identity, indication, diagnosis, dose appropriateness, handwriting, patient facts or the 85% clinical-accuracy target. Only authorized, appropriately de-identified or simulated documents should be used in this local research build. Do not use the public preview for identifiable health data.
