"""
api_client.py — Thin wrapper around the FastAPI backend.
All HTTP calls live here so the Streamlit pages stay clean.
"""
import requests
import streamlit as st

BASE_URL = "http://localhost:8000"


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle(resp: requests.Response):
    """Raise a user-friendly error or return parsed JSON."""
    if resp.status_code in (200, 201):
        if resp.content:
            return resp.json(), None
        return {}, None
    if resp.status_code == 204:
        return {}, None
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    return None, str(detail)


# ─── Auth ─────────────────────────────────────────────────────────────────────
def register(username: str, password: str, full_name: str):
    resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"username": username, "password": password, "full_name": full_name},
    )
    return _handle(resp)


def login(username: str, password: str):
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
    )
    return _handle(resp)


def get_me():
    resp = requests.get(f"{BASE_URL}/auth/me", headers=_headers())
    return _handle(resp)


# ─── Tasks ────────────────────────────────────────────────────────────────────
def list_tasks(status_filter=None, priority_filter=None):
    params = {}
    if status_filter:
        params["status_filter"] = status_filter
    if priority_filter:
        params["priority_filter"] = priority_filter
    resp = requests.get(f"{BASE_URL}/tasks", headers=_headers(), params=params)
    return _handle(resp)


def create_task(title: str, description: str, priority: str, due_date=None):
    payload = {"title": title, "description": description, "priority": priority}
    if due_date:
        payload["due_date"] = str(due_date)
    resp = requests.post(f"{BASE_URL}/tasks", headers=_headers(), json=payload)
    return _handle(resp)


def update_task(task_id: str, **kwargs):
    resp = requests.put(
        f"{BASE_URL}/tasks/{task_id}", headers=_headers(), json=kwargs
    )
    return _handle(resp)


def delete_task(task_id: str):
    resp = requests.delete(f"{BASE_URL}/tasks/{task_id}", headers=_headers())
    return _handle(resp)


def get_stats():
    resp = requests.get(f"{BASE_URL}/tasks/stats/summary", headers=_headers())
    return _handle(resp)
