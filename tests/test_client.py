#!/usr/bin/env python3
"""Test client — mock PostgREST. Chạy: .venv/bin/python -m tests.test_client"""
import os
import json

os.environ["THIEPONLINE_INVITATION_ID"] = "INV-1"
from thieponline_guests_mcp import client


class FakeProvider:
    def __init__(self):
        self.tok = "tok0"
        self.forced = 0

    def get_access_token(self):
        return self.tok

    def force_refresh(self):
        self.forced += 1
        self.tok = "tok1"
        return self.tok


def test_slugify():
    assert client.slugify("Em Thêu +") == "em-theu"
    assert client.slugify("Vợ chồng anh Vinh") == "vo-chong-anh-vinh"
    assert client.slugify("Đặng Thị Đào") == "dang-thi-dao"
    assert client.slugify("ngoctp") == "ngoctp"
    assert client.slugify("   ") == "guest"
    print("PASS slugify")


def capture(responses):
    c = client.GuestClient(provider=FakeProvider())
    calls = []

    def fake_req(method, path, body=None, extra_headers=None, _retried=False):
        calls.append({"method": method, "path": path, "body": body, "headers": extra_headers})
        return 200, responses.pop(0)

    c._request = fake_req
    return c, calls


def test_list_query():
    c, calls = capture([[{"id": "1"}]])
    c.list_guests(search="an")
    p = calls[0]["path"]
    assert "invitation_id=eq.INV-1" in p and "name=ilike.*an*" in p and "order=created_at.asc" in p
    print("PASS list query shape")


def test_add_slug_defaults():
    c, calls = capture([[{"id": "9"}]])
    c.add_guest("Em Huy +", invite_message="hello")
    b = calls[0]["body"]
    assert b["slug"] == "em-huy" and b["salutation"] == "Thân Mời"
    assert b["invitation_id"] == "INV-1" and b["invite_message"] == "hello"
    assert calls[0]["headers"]["Prefer"] == "return=representation"
    print("PASS add slug+defaults+invitation_id")


def test_add_rejects_empty():
    c, _ = capture([])
    for bad in ("", "   ", None):
        try:
            c.add_guest(bad)
            assert False
        except ValueError:
            pass
    print("PASS add rejects empty name")


def test_update_partial():
    c, calls = capture([[{"id": "9"}]])
    c.update_guest("9", name="Vợ chồng anh Vinh")
    assert calls[0]["body"] == {"name": "Vợ chồng anh Vinh", "slug": "vo-chong-anh-vinh"}
    c2, calls2 = capture([[{"id": "9"}]])
    c2.update_guest("9", invite_message="x")
    assert calls2[0]["body"] == {"invite_message": "x"}
    print("PASS update partial + slug on rename")


def test_update_requires_field():
    c, _ = capture([])
    try:
        c.update_guest("9")
        assert False
    except ValueError:
        pass
    print("PASS update requires field")


def test_delete():
    c, calls = capture([None])
    assert c.delete_guest("9") == {"deleted": "9"}
    assert calls[0]["method"] == "DELETE" and "id=eq.9" in calls[0]["path"]
    print("PASS delete")


def test_401_retry():
    c = client.GuestClient(provider=FakeProvider())
    seq = [(401, None), (200, [{"id": "1"}])]

    class Resp:
        def __init__(self, s, p):
            self.status = s; self._p = p
        def read(self):
            return json.dumps(self._p).encode() if self._p is not None else b""
        def __enter__(self): return self
        def __exit__(self, *a): return False

    import urllib.error

    def fake_urlopen(req):
        s, p = seq.pop(0)
        if s == 401:
            raise urllib.error.HTTPError(req.full_url, 401, "u", {}, None)
        return Resp(s, p)

    client.urllib.request.urlopen = fake_urlopen
    status, rows = c._request("GET", "invitation_guests?select=*")
    assert status == 200 and rows == [{"id": "1"}] and c.provider.forced == 1
    print("PASS 401 → force_refresh → retry")


if __name__ == "__main__":
    test_slugify()
    test_list_query()
    test_add_slug_defaults()
    test_add_rejects_empty()
    test_update_partial()
    test_update_requires_field()
    test_delete()
    test_401_retry()
    print("\nALL CLIENT TESTS PASS")
