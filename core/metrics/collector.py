"""Authoritative simulation metrics collected from actual events/state transitions."""
from __future__ import annotations
from typing import Dict, List, Any
import math


class MetricsCollector:
    def __init__(self):
        self.task_completion_times: List[float] = []  # creation -> completion
        self.task_execution_times: List[float] = []
        self.task_waiting_times: List[float] = []
        self.route_lengths: List[float] = []
        self.planning_latencies: List[float] = []
        self.failure_detection_times: List[float] = []
        self.task_reassignment_times: List[float] = []
        self.deadlock_recovery_times: List[float] = []
        self.recovery_detection_times: List[float] = []
        self.recovery_reassignment_times: List[float] = []
        self.recovery_replanning_times: List[float] = []
        self.recovery_total_times: List[float] = []
        self.network_latency_samples_ms: List[float] = []
        self.conflict_count = 0
        self.collision_count = 0
        self.deadlock_count = 0
        self.task_reassignments = 0
        self.messages_sent = 0
        self.messages_dropped = 0
        self.stale_messages = 0
        self.messages_delivered = 0
        self.messages_duplicated = 0
        self.messages_reordered = 0
        self.total_energy_consumed = 0.0
        self.available_robot_time = 0.0
        self.total_robot_time = 0.0
        self.idle_robot_time = 0.0
        self.waiting_robot_time = 0.0
        self.total_distance = 0.0
        self.reroute_count = 0

    def snapshot_dict(self) -> Dict[str, Any]:
        """Serialize all mutable metric state required for exact snapshot restoration."""
        return {
            "task_completion_times": list(self.task_completion_times),
            "task_execution_times": list(self.task_execution_times),
            "task_waiting_times": list(self.task_waiting_times),
            "route_lengths": list(self.route_lengths),
            "planning_latencies": list(self.planning_latencies),
            "failure_detection_times": list(self.failure_detection_times),
            "task_reassignment_times": list(self.task_reassignment_times),
            "deadlock_recovery_times": list(self.deadlock_recovery_times),
            "recovery_detection_times": list(self.recovery_detection_times),
            "recovery_reassignment_times": list(self.recovery_reassignment_times),
            "recovery_replanning_times": list(self.recovery_replanning_times),
            "recovery_total_times": list(self.recovery_total_times),
            "network_latency_samples_ms": list(self.network_latency_samples_ms),
            "conflict_count": self.conflict_count,
            "collision_count": self.collision_count,
            "deadlock_count": self.deadlock_count,
            "task_reassignments": self.task_reassignments,
            "messages_sent": self.messages_sent,
            "messages_dropped": self.messages_dropped,
            "stale_messages": self.stale_messages,
            "messages_delivered": self.messages_delivered,
            "messages_duplicated": self.messages_duplicated,
            "messages_reordered": self.messages_reordered,
            "total_energy_consumed": self.total_energy_consumed,
            "available_robot_time": self.available_robot_time,
            "total_robot_time": self.total_robot_time,
            "idle_robot_time": self.idle_robot_time,
            "waiting_robot_time": self.waiting_robot_time,
            "total_distance": self.total_distance,
            "reroute_count": self.reroute_count,
        }

    def restore_snapshot(self, data: Dict[str, Any]) -> None:
        for name in (
            "task_completion_times", "task_execution_times", "task_waiting_times",
            "route_lengths", "planning_latencies", "failure_detection_times",
            "task_reassignment_times", "deadlock_recovery_times", "network_latency_samples_ms",
            "recovery_detection_times", "recovery_reassignment_times", "recovery_replanning_times",
            "recovery_total_times",
        ):
            setattr(self, name, [float(v) for v in data.get(name, [])])
        for name in (
            "conflict_count", "collision_count", "deadlock_count", "task_reassignments",
            "messages_sent", "messages_dropped", "stale_messages",
        ):
            setattr(self, name, int(data.get(name, 0)))
        for name in ("total_energy_consumed", "available_robot_time", "total_robot_time", "idle_robot_time", "waiting_robot_time", "total_distance"):
            setattr(self, name, float(data.get(name, 0.0)))
        self.reroute_count = int(data.get("reroute_count", 0))
        self.messages_delivered = int(data.get("messages_delivered", 0))
        self.messages_duplicated = int(data.get("messages_duplicated", 0))
        self.messages_reordered = int(data.get("messages_reordered", 0))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_count": self.conflict_count,
            "collision_count": self.collision_count,
            "deadlock_count": self.deadlock_count,
            "task_reassignments": self.task_reassignments,
            "messages_sent": self.messages_sent,
            "messages_dropped": self.messages_dropped,
            "stale_messages": self.stale_messages,
            "messages_delivered": self.messages_delivered,
            "messages_duplicated": self.messages_duplicated,
            "messages_reordered": self.messages_reordered,
            "planning_latency": self._mean(self.planning_latencies),
            "network_latency": self._network_summary(),
            "total_energy_consumed": round(self.total_energy_consumed, 4),
            "total_distance": round(self.total_distance, 3),
            "reroute_count": self.reroute_count,
            "utilization": round(((self.total_robot_time - self.idle_robot_time - self.waiting_robot_time) / self.total_robot_time * 100.0) if self.total_robot_time else 0.0, 3),
        }

    @staticmethod
    def _mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _percentile(values: List[float], q: float) -> float | None:
        if not values:
            return None
        xs = sorted(values)
        if len(xs) == 1:
            return xs[0]
        pos = (len(xs) - 1) * q
        lo, hi = math.floor(pos), math.ceil(pos)
        if lo == hi:
            return xs[lo]
        return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)

    def _network_summary(self) -> Dict[str, Any]:
        vals = self.network_latency_samples_ms
        return {
            "mean_ms": round(self._mean(vals), 3),
            "median_ms": round(self._percentile(vals, 0.50) or 0.0, 3),
            "p95_ms": round(self._percentile(vals, 0.95) or 0.0, 3),
            "sample_count": len(vals),
        }

    def sync_network_metrics(self, network: Dict[str, Any]) -> None:
        """Copy authoritative transport counters into the metrics collector.

        NetworkSimulator remains the source of truth; this method deliberately
        avoids incrementing counters independently and therefore cannot drift
        from the transport layer.
        """
        self.messages_sent = int(network.get("messages_sent", self.messages_sent))
        self.messages_dropped = int(network.get("messages_dropped", self.messages_dropped))
        self.messages_delivered = int(network.get("messages_delivered", self.messages_delivered))
        self.messages_duplicated = int(network.get("messages_duplicated", self.messages_duplicated))
        self.messages_reordered = int(network.get("messages_reordered", self.messages_reordered))
        self.stale_messages = int(network.get("stale_messages", self.stale_messages))
        samples = network.get("latency_samples_ms")
        if samples is not None:
            self.network_latency_samples_ms = [float(v) for v in samples]

    def record_conflict(self): self.conflict_count += 1
    def record_collision(self): self.collision_count += 1
    def record_deadlock(self, recovery_time: float):
        self.deadlock_count += 1
        self.deadlock_recovery_times.append(recovery_time)
    def record_failure_detection(self, latency: float): self.failure_detection_times.append(latency)
    def record_task_reassignment(self, duration: float):
        self.task_reassignments += 1
        self.task_reassignment_times.append(duration)

    def record_recovery_detection(self, duration: float):
        self.recovery_detection_times.append(max(0.0, float(duration)))

    def record_recovery_reassignment(self, duration: float):
        self.recovery_reassignment_times.append(max(0.0, float(duration)))

    def record_recovery_replanning(self, duration: float):
        self.recovery_replanning_times.append(max(0.0, float(duration)))

    def record_recovery_total(self, duration: float):
        self.recovery_total_times.append(max(0.0, float(duration)))
    def record_planning_latency(self, duration_ms: float): self.planning_latencies.append(duration_ms)
    def record_reroute(self): self.reroute_count += 1
    def record_network_latency(self, latency_ms: float): self.network_latency_samples_ms.append(latency_ms)
    def record_task_completion(self, waiting_time: float, execution_time: float, route_length: float, completion_time: float | None = None):
        self.task_waiting_times.append(waiting_time)
        self.task_execution_times.append(execution_time)
        if completion_time is not None:
            self.task_completion_times.append(completion_time)
        self.route_lengths.append(route_length)
        self.total_distance += float(route_length)

    def record_robot_time(self, dt: float, robot_states: List[str], failed_state: str = "FAILED"):
        count = len(robot_states)
        self.total_robot_time += count * dt
        self.available_robot_time += sum(1 for s in robot_states if s != failed_state) * dt
        self.idle_robot_time += sum(1 for s in robot_states if s == "IDLE") * dt
        self.waiting_robot_time += sum(1 for s in robot_states if s == "WAITING") * dt

    def get_summary(self, total_tasks: int, completed_tasks: int, current_time: float, resilience_state_durations: Dict[str, float], failed_tasks: int = 0) -> Dict[str, Any]:
        completion_times = self.task_completion_times
        makespan = max(completion_times) if completion_times else current_time
        avg_completion = self._mean(completion_times)
        avg_wait = self._mean(self.task_waiting_times)
        avg_exec = self._mean(self.task_execution_times)
        avg_route = self._mean(self.route_lengths)
        avg_det = self._mean(self.failure_detection_times)
        avg_reassign = self._mean(self.task_reassignment_times)
        avg_dl = self._mean(self.deadlock_recovery_times)
        avg_recovery_detection = self._mean(self.recovery_detection_times)
        avg_recovery_reassignment = self._mean(self.recovery_reassignment_times)
        avg_recovery_replanning = self._mean(self.recovery_replanning_times)
        avg_recovery_total = self._mean(self.recovery_total_times)
        task_failures = max(0, int(failed_tasks))
        network = self._network_summary()
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "task_completion_rate": round((completed_tasks / total_tasks * 100.0) if total_tasks else 0.0, 2),
            "task_failure_rate": round((task_failures / total_tasks * 100.0) if total_tasks else 0.0, 2),
            "pending_task_count": max(0, total_tasks - completed_tasks - task_failures),
            "makespan": round(makespan, 3),
            "average_task_completion_time": round(avg_completion, 3),
            "average_waiting_time": round(avg_wait, 3),
            "average_execution_time": round(avg_exec, 3),
            "average_route_length": round(avg_route, 3),
            "throughput_tasks_per_minute": round((completed_tasks / makespan * 60.0) if makespan > 0 else 0.0, 4),
            "robot_availability": round((self.available_robot_time / self.total_robot_time * 100.0) if self.total_robot_time else 100.0, 3),
            "idle_time": round(self.idle_robot_time, 3),
            "waiting_time": round(self.waiting_robot_time, 3),
            "planning_latency_ms": round(self._mean(self.planning_latencies), 4),
            "planning_latency_sample_count": len(self.planning_latencies),
            "planning_latency_p95_ms": round(self._percentile(self.planning_latencies, 0.95) or 0.0, 4),
            "conflict_count": self.conflict_count,
            "collision_count": self.collision_count,
            "deadlock_count": self.deadlock_count,
            "deadlock_recovery_time": round(avg_dl, 3),
            "failure_detection_time": round(avg_det, 3),
            "task_reassignment_time": round(avg_reassign, 3),
            "recovery_detection_time": round(avg_recovery_detection, 3),
            "recovery_reassignment_time": round(avg_recovery_reassignment, 3),
            "recovery_replanning_time": round(avg_recovery_replanning, 3),
            "recovery_time": round(avg_recovery_total, 3),
            "normal_duration": round(float(resilience_state_durations.get("NORMAL", 0.0)), 3),
            "degraded_duration": round(float(resilience_state_durations.get("DEGRADED", 0.0)), 3),
            "local_autonomy_duration": round(float(resilience_state_durations.get("LOCAL_AUTONOMY", 0.0)), 3),
            "resync_duration": round(float(resilience_state_durations.get("RESYNC", 0.0)), 3),
            "failed_duration": round(float(resilience_state_durations.get("FAILED", 0.0)), 3),
            "task_reassignments": self.task_reassignments,
            "messages_sent": self.messages_sent,
            "messages_dropped": self.messages_dropped,
            "messages_delivered": self.messages_delivered,
            "messages_duplicated": self.messages_duplicated,
            "messages_reordered": self.messages_reordered,
            "packet_loss_rate": round((self.messages_dropped / self.messages_sent * 100.0) if self.messages_sent else 0.0, 4),
            "network_latency_ms": network["mean_ms"],
            "network_latency_p50_ms": network["median_ms"],
            "network_latency_p95_ms": network["p95_ms"],
            "network_latency_sample_count": network["sample_count"],
            "stale_messages": self.stale_messages,
            "degraded_duration": round(resilience_state_durations.get("DEGRADED", 0.0), 3),
            "local_autonomy_duration": round(resilience_state_durations.get("LOCAL_AUTONOMY", 0.0), 3),
            "resync_duration": round(resilience_state_durations.get("RESYNC", 0.0), 3),
            "total_energy_consumed": round(self.total_energy_consumed, 4),
            "total_distance": round(self.total_distance, 3),
            "reroute_count": self.reroute_count,
            "utilization": round(((self.total_robot_time - self.idle_robot_time - self.waiting_robot_time) / self.total_robot_time * 100.0) if self.total_robot_time else 0.0, 3),
        }
