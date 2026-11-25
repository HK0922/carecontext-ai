"""Inspectable BM25 baseline. No embedding model or network is required."""
from collections import Counter
import math
import re
import unicodedata

STOP = set('a an the is are was were be been being what which who when where why how do does did has have had i me my we our you your their patient patients case record records documented documentation show tell summarize summary please all any about for of in on at to from with and or it its this that there latest current noted note notes explain give says say evidence'.split())
ALIASES = {
    "allergies": "allergy", "allergic": "allergy", "medications": "medication", "meds": "medication",
    "medicine": "medication", "drugs": "medication", "appointments": "appointment", "visit": "appointment",
    "visits": "appointment", "followup": "appointment", "follow": "appointment", "scheduled": "appointment",
    "transportation": "transport", "ride": "transport", "rides": "transport", "supplies": "supply",
    "dressings": "dressing", "blocking": "barrier", "blocked": "barrier", "barriers": "barrier",
    "pending": "barrier", "outstanding": "barrier", "missing": "barrier", "unresolved": "barrier",
    "referrals": "referral", "changed": "change", "changes": "change", "differences": "change",
    "discrepancies": "change", "conflicts": "change", "conflicting": "change",
    "measurements": "measurement", "size": "measurement", "wounds": "wound", "results": "result",
    "called": "contact", "phone": "contact", "calls": "contact", "calling": "contact",
    "a1c": "hba1c", "hba1c": "hba1c", "blood": "blood", "pressure": "pressure",
    "process": "workflow", "policy": "workflow", "procedure": "workflow",
}

def tokens(text):
    raw = re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKC", text).lower())
    return [ALIASES.get(t, t) for t in raw if t not in STOP and t not in {"up", "s"}]

def rank(question, passages, patient, limit=6):
    ignored = set(tokens(patient["name"])) | {patient["id"].lower()}
    query = set(tokens(question)) - ignored
    if not query or not passages:
        return []
    docs = [tokens(p.text + ' ' + ' '.join(p.tags)) for p in passages]
    avg = sum(map(len, docs)) / len(docs)
    df = Counter(t for doc in docs for t in set(doc))
    ranked = []
    for p, doc in zip(passages, docs):
        counts = Counter(doc)
        overlap = query & counts.keys()
        # Require literal/concept overlap; abstain when no usable evidence is retrieved.
        if not overlap:
            continue
        score = 0.0
        for t in overlap:
            idf = math.log(1 + (len(docs) - df[t] + .5) / (df[t] + .5))
            score += idf * counts[t] * 2.2 / (counts[t] + 1.2 * (.25 + .75 * len(doc) / avg))
        # These are retrieval scores, not confidence or medical correctness probabilities.
        ranked.append({"passage": p, "score": round(score, 5), "matched_terms": sorted(overlap)})
    return sorted(ranked, key=lambda r: (r["score"], r["passage"].date), reverse=True)[:limit]

def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC', text).split()).strip()
