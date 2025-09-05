from __future__ import annotations

import importlib
import pathlib
import pytest


@pytest.fixture()
def test_db_url(tmp_path: pathlib.Path) -> str:
    dbpath = tmp_path / "test.db"
    return f"sqlite:///{dbpath}"


@pytest.fixture()
def app_client(monkeypatch: pytest.MonkeyPatch, test_db_url: str):

    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "2")


    from app.core import settings as settings_module
    importlib.reload(settings_module)

    from app.db import session as session_module
    importlib.reload(session_module)

    
    import app.models.link as link_model
    importlib.reload(link_model)

    session_module.db.create_all()

  
    from app.services import rate_limit as rl_module
    importlib.reload(rl_module)
    rl_module.reset()

    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    yield client


@pytest.fixture()
def db_session(monkeypatch: pytest.MonkeyPatch, test_db_url: str):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DATABASE_URL", test_db_url)

    from app.core import settings as settings_module
    importlib.reload(settings_module)

    from app.db import session as session_module
    importlib.reload(session_module)

    import app.models.link as link_model
    importlib.reload(link_model)

    session_module.db.create_all()

    with session_module.db.session() as s:
        yield s
