"""In-memory session store for purification sessions."""
from __future__ import annotations

import time
import uuid

from .engine.session import PurificationSession


class SessionStore:
    """Thread-safe in-memory store for active purification sessions."""

    def __init__(self, timeout_seconds: int = 7200, max_sessions: int = 100) -> None:
        self._sessions: dict[str, PurificationSession] = {}
        self._timeout = timeout_seconds
        self._max_sessions = max_sessions

    def create(self) -> PurificationSession:
        """Create a new session and return it."""
        self.cleanup_expired()
        session_id = uuid.uuid4().hex
        session = PurificationSession(session_id)
        session.created_at = time.time()
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> PurificationSession | None:
        """Retrieve a session by ID, or None if not found / expired."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if time.time() - session.created_at > self._timeout:
            self.delete(session_id)
            return None
        return session

    def delete(self, session_id: str) -> None:
        """Remove a session."""
        self._sessions.pop(session_id, None)

    def cleanup_expired(self) -> None:
        """Remove all sessions that have exceeded the timeout."""
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.created_at > self._timeout
        ]
        for sid in expired:
            del self._sessions[sid]
