#!/usr/bin/env python3
"""Export khách mời ra CSV text (UTF-8 BOM). Chỉ stdlib csv."""
import csv
import io

OUT = "Danh_sach_khach_moi_cuoi.csv"
HEADERS = ["STT", "Tên khách", "Lời nhắn", "Link thiệp"]


def build_csv(guests):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEADERS)
    for i, g in enumerate(guests, start=1):
        w.writerow([i, g.get("name") or "", g.get("invite_message") or "", g.get("invite_url") or ""])
    return buf.getvalue()


def export_guests(guests, out=OUT):
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        f.write(build_csv(guests))
    return out, len(guests)
