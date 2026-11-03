#!/usr/bin/env python3
"""Config cho thieponline-guests-mcp.

SUPABASE_URL + anon(publishable) key: HARDCODE — chúng vốn công khai trong
JS bundle của thieponline.app, không phải secret.
invitation_id + refresh_token: per-user, lấy từ biến môi trường.
Refresh token xoay vòng (rotate) được cache ở home dir để bền qua các lần chạy uvx.
"""
import os
from pathlib import Path

# --- public, hardcode ---
SUPABASE_URL = "https://dudcjocrigjgnprdkijw.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_Ph3JsaNbT5YWufeDCzUtSg_6jl9fRoE"

# --- per-user, qua env ---
# THIEPONLINE_INVITATION_ID : id thiệp cưới (bắt buộc để thêm khách)
# THIEPONLINE_REFRESH_TOKEN : refresh token Supabase (seed lần đầu; sau đó dùng cache)
# THIEPONLINE_ACCESS_TOKEN  : (tùy chọn) access token tĩnh, fallback nếu không có refresh


def invitation_id():
    return os.environ.get("THIEPONLINE_INVITATION_ID") or None


def env_refresh_token():
    return os.environ.get("THIEPONLINE_REFRESH_TOKEN") or None


def env_access_token():
    return os.environ.get("THIEPONLINE_ACCESS_TOKEN") or None


def cache_dir():
    d = Path(os.environ.get("THIEPONLINE_CACHE_DIR") or (Path.home() / ".thieponline-guests-mcp"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def token_cache_path():
    return cache_dir() / "token.json"
