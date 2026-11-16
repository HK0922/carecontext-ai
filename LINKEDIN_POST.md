# LinkedIn draft

If an AI answers a question about a patient record, can you trace every statement back to its source?

That's the question behind my second project: CareContext.

• Ask questions across synthetic clinical records.
• Open dated citations and inspect the original passages.
• Compare differing entries and surface missing evidence.
• Save a human review and export the evidence brief.

Built with Python, FastAPI, SQLite, and a browser-native interface. Local retrieval runs without an API key; optional model mode selects from retrieved source IDs.

Validation so far: 68 Python tests, 5 frontend utility tests, and 24/24 labeled fixture checks. These are synthetic engineering checks, not clinical validation. Live model, Docker, and browser checks are still pending.

I used AI-assisted development to turn the idea into a working, testable application, with explicit limits on what it can claim.

I'm interested in AI engineering and healthtech opportunities where evidence and reliability matter.

GitHub: https://github.com/HK0922/carecontext-ai

What would you inspect first: the answer, the source, or the missing context?

#HealthTech #AIEngineering #BuildInPublic

---

Publish after uploading the repository and verifying the link. The 24 fixture checks are included in the Python suite. Pair the post with a screenshot or short recording from the local app. Do not describe the branded README diagram as an application screenshot.
