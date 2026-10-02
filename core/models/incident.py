"""Incident and alert model for ResilientEdge."""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class IncidentSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Incident:
    incident_id: str
    timestamp: float
    entity: str  # e.g., "R2", "NETWORK", "PLANNER", "TASK_MGR"
    fault: Optional[str]
    severity: IncidentSeverity
    state: str  # current system or robot state
    message: str

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "incident_id": self.incident_id,
            "timestamp": round(self.timestamp, 2),
            "entity": self.entity,
            "fault": self.fault,
            "severity": self.severity.value,
            "state": self.state,
            "message": self.message,
        }
        if hasattr(self, "fault_time"):
            data["fault_time"] = round(float(self.fault_time), 4)
        if hasattr(self, "detection_time"):
            data["detection_time"] = round(float(self.detection_time), 4)
        if hasattr(self, "detection_latency"):
            data["detection_latency"] = round(float(self.detection_latency), 4)
        if hasattr(self, "lifecycle"):
            data["lifecycle"] = str(self.lifecycle)
        if hasattr(self, "resolved_time"):
            data["resolved_time"] = round(float(self.resolved_time), 4)
        return data
