"""Integration tests for session lifecycle endpoints.

Tests session creation, mixture selection, and state retrieval.
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_create_session(client: AsyncClient):
    """POST /api/sessions returns a new session ID."""
    resp = await client.post("/api/sessions")
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["phase"] == "splash"


async def test_get_session_state(client: AsyncClient):
    """GET /api/sessions/{id}/state returns full state."""
    create_resp = await client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    resp = await client.get(f"/api/sessions/{session_id}/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id
    assert data["phase"] == "splash"


async def test_choose_mixture(client: AsyncClient):
    """POST /api/sessions/{id}/choose-mixture sets mixture."""
    create_resp = await client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    resp = await client.post(
        f"/api/sessions/{session_id}/choose-mixture",
        json={"name": "Easy3_Mixture"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "enzyme_selection"
    assert len(data["proteins"]) > 0
    assert data["mixture_name"] == "Easy3_Mixture"


async def test_choose_enzyme(client: AsyncClient):
    """POST /api/sessions/{id}/choose-enzyme sets enzyme index."""
    create_resp = await client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    await client.post(
        f"/api/sessions/{session_id}/choose-mixture",
        json={"name": "Easy3_Mixture"},
    )
    resp = await client.post(
        f"/api/sessions/{session_id}/choose-enzyme",
        json={"enzyme_index": 0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "running"
    assert data["enzyme_index"] == 0
    assert len(data["records"]) == 1
    assert data["records"][0]["step_type"] == "Initial"


async def test_delete_session(client: AsyncClient):
    """DELETE /api/sessions/{id} removes the session."""
    create_resp = await client.post("/api/sessions")
    session_id = create_resp.json()["session_id"]

    resp = await client.delete(f"/api/sessions/{session_id}")
    assert resp.status_code == 204

    resp = await client.get(f"/api/sessions/{session_id}/state")
    assert resp.status_code == 404
