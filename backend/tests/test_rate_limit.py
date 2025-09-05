from __future__ import annotations
from uuid import uuid4
from datetime import datetime, timedelta, timezone

LONG_URL = "https://tabs.ultimate-guitar.com/tab/alice-in-chains/nutshell-chords-127561"

def test_resolve_unknown_and_expired(app_client, monkeypatch):

    r0 = app_client.get("/api/resolve/rl_doesnotexist")
    assert r0.status_code == 200
    assert r0.json() == {"exists": False, "expired": False}


    alias = f"oldrl_{uuid4().hex[:6]}"
    future_iso = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    r = app_client.post("/api/shorten", json={"url": LONG_URL, "alias": alias, "expires_at": future_iso})
    assert r.status_code == 201, r.text


    from app.services import url_service as us
    real_datetime = datetime

    class _FutureDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.now(tz) + timedelta(days=2)

    monkeypatch.setattr(us, "datetime", _FutureDatetime)

    r2 = app_client.get(f"/api/resolve/{alias}")
    assert r2.status_code == 200
    assert r2.json() == {"exists": True, "expired": True}
