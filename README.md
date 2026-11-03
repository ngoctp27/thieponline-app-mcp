# thieponline-guests-mcp

MCP server để AI agent quản lý khách mời trên [thieponline.app](https://thieponline.app) — liệt kê, thêm, sửa, xóa khách và xuất CSV. Backend là Supabase; server tự refresh access token.

- Repo: https://github.com/ngoctp27/thieponline-app-mcp
- Trang: https://ngoctp27.github.io/thieponline-app-mcp/
- Cài bằng `uvx` trực tiếp từ GitHub, không cần clone.

## Tool

| Tool | Mô tả |
|---|---|
| `list_guests(search="")` | Liệt kê khách; `search` lọc theo tên. Mỗi khách kèm `invite_url` (link thiệp gửi khách). |
| `get_guest(guest_id)` | Chi tiết 1 khách theo id (uuid). |
| `add_guest(name, invite_message="", salutation="")` | Thêm khách. `name` bắt buộc; `salutation` trống → mặc định `Thân Mời`. slug tự sinh từ tên. |
| `update_guest(guest_id, name="", invite_message="", salutation="")` | Sửa khách; chỉ truyền field muốn đổi. Đổi `name` cập nhật slug. |
| `delete_guest(guest_id)` | Xóa khách (không hoàn tác). |
| `export_guests_to_csv()` | Xuất CSV `Danh_sach_khach_moi_cuoi.csv` (cột STT, Tên khách, Lời nhắn, Link thiệp). |

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

> **Làm đúng thứ tự để token không chết ngay:** nếu token báo hết hạn, hãy **đăng xuất (logout) rồi đăng nhập (login) lại** thieponline.app để Supabase cấp session hoàn toàn mới, lấy `refresh_token`, **rồi đóng hết tab thieponline.app** trước khi dán vào MCP.

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

## Cách nhanh — lấy cả 2 giá trị bằng Chrome Console (JS)

Nhanh nhất: mở [thieponline.app/guests](https://thieponline.app/guests) (đã đăng nhập), nhấn F12 → tab **Console**, dán đoạn JS dưới đây và Enter. Nó tự đọc `invitation_id`, decode `refresh_token`, rồi in sẵn khối `env` để copy-paste thẳng vào `mcp.json`:

```js
(() => {
  const ref = "dudcjocrigjgnprdkijw";
  const base = `sb-${ref}-auth-token`;
  const readCookie = n => document.cookie.split("; ").find(c => c.startsWith(n + "="))?.split("=").slice(1).join("=");
  const b64urlToJson = s => {
    s = s.replace(/^base64-/, "").replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    const bin = atob(s);
    const bytes = Uint8Array.from(bin, c => c.charCodeAt(0));
    return JSON.parse(new TextDecoder("utf-8").decode(bytes));
  };
  // session: cookie chia .0/.1, hoac cookie/localStorage gop
  let raw;
  const p0 = readCookie(base + ".0");
  if (p0) raw = decodeURIComponent(p0) + decodeURIComponent(readCookie(base + ".1") || "");
  else { raw = readCookie(base) || localStorage.getItem(base); if (raw) raw = decodeURIComponent(raw); }
  if (!raw) { console.error("Khong tim thay session. Ban da dang nhap thieponline.app chua?"); return; }

  const session = b64urlToJson(raw);
  const invitation = readCookie("lastActiveInvitationId") || localStorage.getItem("lastActiveInvitationId");

  console.log("THIEPONLINE_INVITATION_ID =", invitation);
  console.log("THIEPONLINE_REFRESH_TOKEN =", session.refresh_token);
  console.log("\n--- Copy khoi env duoi vao mcp.json ---");
  console.log(JSON.stringify({
    THIEPONLINE_INVITATION_ID: invitation,
    THIEPONLINE_REFRESH_TOKEN: session.refresh_token,
  }, null, 2));
})();
```

> Meo: neu Console chan dan (canh bao "Allow pasting"), go `allow pasting` roi Enter, sau do dan lai.

> **Quan trọng — token xoay vòng:** Supabase refresh token dùng 1 lần rồi đổi. Nếu trình duyệt đang mở thieponline.app, nó sẽ tự refresh và làm token bạn copy hết hạn. Hãy **đóng hết tab thieponline.app** trước khi copy token cho MCP. Server lưu token xoay vòng vào `~/.thieponline-guests-mcp/token.json`, nên sau lần seed đầu tiên nó tự duy trì.
>
> **Nếu token đã hết hạn / báo lỗi xác thực:** đăng xuất (logout) khỏi thieponline.app → đăng nhập (login) lại → lấy `refresh_token` mới bằng đoạn JS ở trên → đóng hết tab thieponline.app → dán token mới vào `mcp.json` → xoá cache cũ `rm ~/.thieponline-guests-mcp/token.json` → restart MCP client.

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
