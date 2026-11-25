import httpx
import pytest
from fastapi.testclient import TestClient
from carecontext.api import create_app
from carecontext.literature import PubMed,LiteratureError

XML=b'''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>Fictional <i>example</i> trial</ArticleTitle><Journal><Title>Test journal</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal><AuthorList><Author><ForeName>Test</ForeName><LastName>Author</LastName></Author></AuthorList><Abstract><AbstractText Label="RESULTS">Synthetic test fixture, not medical evidence.</AbstractText></Abstract><PublicationTypeList><PublicationType>Randomized Controlled Trial</PublicationType></PublicationTypeList></Article><CommentsCorrectionsList><CommentsCorrections RefType="ErratumIn"><PMID>999</PMID></CommentsCorrections></CommentsCorrectionsList></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.000/test</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''
def service(xml=XML,ids=None):
 def handler(r):
  if 'esearch' in str(r.url):return httpx.Response(200,json={'esearchresult':{'count':'1','idlist':['123'] if ids is None else ids,'querytranslation':'test'}})
  return httpx.Response(200,content=xml)
 return PubMed(httpx.MockTransport(handler))
def test_source_parsing():
 p=service().search('test')['articles'][0]
 assert p['title']=='Fictional example trial'
 assert p['abstract'][0]['label']=='RESULTS'
 assert p['url']=='https://pubmed.ncbi.nlm.nih.gov/123/'
 assert p['notices'][0]['type']=='ErratumIn'
def test_empty_search():assert service(ids=[]).search('test')['status']=='no_results'
def test_cached_result():
 s=service();assert s.search('test')['cached'] is False;assert s.search('test')['cached'] is True
def test_filters_visible():
 r=service(ids=[]).search('wound','review',2020)
 assert 'systematic review[Publication Type]' in r['executed_query'] and '2020/01/01' in r['executed_query']
def test_missing_abstract():assert service(XML.replace(b'<Abstract>',b'<Unused>').replace(b'</Abstract>',b'</Unused>')).search('test')['articles'][0]['abstract']==[]
def test_unknown_article_not_injected():assert service(XML.replace(b'<PMID>123</PMID>',b'<PMID>888</PMID>')).search('test')['articles']==[]
def test_invalid_xml():
 with pytest.raises(LiteratureError):service(b'<bad>').search('test')
def test_upstream_error():
 s=PubMed(httpx.MockTransport(lambda r:httpx.Response(503)))
 with pytest.raises(LiteratureError):s.search('test')
def test_api_contract(tmp_path):
 with TestClient(create_app(tmp_path/'db',literature=service())) as c:
  assert c.post('/api/literature/search',json={'query':'test'}).status_code==403
  c.headers['X-CareContext-Session']=c.get('/api/config').json()['session']
  assert c.post('/api/literature/search',json={'query':'test'}).json()['articles'][0]['pmid']=='123'
  assert c.post('/api/literature/search',json={'query':'test','study_type':'invalid'}).status_code==422
