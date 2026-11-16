"""A constrained evidence brief with no model-authored clinical statements."""
import re
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4
from .retrieval import rank, normalize, tokens

ADVICE = re.compile(r"\b(diagnos\w*|prescrib\w*|dosage|recommend\w*|should\s+\w+\s+(?:take|start|stop|use)|(?:what|which)\s+(?:treatment|antibiotic|drug)|treat\s+(?:this|the|my)|cure|emergency|triage)\b", re.I)
INJECTION = re.compile(r"ignore\s+(?:all|previous|prior)|system\s+prompt|reveal\s+.*(?:key|secret)|other\s+patients?|all\s+patients?|<script", re.I)

class Engine:
    def __init__(self, catalog, selector=None):
        self.catalog, self.selector = catalog, selector

    def answer(self, patient_id, question, mode="local", include_reference=False, as_of=None):
        start = perf_counter()
        patient = self.catalog.patient(patient_id)
        result = {"id": uuid4().hex, "created_at": datetime.now(timezone.utc).isoformat(),
                  "patient_id": patient_id, "question": question, "mode": mode,
                  "as_of": as_of, "include_reference": include_reference, "status": "evidence_found",
                  "summary": "Direct excerpts from the selected case. Review each source in context.",
                  "evidence": [], "retrieval": [], "warnings": [], "corpus_sha256": self.catalog.digest}
        if ADVICE.search(question):
            result.update(status="outside_scope", summary="This workspace retrieves recorded evidence. It cannot recommend treatment, diagnose, prescribe, or assess urgency. Ask what the synthetic record documents.")
        elif INJECTION.search(question) or any(
            any(re.search(r'\b'+re.escape(name)+r'\b',question,re.I) for name in p['name'].split())
            for p in self.catalog.patients.values() if p['id'] != patient_id
        ):
            result.update(status="outside_scope", summary="This request falls outside the selected case and evidence-review scope.")
        else:
            candidates = rank(question, self.catalog.scope(patient_id, include_reference, as_of), patient)
            result["retrieval"] = [{"source_id": r["passage"].id, "score": r["score"], "matched_terms": r["matched_terms"]} for r in candidates]
            if mode == "model":
                if self.selector is None:
                    raise ValueError("Model mode is not configured")
                selected = self.selector.select(question, candidates) if candidates else []
            else:
                selected = [r["passage"].id for r in candidates[:4]]
            allowed = {r["passage"].id for r in candidates}
            # Independent boundary even if a custom provider bypasses its own validation.
            if any(s not in allowed for s in selected):
                raise ValueError("Selector returned a source outside the retrieved scope")
            for source_id in dict.fromkeys(selected):
                p = self.catalog.passages[source_id]
                result["evidence"].append({**p.public(), "citation": len(result["evidence"]) + 1,
                                           "verification": "exact_source_match"})
            if not result["evidence"]:
                result.update(status="insufficient_evidence", summary="No supporting passages were selected in the available record. Missing evidence is not evidence of absence. Try a more specific record question.")
            referenced_fields = {e["field"] for e in result["evidence"] if e["field"]}
            result["warnings"] = [c for c in self.catalog.changes(patient_id, as_of)
                                  if c["field"] in referenced_fields or "change" in tokens(question)]
        result["elapsed_ms"] = round((perf_counter() - start) * 1000, 2)
        result["verification"] = {"method": "exact source excerpts", "verified": len(result["evidence"]),
                                  "total": len(result["evidence"]), "limit": "Checks provenance, not clinical truth, completeness, or semantic relevance."}
        return result

    def verify(self, patient_id, claims):
        self.catalog.patient(patient_id)
        results = []
        for claim in claims:
            source = self.catalog.passages.get(claim["source_id"])
            if source is None:
                verdict, reason = "unverified", "Source ID does not exist."
            elif source.patient_id not in (None, patient_id):
                verdict, reason = "unverified", "Source is outside the selected case."
            elif normalize(claim["text"]) != normalize(source.text):
                verdict, reason = "unverified", "Text is not a complete exact source excerpt. Paraphrases require human review."
            else:
                verdict, reason = "source_match", "Complete source excerpt matched. This does not establish clinical truth."
            results.append({**claim, "verdict": verdict, "reason": reason})
        return results
