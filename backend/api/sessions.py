"""Session lifecycle endpoints. Spec 1.1."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from ..dependencies import get_data_dir, get_session, get_session_store
from ..engine.enums import SessionPhase
from ..engine.mixture_io import (
    load_mixture,
    parse_ppmixture_file,
    resolve_mixture_path,
)
from ..engine.protein_data import initialize_proteins
from ..engine.session import PurificationSession
from ..session_store import SessionStore
from .schemas import ChooseEnzymeRequest, ChooseMixtureRequest

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_session(
    store: SessionStore = Depends(get_session_store),
) -> dict:
    """Create a new purification session."""
    session = store.create()
    return session.to_state_dict()


@router.post("/load")
async def load_session(
    file: UploadFile,
    store: SessionStore = Depends(get_session_store),
) -> dict:
    """Upload a .ppmixture file to create a restored session."""
    content = await file.read()
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".ppmixture", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        proteins, enzyme_index, history = parse_ppmixture_file(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    session = store.create()
    session.proteins = proteins
    initialize_proteins(session.proteins)
    session.mixture_name = Path(file.filename or "Unknown").stem

    if history and enzyme_index is not None:
        session.enzyme_index = enzyme_index
        session.account.records = history
        session.phase = SessionPhase.RUNNING
        session.step = len(history) - 1  # subtract initial record
    else:
        session.phase = SessionPhase.ENZYME_SELECTION

    return session.to_state_dict()


@router.get("/{session_id}/state")
async def get_state(
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Get the full state snapshot of a session."""
    return session.to_state_dict()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> None:
    """Delete/abandon a session."""
    store.delete(session_id)


@router.post("/{session_id}/choose-mixture")
async def choose_mixture(
    request: ChooseMixtureRequest,
    session: PurificationSession = Depends(get_session),
    data_dir: Path = Depends(get_data_dir),
) -> dict:
    """Select a protein mixture to work with."""
    if session.phase != SessionPhase.SPLASH:
        raise HTTPException(status_code=409, detail="Mixture already chosen")

    try:
        mixture_path = resolve_mixture_path(data_dir, request.name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Mixture '{request.name}' not found")

    session.proteins = load_mixture(mixture_path)
    initialize_proteins(session.proteins)
    session.mixture_name = request.name
    session.phase = SessionPhase.ENZYME_SELECTION
    return session.to_state_dict()


@router.post("/{session_id}/choose-enzyme")
async def choose_enzyme(
    request: ChooseEnzymeRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Select the target enzyme to purify."""
    if session.phase != SessionPhase.ENZYME_SELECTION:
        raise HTTPException(status_code=409, detail="Not in enzyme selection phase")

    if not (0 <= request.enzyme_index < len(session.proteins)):
        raise HTTPException(status_code=422, detail="Invalid enzyme index")

    session.enzyme_index = request.enzyme_index
    session.account.get_initial_record(session.proteins, session.enzyme_index)
    session.phase = SessionPhase.RUNNING
    return session.to_state_dict()
