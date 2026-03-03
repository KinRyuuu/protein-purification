"""PAGE electrophoresis endpoints. Spec 6."""
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_session
from ..engine import gel
from ..engine.constants import COST_1D_PAGE, COST_2D_PAGE
from ..engine.session import PurificationSession
from .schemas import Page1DRequest, Page2DRequest

router = APIRouter(prefix="/api/sessions", tags=["electrophoresis"])


@router.post("/{session_id}/page-1d")
async def run_page_1d(
    request: Page1DRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Run 1D SDS-PAGE on selected fractions."""
    if not session.has_fractions:
        raise HTTPException(status_code=409, detail="No fractions available for PAGE")
    bands = gel.calculate_1d_bands(session.proteins, session.fractions, request.fractions)
    session.account.total_cost += COST_1D_PAGE
    session.gel_data = bands
    session.two_d_gel = False
    return session.to_state_dict()


@router.post("/{session_id}/page-2d")
async def run_page_2d(
    request: Page2DRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Run 2D PAGE on a single fraction."""
    if not session.has_fractions:
        raise HTTPException(status_code=409, detail="No fractions available for PAGE")
    spots = gel.calculate_2d_spots(session.proteins, session.fractions, request.fraction)
    session.account.total_cost += COST_2D_PAGE
    session.gel_data = spots
    session.two_d_gel = True
    return session.to_state_dict()


@router.post("/{session_id}/toggle-stain")
async def toggle_stain(
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Toggle between Coomassie and immunoblot staining."""
    session.show_blot = not session.show_blot
    return session.to_state_dict()
