from __future__ import annotations
import os, time, base64, json, urllib.parse, requests
from typing import Dict, Any, Tuple

# =========== GOOGLE ===========
GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"


def google_auth_url(scopes: list[str], redirect_uri: str, state: str = "state") -> str:
    params = {
        "client_id": os.getenv("GCP_CLIENT_ID", ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH}?{urllib.parse.urlencode(params)}"


def google_exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    data = {
        "code": code,
        "client_id": os.getenv("GCP_CLIENT_ID", ""),
        "client_secret": os.getenv("GCP_CLIENT_SECRET", ""),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    r = requests.post(GOOGLE_TOKEN, data=data, timeout=10)
    out = r.json()
    # simpan refresh/access ke ENV sementara (dev); produksi → secret store
    if "refresh_token" in out:
        os.environ["G_REFRESH_TOKEN"] = out["refresh_token"]
    if "access_token" in out:
        os.environ["G_ACCESS_TOKEN"] = out["access_token"]
    return out


def google_refresh(refresh_token: str) -> Dict[str, Any]:
    data = {
        "refresh_token": refresh_token,
        "client_id": os.getenv("GCP_CLIENT_ID", ""),
        "client_secret": os.getenv("GCP_CLIENT_SECRET", ""),
        "grant_type": "refresh_token",
    }
    r = requests.post(GOOGLE_TOKEN, data=data, timeout=10)
    out = r.json()
    if "access_token" in out:
        os.environ["G_ACCESS_TOKEN"] = out["access_token"]
    return out


# Helper untuk adapters lo:
def ensure_google_access(service: str) -> str:
    """
    service in {"gmail","gcal","gdrive","gcontacts"}
    Return: access_token (string) atau "" kalau gagal.
    """
    access = os.getenv("G_ACCESS_TOKEN", "")
    if access:
        return access
    rft = os.getenv("G_REFRESH_TOKEN", "")
    if not rft:
        return ""
    out = google_refresh(rft)
    return out.get("access_token", "")


# =========== MICROSOFT ===========
MS_TOKEN = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def ms_exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    url = MS_TOKEN.format(tenant=os.getenv("MS_TENANT_ID", "common"))
    data = {
        "client_id": os.getenv("MS_CLIENT_ID", ""),
        "client_secret": os.getenv("MS_CLIENT_SECRET", ""),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "code": code,
    }
    r = requests.post(url, data=data, timeout=10)
    out = r.json()
    if "refresh_token" in out:
        os.environ["MS_REFRESH_TOKEN"] = out["refresh_token"]
    if "access_token" in out:
        os.environ["MS_ACCESS_TOKEN"] = out["access_token"]
    return out


def ms_refresh(refresh_token: str | None = None) -> Dict[str, Any]:
    url = MS_TOKEN.format(tenant=os.getenv("MS_TENANT_ID", "common"))
    rt = refresh_token or os.getenv("MS_REFRESH_TOKEN", "")
    data = {
        "client_id": os.getenv("MS_CLIENT_ID", ""),
        "client_secret": os.getenv("MS_CLIENT_SECRET", ""),
        "grant_type": "refresh_token",
        "refresh_token": rt,
        "scope": "https://graph.microsoft.com/.default offline_access",
    }
    r = requests.post(url, data=data, timeout=10)
    out = r.json()
    if "access_token" in out:
        os.environ["MS_ACCESS_TOKEN"] = out["access_token"]
    return out


def ensure_ms_access() -> str:
    access = os.getenv("MS_ACCESS_TOKEN", "")
    if access:
        return access
    if not os.getenv("MS_REFRESH_TOKEN", ""):
        return ""
    out = ms_refresh()
    return out.get("access_token", "")
