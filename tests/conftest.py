"""Shared test fixtures for the protein purification test suite."""
import pytest
from pathlib import Path

from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.dependencies import get_session_store


@pytest.fixture
def data_dir() -> Path:
    """Path to the test data directory."""
    return Path(__file__).parent.parent / "data" / "mixtures"


@pytest.fixture
def default_mixture_path(data_dir: Path) -> Path:
    """Path to the Default_Mixture.txt file."""
    return data_dir / "Default_Mixture.txt"


@pytest.fixture
def easy3_mixture_path(data_dir: Path) -> Path:
    """Path to the Easy3_Mixture.txt file."""
    return data_dir / "Easy3_Mixture.txt"


@pytest.fixture(autouse=True)
def _fresh_store():
    """Reset the session store between tests."""
    store = get_session_store()
    store._sessions.clear()


@pytest.fixture
async def client():
    """Async HTTP client bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def running_session(client: AsyncClient) -> str:
    """Create a session in RUNNING state (mixture chosen, enzyme selected).

    Returns the session_id.
    """
    resp = await client.post("/api/sessions")
    session_id = resp.json()["session_id"]

    await client.post(
        f"/api/sessions/{session_id}/choose-mixture",
        json={"name": "Easy3_Mixture"},
    )
    await client.post(
        f"/api/sessions/{session_id}/choose-enzyme",
        json={"enzyme_index": 0},
    )
    return session_id
