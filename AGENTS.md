# AGENTS.md

MCP server cho AI agent quản lý khách mời đám cưới trên [thieponline.app](https://thieponline.app). Backend Supabase (PostgREST); server tự refresh + cache access token.

## 6 tool

| Tool | Mô tả |
|---|---|
| `list_guests(search="")` | Liệt kê khách; `search` lọc theo tên (ilike, không phân biệt hoa thường). |
| `get_guest(guest_id)` | Chi tiết 1 khách theo id (uuid). |
| `add_guest(name, invite_message="", salutation="")` | Thêm khách; `name` bắt buộc, `slug` tự sinh, `salutation` mặc định "Thân Mời". |
| `update_guest(guest_id, name="", invite_message="", salutation="")` | Sửa khách; chỉ truyền field muốn đổi, cần ≥1 field. Đổi `name` → slug cập nhật theo. |
| `delete_guest(guest_id)` | Xóa khách — **không hoàn tác**. |
| `export_guests_to_csv()` | Xuất `Danh_sach_khach_moi_cuoi.csv` (STT, Tên khách, Lời nhắn, Link thiệp). |

Mỗi khách trả về `{id, name, invite_message, invite_url}`. `invite_url` dạng `https://thieponline.app/i/{invitation_slug}/{guest_slug}`.

## Môi trường (truyền qua khối `env` trong mcp.json)

| Biến | Bắt buộc | Vai trò |
|---|---|---|
| `THIEPONLINE_INVITATION_ID` | ✅ | id thiệp cưới — xác định tập khách để thao tác. |
| `THIEPONLINE_REFRESH_TOKEN` | ✅ (seed đầu) | refresh token Supabase. Xoay vòng 1 lần/dùng; sau khi seed, server tự lưu bản mới vào `~/.thieponline-guests-mcp/token.json`. |
| `THIEPONLINE_ACCESS_TOKEN` | ⬜ | access token tĩnh, fallback nếu không có refresh token. |

`SUPABASE_URL` + anon key là public, hardcode trong `config.py` — không cần cấu hình. Cách lấy 2 giá trị env: xem [README](README.md#lấy-2-giá-trị-cấu-hình).

## Xử lý lỗi (quan trọng cho agent)

Khi tool trả `{"error": ...}`:

- **Lỗi xác thực / token hết hạn** (message bắt đầu "Lỗi xác thực với thieponline"): message đã chứa hướng dẫn từng bước. Chuyển nguyên văn cho người dùng. Tóm tắt: **logout → login lại thieponline.app → lấy `refresh_token` mới → đóng hết tab → dán vào mcp.json → `rm ~/.thieponline-guests-mcp/token.json` → restart MCP client.** Agent **không** tự lấy token được (cần thao tác trình duyệt của người dùng).
- **Lỗi kết nối** ("Lỗi kết nối tới thieponline"): mạng/Supabase gián đoạn — bảo người dùng thử lại sau, **không** đòi token mới.
- **Lỗi khác**: hiển thị message cho người dùng.

Message chẩn đoán sinh ở `diagnostics.py` (`diagnose_refresh_error`). Đừng tự chế lại hướng dẫn — dùng nguyên văn server trả.

## Kiến trúc

| File | Trách nhiệm |
|---|---|
| `src/thieponline_guests_mcp/server.py` | FastMCP, định nghĩa 6 tool, `_guard` bọc lỗi, validate auth lúc khởi động. |
| `.../client.py` | CRUD `invitation_guests` qua PostgREST; retry 1 lần khi 401; `slugify` khớp slug app sinh. |
| `.../auth.py` | `TokenProvider`: refresh access token, cache refresh token xoay vòng. |
| `.../diagnostics.py` | Dịch mã lỗi Supabase → hướng dẫn tiếng Việt. |
| `.../export.py` | Xuất CSV (UTF-8 BOM, stdlib `csv`). |
| `.../config.py` | Hằng public + đọc env + đường dẫn cache. |

Chỉ dùng stdlib `urllib` cho HTTP (không thêm dependency ngoài `fastmcp`).

## Chạy & test

- Chạy: `uvx --from git+https://github.com/ngoctp27/thieponline-app-mcp thieponline-guests-mcp` (ép tải lại: thêm `--refresh`).
- Test: `cd src && ../.venv/bin/python -m tests.<tên_test>` — ví dụ `tests.test_diagnostics`. Test là script stdlib thuần (assert + print), không cần pytest.

## Ranh giới

- RSVP ở bảng riêng, chỉ khách tự điền qua trang công khai — server này **không** ghi RSVP.
- Token chỉ truy cập dữ liệu của chính tài khoản đăng nhập (RLS). `refresh_token` là bí mật cá nhân — giữ trong `env`, **không** commit.
