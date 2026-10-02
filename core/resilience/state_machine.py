"""Authoritative resilience state machine for the multi-robot system."""
from enum import Enum
from typing import Dict, List, Any, Optional


class ResilienceState(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    LOCAL_AUTONOMY = "LOCAL_AUTONOMY"
    RECOVERY = "RECOVERY"
    RESYNC = "RESYNC"
    FAILED = "FAILED"


class ResilienceStateMachine:
    """Deterministic, auditable global resilience state machine.

    The machine owns the global resilience state. Every transition is recorded
    with timestamp, entity, old state, new state, and reason so telemetry and
    snapshot/restore can reproduce the state history.
    """

    _ALLOWED = {
        ResilienceState.NORMAL: {
            ResilienceState.DEGRADED, ResilienceState.LOCAL_AUTONOMY,
            ResilienceState.RECOVERY, ResilienceState.FAILED,
        },
        ResilienceState.DEGRADED: {
            ResilienceState.NORMAL, ResilienceState.LOCAL_AUTONOMY,
            ResilienceState.RECOVERY, ResilienceState.RESYNC, ResilienceState.FAILED,
        },
        ResilienceState.LOCAL_AUTONOMY: {
            ResilienceState.DEGRADED, ResilienceState.RECOVERY,
            ResilienceState.RESYNC, ResilienceState.FAILED,
        },
        ResilienceState.RECOVERY: {
            ResilienceState.NORMAL, ResilienceState.DEGRADED,
            ResilienceState.LOCAL_AUTONOMY, ResilienceState.RESYNC,
            ResilienceState.FAILED,
        },
        ResilienceState.RESYNC: {
            ResilienceState.NORMAL, ResilienceState.DEGRADED,
            ResilienceState.LOCAL_AUTONOMY, ResilienceState.RECOVERY,
            ResilienceState.FAILED,
        },
        ResilienceState.FAILED: {
            ResilienceState.RECOVERY, ResilienceState.RESYNC,
        },
    }

    def __init__(self):
        self.current_state: ResilienceState = ResilienceState.NORMAL
        self.transitions: List[Dict[str, Any]] = []
        self.state_durations: Dict[str, float] = {s.value: 0.0 for s in ResilienceState}
        self.last_transition_time: float = 0.0

    def transition(
        self,
        new_state: ResilienceState,
        current_time: float,
        reason: str,
        entity: str = "SYSTEM",
        force: bool = False,
    ) -> bool:
        """Transition state and emit one auditable transition record.

        Returns True only when a state change occurred. Invalid transitions are
        rejected unless ``force`` is explicitly requested by recovery logic.
        """
        new_state = ResilienceState(new_state)
        if new_state == self.current_state:
            return False
        if not force and new_state not in self._ALLOWED[self.current_state]:
            raise ValueError(
                f"invalid resilience transition: {self.current_state.value} -> {new_state.value}"
            )

        now = float(current_time)
        elapsed = now - self.last_transition_time
        self.state_durations[self.current_state.value] += max(0.0, elapsed)
        old_state = self.current_state
        event = {
            "timestamp": round(now, 4),
            "entity": str(entity),
            "old_state": old_state.value,
            "new_state": new_state.value,
            "reason": str(reason),
        }
        self.transitions.append(event)
        self.current_state = new_state
        self.last_transition_time = now
        return True

    def update_durations(self, current_time: float):
        now = float(current_time)
        elapsed = now - self.last_transition_time
        if elapsed > 0:
            self.state_durations[self.current_state.value] += elapsed
            self.last_transition_time = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "state_durations": {k: round(v, 4) for k, v in self.state_durations.items()},
            "recent_transitions": self.transitions[-50:],
            "last_transition_time": round(self.last_transition_time, 4),
        }

    def restore_snapshot(self, data: Dict[str, Any], current_time: float) -> None:
        try:
            self.current_state = ResilienceState(data.get("current_state", "NORMAL"))
        except ValueError as exc:
            raise ValueError(f"invalid resilience state: {data.get('current_state')!r}") from exc
        raw_durations = data.get("state_durations", {})
        self.state_durations = {
            s.value: float(raw_durations.get(s.value, 0.0)) for s in ResilienceState
        }
        self.transitions = []
        for event in data.get("recent_transitions", []):
            self.transitions.append({
                "timestamp": float(event.get("timestamp", 0.0)),
                "entity": str(event.get("entity", "SYSTEM")),
                "old_state": str(event.get("old_state", "NORMAL")),
                "new_state": str(event.get("new_state", self.current_state.value)),
                "reason": str(event.get("reason", "")),
            })
        self.transitions = self.transitions[-50:]
        self.last_transition_time = float(data.get("last_transition_time", current_time))
