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


# ---------------------------------------------------------------------------
# FINISHED state banner key tests
# ---------------------------------------------------------------------------

async def test_api_response_has_failure_message(client: AsyncClient, running_session: str):
    """API response includes failure_message (snake_case) when enzyme is lost."""
    from backend.dependencies import get_session_store

    sid = running_session
    # Drain the enzyme directly on the server-side session object
    store = get_session_store()
    session = store.get(sid)
    session.proteins[session.enzyme_index].amount = 0.0
    session.proteins[session.enzyme_index].activity = 0

    # Heat treatment will call check_failure → detect lost enzyme → FINISHED
    resp = await client.post(
        f"/api/sessions/{sid}/separate",
        json={"type": "heat_treatment", "temperature": 50.0, "duration": 10.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "finished", f"Expected finished, got {data['phase']}"
    assert "failure_message" in data, "failure_message missing from API response"
    assert "success_message" not in data


async def test_api_response_has_success_message(client: AsyncClient, running_session: str):
    """GET /state returns success_message (snake_case) when FINISHED with success records."""
    from backend.dependencies import get_session_store
    from backend.engine.enums import SessionPhase
    from backend.engine.step_record import StepRecord

    sid = running_session
    store = get_session_store()
    session = store.get(sid)

    # Inject records that meet success thresholds (enrichment>=10, yield>=5)
    session.account.records = [
        StepRecord("Initial", 100.0, 2000.0, 100.0, 1.0, 0.0),
        StepRecord("Affinity", 5.0, 2000.0, 80.0, 15.0, 0.5),
    ]
    session.phase = SessionPhase.FINISHED

    resp = await client.get(f"/api/sessions/{sid}/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "finished"
    assert "success_message" in data, "success_message missing from API response"
    assert "failure_message" not in data
