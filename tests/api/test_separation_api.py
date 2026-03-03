"""Integration tests for separation technique endpoints.

Tests running separations and verifying state transitions.
"""
import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_run_ammonium_sulfate(client: AsyncClient, running_session: str):
    """POST /api/sessions/{id}/separate with AS, then as-choice."""
    sid = running_session

    # Run ammonium sulfate separation
    resp = await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "ammonium_sulfate", "saturation": 50.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "as_result" in data
    assert data["pooled"] is False

    # Choose soluble fraction
    resp = await client.post(
        f"/api/sessions/{sid}/as-choice",
        json={"choice": "soluble"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pooled"] is True
    assert data["step"] == 1


async def test_run_gel_filtration(client: AsyncClient, running_session: str):
    """POST /api/sessions/{id}/separate with gel filtration params."""
    sid = running_session

    resp = await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "gel_filtration", "matrix": "sephadex_g100"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["has_fractions"] is True
    assert len(data["fractions"]) > 0


async def test_pool_fractions(client: AsyncClient, running_session: str):
    """POST /api/sessions/{id}/pool updates protein amounts."""
    sid = running_session

    # Run gel filtration first
    await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "gel_filtration", "matrix": "sephadex_g100"},
    )

    # Pool all fractions
    resp = await client.post(
        f"/api/sessions/{sid}/pool",
        json={"start": 1, "end": 125},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pooled"] is True
    assert data["has_fractions"] is False
    assert data["step"] == 1


async def test_assay(client: AsyncClient, running_session: str):
    """POST /api/sessions/{id}/assay enables enzyme activity display."""
    sid = running_session

    # Run gel filtration first
    await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "gel_filtration", "matrix": "sephadex_g100"},
    )

    resp = await client.post(f"/api/sessions/{sid}/assay")
    assert resp.status_code == 200
    data = resp.json()
    assert data["assayed"] is True


async def test_abandon_step(client: AsyncClient, running_session: str):
    """POST /api/sessions/{id}/abandon-step reverts to pooled state."""
    sid = running_session

    # Run gel filtration first
    await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "gel_filtration", "matrix": "sephadex_g100"},
    )

    resp = await client.post(f"/api/sessions/{sid}/abandon-step")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pooled"] is True
    assert data["has_fractions"] is False
