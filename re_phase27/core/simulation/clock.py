"""Deterministic simulation clock."""
from typing import Dict, Any


class SimulationClock:
    def __init__(self, time_step: float = 0.1):
        self.time_step: float = time_step  # dt per tick in seconds
        self.current_time: float = 0.0
        self.tick_count: int = 0
        self.is_paused: bool = False
        self.time_scale: float = 1.0  # multiplier: 0.5x, 1x, 2x, 5x

    def tick(self) -> float:
        """Advance time by time_step if not paused. Returns new current_time."""
        if not self.is_paused:
            self.current_time += self.time_step
            self.tick_count += 1
        return self.current_time

    def step(self) -> float:
        """Advance exactly one tick even if paused (single-step mode)."""
        return self.force_step()

    def force_step(self) -> float:
        """Explicitly advance exactly one tick even when simulation is paused."""
        self.current_time += self.time_step
        self.tick_count += 1
        return self.current_time

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def reset(self):
        self.current_time = 0.0
        self.tick_count = 0
        self.is_paused = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_time": round(self.current_time, 2),
            "tick_count": self.tick_count,
            "is_paused": self.is_paused,
            "time_step": self.time_step,
            "time_scale": self.time_scale,
        }
