from __future__ import annotations
from datetime import datetime, timedelta, timezone
from app.services import url_service

LONG_URL = "https://tabs.ultimate-guitar.com/tab/alice-in-chains/nutshell-chords-127561"

def test_create_with_alias_and_conflict(db_session):
    code, link = url_service.create_short_link(db_session, url=LONG_URL, alias="test123")
    assert code == "test123"
    assert link.long_url == LONG_URL
    try:
        url_service.create_short_link(db_session, url=LONG_URL, alias="test123")
        assert False, "expected AliasTakenError"
    except url_service.AliasTakenError:
        pass

def test_create_generated_and_resolve_active(db_session):
    code, _ = url_service.create_short_link(db_session, url=LONG_URL)
    data = url_service.resolve(db_session, code=code)
    assert data == {"exists": True, "expired": False, "long_url": LONG_URL}

def test_resolve_unknown_and_expired(db_session):
    # unknown
    assert url_service.resolve(db_session, code="__does_not_exist__") == {"exists": False, "expired": False}

    # expired: create future, then flip to past
    future = datetime.now(timezone.utc) + timedelta(days=1)
    past = datetime.now(timezone.utc) - timedelta(days=1)
    code, link = url_service.create_short_link(db_session, url=LONG_URL, alias="oldalias", expires_at=future)
    link.expires_at = past
    db_session.commit()

    data = url_service.resolve(db_session, code=code)
    assert data["exists"] is True and data["expired"] is True and "long_url" not in data
