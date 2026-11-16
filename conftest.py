import pytest
from fastapi.testclient import TestClient
from carecontext.api import create_app
from carecontext.catalog import Catalog
from carecontext.engine import Engine

@pytest.fixture
def catalog(): return Catalog()
@pytest.fixture
def engine(catalog): return Engine(catalog)
@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.delenv('CARECONTEXT_MODEL',raising=False)
    with TestClient(create_app(tmp_path/'test.sqlite3')) as c:
        c.headers['X-CareContext-Session']=c.get('/api/config').json()['session']
        yield c
