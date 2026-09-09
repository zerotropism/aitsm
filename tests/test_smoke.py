"""Smoke tests: JWT, API auth, MCP server. Nothing here needs Chroma or an LLM."""

import importlib.util

import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token, decode_access_token


def test_jwt_roundtrip():
    token = create_access_token({"sub": "u1", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "u1"
    assert decode_access_token(token[:-3] + "xyz") is None


def test_api_register_login_and_auth_guard():
    from main import app

    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}

    assert client.get("/tickets").status_code == 401

    r = client.post(
        "/auth/register",
        json={"email": "t@aitsm.dev", "password": "pw", "full_name": "T"},
    )
    assert r.status_code == 201

    r = client.post("/auth/token", data={"username": "t@aitsm.dev", "password": "pw"})
    assert r.status_code == 200
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(
        "/tickets", json={"title": "smoke", "description": "smoke test"}, headers=headers
    )
    assert r.status_code == 201
    assert r.json()["status"] == "open"


@pytest.mark.anyio
async def test_mcp_server_tools():
    from fastmcp import Client

    # mcp/server.py cannot be imported as `mcp.server` (name clash with the mcp SDK);
    # load it by path until the package is renamed.
    spec = importlib.util.spec_from_file_location("aitsm_mcp", "mcp/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    async with Client(module.mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert {"create_ticket", "get_ticket", "list_tickets", "search_kb", "deflect"} <= tools
        assert len(tools) == 11

        created = await client.call_tool(
            "create_ticket", {"title": "mcp", "description": "via mcp"}
        )
        fetched = await client.call_tool("get_ticket", {"ticket_id": created.data["id"]})
        assert fetched.data["title"] == "mcp"


@pytest.fixture
def anyio_backend():
    return "asyncio"
