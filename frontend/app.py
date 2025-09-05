# frontend/streamlit_app.py
from __future__ import annotations

import os
import requests
import streamlit as st
from datetime import datetime, timezone, date, time
from urllib.parse import urljoin
from dotenv import load_dotenv

# -------------------------- Config / helpers --------------------------

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/"

def api_post(path: str, json: dict):
    try:
        r = requests.post(urljoin(BACKEND_URL, path.lstrip("/")), json=json, timeout=10)
        return r.status_code, (r.json() if "application/json" in r.headers.get("content-type","") else r.text)
    except Exception as e:
        return 599, {"detail": f"Network error: {e}"}

def api_get(path: str):
    try:
        r = requests.get(urljoin(BACKEND_URL, path.lstrip("/")), timeout=10)
        return r.status_code, (r.json() if "application/json" in r.headers.get("content-type","") else r.text)
    except Exception as e:
        return 599, {"detail": f"Network error: {e}"}

def iso_or_none(exp_date: date | None, exp_time: time | None) -> str | None:
    if not exp_date:
        return None
    t = exp_time or time(0, 0, 0)
    dt = datetime.combine(exp_date, t)
    # send as UTC ISO 8601 (your API treats naive as UTC; we’ll be explicit)
    return dt.replace(tzinfo=timezone.utc).isoformat()


# ------------------------------- UI -------------------------------

st.set_page_config(page_title="URL Shortener", page_icon="🔗", layout="centered")

with st.sidebar:
    st.markdown("### Backend")
    st.write("Point this UI to your FastAPI server:")
    backend_url_input = st.text_input("Backend base URL", value=BACKEND_URL, help="e.g., http://localhost:8000")
    if backend_url_input.strip():
        BACKEND_URL = backend_url_input.strip().rstrip("/") + "/"
    st.caption("CORS: make sure your API allows this Streamlit origin (defaults to http://localhost:8501 in dev).")

st.title("🔗 URL Shortener")

(tab_shorten,) = st.tabs(["Shorten"])

# --------------------------- Shorten tab ---------------------------
with tab_shorten:
    st.subheader("Create a short link")

    with st.form("shorten_form", clear_on_submit=False):
        long_url = st.text_input("Long URL", placeholder="https://example.com/article/123")
        alias = st.text_input("Custom alias (optional)", placeholder="my-custom-code")
        col1, col2 = st.columns(2)
        with col1:
            exp_date = st.date_input("Expires on (UTC)", value=None, format="YYYY-MM-DD")
        with col2:
            exp_time = st.time_input("Expiration time (UTC)", value=None)

        submit = st.form_submit_button("Shorten")

    if submit:
        payload = {"url": long_url}
        if alias.strip():
            payload["alias"] = alias.strip()
        exp_iso = iso_or_none(exp_date if exp_date != date.min else None, exp_time)
        if exp_iso:
            payload["expires_at"] = exp_iso

        code, body = api_post("/api/shorten", payload)

        if code == 201:
            short_url = body["short_url"]
            st.success("Short link created!")
            st.markdown(f"**Short URL:** [{short_url}]({short_url})")
            st.code(short_url, language="text")
            st.session_state.setdefault("history", []).insert(0, {"long": long_url, "short": short_url})
        elif code == 400:
            st.error(f"Invalid input: {body.get('detail', body)}")
        elif code == 409:
            st.warning("Alias already taken. Try a different one.")
        elif code == 429:
            st.warning("Rate limit exceeded. Please wait a bit and try again.")
        elif code in (503, 599):
            st.error(f"Service/Network issue: {body if isinstance(body,str) else body.get('detail', body)}")
        else:
            st.error(f"Unexpected error ({code}): {body}")

    if st.session_state.get("history"):
        st.divider()
        st.caption("Recent links (this session)")
        for item in st.session_state["history"][:10]:
            st.markdown(f"- [{item['short']}]({item['short']}) → {item['long']}")

