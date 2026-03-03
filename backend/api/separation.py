"""Separation technique endpoints. Spec 4."""
from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_session
from ..engine import separation
from ..engine.constants import COST_AMMONIUM_SULFATE, COST_HEAT_TREATMENT
from ..engine.enums import (
    GradientType,
    IonExchangeMedia,
    SeparationType,
)
from ..engine.session import PurificationSession
from .schemas import ASChoiceRequest, SeparationRequest

router = APIRouter(prefix="/api/sessions", tags=["separation"])


def _reset_fraction_state(session: PurificationSession) -> None:
    """Reset fraction-related state after a new chromatographic separation."""
    session.has_fractions = True
    session.pooled = False
    session.assayed = False
    session.scale = 0.5
    session.over_diluted = False
    session.two_d_gel = False
    session.show_blot = False
    session.gel_data = None


def _run_ion_exchange(request: SeparationRequest, session: PurificationSession) -> list[list[float]]:
    """Route ion exchange to the correct engine function."""
    media = request.media
    gradient_type = request.gradient_type
    ph = request.ph
    start_grad = request.start_grad
    end_grad = request.end_grad

    if media is None or gradient_type is None or ph is None or start_grad is None or end_grad is None:
        raise HTTPException(status_code=422, detail="Ion exchange requires media, gradient_type, ph, start_grad, end_grad")

    is_anion = media in (IonExchangeMedia.DEAE_CELLULOSE, IonExchangeMedia.Q_SEPHAROSE)
    titratable = media in (IonExchangeMedia.DEAE_CELLULOSE, IonExchangeMedia.CM_CELLULOSE)

    if is_anion:
        if gradient_type == GradientType.SALT:
            return separation.deae_salt_elution(session.proteins, start_grad, end_grad, ph, titratable)
        else:
            return separation.deae_ph_elution(session.proteins, start_grad, end_grad, ph, titratable)
    else:
        if gradient_type == GradientType.SALT:
            return separation.cm_salt_elution(session.proteins, start_grad, end_grad, ph, titratable)
        else:
            return separation.cm_ph_elution(session.proteins, start_grad, end_grad, ph, titratable)


@router.post("/{session_id}/separate")
async def run_separation(
    request: SeparationRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Run a separation technique on the current protein mixture."""
    if not session.can_separate():
        raise HTTPException(status_code=409, detail="Cannot run separation in current state")

    if request.type == SeparationType.AMMONIUM_SULFATE:
        if request.saturation is None:
            raise HTTPException(status_code=422, detail="Ammonium sulfate requires saturation")
        result = separation.ammonium_sulfate(session.proteins, request.saturation)
        session.as_result = result
        session.pooled = False
        session.separation_title = "Ammonium sulfate"
        return session.to_state_dict()

    if request.type == SeparationType.HEAT_TREATMENT:
        if request.temperature is None or request.duration is None:
            raise HTTPException(status_code=422, detail="Heat treatment requires temperature and duration")
        separation.heat_treatment(session.proteins, request.temperature, request.duration)
        session.account.add_step("Heat treatment", session.proteins, session.enzyme_index, COST_HEAT_TREATMENT)
        session.step += 1
        session.separation_title = "Heat treatment"
        failure = session.account.check_failure(session.proteins, session.enzyme_index)
        if failure:
            session.phase = session.phase.FINISHED
        elif session.account.check_success():
            session.phase = session.phase.FINISHED
        return session.to_state_dict()

    if request.type == SeparationType.GEL_FILTRATION:
        if request.matrix is None:
            raise HTTPException(status_code=422, detail="Gel filtration requires matrix")
        fractions = separation.gel_filtration(session.proteins, request.matrix)
        session.fractions = fractions
        _reset_fraction_state(session)
        session.has_gradient = False
        session.separation_title = "Gel filtration"
        return session.to_state_dict()

    if request.type == SeparationType.ION_EXCHANGE:
        fractions = _run_ion_exchange(request, session)
        session.fractions = fractions
        _reset_fraction_state(session)
        session.has_gradient = True
        session.gradient_start = request.start_grad or 0.0
        session.gradient_end = request.end_grad or 0.0
        session.gradient_type = (request.gradient_type or GradientType.SALT).value
        session.separation_title = "Ion exchange"
        return session.to_state_dict()

    if request.type == SeparationType.HIC:
        start = request.start_grad
        end = request.end_grad
        medium = request.medium
        if start is None or end is None or medium is None:
            raise HTTPException(status_code=422, detail="HIC requires start_grad, end_grad, medium")

        if not request.confirmed:
            precip = separation.check_hic_precipitation(session.proteins, start)
            if precip >= 0.001:
                session.hic_precipitation = precip
                return session.to_state_dict()

        session.hic_precipitation = 0.0
        fractions = separation.hic(session.proteins, start, end, medium)
        session.fractions = fractions
        _reset_fraction_state(session)
        session.has_gradient = True
        session.gradient_start = start
        session.gradient_end = end
        session.gradient_type = "salt"
        session.separation_title = "HIC"
        return session.to_state_dict()

    if request.type == SeparationType.AFFINITY:
        if request.ligand is None or request.elution is None:
            raise HTTPException(status_code=422, detail="Affinity requires ligand and elution")
        fractions = separation.affinity(session.proteins, session.enzyme_index, request.ligand, request.elution)
        session.fractions = fractions
        _reset_fraction_state(session)
        session.has_gradient = False
        session.separation_title = "Affinity"
        return session.to_state_dict()

    raise HTTPException(status_code=422, detail=f"Unknown separation type: {request.type}")


@router.post("/{session_id}/as-choice")
async def as_choice(
    request: ASChoiceRequest,
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Choose soluble or insoluble fraction after ammonium sulfate precipitation."""
    if session.as_result is None:
        raise HTTPException(status_code=409, detail="No ammonium sulfate result pending")

    chosen = session.as_result[request.choice]
    for i, p in enumerate(session.proteins):
        p.amount = chosen[i]

    session.as_result = None
    session.pooled = True
    session.account.add_step("Ammonium sulfate", session.proteins, session.enzyme_index, COST_AMMONIUM_SULFATE)
    session.step += 1

    failure = session.account.check_failure(session.proteins, session.enzyme_index)
    if failure:
        session.phase = session.phase.FINISHED
    elif session.account.check_success():
        session.phase = session.phase.FINISHED

    return session.to_state_dict()


@router.post("/{session_id}/abandon-step")
async def abandon_step(
    session: PurificationSession = Depends(get_session),
) -> dict:
    """Discard current separation and return to pooled state."""
    session.has_fractions = False
    session.pooled = True
    session.fractions = []
    session.gel_data = None
    session.as_result = None
    session.assayed = False
    session.scale = 0.5
    session.over_diluted = False
    session.two_d_gel = False
    session.show_blot = False
    session.hic_precipitation = 0.0
    return session.to_state_dict()
