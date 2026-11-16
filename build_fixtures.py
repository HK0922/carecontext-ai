"""Build author-written fictional records; no patient data or medical guidance."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
patients = [
    {"id": "demo-001", "name": "Maya Chen", "initials": "MC", "age": 62, "label": "Wound clinic follow-up", "focus": "Transport and supply coordination", "updated": "2026-05-14", "color": "sage", "questions": ["What is blocking Maya's follow-up?", "What allergy information changed?", "What is the recorded appointment date?", "Is an HbA1c result available?"]},
    {"id": "demo-002", "name": "Oliver Brooks", "initials": "OB", "age": 48, "label": "Referral coordination", "focus": "Referral and contact reconciliation", "updated": "2026-05-13", "color": "sand", "questions": ["What is the referral status?", "What contact attempts are documented?", "What allergy is recorded?", "What supply delivery is documented?"]},
    {"id": "demo-003", "name": "Amara Lewis", "initials": "AL", "age": 71, "label": "Home visit coordination", "focus": "Visit scheduling and record changes", "updated": "2026-05-15", "color": "lavender", "questions": ["When is the home appointment?", "What measurements changed?", "What medication is recorded?", "What is blocking the visit?"]},
]
documents = []
def doc(id, patient, title, date, kind, author, entries):
    documents.append({"id": id, "patient_id": patient, "title": title, "date": date,
                      "kind": kind, "author": author, "synthetic": True,
                      "entries": [{"text": e[0], "tags": e[1], **({"field": e[2], "value": e[3]} if len(e)>2 else {})} for e in entries]})

doc('MC-01','demo-001','Intake note','2026-05-06','record','Synthetic intake coordinator',[
 ('Maya Chen is enrolled in the fictional wound-clinic follow-up pathway.', ['wound','intake']),
 ('The intake allergy field lists no known drug allergies.', ['allergy','change'], 'allergy','none recorded'),
 ('The medication list records metformin; dose and frequency are not included in this sample.', ['medication'], 'medication','metformin'),
 ('The intake wound measurement is recorded as 2.4 cm by 1.8 cm.', ['wound','measurement'], 'measurement','2.4 x 1.8 cm'),
])
doc('MC-02','demo-001','Nursing follow-up','2026-05-10','record','Synthetic nursing note',[
 ('The nursing allergy field lists a patient-reported penicillin allergy with rash; reconciliation remains open.', ['allergy','change','barrier'], 'allergy','penicillin rash'),
 ('The recorded wound measurement is 2.2 cm by 1.7 cm; no clinical interpretation is included.', ['wound','measurement','change'], 'measurement','2.2 x 1.7 cm'),
 ('The dressing supply request was sent to the fictional supplier on May 10.', ['dressing','supply']),
])
doc('MC-03','demo-001','Scheduling update','2026-05-12','record','Synthetic scheduling team',[
 ('The follow-up appointment is booked for May 18, 2026 at 10:30 AM.', ['appointment'], 'appointment','2026-05-18 10:30'),
 ('Transport for the follow-up appointment has not been confirmed; the transport coordinator owns the callback.', ['transport','appointment','barrier']),
 ('A contact attempt on May 12 reached voicemail; no return call is documented in this note.', ['contact','barrier']),
])
doc('MC-04','demo-001','Coordination handoff','2026-05-14','record','Synthetic care coordinator',[
 ('Transport confirmation remains pending and may prevent attendance at the follow-up appointment.', ['transport','barrier','appointment']),
 ('The dressing supply delivery date is still unconfirmed; the care coordinator is awaiting a supplier reply.', ['dressing','supply','barrier']),
 ('Allergy reconciliation is assigned to the clinical team and has not been marked complete.', ['allergy','barrier']),
])
doc('OB-01','demo-002','Referral intake','2026-05-04','record','Synthetic referral coordinator',[
 ('Oliver Brooks has a referral request for the fictional wound review clinic.', ['referral','wound']),
 ('The referral packet is missing the referring clinician signature.', ['referral','barrier']),
 ('The allergy list records latex sensitivity.', ['allergy'], 'allergy','latex sensitivity'),
])
doc('OB-02','demo-002','Telephone log','2026-05-08','record','Synthetic contact team',[
 ('A contact call on May 8 confirmed the callback number in the demo record.', ['contact']),
 ('The referring office was asked to send the signed referral; no signed copy is recorded in this log.', ['referral','barrier']),
])
doc('OB-03','demo-002','Referral reconciliation','2026-05-13','record','Synthetic referral coordinator',[
 ('The signed referral arrived on May 13 and the referral packet is now recorded as complete.', ['referral'], 'referral','complete'),
 ('An appointment slot has not yet been assigned; scheduling owns the next contact attempt.', ['appointment','contact','barrier']),
 ('The record contains no completed supply-delivery confirmation.', ['supply','delivery']),
])
doc('AL-01','demo-003','Home care intake','2026-05-05','record','Synthetic home care team',[
 ('Amara Lewis is registered for a fictional home wound-review visit.', ['wound','appointment']),
 ('The medication list records amlodipine; no dose or frequency is supplied in this sample.', ['medication'], 'medication','amlodipine'),
 ('The intake measurement is recorded as 3.0 cm by 2.1 cm.', ['wound','measurement','change'], 'measurement','3.0 x 2.1 cm'),
])
doc('AL-02','demo-003','Visit scheduling','2026-05-09','record','Synthetic scheduling team',[
 ('The home appointment was initially recorded for May 16, 2026 at 9:00 AM.', ['appointment','change'], 'appointment','2026-05-16 09:00'),
 ('Building access instructions are missing; the coordinator requested a callback.', ['access','contact','barrier']),
])
doc('AL-03','demo-003','Updated home visit note','2026-05-15','record','Synthetic care coordinator',[
 ('The home appointment is now recorded for May 19, 2026 at 2:00 PM, replacing the earlier scheduling entry.', ['appointment','change'], 'appointment','2026-05-19 14:00'),
 ('Building access instructions were confirmed on May 15; the access task is marked complete.', ['access']),
 ('The latest recorded measurement is 2.8 cm by 2.0 cm; the sample does not interpret the change.', ['wound','measurement','change'], 'measurement','2.8 x 2.0 cm'),
])
doc('REF-01',None,'Demo record review rules','2026-05-01','reference','CareContext fixture authors',[
 ('In this fictional workflow, a review note links each extracted statement to its original dated source.', ['workflow','source','review']),
 ('When recorded values differ, the reviewer preserves both dated entries and assigns reconciliation to a human owner.', ['workflow','change','reconciliation']),
 ('A missing record is described as unavailable evidence and is not converted into a negative clinical finding.', ['workflow','missing','evidence']),
])
doc('REF-02',None,'Demo coordination checklist','2026-05-01','reference','CareContext fixture authors',[
 ('The fictional scheduling checklist tracks appointment date, contact attempts, transport confirmation, and the owner of each open task.', ['workflow','appointment','contact','transport']),
 ('The fictional supply checklist tracks request date, supplier reply, delivery confirmation, and the responsible coordinator.', ['workflow','supply','delivery']),
])
payload = {"version":"1.0", "synthetic":True, "description":"Entirely fictional teaching records and author-written workflow references. Not clinical guidance.", "patients":patients,"documents":documents}
(root/'carecontext/data/cases.json').write_text(json.dumps(payload,indent=2)+'\n')
print(f'Wrote {len(patients)} cases, {len(documents)} documents')
