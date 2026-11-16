# Project instructions

CareContext is a local synthetic evidence review prototype. Preserve the patient boundary, dated citations, exact source verification, and explicit abstention. Do not claim clinical validation or compliance certification.

Use `python -m pytest`, `node --test tests/frontend.test.mjs`, and `carecontext evaluate` after changing relevant behavior. Regenerate `evaluations/results.json` when fixtures or retrieval change. State whether a model or only the deterministic baseline was tested.

Keep the frontend dependency-free. Use text escaping for all dynamic HTML. Follow the existing muted green, ivory, and serif-heading visual system. Controls must remain keyboard accessible, responsive, and functional.

Keep user secrets and SQLite databases out of version control and archives. No real patient information belongs in examples, issue reports, or test data.
