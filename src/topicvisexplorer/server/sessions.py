"""In-memory session store with LRU eviction.

Replaces the legacy IP-based ``MaxClientQueue`` (which broke behind
proxies and load balancers). Sessions are keyed by an opaque token
served as a cookie; the eviction policy is **least recently accessed**,
not arrival-time FIFO, so an active user is never evicted.

This module is intentionally synchronous + threadsafe so it works
inside a single-process uvicorn workers configuration. Multi-worker
deployments need a shared store (Redis / DB); that's deferred to v1.1.
"""

from __future__ import annotations

import secrets
import threading
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


@dataclass
class SessionState:
    """Per-session storage replacing the legacy global dicts."""

    session_id: str
    created_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)
    single_corpus: dict[str, Any] = field(default_factory=dict)
    multi_corpora: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)


class SessionStore:
    """Threadsafe LRU-bounded session container.

    Parameters
    ----------
    max_sessions:
        Maximum number of sessions kept in memory. When the (max+1)-th
        new session is created, the least-recently-accessed session is
        evicted.
    ttl_seconds:
        Sessions inactive for more than ``ttl_seconds`` are evicted on
        the next access. ``None`` disables time-based eviction.
    """

    def __init__(self, *, max_sessions: int = 16, ttl_seconds: float | None = 3600.0) -> None:
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds
        self._sessions: OrderedDict[str, SessionState] = OrderedDict()
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)

    def new(self) -> SessionState:
        """Create a fresh session with a cryptographically random id."""
        sid = f"sess-{uuid.uuid4().hex[:12]}-{secrets.token_urlsafe(8)}"
        with self._lock:
            self._evict_expired_locked()
            while len(self._sessions) >= self.max_sessions:
                evicted_id, _ = self._sessions.popitem(last=False)
                logger.info("Evicted oldest session %s (LRU).", evicted_id)
            state = SessionState(session_id=sid)
            self._sessions[sid] = state
            return state

    def get(self, session_id: str) -> SessionState | None:
        with self._lock:
            self._evict_expired_locked()
            state = self._sessions.get(session_id)
            if state is None:
                return None
            state.last_seen_at = time.time()
            self._sessions.move_to_end(session_id)
            return state

    def get_or_create(self, session_id: str | None) -> SessionState:
        """Get the session, creating a new one if missing/None/unknown."""
        if session_id:
            existing = self.get(session_id)
            if existing is not None:
                return existing
        return self.new()

    def _evict_expired_locked(self) -> None:
        if self.ttl_seconds is None:
            return
        cutoff = time.time() - self.ttl_seconds
        expired = [sid for sid, s in self._sessions.items() if s.last_seen_at < cutoff]
        for sid in expired:
            self._sessions.pop(sid, None)
            logger.info("Evicted expired session %s.", sid)

    def reset(self) -> None:
        """Drop all sessions. Used by tests."""
        with self._lock:
            self._sessions.clear()
