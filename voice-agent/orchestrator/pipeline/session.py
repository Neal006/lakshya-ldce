from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
import time


class SessionState(str, Enum):
    greeting = "greeting"
    collecting = "collecting"
    confirming = "confirming"
    classifying = "classifying"
    resolving = "resolving"
    ticket_created = "ticket_created"
    done = "done"
    error = "error"


@dataclass
class CallSession:
    call_sid: str
    state: SessionState = SessionState.greeting
    transcript: list[str] = field(default_factory=list)
    extracted_data: dict = field(default_factory=dict)
    classification: dict = field(default_factory=dict)
    resolution: dict = field(default_factory=dict)
    ticket_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    turn_count: int = 0
    max_turns: int = 4

    @property
    def full_transcript(self) -> str:
        return " ".join(self.transcript)

    def is_expired(self, timeout: int = 300) -> bool:
        return (time.time() - self.created_at) > timeout


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, CallSession] = {}

    def create_session(self, call_sid: str) -> CallSession:
        session = CallSession(call_sid=call_sid)
        self._sessions[call_sid] = session
        return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        return self._sessions.get(call_sid)

    def close_session(self, call_sid: str) -> Optional[CallSession]:
        return self._sessions.pop(call_sid, None)

    def update_state(self, call_sid: str, new_state: SessionState) -> Optional[CallSession]:
        session = self._sessions.get(call_sid)
        if session:
            session.state = new_state
        return session

    def cleanup_expired(self, timeout: int = 300) -> int:
        expired = [sid for sid, s in self._sessions.items() if s.is_expired(timeout)]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)