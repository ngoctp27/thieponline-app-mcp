#!/usr/bin/env python3
"""Chẩn đoán lỗi auth/PostgREST → hướng dẫn cụ thể cho người dùng (tiếng Việt).

Human nhìn console log của Supabase (vd 'refresh_token_already_used') sẽ không biết
xử lý. Module này dịch mã lỗi thành các bước thao tác rõ ràng.
"""

# các bước lấy token mới — dùng chung, nhắc đúng quy trình tránh token chết lại.
# Logout + login lại đảm bảo Supabase cấp session HOÀN TOÀN MỚI (refresh_token chưa
# bị xoay vòng), tránh copy nhầm token đã chết.
_STEPS_GET_TOKEN = (
    "Cách lấy refresh_token MỚI (làm đúng thứ tự để token không chết ngay):\n"
    "  1. Mở https://thieponline.app → ĐĂNG XUẤT (logout) khỏi tài khoản.\n"
    "  2. ĐĂNG NHẬP (login) lại — Supabase cấp session mới, refresh_token còn nguyên.\n"
    "  3. Vào trang https://thieponline.app/guests.\n"
    "  4. Nhấn F12 → tab Console → dán đoạn JS trong README (mục 'Chrome Console')\n"
    "     → Enter. Nó in ra khối env gồm THIEPONLINE_INVITATION_ID + THIEPONLINE_REFRESH_TOKEN.\n"
    "  5. Copy giá trị THIEPONLINE_REFRESH_TOKEN.\n"
    "  6. ĐÓNG HẾT tab thieponline.app (kể cả tab chạy nền) — nếu còn mở, trình duyệt\n"
    "     tự refresh và giết token bạn vừa copy.\n"
    "  7. Dán token mới vào khối \"env\" của server thieponline-guests trong mcp.json.\n"
    "  8. Xoá file cache token cũ: rm ~/.thieponline-guests-mcp/token.json\n"
    "  9. Restart MCP client (Kiro), gọi lại tool."
)


def diagnose_refresh_error(status, body):
    """body: dict JSON lỗi từ Supabase /auth/v1/token. Trả message hướng dẫn."""
    code = ""
    msg = ""
    if isinstance(body, dict):
        code = (body.get("error_code") or body.get("code") or "")
        msg = (body.get("msg") or body.get("error_description") or body.get("error") or "")
    code = str(code).lower()

    if code == "refresh_token_already_used" or "already used" in str(msg).lower():
        why = ("refresh_token này đã được dùng rồi nên không còn hợp lệ. "
               "Supabase xoay vòng token mỗi lần dùng — thường do bạn đang mở "
               "thieponline.app trên trình duyệt (nó tự refresh song song với MCP), "
               "hoặc token đã bị dùng ở nơi khác.")
    elif code in ("refresh_token_not_found", "validation_failed") or "not valid" in str(msg).lower():
        why = ("refresh_token không tồn tại hoặc sai định dạng — có thể đã hết hạn, "
               "bị thu hồi, hoặc copy thiếu/thừa ký tự.")
    elif status in (401, 403):
        why = "Session bị thu hồi hoặc anon key sai (hiếm — anon key nhúng sẵn trong server)."
    elif status == 0 or status >= 500:
        why = (f"Không gọi được Supabase (HTTP {status}). Có thể mất mạng hoặc "
               "thieponline/Supabase đang gián đoạn. Thử lại sau ít phút.")
        # lỗi mạng: không cần lấy token mới
        return f"Lỗi kết nối tới thieponline.\n\nNguyên nhân: {why}"
    else:
        why = f"Supabase trả lỗi [HTTP {status}] code={code or '?'} msg={msg or '?'}."

    return f"Lỗi xác thực với thieponline.\n\nNguyên nhân: {why}\n\n{_STEPS_GET_TOKEN}"


def no_refresh_token_message():
    return (
        "Chưa có refresh_token để xác thực với thieponline.\n\n"
        + _STEPS_GET_TOKEN
    )
