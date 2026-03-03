"""Mixture listing endpoints. Spec 3.1."""
from pathlib import Path

from fastapi import APIRouter, Depends

from ..dependencies import get_data_dir
from ..engine.mixture_io import list_bundled_mixtures

router = APIRouter(prefix="/api/mixtures", tags=["mixtures"])


@router.get("")
async def list_mixtures(
    data_dir: Path = Depends(get_data_dir),
) -> dict:
    """List available bundled protein mixtures."""
    return {"mixtures": list_bundled_mixtures(data_dir)}
