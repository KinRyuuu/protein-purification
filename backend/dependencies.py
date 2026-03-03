"""FastAPI dependency injection helpers."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, HTTPException

from .config import Settings
from .engine.session import PurificationSession
from .session_store import SessionStore

_store: SessionStore | None = None

# Project root: protein_purification_web/
_WEB_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    return Settings()


def get_data_dir(settings: Settings = Depends(get_settings)) -> Path:
    """Resolve the data_dir setting relative to the web project root."""
    data_path = Path(settings.data_dir)
    if data_path.is_absolute():
        return data_path
    return _WEB_PROJECT_ROOT / data_path


def get_session_store() -> SessionStore:
    """Return the global SessionStore singleton."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store


def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> PurificationSession:
    """Resolve a session by path parameter, raising 404 if missing."""
    session = store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
