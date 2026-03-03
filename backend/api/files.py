"""File save/load endpoints. Spec 11."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..dependencies import get_session
from ..engine.mixture_io import write_ppmixture_file
from ..engine.session import PurificationSession

router = APIRouter(prefix="/api/sessions", tags=["files"])


@router.get("/{session_id}/save")
async def save_session(
    session: PurificationSession = Depends(get_session),
) -> Response:
    """Download the current session as a .ppmixture file."""
    enzyme_index = session.enzyme_index if session.enzyme_index >= 0 else None
    history = session.account.records if enzyme_index is not None else None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".ppmixture", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        write_ppmixture_file(tmp_path, session.proteins, enzyme_index, history)
        content = tmp_path.read_text()
    finally:
        tmp_path.unlink(missing_ok=True)

    filename = f"{session.mixture_name or 'session'}.ppmixture"
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
