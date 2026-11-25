"""SQLite snapshots preserve exactly what was reviewed. Queries use parameters."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL, review TEXT)')

    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def save(self, answer):
        with self.connect() as db:
            db.execute('INSERT INTO runs (id,patient_id,created_at,payload) VALUES (?,?,?,?)',
                       (answer['id'],answer['patient_id'],answer['created_at'],json.dumps(answer)))

    def get(self, run_id):
        with self.connect() as db:
            row = db.execute('SELECT payload,review FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None: raise KeyError(run_id)
        return {**json.loads(row['payload']), 'review': json.loads(row['review']) if row['review'] else None}

    def history(self, patient_id):
        with self.connect() as db:
            rows = db.execute('SELECT id,created_at,payload,review FROM runs WHERE patient_id=? ORDER BY created_at DESC LIMIT 30',(patient_id,)).fetchall()
        return [{"id":r['id'],"created_at":r['created_at'],"question":json.loads(r['payload'])['question'],
                 "status":json.loads(r['payload'])['status'],"review":json.loads(r['review']) if r['review'] else None} for r in rows]

    def review(self, run_id, decision, note):
        review = {"decision":decision,"note":note,"saved_at":datetime.now(timezone.utc).isoformat(),
                  "label":"Human annotation; not source-verified evidence"}
        with self.connect() as db:
            cur = db.execute('UPDATE runs SET review=? WHERE id=?',(json.dumps(review),run_id))
            if cur.rowcount == 0: raise KeyError(run_id)
        return review

    def delete(self, patient_id):
        with self.connect() as db:
            return db.execute('DELETE FROM runs WHERE patient_id=?',(patient_id,)).rowcount

def markdown(answer, patient):
    lines = ['# CareContext evidence review', '', '**Synthetic demonstration only. Not clinical advice.**', '',
             f"Case: {patient['name']} ({patient['id']})", f"Question: {answer['question']}",
             f"Run: {answer['id']}", f"Created: {answer['created_at']}",
             f"Mode: {answer['mode']}", f"Record cutoff: {answer['as_of'] or 'all available dates'}", '',
             answer['summary'], '', '## Source excerpts', '']
    for e in answer['evidence']:
        lines += [f"[{e['citation']}] {e['text']}", f"Source: {e['id']} | {e['title']} | {e['date']} | {e['kind']}", '']
    if answer['warnings']:
        lines += ['## Differing recorded values','']
        for w in answer['warnings']:
            lines += [f"{w['field']}: {w['message']}"]
            for p in [w['latest'],*w['previous']]: lines += [f"- {p['date']}: {p['text']} ({p['id']})"]
    if answer.get('review'):
        lines += ['', '## Human review', answer['review']['label'], answer['review']['decision'], answer['review']['note']]
    lines += ['', '## Verification boundary', answer['verification']['limit'], f"Corpus SHA-256: {answer['corpus_sha256']}"]
    return '\n'.join(lines)+'\n'
