# thieponline-guests-mcp

MCP server để AI agent quản lý khách mời trên [thieponline.app](https://thieponline.app) — liệt kê, thêm, sửa, xóa khách và xuất CSV. Backend là Supabase; server tự refresh access token.

- Repo: https://github.com/ngoctp27/thieponline-app-mcp
- Trang: https://ngoctp27.github.io/thieponline-app-mcp/
- Cài bằng `uvx` trực tiếp từ GitHub, không cần clone.

## Tool

| Tool | Mô tả |
|---|---|
| `list_guests(search="")` | Liệt kê khách; `search` lọc theo tên (không phân biệt hoa thường). |
| `get_guest(guest_id)` | Chi tiết 1 khách theo id (uuid). |
| `add_guest(name, invite_message="", salutation="")` | Thêm khách. `name` bắt buộc; `salutation` trống → mặc định `Thân Mời`. slug tự sinh từ tên. |
| `update_guest(guest_id, name="", invite_message="", salutation="")` | Sửa khách; chỉ truyền field muốn đổi. Đổi `name` cập nhật slug. |
| `delete_guest(guest_id)` | Xóa khách (không hoàn tác). |
| `export_guests_to_csv()` | Xuất tất cả khách ra `Danh_sach_khach_moi_cuoi.csv` (cột STT, Tên khách, Lời nhắn). |

> Ghi chú: RSVP (xác nhận dự) lưu ở bảng riêng, chỉ khách tự điền qua trang công khai — server này không ghi RSVP.

## Cài đặt (MCP client)

Thêm vào file cấu hình MCP (`mcp.json` / `claude_desktop_config.json` / `.kiro/settings/mcp.json`):

```json
{
  "mcpServers": {
    "thieponline-guests": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/ngoctp27/thieponline-app-mcp",
        "thieponline-guests-mcp"
      ],
      "env": {
        "THIEPONLINE_INVITATION_ID": "<id-thiệp-của-bạn>",
        "THIEPONLINE_REFRESH_TOKEN": "<refresh-token-của-bạn>"
      }
    }
  }
}
```

Cần [uv](https://docs.astral.sh/uv/) (`uvx`) cài sẵn. `uvx` tự tải package + dependency (fastmcp) khi chạy.

## Lấy 2 giá trị cấu hình

Đăng nhập [thieponline.app](https://thieponline.app) trên trình duyệt, mở trang quản lý khách (`/guests`), rồi mở DevTools (F12).

### `THIEPONLINE_INVITATION_ID`
- DevTools → **Application** → **Local Storage** → `https://thieponline.app` → key `lastActiveInvitationId`. Copy value (dạng `xxxxxxxx-xxxx-...`).
- Hoặc **Cookies** → cùng key `lastActiveInvitationId`.

### `THIEPONLINE_REFRESH_TOKEN`
Supabase lưu session trong **Cookies** (`Application` → `Cookies` → `https://thieponline.app`), chia 2 cookie:
- `sb-dudcjocrigjgnprdkijw-auth-token.0`
- `sb-dudcjocrigjgnprdkijw-auth-token.1`

Ghép `.0` + `.1`, bỏ tiền tố `base64-`, decode base64 ra JSON, lấy field `refresh_token`:

```bash
python3 - <<'PY'
import base64, json
p0 = "base64-...dán phần .0 (bỏ 'base64-')..."
p1 = "...dán phần .1..."
raw = p0.replace("base64-", "") + p1
print(json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))["refresh_token"])
PY
```

> **Quan trọng — token xoay vòng:** Supabase refresh token dùng 1 lần rồi đổi. Nếu trình duyệt đang mở thieponline.app, nó sẽ tự refresh và làm token bạn copy hết hạn. Hãy **đóng hết tab thieponline.app** trước khi copy token cho MCP. Server lưu token xoay vòng vào `~/.thieponline-guests-mcp/token.json`, nên sau lần seed đầu tiên nó tự duy trì.

## Dành cho AI agent

- Biến môi trường bắt buộc: `THIEPONLINE_INVITATION_ID`, `THIEPONLINE_REFRESH_TOKEN` (truyền qua khối `env` trong cấu hình MCP, **không** hard-code vào code/commit).
- `SUPABASE_URL` và anon key là public, đã nhúng sẵn trong server — không cần cấu hình.
- Nếu tool trả `{"error": ...}` nhắc token hết hạn: yêu cầu người dùng lấy lại `THIEPONLINE_REFRESH_TOKEN` theo mục trên.
- Token chỉ truy cập được dữ liệu của chính tài khoản đăng nhập (RLS). Mỗi người dùng cần token riêng.

## Bảo mật

- `refresh_token` là bí mật cá nhân — không commit, không chia sẻ. Giữ trong `env` của MCP client hoặc cache `~/.thieponline-guests-mcp/token.json`.
- Repo này không chứa token của ai. Anon key nhúng sẵn là khóa publishable công khai (vốn lộ trong bundle web của thieponline.app), không phải secret.

## Phát triển

```bash
python3 -m venv .venv && .venv/bin/pip install -e .
# chạy test (không cần token thật):
.venv/bin/python -m tests.test_auth
.venv/bin/python -m tests.test_client
.venv/bin/python -m tests.test_export
.venv/bin/python -m tests.test_mcp
```

## License

MIT
