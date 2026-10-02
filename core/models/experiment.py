"""Experiment and benchmark run models."""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class Experiment:
    experiment_id: str
    scenario: str
    seed: int = 42
    robot_count: int = 3
    task_count: int = 6
    start_time: float = 0.0
    end_time: Optional[float] = None
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "scenario": self.scenario,
            "seed": self.seed,
            "robot_count": self.robot_count,
            "task_count": self.task_count,
            "start_time": round(self.start_time, 2),
            "end_time": round(self.end_time, 2) if self.end_time is not None else None,
            "status": self.status,
            "metrics": self.metrics,
        }
