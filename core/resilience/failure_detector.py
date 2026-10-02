"""Observable failure detection for robots and communication.

Phase 13 deliberately separates *detection* from fault injection. The detector
consumes observable robot/network behavior and records fault_time,
detection_time, and detection_latency for every detected condition.
"""
from typing import Dict, List, Optional, Any
from core.models.robot import Robot, RobotState
from core.models.incident import Incident, IncidentSeverity


class FailureDetector:
    def __init__(
        self,
        heartbeat_timeout: float = 2.0,
        network_loss_threshold: float = 0.50,
        network_latency_threshold: float = 0.50,
    ):
        self.heartbeat_timeout = float(heartbeat_timeout)
        self.network_loss_threshold = float(network_loss_threshold)
        self.network_latency_threshold = float(network_latency_threshold)
        self.detected_failures: Dict[str, float] = {}
        self.detection_records: List[Dict[str, Any]] = []
        self._last_sent = 0
        self._last_dropped = 0
        self._last_partitioned = False
        self._network_condition_since: Dict[str, float] = {}
        # condition key -> one authoritative active incident id
        self._active_network_incidents: Dict[str, str] = {}

    def _incident(self, incident_id: str, timestamp: float, entity: str, fault: str,
                  severity: IncidentSeverity, state: str, message: str,
                  fault_time: float) -> Incident:
        detection_latency = max(0.0, float(timestamp) - float(fault_time))
        self.detection_records.append({
            "entity": entity, "fault": fault,
            "fault_time": float(fault_time),
            "detection_time": float(timestamp),
            "detection_latency": detection_latency,
        })
        inc = Incident(incident_id=incident_id, timestamp=timestamp, entity=entity,
                       fault=fault, severity=severity, state=state, message=message)
        inc.fault_time = float(fault_time)
        inc.detection_time = float(timestamp)
        inc.detection_latency = detection_latency
        inc.lifecycle = "ACTIVE"
        inc.last_observed_time = float(timestamp)
        return inc

    @staticmethod
    def _resolve_incident(inc: Incident, timestamp: float) -> None:
        inc.lifecycle = "RESOLVED"
        inc.resolved_time = float(timestamp)
        inc.last_observed_time = float(timestamp)

    def check_robot_heartbeats(self, robots: Dict[str, Robot], current_time: float) -> List[Incident]:
        incidents: List[Incident] = []
        for rid, robot in robots.items():
            time_since_heartbeat = current_time - robot.last_heartbeat
            if robot.state == RobotState.FAILED:
                if rid not in self.detected_failures:
                    self.detected_failures[rid] = current_time
                    # Explicit FAILED state carries the actual transition time.
                    # Fall back to heartbeat timeout semantics only when it is unavailable.
                    fault_time = (
                        float(robot.failed_at)
                        if robot.failed_at is not None
                        else float(robot.last_heartbeat) + self.heartbeat_timeout
                    )
                    incidents.append(self._incident(
                        f"inc_failure_{rid}_{int(current_time*10)}", current_time, rid,
                        "ROBOT_FAILURE_DETECTED", IncidentSeverity.CRITICAL,
                        robot.state.value,
                        f"Robot {rid} failure detected at simulation time {current_time:.1f}s.",
                        fault_time,
                    ))
                continue
            if time_since_heartbeat > self.heartbeat_timeout:
                if rid not in self.detected_failures:
                    self.detected_failures[rid] = current_time
                    fault_time = float(robot.last_heartbeat) + self.heartbeat_timeout
                    incidents.append(self._incident(
                        f"inc_hb_{rid}_{int(current_time*10)}", current_time, rid,
                        "HEARTBEAT_TIMEOUT", IncidentSeverity.CRITICAL, robot.state.value,
                        f"Robot {rid} heartbeat timeout ({time_since_heartbeat:.1f}s > {self.heartbeat_timeout}s)",
                        fault_time,
                    ))
            if robot.battery < 10.0 and robot.state != RobotState.DEGRADED:
                incidents.append(self._incident(
                    f"inc_bat_{rid}_{int(current_time*10)}", current_time, rid,
                    "CRITICAL_LOW_BATTERY", IncidentSeverity.WARNING, robot.state.value,
                    f"Robot {rid} battery critical at {robot.battery:.1f}%", current_time,
                ))
        return incidents

    def check_network(self, network_metrics: Dict[str, Any], current_time: float) -> List[Incident]:
        """Detect network faults from observations with edge-triggered incidents."""
        now = float(current_time)
        incidents: List[Incident] = []
        sent = int(network_metrics.get("messages_sent", 0))
        dropped = int(network_metrics.get("messages_dropped", 0))
        latency = float(network_metrics.get("latency_ms", 0.0)) / 1000.0
        partitioned = bool(network_metrics.get("is_partitioned", False))
        delta_sent = max(0, sent - self._last_sent)
        delta_dropped = max(0, dropped - self._last_dropped)
        self._last_sent, self._last_dropped = sent, dropped
        observed_loss = delta_dropped / delta_sent if delta_sent > 0 else 0.0
        conditions = {
            "PACKET_LOSS_DETECTED": observed_loss >= self.network_loss_threshold,
            "HIGH_NETWORK_LATENCY": latency >= self.network_latency_threshold,
            "NETWORK_PARTITION_DETECTED": partitioned,
        }
        for key, active in conditions.items():
            if active:
                self._network_condition_since.setdefault(key, now)
            else:
                self._network_condition_since.pop(key, None)
                active_id = self._active_network_incidents.pop(key, None)
                if active_id:
                    # The object is resolved by mutating the authoritative incident
                    # held in the detector's active registry below.
                    active_inc = getattr(self, "_incident_objects", {}).get(active_id)
                    if active_inc is not None:
                        self._resolve_incident(active_inc, now)
        if not hasattr(self, "_incident_objects"):
            self._incident_objects: Dict[str, Incident] = {}

        def emit_or_update(key: str, fault: str, severity: IncidentSeverity, state: str, message: str) -> None:
            active_id = self._active_network_incidents.get(key)
            if active_id:
                inc = self._incident_objects.get(active_id)
                if inc is not None:
                    inc.last_observed_time = now
                    inc.message = message
                return
            fault_time = self._network_condition_since[key]
            inc = self._incident(
                f"inc_net_{key.lower()}_{int(now*10)}", now, "NETWORK", fault,
                severity, state, message, fault_time,
            )
            self._active_network_incidents[key] = inc.incident_id
            self._incident_objects[inc.incident_id] = inc
            incidents.append(inc)

        if conditions["PACKET_LOSS_DETECTED"]:
            emit_or_update(
                "PACKET_LOSS_DETECTED", "PACKET_LOSS_DETECTED", IncidentSeverity.WARNING, "DEGRADED",
                f"Observed packet loss {observed_loss*100:.1f}% over the current transport window.",
            )
        if conditions["HIGH_NETWORK_LATENCY"]:
            emit_or_update(
                "HIGH_NETWORK_LATENCY", "HIGH_NETWORK_LATENCY", IncidentSeverity.WARNING, "DEGRADED",
                f"Observed network latency {latency*1000:.1f}ms.",
            )
        if partitioned and not self._last_partitioned:
            emit_or_update(
                "NETWORK_PARTITION_DETECTED", "NETWORK_PARTITION_DETECTED", IncidentSeverity.CRITICAL,
                "LOCAL_AUTONOMY", "Observed network partition in the transport layer.",
            )
        self._last_partitioned = partitioned
        return incidents

    def active_incidents(self) -> Dict[str, Incident]:
        return {key: self._incident_objects[iid] for key, iid in self._active_network_incidents.items()
                if iid in getattr(self, "_incident_objects", {})}

    def snapshot(self) -> Dict[str, Any]:
        return {
            "detected_failures": dict(self.detected_failures),
            "detection_records": list(self.detection_records),
            "last_sent": self._last_sent,
            "last_dropped": self._last_dropped,
            "last_partitioned": self._last_partitioned,
            "network_condition_since": dict(self._network_condition_since),
            "active_network_incidents": dict(self._active_network_incidents),
        }

    def restore(self, data: Dict[str, Any]) -> None:
        self.detected_failures = {str(k): float(v) for k, v in data.get("detected_failures", {}).items()}
        self.detection_records = [dict(v) for v in data.get("detection_records", [])]
        self._last_sent = int(data.get("last_sent", 0))
        self._last_dropped = int(data.get("last_dropped", 0))
        self._last_partitioned = bool(data.get("last_partitioned", False))
        self._network_condition_since = {str(k): float(v) for k, v in data.get("network_condition_since", {}).items()}
        self._active_network_incidents = {str(k): str(v) for k, v in data.get("active_network_incidents", {}).items()}
        # Incident objects are rebound by SimulationEngine after its incident history is restored.
        self._incident_objects = {}
