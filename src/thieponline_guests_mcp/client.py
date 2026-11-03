#!/usr/bin/env python3
"""CRUD khách mời (`invitation_guests`) qua Supabase PostgREST.

Dùng auth.get_provider() lấy access token; retry 1 lần khi 401 (force_refresh).
Field v1: name, invite_message (+ salutation mặc định, invitation_id, slug tự sinh).
Chỉ stdlib urllib.
"""
import json
import re
import unicodedata
import urllib.request
import urllib.error
import urllib.parse

from . import auth, config

GUEST_TABLE = "invitation_guests"
DEFAULT_SALUTATION = "Thân Mời"
_EXTRA = {"đ": "d", "Đ": "d"}


def slugify(name):
    """'Vợ chồng anh Vinh' -> 'vo-chong-anh-vinh'. Khớp slug app sinh."""
    name = "".join(_EXTRA.get(c, c) for c in name)
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name or "guest"


class GuestClient:
    def __init__(self, provider=None):
        self.provider = provider or auth.get_provider()
        self.url = config.SUPABASE_URL.rstrip("/")
        self.anon = config.SUPABASE_ANON_KEY
        self.invitation_id = config.invitation_id()

    def _headers(self, extra=None):
        h = {
            "apikey": self.anon,
            "Authorization": f"Bearer {self.provider.get_access_token()}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def _request(self, method, path, body=None, extra_headers=None, _retried=False):
        url = f"{self.url}/rest/v1/{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, headers=self._headers(extra_headers), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode()
                return resp.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            if e.code == 401 and not _retried:
                self.provider.force_refresh()
                return self._request(method, path, body, extra_headers, _retried=True)
            raw = e.read().decode()
            try:
                detail = json.loads(raw)
            except Exception:
                detail = raw
            raise RuntimeError(f"PostgREST {method} {path} HTTP {e.code}: {detail}")

    def list_guests(self, search=None):
        q = "select=id,name,salutation,invite_message,slug,created_at&order=created_at.asc"
        if self.invitation_id:
            q += f"&invitation_id=eq.{self.invitation_id}"
        if search:
            q += f"&name=ilike.*{urllib.parse.quote(search)}*"
        _, rows = self._request("GET", f"{GUEST_TABLE}?{q}")
        return rows or []

    def get_guest(self, guest_id):
        _, rows = self._request("GET", f"{GUEST_TABLE}?id=eq.{guest_id}&select=*")
        return rows[0] if rows else None

    def add_guest(self, name, invite_message=None, salutation=None, invitation_id=None):
        inv = invitation_id or self.invitation_id
        if not inv:
            raise ValueError("Cần invitation_id (đặt THIEPONLINE_INVITATION_ID trong env)")
        if not name or not name.strip():
            raise ValueError("name không được rỗng")
        body = {
            "name": name.strip(),
            "slug": slugify(name),
            "salutation": salutation or DEFAULT_SALUTATION,
            "invitation_id": inv,
        }
        if invite_message is not None:
            body["invite_message"] = invite_message
        _, rows = self._request("POST", GUEST_TABLE, body,
                                extra_headers={"Prefer": "return=representation"})
        return rows[0] if rows else None

    def update_guest(self, guest_id, name=None, invite_message=None, salutation=None):
        patch = {}
        if name is not None:
            patch["name"] = name.strip()
            patch["slug"] = slugify(name)
        if invite_message is not None:
            patch["invite_message"] = invite_message
        if salutation is not None:
            patch["salutation"] = salutation
        if not patch:
            raise ValueError("Không có field nào để cập nhật")
        _, rows = self._request("PATCH", f"{GUEST_TABLE}?id=eq.{guest_id}", patch,
                                extra_headers={"Prefer": "return=representation"})
        return rows[0] if rows else None

    def delete_guest(self, guest_id):
        self._request("DELETE", f"{GUEST_TABLE}?id=eq.{guest_id}")
        return {"deleted": guest_id}
