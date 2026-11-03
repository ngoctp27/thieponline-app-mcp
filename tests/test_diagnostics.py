#!/usr/bin/env python3
"""Test diagnostics — chẩn đoán lỗi → hướng dẫn cụ thể. .venv/bin/python -m tests.test_diagnostics"""
from thieponline_guests_mcp import diagnostics as dg


def test_already_used_gives_steps():
    m = dg.diagnose_refresh_error(400, {"error_code": "refresh_token_already_used", "msg": "already used"})
    assert "đã được dùng rồi" in m
    assert "Đóng HẾT tab" in m and "Console" in m and "mcp.json" in m
    assert "token.json" in m  # nhắc xoá cache
    print("PASS already_used → hướng dẫn từng bước")


def test_not_valid():
    m = dg.diagnose_refresh_error(400, {"error_code": "validation_failed", "msg": "Refresh token is not valid"})
    assert "không tồn tại hoặc sai định dạng" in m and "Đóng HẾT tab" in m
    print("PASS token not valid → hướng dẫn")


def test_network_error_no_token_steps():
    m = dg.diagnose_refresh_error(503, {})
    assert "Lỗi kết nối" in m and "thử lại" in m.lower()
    assert "Đóng HẾT tab" not in m  # lỗi mạng không bảo lấy token mới
    print("PASS lỗi mạng → không đòi token mới")


def test_no_refresh_message():
    m = dg.no_refresh_token_message()
    assert "Chưa có refresh_token" in m and "Console" in m
    print("PASS no refresh token message")


if __name__ == "__main__":
    test_already_used_gives_steps()
    test_not_valid()
    test_network_error_no_token_steps()
    test_no_refresh_message()
    print("\nALL DIAGNOSTICS TESTS PASS")
