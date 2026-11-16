# Synthetic data card

## Origin and intended use

All case records and references were authored specifically for this portfolio project. No real patient records, EHR exports, external medical guidelines, or scraped healthcare data are included. Names, dates, notes, and events are fictional. Any similarity to a real person is incidental.

Three cases demonstrate coordination around a fictional wound clinic: transport and supplies, referral completion, and a rescheduled home visit. Twelve documents include ten case records and two shared workflow references. The dataset has 34 sentence-level passages. Use the authoritative count from `/api/config` or the release validation script if fixtures change.

The reference documents describe fictional workflow conventions. They are not clinical guidelines. Medication names and measurements are example record fields, not recommendations or treatment instructions. No clinical inference should be drawn from them.

## Schema

Patients: ID, fictional name, initials, age, case label, focus, last-record date, UI color, suggested questions.

Documents: ID, optional patient ID (null for shared references), title, date, kind, author label, synthetic flag, and entries.

Entries: exact text, manually authored retrieval tags, optional structured field/value pair for change detection. Passage IDs are stable document ID plus one-based entry index.

## Regeneration

`python scripts/build_fixtures.py` writes `carecontext/data/cases.json` from the authoring script. Run the test suite and evaluation after editing it. If you reorder entries, passage IDs and evaluation labels must be updated together.

## Limitations

The records are sparse, English-only, manually tagged, and restricted to a narrow workflow. They do not model clinical complexity or realistic population variation. The supplied source labels are not independently reviewed ground truth.
