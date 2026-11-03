#!/usr/bin/env python3
"""Test server tools — fake client. Chạy: .venv/bin/python -m tests.test_mcp"""
import asyncio
import json

from thieponline_guests_mcp import server


class FakeClient:
    def list_guests(self, search=None):
        self.search = search
        return [
            {"id": "1", "name": "Em Thêu +", "invite_message": "hi", "slug": "em-theu", "invite_url": "https://thieponline.app/i/inv/em-theu"},
            {"id": "2", "name": "ngoctp", "invite_message": "", "slug": "ngoctp"},
        ]

    def add_guest(self, name, invite_message=None, salutation=None):
        self.added = (name, invite_message, salutation)
        return {"id": "9", "name": name, "invite_message": invite_message}

    def update_guest(self, gid, name=None, invite_message=None, salutation=None):
        return {"id": gid, "name": name or "old"}


EXPECTED = {"list_guests", "get_guest", "add_guest", "update_guest", "delete_guest", "export_guests_to_csv"}


def _payload(result):
    data = result.structured_content if result.structured_content is not None else json.loads(result.content[0].text)
    if isinstance(data, dict) and "result" in data:
        return data["result"]
    return data


def test_six_tools():
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    assert EXPECTED <= names, EXPECTED - names
    for t in tools:
        if t.name in EXPECTED:
            assert t.description and t.description.strip()
    print(f"PASS 6 tool đăng ký: {sorted(EXPECTED)}")


def test_list_smoke():
    server._CLIENT = FakeClient()
    data = _payload(asyncio.run(server.mcp.call_tool("list_guests", {"search": "em"})))
    assert len(data) == 2 and data[0] == {"id": "1", "name": "Em Thêu +", "invite_message": "hi", "invite_url": "https://thieponline.app/i/inv/em-theu"}
    assert server._CLIENT.search == "em"
    print("PASS list_guests smoke")


def test_add_defaults():
    server._CLIENT = FakeClient()
    asyncio.run(server.mcp.call_tool("add_guest", {"name": "A", "invite_message": "", "salutation": ""}))
    assert server._CLIENT.added == ("A", None, None)
    print("PASS add map rỗng→None")


def test_update_requires_field():
    server._CLIENT = FakeClient()
    data = _payload(asyncio.run(server.mcp.call_tool("update_guest", {"guest_id": "9"})))
    assert "error" in data
    print("PASS update báo lỗi khi thiếu field")


class FailClient:
    def list_guests(self, search=None):
        raise RuntimeError("Lỗi xác thực với thieponline.\n\nNguyên nhân: token chết")


def test_startup_validation_exits_on_auth_fail():
    server._CLIENT = FailClient()
    try:
        server._validate_auth_or_exit()
        assert False, "phải SystemExit khi auth fail lúc startup"
    except SystemExit as e:
        assert e.code == 1
    server._CLIENT = None
    print("PASS startup validation → exit(1) khi auth fail")


if __name__ == "__main__":
    test_six_tools()
    test_list_smoke()
    test_add_defaults()
    test_update_requires_field()
    test_startup_validation_exits_on_auth_fail()
    print("\nALL MCP TESTS PASS")
