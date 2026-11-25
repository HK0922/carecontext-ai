"""Labeled, deliberately small fixture evaluation; not a clinical benchmark."""
from datetime import datetime, timezone
import json
from .catalog import DATA

def evaluate(engine):
    cases=json.loads((DATA/'eval_cases.json').read_text())
    results=[]; expected=found=leaks=excerpts=matched=0
    for case in cases:
        answer=engine.answer(case['patient_id'],case['question'],include_reference=case.get('include_reference',False),as_of=case.get('as_of'))
        sources={r['source_id'] for r in answer['retrieval']}
        required=set(case['expected_sources'])
        expected+=len(required);found+=len(required & sources)
        case_leaks=sum(e['patient_id'] not in (None,case['patient_id']) for e in answer['evidence']);leaks+=case_leaks
        date_ok=all(not case.get('as_of') or e['date']<=case['as_of'] for e in answer['evidence'])
        exact=all(engine.catalog.passages[e['id']].text==e['text'] for e in answer['evidence'])
        excerpts+=len(answer['evidence']);matched+=sum(engine.catalog.passages[e['id']].text==e['text'] for e in answer['evidence'])
        warning_ok=not case.get('expect_warning') or any(w['field']==case['expect_warning'] for w in answer['warnings'])
        passed=answer['status']==case['status'] and required.issubset(sources) and not case_leaks and date_ok and exact and warning_ok
        results.append({'id':case['id'],'category':case['category'],'question':case['question'],
                        'patient_id':case['patient_id'],'expected_status':case['status'],'actual_status':answer['status'],
                        'expected_sources':sorted(required),'retrieved_sources':sorted(sources),'passed':bool(passed)})
    return {'created_at':datetime.now(timezone.utc).isoformat(),'mode':'local','corpus_sha256':engine.catalog.digest,
            'summary':{'total':len(results),'passed':sum(r['passed'] for r in results),'retrieval_recall_at_6':round(found/expected,4) if expected else 0,
                       'cross_case_leaks':leaks,'exact_source_match_rate':matched/excerpts if excerpts else 0},
            'limitations':'Author-written fixture checks on 3 synthetic cases. Exact matches are enforced by construction; they do not measure clinical truth. No held-out clinical dataset or live model evaluation.',
            'results':results}
