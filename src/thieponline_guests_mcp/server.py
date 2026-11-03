#!/usr/bin/env python3
"""FastMCP server quản lý khách mời thieponline.app.

6 tool: list/get/add/update/delete khách + export CSV.
Khách lưu trên Supabase (bảng invitation_guests) của thieponline.app.
Auth tự refresh access token (auth.py) + cache token xoay vòng ở home dir.
"""
from fastmcp import FastMCP

from . import export

mcp = FastMCP("thieponline-guests")

_CLIENT = None


def _client():
    global _CLIENT
    if _CLIENT is None:
        from .client import GuestClient
        _CLIENT = GuestClient()
    return _CLIENT


_TOKEN_HINT = (
    "Lỗi xác thực với thieponline (token hết hạn hoặc bị thu hồi). "
    "Hãy đóng hết tab thieponline.app trong trình duyệt, lấy lại refresh_token mới "
    "từ cookie sb-dudcjocrigjgnprdkijw-auth-token và cập nhật THIEPONLINE_REFRESH_TOKEN."
)


def _slim(g):
    if not g:
        return None
    return {"id": g.get("id"), "name": g.get("name"), "invite_message": g.get("invite_message")}


def _guard(fn):
    try:
        return fn()
    except RuntimeError as e:
        msg = str(e)
        if "Refresh" in msg or "401" in msg:
            return {"error": _TOKEN_HINT, "detail": msg}
        return {"error": f"Lỗi khi gọi thieponline: {msg}"}
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool
def list_guests(search: str = "") -> list:
    """Liệt kê khách mời của thiệp cưới trên thieponline.app.

    search: lọc theo tên khách (không phân biệt hoa thường), để trống = tất cả.
    Trả về danh sách {id, name, invite_message}.
    """
    return _guard(lambda: [_slim(g) for g in _client().list_guests(search=search or None)])


@mcp.tool
def get_guest(guest_id: str) -> dict:
    """Lấy chi tiết 1 khách theo id (uuid). Trả về toàn bộ field của khách."""
    return _guard(lambda: _client().get_guest(guest_id) or {"error": "Không tìm thấy khách."})


@mcp.tool
def add_guest(name: str, invite_message: str = "", salutation: str = "") -> dict:
    """Thêm khách mời mới vào thiệp cưới.

    name: tên khách (bắt buộc). invite_message: lời nhắn/lời mời riêng (tùy chọn).
    salutation: lời xưng hô, để trống dùng mặc định 'Thân Mời'.
    slug được tự sinh từ tên. Trả về khách vừa tạo (gồm id).
    """
    return _guard(lambda: _slim(_client().add_guest(
        name,
        invite_message=invite_message or None,
        salutation=salutation or None,
    )))


@mcp.tool
def update_guest(guest_id: str, name: str = "", invite_message: str = "", salutation: str = "") -> dict:
    """Cập nhật khách theo id. Chỉ truyền field muốn đổi (field để trống = giữ nguyên).

    Phải có ít nhất 1 field. Đổi name sẽ tự cập nhật slug.
    """
    if not (name or invite_message or salutation):
        return {"error": "Cần ít nhất 1 field để cập nhật (name / invite_message / salutation)."}
    return _guard(lambda: _slim(_client().update_guest(
        guest_id,
        name=name or None,
        invite_message=invite_message or None,
        salutation=salutation or None,
    )))


@mcp.tool
def delete_guest(guest_id: str) -> dict:
    """Xóa khách khỏi thiệp cưới theo id (uuid). Hành động không hoàn tác được."""
    return _guard(lambda: _client().delete_guest(guest_id))


@mcp.tool
def export_guests_to_csv() -> dict:
    """Xuất toàn bộ khách mời ra file CSV (Danh_sach_khach_moi_cuoi.csv).

    Cột: STT, Tên khách, Lời nhắn. Trả về {path, count}.
    """
    def run():
        guests = _client().list_guests()
        path, n = export.export_guests(guests)
        return {"path": path, "count": n}
    return _guard(run)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
