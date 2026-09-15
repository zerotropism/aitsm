"""Smoke tests: JWT, API auth, MCP server. Nothing here needs Chroma or an LLM."""

import pytest
from fastapi.testclient import TestClient

from aitsm.core.security import create_access_token, decode_access_token


def test_jwt_roundtrip():
    token = create_access_token({"sub": "u1", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "u1"
    assert decode_access_token(token[:-3] + "xyz") is None


def test_api_register_login_and_auth_guard():
    from aitsm.app import app

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
        "/tickets",
        json={"title": "smoke", "description": "smoke test"},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["status"] == "open"


@pytest.mark.anyio
async def test_mcp_server_tools():
    from fastmcp import Client

    from aitsm.mcp_server.server import mcp

    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert {
            "create_ticket",
            "get_ticket",
            "list_tickets",
            "search_kb",
            "deflect",
        } <= tools
        assert len(tools) == 11

        created = await client.call_tool(
            "create_ticket", {"title": "mcp", "description": "via mcp"}
        )
        fetched = await client.call_tool("get_ticket", {"ticket_id": created.data["id"]})
        assert fetched.data["title"] == "mcp"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_mcp_business_error_fails_the_call():
    """A missing ticket must fail the tool call, not return {"error": ...} as a success."""
    from fastmcp import Client
    from fastmcp.exceptions import ToolError

    from aitsm.mcp_server.server import mcp

    async with Client(mcp) as client:
        with pytest.raises(ToolError, match="not found"):
            await client.call_tool("get_ticket", {"ticket_id": "does-not-exist"})


@pytest.mark.anyio
async def test_mcp_filters_are_optional():
    """Without defaults, a model has to pass three explicit nulls to list tickets."""
    from fastmcp import Client

    from aitsm.mcp_server.server import mcp

    async with Client(mcp) as client:
        tool = next(t for t in await client.list_tools() if t.name == "list_tickets")
        assert "status" not in tool.input_schema.get("required", [])

        result = await client.call_tool("list_tickets", {})
        assert isinstance(result.data, list)


def test_console_entry_points_resolve():
    """Each [project.scripts] target must exist, or the command fails only at run time."""
    from importlib import import_module

    for module, attribute in (
        ("aitsm.app", "main"),
        ("aitsm.mcp_server.server", "main"),
        ("aitsm.scripts.bootstrap", "main"),
    ):
        assert hasattr(import_module(module), attribute), f"{module}:{attribute}"


def test_llm_backend_selection():
    from aitsm.core.llm import GatewayLLM, OllamaLLM, get_llm

    get_llm.cache_clear()
    assert isinstance(get_llm(), OllamaLLM | GatewayLLM)
    get_llm.cache_clear()


def test_unreachable_backend_raises_a_domain_error():
    """A model outage must be an LLMError, which the MCP layer turns into a ToolError."""
    import pytest

    from aitsm.core.llm import LLMError, OllamaLLM

    llm = OllamaLLM("http://127.0.0.1:1", "nope", timeout=0.5)
    with pytest.raises(LLMError, match="unavailable"):
        llm.invoke("ping")


def test_search_score_increases_as_distance_decreases(tmp_path, monkeypatch):
    """Chroma returns a distance; callers and models read `score` as "higher is better"."""
    from aitsm.core.config import settings
    from aitsm.vector import chroma_client

    monkeypatch.setattr(settings, "CHROMA_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr(chroma_client, "_client", None)

    chroma_client.index_article("a", "Connexion VPN impossible", "Le tunnel VPN échoue", [])
    chroma_client.index_article("b", "Imprimante réseau", "La file d'impression bloque", [])

    hits = chroma_client.search_articles("problème de connexion VPN", n_results=2)

    assert [h["id"] for h in hits] == ["a", "b"]
    assert hits[0]["score"] > hits[1]["score"]
    assert hits[0]["distance"] < hits[1]["distance"]


def test_seeded_addresses_pass_the_registration_schema():
    """Demo accounts must use addresses the API would accept, or the data contradicts the API."""
    from aitsm.core.database import SessionLocal
    from aitsm.models.user import User
    from aitsm.schemas.user import UserCreate

    db = SessionLocal()
    try:
        addresses = [user.email for user in db.query(User).all()]
    finally:
        db.close()

    for address in addresses:
        UserCreate(email=address, password="x" * 12)
