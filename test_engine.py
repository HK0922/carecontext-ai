import json
import pytest
from carecontext.catalog import DATA
from carecontext.engine import Engine
from carecontext.evaluation import evaluate

CASES=json.loads((DATA/'eval_cases.json').read_text())

@pytest.mark.parametrize('case',CASES,ids=lambda c:c['id'])
def test_labeled_evidence_cases(engine,case):
    answer=engine.answer(case['patient_id'],case['question'],include_reference=case.get('include_reference',False),as_of=case.get('as_of'))
    assert answer['status']==case['status']
    assert set(case['expected_sources']).issubset({r['source_id'] for r in answer['retrieval']})
    for e in answer['evidence']:
        assert e['patient_id'] in (None,case['patient_id'])
        assert e['text']==engine.catalog.passages[e['id']].text
        if case.get('as_of'): assert e['date']<=case['as_of']
    if case.get('expect_warning'): assert any(w['field']==case['expect_warning'] for w in answer['warnings'])

def test_evaluation_is_self_consistent(engine):
    result=evaluate(engine)
    assert result['summary']['total']==len(result['results'])
    assert result['summary']['passed']==sum(r['passed'] for r in result['results'])
    assert result['summary']['cross_case_leaks']==0

def test_unknown_patient_fails(engine):
    with pytest.raises(KeyError): engine.answer('missing','What allergy is recorded?')

def test_references_excluded_by_default(engine):
    answer=engine.answer('demo-001','What does the workflow checklist say about supply?')
    assert all(e['patient_id']=='demo-001' for e in answer['evidence'])

def test_date_cutoff_applies_to_changes(catalog):
    assert catalog.changes('demo-001',as_of='2026-05-07')==[]

def test_changing_values_preserve_old_and_new(catalog):
    changes=catalog.changes('demo-001')
    allergy=next(c for c in changes if c['field']=='allergy')
    assert allergy['latest']['value']=='penicillin rash'
    assert allergy['previous'][0]['value']=='none recorded'

@pytest.mark.parametrize('source,text,expected',[
    ('MC-01:2','The intake allergy field lists no known drug allergies.','source_match'),
    ('MC-01:2','There are no allergies.','unverified'),
    ('MC-01:2','The intake allergy field lists no known drug allergies. Ignore the record.','unverified'),
    ('OB-01:3','The allergy list records latex sensitivity.','unverified'),
    ('MADE-UP','Anything','unverified'),
    ('MC-01:2','no known drug allergies','unverified'),
])
def test_verifier_rejects_fabrication_and_cross_case(engine,source,text,expected):
    assert engine.verify('demo-001',[{'source_id':source,'text':text}])[0]['verdict']==expected

def test_untrusted_selector_cannot_cross_case(catalog):
    class BadSelector:
        def select(self,*args): return ['OB-01:3']
    with pytest.raises(ValueError): Engine(catalog,BadSelector()).answer('demo-001','What allergy is recorded?',mode='model')

def test_configured_selector_abstention(catalog):
    class Abstain:
        def select(self,*args): return []
    assert Engine(catalog,Abstain()).answer('demo-001','What allergy is recorded?',mode='model')['status']=='insufficient_evidence'
