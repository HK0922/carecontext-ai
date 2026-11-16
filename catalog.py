"""Immutable fixture corpus with explicit patient boundaries and source lineage."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json

DATA = Path(__file__).parent / "data"

@dataclass(frozen=True)
class Passage:
    id: str
    document_id: str
    patient_id: str | None
    title: str
    date: str
    kind: str
    text: str
    tags: tuple[str, ...]
    field: str | None = None
    value: str | None = None

    def public(self):
        return asdict(self)

class Catalog:
    def __init__(self, path: Path | None = None):
        self.raw = json.loads((path or DATA / "cases.json").read_text())
        self.patients = {p["id"]: p for p in self.raw["patients"]}
        self.documents = {d["id"]: d for d in self.raw["documents"]}
        if len(self.documents) != len(self.raw["documents"]):
            raise ValueError("Duplicate document ID")
        self.passages = {}
        for d in self.documents.values():
            if d["patient_id"] is not None and d["patient_id"] not in self.patients:
                raise ValueError("Unknown patient in source")
            for i, entry in enumerate(d["entries"], 1):
                p = Passage(f'{d["id"]}:{i}', d["id"], d["patient_id"], d["title"],
                            d["date"], d["kind"], entry["text"], tuple(entry["tags"]),
                            entry.get("field"), entry.get("value"))
                self.passages[p.id] = p
        self.digest = hashlib.sha256(json.dumps(self.raw, sort_keys=True).encode()).hexdigest()

    def patient(self, patient_id):
        if patient_id not in self.patients:
            raise KeyError(patient_id)
        return self.patients[patient_id]

    def scope(self, patient_id, include_reference=False, as_of=None):
        self.patient(patient_id)
        return [p for p in self.passages.values()
                if (p.patient_id == patient_id or (include_reference and p.patient_id is None))
                and (as_of is None or p.date <= as_of)]

    def timeline(self, patient_id, as_of=None):
        self.patient(patient_id)
        return sorted([d for d in self.documents.values() if d["patient_id"] == patient_id
                       and (as_of is None or d["date"] <= as_of)], key=lambda d: d["date"], reverse=True)

    def changes(self, patient_id, as_of=None):
        fields = {}
        for p in self.scope(patient_id, as_of=as_of):
            if p.field:
                fields.setdefault(p.field, []).append(p)
        changes = []
        for field, entries in fields.items():
            ordered = sorted(entries, key=lambda p: (p.date, p.id), reverse=True)
            if len({p.value for p in ordered}) > 1:
                changes.append({"field": field, "latest": ordered[0].public(),
                                "previous": [p.public() for p in ordered[1:]],
                                "message": "Recorded values differ. The latest entry does not resolve the discrepancy."})
        return changes
