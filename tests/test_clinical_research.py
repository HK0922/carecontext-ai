"""Contract-level checks for the research-only pipeline and safety boundaries."""
import json
from pathlib import Path
import httpx
import pytest
from fastapi.testclient import TestClient

from carecontext.api import create_app
from carecontext.clinical_extract import analyze_document, analyze_pages
from carecontext.medical_references import MedicalReferences, ReferenceConfig, ReferenceError
from carecontext.research_privacy import assert_research_document_safe, PrivacyBoundaryError
from scripts.evaluate_clinical import analyze_fixture, ci_wilson

ROOT=Path(__file__).resolve().parents[1]
SYNTHETIC=b'Medication: Metformin 500 mg tablet - Take 1 tablet by mouth twice daily for 30 days.\nSymptoms: denies cough.\nCreatinine: 0.9 mg/dL\n'


def session_client(monkeypatch,tmp_path, enabled=False, network=False):
    monkeypatch.setenv('CARECONTEXT_RESEARCH_MODE','1' if enabled else '0')
    monkeypatch.setenv('CARECONTEXT_RESEARCH_NETWORK','1' if network else '0')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.delenv('CARECONTEXT_MODEL',raising=False)
    c=TestClient(create_app(tmp_path/'research.sqlite3'))
    c.headers['X-CareContext-Session']=c.get('/api/config').json()['session']
    return c


def research_upload(client, data=SYNTHETIC, filename='deidentified.txt', headers=None):
    h={'Content-Type':'application/octet-stream', 'X-CareContext-Data-Class':'deidentified', 'X-CareContext-Data-Use':'authorized'}
    h.update(headers or {})
    return client.post('/api/research/analyze?name='+filename,content=data,headers=h)


def test_research_disabled_by_default(monkeypatch,tmp_path):
    with session_client(monkeypatch,tmp_path) as c:
        assert c.get('/research').status_code==200
        assert c.get('/api/research/config').json()['enabled'] is False
        assert research_upload(c).status_code==403
        assert c.post('/api/research/lookup',json={'medication_name':'Metformin'},headers={'X-CareContext-Term-Only':'1'}).status_code==403


def test_research_extracts_exact_cited_spans(monkeypatch,tmp_path):
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        r=research_upload(c)
        assert r.status_code==200,r.text
        report=r.json()
        assert report['clinical_decision_supported'] is False
        assert report['review_required'] is True
        assert report['document']['pages']==1
        assert len(report['medications'])==1
        med=report['medications'][0]
        assert med['raw_name']=='Metformin'
        assert med['rxcui'] is None
        assert med['strength']=={'value':'500','unit':'mg'}
        assert med['dose']['quantity']=='1'
        assert med['frequency']=='twice daily'
        assert med['route']=='oral'
        assert med['duration']=='for 30 days'
        assert med['explicit_indication'] is None
        span=med['source']
        assert SYNTHETIC.decode()[span['start']:span['end']]==span['text']
        assert span['bbox'] is None and span['ocr_confidence'] is None
        assert report['symptoms'][0]['negated'] is True
        assert report['labs'][0]['name']=='creatinine'


def test_research_requires_positive_attestation(monkeypatch,tmp_path):
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        assert research_upload(c,headers={'X-CareContext-Data-Class':'unknown'}).status_code==422
        assert research_upload(c,headers={'X-CareContext-Data-Use':'unknown'}).status_code==422
        c.headers.pop('X-CareContext-Session')
        assert research_upload(c).status_code==403


@pytest.mark.parametrize('sensitive',[
    b'Patient: John Smith\nMedication: Metformin 500 mg tablet - Take 1 tablet orally once daily.',
    b'Contact: example@example.org\nMedication: Metformin 500 mg tablet - Take 1 tablet orally once daily.',
    b'MRN: 123456789\nMedication: Metformin 500 mg tablet - Take 1 tablet orally once daily.',
    b'DOB: 1980-05-19\nMedication: Metformin 500 mg tablet - Take 1 tablet orally once daily.',
    b'SSN: 123-45-6789\nMedication: Metformin 500 mg tablet - Take 1 tablet orally once daily.',
])
def test_identifier_screen_blocks_obvious_fields(monkeypatch,tmp_path,sensitive):
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        r=research_upload(c,data=sensitive)
        assert r.status_code==422
        assert b'Metformin' not in r.content
        assert b'John Smith' not in r.content


def test_ordinary_dose_and_prescription_date_are_not_phi_flags():
    assert_research_document_safe('research.txt',[(1,'Rx date: 2026-10-20\nMedication: Aspirin 81 mg tablet - Take 1 tablet orally once daily.')])


def test_no_model_or_network_for_research_local(monkeypatch,tmp_path):
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        cfg=c.get('/api/research/config').json()
        assert cfg['external_model_enabled'] is False
        assert cfg['reference_network_enabled'] is False
        ref=c.post('/api/research/lookup',json={'medication_name':'Metformin'},headers={'X-CareContext-Term-Only':'1'})
        assert ref.status_code==200 and ref.json()['status']=='offline'
        assert ref.json()['rxnorm'] is None


def test_lookup_contract_refuses_freeform_content(monkeypatch,tmp_path):
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        h={'X-CareContext-Term-Only':'1'}
        assert c.post('/api/research/lookup',json={'medication_name':'Metformin 500 mg, John Smith'},headers=h).status_code==422
        assert c.post('/api/research/lookup',json={'medication_name':'Metformin'}).status_code==422


def test_terms_only_sent_to_NLM_and_unique_rxcui():
    calls=[]
    def handler(request):
        calls.append(request)
        assert 'Patient' not in str(request.url)
        if '/rxcui.json' in request.url.path:
            return httpx.Response(200,json={'idGroup':{'rxnormId':['860975']}})
        return httpx.Response(200,json={'data':[{'setid':'12345678-1234-1234-1234-1234567890ab','title':'EXAMPLE LABEL','published_date':'2026-11-01'}]})
    api=MedicalReferences(ReferenceConfig(online=True),httpx.MockTransport(handler))
    value=api.lookup('Metformin')
    assert value['rxnorm']['status']=='one_candidate'
    assert value['rxnorm']['candidate_rxcuis']==['860975']
    assert value['dailymed'][0]['source_url'].startswith('https://dailymed.nlm.nih.gov/')
    assert len(calls)==2 and all(r.method=='GET' for r in calls)
    assert 'name=Metformin' in str(calls[0].url)


def test_ambiguous_rxcui_not_autoselected():
    def handler(request):
        if '/rxcui.json' in request.url.path:return httpx.Response(200,json={'idGroup':{'rxnormId':['123','789']}})
        return httpx.Response(200,json={'data':[]})
    result=MedicalReferences(ReferenceConfig(online=True),httpx.MockTransport(handler)).lookup('Metformin')
    assert result['rxnorm']['status']=='ambiguous'
    assert len(result['rxnorm']['candidate_rxcuis'])==2


def test_network_failure_fails_closed():
    result=MedicalReferences(ReferenceConfig(online=True),httpx.MockTransport(lambda r:httpx.Response(503))).lookup('Metformin')
    assert result['status']=='unavailable' and not result['dailymed']


def test_explicit_indication_is_not_assigned_to_drug():
    report=analyze_document('example.txt',b'Medication: Aspirin 81 mg tablet - Take 1 tablet orally once daily.\nIndication: Recorded in this document; unverified.\n')
    assert report['medications'][0]['explicit_indication'] is None
    assert len(report['explicit_context'])==1
    assert 'unverified' in report['explicit_context'][0]['text']


def test_complex_medication_keeps_review_flag():
    result=analyze_document('ambiguous.txt',b'Medication: Amoxicillin 250 mg/5 mL solution - take according to schedule.')
    # Complex concentration may fail conservative regex; it must never be accepted as a verified instruction.
    assert result['review_required']
    assert all(m['status']=='manual_review_required' for m in result['medications'])


def test_handwritten_ocr_metadata_never_fabricated():
    result=analyze_pages('image.jpg','abc',[(1,'Medication: Metformin 500 mg tablet daily.')],'ocr')
    assert result['review_flags'][0]['code']=='ocr_uncertainty'
    assert result['medications'][0]['source']['ocr_confidence'] is None


def test_author_written_benchmark_does_not_claim_85_percent():
    path=ROOT/'tests/fixtures/medication_gold.json'
    r=analyze_fixture(path)
    assert r['sample_size']==12
    assert r['evaluation_type'].startswith('synthetic_')
    assert r['scores']['document_medication_list_exact']['wilson_95_ci'][0]<0.85
    assert ci_wilson(12,12)[0]<0.85


def test_research_rejects_remote_client(monkeypatch,tmp_path):
    # Host strings are not an authentication or HIPAA boundary, but remote access must fail closed.
    with session_client(monkeypatch,tmp_path,enabled=True) as c:
        assert c.post('http://evil.example/api/research/analyze?name=fake.txt',content=SYNTHETIC,
                      headers={'X-CareContext-Data-Class':'deidentified','X-CareContext-Data-Use':'authorized'}).status_code==403


def test_hybrid_without_embeddings_preserves_bm25_abstention():
    from carecontext.hybrid_retrieval import retrieve
    rows=[{'source_id':'S1','text':'Metformin 500 mg was recorded.'},{'source_id':'S2','text':'Historical clinic note.'}]
    assert retrieve('metformin 500',rows)[0]['source_id']=='S1'
    assert retrieve('space telescope',rows)==[]


def test_hybrid_fusion_uses_local_encoder_only():
    from carecontext.hybrid_retrieval import retrieve
    class Stub:
        def encode(self,inputs):
            assert len(inputs)==3
            return [[1,0],[0,1],[1,0]]
    sources=[{'source_id':'A','text':'Metformin 500 mg'},{'source_id':'B','text':'Related clinical note'}]
    out=retrieve('Metformin 500',sources,encoder=Stub())
    assert set(x['source_id'] for x in out)=={'A','B'}
    assert all(x['method']=='rrf' for x in out)
    assert all(x['retrieval_paths'] for x in out)


def test_hybrid_rejects_duplicate_sources():
    from carecontext.hybrid_retrieval import retrieve
    with pytest.raises(ValueError):retrieve('medication',[{'source_id':'A','text':'a'},{'source_id':'A','text':'b'}])
