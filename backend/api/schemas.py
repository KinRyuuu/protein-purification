"""Pydantic request models for API endpoints."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from ..engine.enums import (
    AffinityLigand,
    ElutionMethod,
    GelMatrix,
    GradientType,
    HICMedia,
    IonExchangeMedia,
    SeparationType,
)


class ChooseMixtureRequest(BaseModel):
    name: str


class ChooseEnzymeRequest(BaseModel):
    enzyme_index: int


class SeparationRequest(BaseModel):
    type: SeparationType
    saturation: float | None = None
    temperature: float | None = None
    duration: float | None = None
    matrix: GelMatrix | None = None
    media: IonExchangeMedia | None = None
    ph: float | None = None
    gradient_type: GradientType | None = None
    start_grad: float | None = None
    end_grad: float | None = None
    medium: HICMedia | None = None
    ligand: AffinityLigand | None = None
    elution: ElutionMethod | None = None
    confirmed: bool = False


class ASChoiceRequest(BaseModel):
    choice: Literal["soluble", "insoluble"]


class PoolRequest(BaseModel):
    start: int
    end: int


class Page1DRequest(BaseModel):
    fractions: list[int]


class Page2DRequest(BaseModel):
    fraction: int
