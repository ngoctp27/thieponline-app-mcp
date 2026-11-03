#!/usr/bin/env python3
"""Test auth — mock HTTP + tmp cache dir. Chạy: .venv/bin/python -m tests.test_auth"""
import os
import json
import time
import base64
import tempfile

from thieponline_guests_mcp import auth, config


def make_jwt(exp):
    header = base64.urlsafe_b64encode(b'{"alg":"ES256"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def setup_tmp_env(access=None, refresh_env=None, cache_refresh=None):
    d = tempfile.mkdtemp()
    os.environ["THIEPONLINE_CACHE_DIR"] = d
    os.environ.pop("THIEPONLINE_ACCESS_TOKEN", None)
    os.environ.pop("THIEPONLINE_REFRESH_TOKEN", None)
    if access:
        os.environ["THIEPONLINE_ACCESS_TOKEN"] = access
    if refresh_env:
        os.environ["THIEPONLINE_REFRESH_TOKEN"] = refresh_env
    if cache_refresh:
        config.token_cache_path().write_text(json.dumps({"refresh_token": cache_refresh}))
    return d


def test_jwt_exp():
    assert auth._jwt_exp(make_jwt(123)) == 123
    assert auth._jwt_exp("garbage") is None
    print("PASS jwt exp parsing")


def test_cache_takes_precedence_over_env():
    setup_tmp_env(refresh_env="env_rt", cache_refresh="cache_rt")
    p = auth.TokenProvider()
    assert p._refresh == "cache_rt", "cache phải ưu tiên hơn env"
    print("PASS cache ưu tiên hơn env")


def test_refresh_and_persist_rotation():
    setup_tmp_env(access=make_jwt(int(time.time()) - 10), refresh_env="old_rt")
    new_access = make_jwt(int(time.time()) + 3600)
    calls = []

    def fake_post(url, headers, body):
        calls.append(body)
        assert body == {"refresh_token": "old_rt"}
        return 200, {"access_token": new_access, "refresh_token": "new_rt"}

    auth._http_post_json = fake_post
    p = auth.TokenProvider()
    assert p.get_access_token() == new_access
    assert len(calls) == 1
    # token xoay vòng được ghi cache file
    saved = json.loads(config.token_cache_path().read_text())
    assert saved["refresh_token"] == "new_rt", saved
    print("PASS refresh + ghi cache token xoay vòng")


def test_cache_while_valid():
    setup_tmp_env(access=make_jwt(int(time.time()) + 3600), refresh_env="rt")
    calls = []
    auth._http_post_json = lambda *a, **k: calls.append(1) or (200, {})
    p = auth.TokenProvider()
    assert p.get_access_token() == p.get_access_token()
    assert len(calls) == 0
    print("PASS token còn hạn không refresh")


def test_refresh_failure_raises():
    setup_tmp_env(refresh_env="dead")
    auth._http_post_json = lambda *a, **k: (400, {"error_code": "validation_failed"})
    p = auth.TokenProvider()
    try:
        p.get_access_token()
        assert False
    except RuntimeError as e:
        assert "Lỗi xác thực" in str(e) or "không tồn tại" in str(e)
    print("PASS refresh fail raises")


def test_missing_token_raises():
    setup_tmp_env()  # không access, không refresh
    try:
        auth.TokenProvider()
        assert False
    except ValueError:
        pass
    print("PASS thiếu token raises")


if __name__ == "__main__":
    test_jwt_exp()
    test_cache_takes_precedence_over_env()
    test_refresh_and_persist_rotation()
    test_cache_while_valid()
    test_refresh_failure_raises()
    test_missing_token_raises()
    print("\nALL AUTH TESTS PASS")
