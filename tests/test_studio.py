"""Contracts for upload, scope, evidence presentation and optional AI response validation."""
import io
import json
import zipfile
import httpx
import pytest
from carecontext.studio_ingest import extract_document, DocumentError
from carecontext.studio_chat import GroundedExplainer, answer_question
from carecontext.providers import ProviderError

SAMPLE_TEXT = ("Fictional test record, dated 2026-08-15. Prior allergy entry was unknown.\n"
               "On 2026-08-19, fictional nurse noted penicillin rash reported by the fictional patient.\n"
               "The follow-up visit is not confirmed.")


def upload(client, filename='fictional.txt', body=SAMPLE_TEXT.encode()):
    return client.post('/api/studio/ingest?name='+filename,
                       content=body,headers={'Content-Type':'application/octet-stream'})


def test_studio_home_and_classic_available(client):
    assert 'Keep the evidence' in client.get('/').text
    assert '/studio.js' in client.get('/').text
    assert 'Research prototype' in client.get('/classic').text
    assert client.get('/api/studio/config').json()['synthetic_only'] is True


def test_upload_and_citation(client):
    uploaded=upload(client)
    assert uploaded.status_code==200
    result=uploaded.json()
    assert result['name']=='fictional.txt'
    assert result['passages'][0]['source_id']
    assert result['passages'][0]['text'].startswith('Fictional')
    data={'question':'What allergy was recorded?','role':'patient','mode':'local','synthetic_ack':True,
          'snippets':result['passages']}
    answer=client.post('/api/studio/answer',json=data)
    assert answer.status_code==200
    a=answer.json()
    assert a['mode']=='local' and a['status']=='evidence_found'
    assert a['citations'][0]['source_name']=='fictional.txt'
    assert 'Not clinically' not in a['answer'] # No diagnostic claims fabricated
    assert a['retrieval'][0]['matched_terms']


def test_disclaimer_enforced(client):
    record=upload(client).json()['passages']
    response=client.post('/api/studio/answer',json={'question':'What was noted?','snippets':record,'synthetic_ack':False})
    assert response.status_code==422


def test_no_citations_for_unrelated_request(client):
    excerpts=upload(client).json()['passages']
    r=client.post('/api/studio/answer',json={'question':'What is the spaceship engine type?','snippets':excerpts,'synthetic_ack':True})
    assert r.json()['status']=='insufficient_evidence'
    assert r.json()['citations']==[]


def test_out_of_scope_medical_advice(client):
    result=upload(client).json()['passages']
    r=client.post('/api/studio/answer',json={'question':'What medication should I take?','snippets':result,'synthetic_ack':True})
    assert r.json()['status']=='outside_scope'
    assert r.json()['citations']==[]


def test_invalid_uploads_rejected(client):
    assert upload(client,'test.pdf',b'not a real PDF').status_code==422
    assert upload(client,'sample.json',b'{}').status_code==422
    assert upload(client,'large.txt',b'c'* (3*1024*1024 +1)).status_code==422
    assert upload(client,'empty.txt',b'').status_code==422


def test_docx_parsing():
    xml='''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Fictional medication list</w:t></w:r></w:p><w:p><w:r><w:t>Follow-up is pending</w:t></w:r></w:p></w:body></w:document>'''
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:z.writestr('word/document.xml',xml)
    doc=extract_document('fake.docx',out.getvalue())
    assert 'Fictional medication list\nFollow-up is pending' in doc['passages'][0]['text']


def test_docx_expansion_limit():
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('word/document.xml','x'*(9*1024*1024))
    with pytest.raises(DocumentError):extract_document('huge.docx',out.getvalue())


def test_empty_pdf_requires_text():
    from pypdf import PdfWriter
    out=io.BytesIO();writer=PdfWriter();writer.add_blank_page(220,220);writer.write(out)
    with pytest.raises(DocumentError,match='No readable text'):
        extract_document('scan.pdf',out.getvalue())


def test_duplicate_source_ids_rejected(client):
    snippets=upload(client).json()['passages'];records=snippets+snippets
    r=client.post('/api/studio/answer',json={'question':'What allergy?','synthetic_ack':True,'snippets':records})
    assert r.status_code==422


def test_optional_model_requires_config(client):
    snippets=upload(client).json()['passages']
    r=client.post('/api/studio/answer',json={'question':'What allergy?','mode':'model','synthetic_ack':True,'snippets':snippets})
    assert r.status_code==502 and 'configured' in r.json()['detail']


def responses(body):
    return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(body)}]}]}


def test_model_structured_citations():
    captured=[]
    def handler(request):
        payload=json.loads(request.content);captured.append(payload)
        return httpx.Response(200,json=responses({'answer':'The fictional report lists a rash after penicillin.','citation_ids':['SRC-1'],'uncertainty':'Review the original file.','abstain':False}))
    model=GroundedExplainer('test-key','test-model',transport=httpx.MockTransport(handler))
    passage={'source_id':'SRC-1','source_name':'fictional.txt','page':1,'text':'The record documents a penicillin rash.'}
    result=answer_question('What penicillin allergy was documented?','patient',[passage],mode='model',explainer=model)
    assert result['status']=='grounded_draft' and len(result['citations'])==1
    assert captured[0]['store'] is False
    assert captured[0]['text']['format']['strict'] is True


def test_model_rejects_hallucinated_source():
    def handler(request):
        return httpx.Response(200,json=responses({'answer':'No','citation_ids':['BAD-ID'],'uncertainty':'','abstain':False}))
    model=GroundedExplainer('test-key','test-model',transport=httpx.MockTransport(handler))
    with pytest.raises(ProviderError,match='nonexistent'):
        model.explain('What allergy?','patient',[{'source_id':'SRC-1','source_name':'test','page':1,'text':'Allergy test.'}],[])


def test_session_required(client):
    client.headers.pop('X-CareContext-Session')
    assert upload(client).status_code==403


def test_question_validation(client):
    excerpts=extract_document('fake.txt',SAMPLE_TEXT.encode())['passages']
    payload={'question':'This is a question','snippets':excerpts,'synthetic_ack':True}
    assert client.post('/api/studio/answer',json={**payload,'role':'superdoctor'}).status_code==422
    assert client.post('/api/studio/answer',json={**payload,'question':'A'*500}).status_code==422


def test_real_pdf_fixture(client):
    from pathlib import Path
    import carecontext
    fixture=Path(carecontext.__file__).parent/'web/fictional_lab_sample.pdf'
    r=upload(client,'fictional_lab_sample.pdf',fixture.read_bytes())
    assert r.status_code==200
    data=r.json()
    assert data['pages']==1
    assert 'HEMOGLOBIN' in data['passages'][0]['text']
    assert '13.4' in data['passages'][0]['text']

