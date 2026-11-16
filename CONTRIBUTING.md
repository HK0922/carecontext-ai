# Contributing

Use synthetic examples only. For a bug, include the selected case, exact question, date filter, mode, expected behavior, actual behavior, and environment. Never include keys, real patient details, or a local database.

Create a focused branch, implement the change, and run relevant checks:

```bash
python -m pytest
npm run check
npm test
carecontext evaluate
python scripts/check_release.py
```

Keep sources and evaluation labels in sync. Do not weaken assertions to improve a reported score. Report whether a test used a live provider, a mock, or the lexical baseline. Update README metrics only after actually running the checks.

Keep all dynamic UI text escaped and all SQL parameterized. Preserve case/date boundaries and visible uncertainty. Update docs when behavior changes. Use the supplied pull request template.
