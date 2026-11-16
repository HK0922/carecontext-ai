import json
import httpx
import pytest
from carecontext.providers import OpenAISelector,ProviderError
from carecontext.retrieval import rank

def selection_transport(payload,status='completed'):
    def handler(request):
        body=json.loads(request.content)
        assert body['store'] is False
        assert body['text']['format']['strict'] is True
        assert body['max_output_tokens']==600
        return httpx.Response(200,json={'status':status,'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(payload)}]}]})
    return httpx.MockTransport(handler)

def candidates(catalog): return rank('What allergy is recorded?',catalog.scope('demo-001'),catalog.patient('demo-001'))

def test_provider_validates_and_deduplicates(catalog):
    p=OpenAISelector('test','test-model',selection_transport({'passage_ids':['MC-01:2','MC-01:2'],'abstain':False}))
    assert p.select('What allergy?',candidates(catalog))==['MC-01:2']

@pytest.mark.parametrize('payload',[
    {'passage_ids':['OB-01:3'],'abstain':False},
    {'passage_ids':['made-up'],'abstain':False},
    {'passage_ids':['MC-01:2'],'abstain':'false'},
    {'passage_ids':None,'abstain':False},
    {'passage_ids':[],'abstain':False,'free_text':'invented claim'},
])
def test_provider_rejects_bad_contract(catalog,payload):
    with pytest.raises(ProviderError):OpenAISelector('test','model',selection_transport(payload)).select('allergy',candidates(catalog))

def test_provider_incomplete_response(catalog):
    with pytest.raises(ProviderError):OpenAISelector('test','model',selection_transport({},'incomplete')).select('allergy',candidates(catalog))

def test_provider_http_error_does_not_expose_secret(catalog):
    t=httpx.MockTransport(lambda r:httpx.Response(401,text='secret detail'))
    with pytest.raises(ProviderError) as e:OpenAISelector('SECRET','model',t).select('allergy',candidates(catalog))
    assert 'SECRET' not in str(e.value) and 'secret detail' not in str(e.value)
