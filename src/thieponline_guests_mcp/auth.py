#!/usr/bin/env python3
"""Cấp access token hợp lệ cho PostgREST, tự refresh khi hết hạn.

Nguồn refresh_token (ưu tiên trên xuống):
  1. cache file ~/.thieponline-guests-mcp/token.json  (token xoay vòng mới nhất)
  2. env THIEPONLINE_REFRESH_TOKEN                      (seed lần đầu)
Sau mỗi refresh, token MỚI được ghi lại cache file (Supabase rotate token 1 lần/dùng).
Fallback: THIEPONLINE_ACCESS_TOKEN tĩnh nếu không có refresh token.
Chỉ dùng stdlib urllib — không thêm dependency.
"""
import json
import time
import base64
import threading
import urllib.request
import urllib.error

from . import config, diagnostics

_LOCK = threading.Lock()  # ponytail: 1 process MCP, global lock đủ


def _read_cache():
    p = config.token_cache_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_cache(refresh_token):
    p = config.token_cache_path()
    p.write_text(json.dumps({"refresh_token": refresh_token}), encoding="utf-8")


def _jwt_exp(token):
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("exp")
    except Exception:
        return None


def _http_post_json(url, headers, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}


class TokenProvider:
    """Cấp access token, tự refresh. Thread-safe cho 1 process MCP."""

    def __init__(self):
        self.url = config.SUPABASE_URL.rstrip("/")
        self.anon = config.SUPABASE_ANON_KEY
        self._access = config.env_access_token()
        self._exp = _jwt_exp(self._access) if self._access else None
        # refresh token: cache file trước, rồi env
        self._refresh = _read_cache().get("refresh_token") or config.env_refresh_token()
        if not self._refresh and not self._access:
            raise ValueError(diagnostics.no_refresh_token_message())

    def _valid(self, skew=60):
        if not self._access:
            return False
        if self._exp is None:
            return True
        return time.time() < (self._exp - skew)

    def _do_refresh(self):
        if not self._refresh:
            raise RuntimeError(diagnostics.no_refresh_token_message())
        status, body = _http_post_json(
            f"{self.url}/auth/v1/token?grant_type=refresh_token",
            {"apikey": self.anon, "Content-Type": "application/json"},
            {"refresh_token": self._refresh},
        )
        if status != 200 or "access_token" not in body:
            raise RuntimeError(diagnostics.diagnose_refresh_error(status, body))
        self._access = body["access_token"]
        self._exp = _jwt_exp(self._access)
        new_refresh = body.get("refresh_token")
        if new_refresh and new_refresh != self._refresh:
            self._refresh = new_refresh
            _write_cache(new_refresh)  # token xoay vòng → lưu cache
        return self._access

    def get_access_token(self):
        with _LOCK:
            if self._valid():
                return self._access
            return self._do_refresh()

    def force_refresh(self):
        with _LOCK:
            return self._do_refresh()


_SINGLETON = None


def get_provider():
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = TokenProvider()
    return _SINGLETON
