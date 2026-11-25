import pytest

def ask(client,**kwargs):
    return client.post('/api/query',json={'patient_id':'demo-001','question':'What allergy is recorded?',**kwargs})

def test_full_review_lifecycle(client):
    answer=ask(client).json();id=answer['id']
    assert answer['evidence']
    review=client.post(f'/api/runs/{id}/review',json={'decision':'needs_followup','note':'Reconcile the two allergy entries.'})
    assert review.status_code==200
    loaded=client.get(f'/api/runs/{id}').json()
    assert loaded['review']['note']=='Reconcile the two allergy entries.'
    export=client.get(f'/api/runs/{id}/export')
    assert 'MC-01:2' in export.text and 'Reconcile the two allergy entries.' in export.text
    assert client.get(f'/api/runs/{id}/export?format=json').json()==loaded
    assert len(client.get('/api/history/demo-001').json())==1
    assert client.delete('/api/history/demo-001').json()['deleted']==1
    assert client.get(f'/api/runs/{id}').status_code==404

@pytest.mark.parametrize('payload',[
    {'question':''},{'question':'   '},{'question':'x'*601},{'mode':'invented'},
    {'as_of':'nonsense'},{'extra':'unknown'},
])
def test_input_validation(client,payload): assert ask(client,**payload).status_code==422

def test_unknown_patient(client): assert ask(client,patient_id='missing').status_code==404
def test_model_requires_configuration(client): assert ask(client,mode='model').status_code==409
def test_health(client): assert client.get('/api/health').json()['synthetic_only'] is True
def test_self_contained_api_docs(client):
    r=client.get('/docs')
    assert r.status_code==200 and 'X-CareContext-Session' in r.text
    assert 'cdn.jsdelivr' not in r.text
    assert '/api/query' in client.get('/openapi.json').json()['paths']
def test_ui_served(client):
    response=client.get('/')
    assert response.status_code==200 and 'CareContext' in response.text
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
def test_security_headers(client):
    r=client.get('/api/patients')
    assert r.headers['x-content-type-options']=='nosniff'
    assert r.headers['cache-control']=='no-store'
def test_sources_are_scoped(client):
    assert all(s['patient_id']=='demo-001' for s in client.get('/api/sources?patient_id=demo-001').json())
def test_sources_unknown_case(client): assert client.get('/api/sources?patient_id=nope').status_code==404
def test_mutation_requires_session(client):
    client.headers.pop('X-CareContext-Session')
    assert ask(client).status_code==403
def test_cross_origin_rejected(client):
    assert client.post('/api/query',json={'patient_id':'demo-001','question':'What allergy?'},headers={'Origin':'https://evil.example'}).status_code==403
def test_oversized_stream(client):
    r=client.post('/api/query',content=b'x'*16001,headers={'Content-Type':'application/json'})
    assert r.status_code==413
def test_review_unknown_run(client):
    assert client.post('/api/runs/missing/review',json={'decision':'reviewed'}).status_code==404
def test_evaluation_endpoint(client):
    r=client.post('/api/evaluations')
    assert r.status_code==200 and r.json()['summary']['total']==24
def test_verification_endpoint(client):
    r=client.post('/api/verify',json={'patient_id':'demo-001','claims':[{'source_id':'MC-01:2','text':'A made-up allergy'}]})
    assert r.json()['results'][0]['verdict']=='unverified'
def test_static_traversal(client):
    assert client.get('/..%2F..%2F.env').status_code==404
def test_extra_review_fields_rejected(client):
    assert client.post('/api/runs/missing/review',json={'decision':'reviewed','owner':'admin'}).status_code==422
