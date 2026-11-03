#!/usr/bin/env python3
"""Test export (CSV). Chạy: .venv/bin/python -m tests.test_export"""
import csv
import io
import os
import tempfile

from thieponline_guests_mcp import export


def test_build_csv():
    guests = [
        {"name": "Em Thêu +", "invite_message": "Lời nhắn ❤️", "invite_url": "https://thieponline.app/i/inv/em-theu"},
        {"name": "Vợ chồng anh Vinh", "invite_message": ""},
        {"name": "ngoctp", "invite_message": "Đến dự nhé"},
    ]
    rows = list(csv.reader(io.StringIO(export.build_csv(guests))))
    assert rows[0] == ["STT", "Tên khách", "Lời nhắn", "Link thiệp"]
    assert len(rows) == 4
    assert rows[1] == ["1", "Em Thêu +", "Lời nhắn ❤️", "https://thieponline.app/i/inv/em-theu"]
    assert rows[2] == ["2", "Vợ chồng anh Vinh", "", ""]
    print("PASS build_csv")


def test_export_bom():
    tmp = tempfile.mktemp(suffix=".csv")
    path, n = export.export_guests([{"name": "Đặng Thị Đào", "invite_message": "hi"}], out=tmp)
    assert n == 1
    assert open(tmp, "rb").read().startswith(b"\xef\xbb\xbf")
    rows = list(csv.reader(io.StringIO(open(tmp, encoding="utf-8-sig").read())))
    assert rows[1] == ["1", "Đặng Thị Đào", "hi", ""]
    os.unlink(tmp)
    print("PASS export BOM + tiếng Việt")


if __name__ == "__main__":
    test_build_csv()
    test_export_bom()
    print("\nALL EXPORT TESTS PASS")
