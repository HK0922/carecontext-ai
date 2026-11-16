"""Public PubMed discovery. Abstracts are sources, not generated clinical advice."""
from collections import OrderedDict
from datetime import datetime, timezone
import threading
import time
from urllib.parse import quote
import xml.etree.ElementTree as ET
import httpx

class LiteratureError(Exception): pass

class PubMed:
    BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
    FILTERS={'all':'','review':'systematic review[Publication Type]','trial':'randomized controlled trial[Publication Type]','guideline':'guideline[Publication Type]'}
    def __init__(self,transport=None):
        self.transport=transport;self.lock=threading.Lock();self.last_request=0.;self.cache=OrderedDict()

    def get(self,client,path,params):
        with self.lock:
            delay=.4-(time.monotonic()-self.last_request)
            if delay>0:time.sleep(delay)
            self.last_request=time.monotonic()
        response=client.get(self.BASE+path,params={**params,'tool':'carecontext'})
        response.raise_for_status()
        if len(response.content)>2_000_000:raise LiteratureError('The source response was too large. Narrow the search.')
        return response

    def search(self,query,study_type='all',since=None):
        if study_type not in self.FILTERS:raise LiteratureError('Unknown study filter.')
        term=f'({query})'
        if self.FILTERS[study_type]:term+=' AND '+self.FILTERS[study_type]
        if since:term+=f' AND ("{since}/01/01"[Date - Publication] : "3000"[Date - Publication])'
        with self.lock:
            cached=self.cache.get(term)
            if cached and time.monotonic()-cached[0]<600:return {**cached[1],'cached':True}
        try:
            with httpx.Client(timeout=18,transport=self.transport,follow_redirects=False) as client:
                search=self.get(client,'esearch.fcgi',{'db':'pubmed','term':term,'retmode':'json','retmax':8,'sort':'relevance'}).json()['esearchresult']
                ids=search.get('idlist',[])
                if not isinstance(ids,list) or len(ids)>8 or any(not str(i).isdigit() for i in ids):raise LiteratureError('Invalid PubMed identifiers.')
                articles=[]
                if ids:
                    xml=self.get(client,'efetch.fcgi',{'db':'pubmed','id':','.join(ids),'retmode':'xml'}).content
                    if b'<!ENTITY' in xml.upper() or b'<!DOCTYPE' in xml.upper() and b'[' in xml.split(b'>',1)[0]:raise LiteratureError('Unsupported source XML.')
                    root=ET.fromstring(xml)
                    for node in root.findall('.//PubmedArticle'):
                        article=node.find('./MedlineCitation/Article')
                        if article is None:continue
                        pmid=node.findtext('./MedlineCitation/PMID','')
                        if pmid not in ids:continue
                        txt=lambda e:''.join(e.itertext()).strip() if e is not None else ''
                        abstract=[{'label':p.get('Label','Abstract'),'text':txt(p)} for p in article.findall('./Abstract/AbstractText') if txt(p)]
                        authors=[(' '.join(filter(None,[a.findtext('ForeName'),a.findtext('LastName')])) or a.findtext('CollectiveName','')) for a in article.findall('./AuthorList/Author')]
                        doi=next((a.text for a in node.findall('./PubmedData/ArticleIdList/ArticleId') if a.get('IdType')=='doi'),'') or ''
                        articles.append({'pmid':pmid,'title':txt(article.find('ArticleTitle')),'journal':article.findtext('./Journal/Title',''),
                                         'year':article.findtext('./Journal/JournalIssue/PubDate/Year') or article.findtext('./Journal/JournalIssue/PubDate/MedlineDate','Date unavailable'),
                                         'authors':authors[:4],'abstract':abstract,'study_types':[txt(p) for p in article.findall('./PublicationTypeList/PublicationType')],
                                         'url':f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/','doi_url':'https://doi.org/'+quote(doi,safe='/') if doi else None,
                                         'notices':[{'type':n.get('RefType','Notice'),'pmid':n.findtext('PMID','')} for n in node.findall('./MedlineCitation/CommentsCorrectionsList/CommentsCorrections')]})
                    order={id:i for i,id in enumerate(ids)};articles.sort(key=lambda p:order[p['pmid']])
                result={'query':query,'executed_query':term,'query_translation':search.get('querytranslation',''),
                        'total_matches':int(search.get('count',0)),'articles':articles,'cached':False,'retrieved_at':datetime.now(timezone.utc).isoformat(),
                        'source':'PubMed / NCBI','status':'sources_found' if articles else 'no_results',
                        'boundary':'Source discovery, not a clinical recommendation. Abstracts may omit limitations; read the full paper and check corrections.'}
                with self.lock:
                    self.cache[term]=(time.monotonic(),result)
                    while len(self.cache)>32:self.cache.popitem(last=False)
                return result
        except LiteratureError:raise
        except (httpx.HTTPError,ValueError,KeyError,TypeError,ImportError,ET.ParseError) as exc:
            raise LiteratureError('PubMed is unavailable or returned an unexpected response. Try again shortly; no substitute results were generated.') from exc
