"""Loopback-first demo API. Fixed synthetic corpus; no record upload endpoint."""
from datetime import date
from pathlib import Path
from typing import Literal
import os
import secrets
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from .studio_ingest import extract_document, extract_pages, DocumentError, MAX_FILE_BYTES
from .studio_chat import answer_question, GroundedExplainer
from .clinical_extract import analyze_pages
from .research_privacy import assert_research_document_safe, PrivacyBoundaryError
from .medical_references import MedicalReferences, ReferenceConfig, ReferenceError
from . import __version__
from .catalog import Catalog
from .engine import Engine
from .providers import OpenAISelector, ProviderError
from .store import Store, markdown
from .literature import PubMed, LiteratureError

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
class Query(StrictModel):
    patient_id: str = Field(min_length=1,max_length=30)
    question: str = Field(min_length=4,max_length=600)
    mode: Literal['local','model'] = 'local'
    include_reference: bool = False
    as_of: date | None = None
class Review(StrictModel):
    decision: Literal['reviewed','needs_followup']
    note: str = Field(default='',max_length=2000)
class LiteratureQuery(StrictModel):
    query: str = Field(min_length=3,max_length=500)
    study_type: Literal['all','review','trial','guideline'] = 'all'
    since: int | None = Field(default=None,ge=1900,le=2100)
class Claim(StrictModel):
    text: str = Field(min_length=1,max_length=1200)
    source_id: str = Field(min_length=1,max_length=40)
class Verification(StrictModel):
    patient_id: str
    claims: list[Claim] = Field(min_length=1,max_length=12)


class StudioSnippet(StrictModel):
    source_id: str = Field(min_length=3,max_length=40)
    source_name: str = Field(min_length=1,max_length=90)
    page: int = Field(ge=1,le=100)
    text: str = Field(min_length=1,max_length=650)

class StudioTurn(StrictModel):
    role: Literal['user','assistant']
    text: str = Field(min_length=1,max_length=1000)

class StudioQuestion(StrictModel):
    question: str = Field(min_length=3,max_length=480)
    role: Literal['patient','clinician','researcher'] = 'patient'
    mode: Literal['local','model'] = 'local'
    synthetic_ack: bool
    snippets: list[StudioSnippet] = Field(min_length=1,max_length=160)
    history: list[StudioTurn] = Field(default_factory=list,max_length=6)

class ResearchLookup(StrictModel):
    medication_name: str = Field(min_length=3,max_length=60)


def create_app(db_path=None, selector=None, literature=None):
    catalog = Catalog()
    if selector is None and os.getenv('OPENAI_API_KEY') and os.getenv('CARECONTEXT_MODEL'):
        selector = OpenAISelector(os.environ['OPENAI_API_KEY'],os.environ['CARECONTEXT_MODEL'])
    engine = Engine(catalog,selector)
    literature = literature or PubMed()
    store = Store(db_path or os.getenv('CARECONTEXT_DB','.data/carecontext.sqlite3'))
    app = FastAPI(title='CareContext',version=__version__,docs_url=None,redoc_url=None,description='Synthetic clinical evidence review. Local demo, not clinical decision support.')
    app.state.engine, app.state.store, app.state.catalog = engine, store, catalog
    # Anti-CSRF session header only: not authentication or a security boundary for multi-user hosting.
    explainer = GroundedExplainer(os.environ['OPENAI_API_KEY'], os.environ['CARECONTEXT_MODEL']) if os.getenv('OPENAI_API_KEY') and os.getenv('CARECONTEXT_MODEL') else None
    research_enabled = os.getenv('CARECONTEXT_RESEARCH_MODE') == '1'
    reference_client = MedicalReferences(ReferenceConfig(online=os.getenv('CARECONTEXT_RESEARCH_NETWORK') == '1'))
    # A same-origin nonce helps prevent cross-origin POST calls to the configured provider.
    nonce = secrets.token_urlsafe(32)

    @app.middleware('http')
    async def boundaries(request: Request, call_next):
        if request.method in ('POST','DELETE','PUT','PATCH'):
            if not secrets.compare_digest(request.headers.get('X-CareContext-Session',''),nonce):
                return JSONResponse({'detail':'Missing session header. Reload the workspace.'},status_code=403)
            origin=request.headers.get('origin')
            if origin and origin.rstrip('/') != str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Cross-origin requests are not accepted.'},status_code=403)
            # Bound actual streamed bytes, not only the caller-supplied Content-Length.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > (MAX_FILE_BYTES + 8192 if request.url.path == '/api/studio/ingest' else 125000 if request.url.path == '/api/studio/answer' else 16000):
                    return JSONResponse({'detail':'Request exceeds the endpoint size limit.'},status_code=413)
            request._body=bytes(body)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Cache-Control']='no-store'
        return response

    def known(patient_id):
        try: return catalog.patient(patient_id)
        except KeyError: raise HTTPException(404,'Unknown synthetic case')

    def run(run_id):
        try: return store.get(run_id)
        except KeyError: raise HTTPException(404,'Review not found')

    @app.get('/api/health')
    def health(): return {'status':'ok','version':__version__,'synthetic_only':True}

    @app.post('/api/literature/search')
    def literature_search(q: LiteratureQuery):
        try:return literature.search(q.query,q.study_type,q.since)
        except LiteratureError as exc:raise HTTPException(502,str(exc))

    @app.get('/docs',include_in_schema=False)
    def api_reference():
        return FileResponse(Path(__file__).parent/'web/api-reference.html')

    @app.get('/api/config')
    def config(): return {'version':__version__,'model_enabled':selector is not None,'session':nonce,'corpus_sha256':catalog.digest,'documents':len(catalog.documents),'passages':len(catalog.passages),'synthetic_only':True}

    @app.get('/api/patients')
    def patients(): return list(catalog.patients.values())

    @app.get('/api/patients/{patient_id}')
    def patient(patient_id: str):
        return {**known(patient_id),'timeline':catalog.timeline(patient_id),'changes':catalog.changes(patient_id)}

    @app.get('/api/sources')
    def sources(patient_id: str, include_reference: bool=False):
        known(patient_id)
        return [p.public() for p in catalog.scope(patient_id,include_reference)]

    @app.post('/api/query')
    def query(q: Query):
        known(q.patient_id)
        if q.mode=='model' and selector is None: raise HTTPException(409,'Model mode requires server-side OPENAI_API_KEY and CARECONTEXT_MODEL.')
        try: answer=engine.answer(q.patient_id,q.question,q.mode,q.include_reference,q.as_of.isoformat() if q.as_of else None)
        except ProviderError as e: raise HTTPException(502,str(e))
        except ValueError: raise HTTPException(502,'Invalid evidence selection; no answer was saved.')
        store.save(answer)
        return answer

    @app.post('/api/verify')
    def verify(q: Verification):
        known(q.patient_id)
        return {'results':engine.verify(q.patient_id,[x.model_dump() for x in q.claims])}

    @app.get('/api/history/{patient_id}')
    def history(patient_id: str): known(patient_id); return store.history(patient_id)

    @app.delete('/api/history/{patient_id}')
    def clear_history(patient_id: str): known(patient_id); return {'deleted':store.delete(patient_id)}

    @app.get('/api/runs/{run_id}')
    def get_run(run_id: str): return run(run_id)

    @app.post('/api/runs/{run_id}/review')
    def review(run_id: str, review: Review):
        run(run_id)
        return store.review(run_id,review.decision,review.note)

    @app.get('/api/runs/{run_id}/export')
    def export(run_id: str, format: Literal['markdown','json']='markdown'):
        answer=run(run_id)
        if format=='json': return JSONResponse(answer,headers={'Content-Disposition':f'attachment; filename="carecontext-{answer["id"]}.json"'})
        return Response(markdown(answer,catalog.patient(answer['patient_id'])),media_type='text/markdown',
                        headers={'Content-Disposition':f'attachment; filename="carecontext-{answer["id"]}.md"'})

    @app.post('/api/evaluations')
    def evaluations():
        from .evaluation import evaluate
        return evaluate(Engine(catalog))

    @app.get('/api/studio/config')
    def studio_config():
        return {'version':__version__,'model_enabled':explainer is not None,
                'synthetic_only':True,'max_file_bytes':MAX_FILE_BYTES,
                'allowed_types':['pdf','docx','txt','md','png','jpg','jpeg'],
                'disclaimer':'Not for real patient information or clinical decisions.'}

    @app.post('/api/studio/ingest')
    async def studio_ingest(request: Request, name: str):
        try:
            return extract_document(name,await request.body())
        except DocumentError as error:
            raise HTTPException(422,str(error))

    @app.post('/api/studio/answer')
    def studio_answer(q: StudioQuestion):
        if not q.synthetic_ack:
            raise HTTPException(422,'Only fictional test records are allowed in this preview.')
        if len({p.source_id for p in q.snippets}) != len(q.snippets):
            raise HTTPException(422,'Source IDs must be unique.')
        try:
            return answer_question(q.question,q.role,[s.model_dump() for s in q.snippets],
                                   q.mode,explainer,[h.model_dump() for h in q.history])
        except ProviderError as error:
            raise HTTPException(502,str(error))

    def research_boundary(request: Request):
        if not research_enabled:
            raise HTTPException(403,'Research intake is disabled. Run the local application with CARECONTEXT_RESEARCH_MODE=1.')
        # TestClient's sentinel hostname is only used for automated tests.
        if request.client is None or request.client.host not in {'127.0.0.1','::1','testclient'} or request.url.hostname not in {'127.0.0.1','localhost','testserver'}:
            raise HTTPException(403,'Research mode is only available on a loopback-only local server.')

    @app.get('/api/research/config')
    def research_config():
        return {'version':__version__,'enabled':research_enabled,
                'reference_network_enabled':reference_client.config.online,
                'external_model_enabled':False,
                'supported_inputs':['PDF','DOCX','TXT','MD','PNG','JPG'],
                'data_policy':'Authorized de-identified documents only. Do not upload real identifiable patient records. Screening is not a privacy guarantee.'}

    @app.post('/api/research/analyze')
    async def research_analyze(request: Request, name: str):
        research_boundary(request)
        if request.headers.get('X-CareContext-Data-Class') != 'deidentified' or request.headers.get('X-CareContext-Data-Use') != 'authorized':
            raise HTTPException(422,'A research-use authorization and de-identification attestation are required.')
        try:
            pages,metadata=extract_pages(name,await request.body())
            assert_research_document_safe(metadata['name'],pages)
            return analyze_pages(metadata['name'],metadata['sha256'],pages,metadata['extraction'])
        except (DocumentError,PrivacyBoundaryError) as exc:
            raise HTTPException(422,str(exc))

    @app.post('/api/research/lookup')
    def research_lookup(request: Request, lookup: ResearchLookup):
        research_boundary(request)
        if request.headers.get('X-CareContext-Term-Only') != '1':
            raise HTTPException(422,'Only a medication name may be submitted to external references.')
        if reference_client.config.online and request.headers.get('X-CareContext-Term-Verified') != '1':
            raise HTTPException(422,'Confirm the medication term contains no identifying information before contacting external references.')
        try:
            return reference_client.lookup(lookup.medication_name)
        except ReferenceError as exc:
            raise HTTPException(422,str(exc))

    @app.get('/research', include_in_schema=False)
    def research_page():
        return FileResponse(Path(__file__).parent/'web/research.html')

    @app.get('/studio',include_in_schema=False)
    @app.get('/',include_in_schema=False)
    def studio_page():
        return FileResponse(Path(__file__).parent/'web/studio.html')

    @app.get('/classic',include_in_schema=False)
    def original_workspace():
        return FileResponse(Path(__file__).parent/'web/index.html')

    app.mount('/', StaticFiles(directory=Path(__file__).parent/'web',html=True),name='web')
    return app
