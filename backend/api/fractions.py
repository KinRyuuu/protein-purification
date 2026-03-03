"""Fraction operations. Spec 4.10, 5."""
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_session
from ..engine import separation
from ..engine.constants import (
    COST_ASSAY,
    COST_DILUTION,
    COST_GEL_FILTRATION,
    COST_ION_EXCHANGE,
    COST_HIC,
    COST_AFFINITY,
    DISPLAY_FRACTIONS,
    MAX_DILUTION,
)
from ..engine.enums import SessionPhase
from ..engine.session import PurificationSession
from .schemas import PoolRequest

router = APIRouter(prefix="/api/sessions", tags=["fractions"])

_TECHNIQUE_COSTS: dict[str, float] = {
    "Gel filtration": COST_GEL_FILTRATION,
    "Ion exchange": COST_ION_EXCHANGE,
    "HIC": COST_HIC,
    "Affinity": COST_AFFINITY,
}


@router.post("/{session_id}/assay")
async def run_assay(
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Run enzyme assay on current fractions."""
    if not session.can_assay():
        raise HTTPException(status_code=409, detail="Cannot assay in current state")
    session.assayed = True
    session.account.total_cost += COST_ASSAY
    return session.to_state_dict()


@router.post("/{session_id}/dilute")
async def dilute(
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Dilute fractions (2x scale increase)."""
    if not session.can_dilute():
        raise HTTPException(status_code=409, detail="Cannot dilute in current state")
    session.scale *= 2.0
    if session.scale >= MAX_DILUTION:
        session.over_diluted = True
    session.account.total_cost += COST_DILUTION
    return session.to_state_dict()


@router.post("/{session_id}/pool")
async def pool(
    request: PoolRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Pool a range of fractions."""
    if not session.can_pool():
        raise HTTPException(status_code=409, detail="Cannot pool in current state")

    if not (1 <= request.start <= request.end <= DISPLAY_FRACTIONS):
        raise HTTPException(status_code=422, detail=f"Fraction range must be 1-{DISPLAY_FRACTIONS}")

    separation.pool_fractions(session.proteins, session.fractions, request.start, request.end)

    cost = _TECHNIQUE_COSTS.get(session.separation_title, COST_GEL_FILTRATION)
    session.account.add_step(session.separation_title, session.proteins, session.enzyme_index, cost)
    session.step += 1

    session.pooled = True
    session.has_fractions = False
    session.scale = 0.5
    session.fractions = []
    session.gel_data = None

    failure = session.account.check_failure(session.proteins, session.enzyme_index)
    if failure:
        session.phase = SessionPhase.FINISHED
    elif session.account.check_success():
        session.phase = SessionPhase.FINISHED

    return session.to_state_dict()
