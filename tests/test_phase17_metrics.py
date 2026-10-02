from core.metrics.collector import MetricsCollector
from core.simulation.engine import SimulationEngine
from core.resilience.state_machine import ResilienceState, ResilienceStateMachine


def test_phase17_required_metrics_are_event_derived():
    m = MetricsCollector()
    m.record_task_completion(2.0, 5.0, 10.0, completion_time=7.0)
    m.record_conflict()
    m.record_deadlock(3.0)
    m.record_failure_detection(1.5)
    m.record_task_reassignment(2.5)
    m.sync_network_metrics({
        "messages_sent": 10,
        "messages_dropped": 2,
        "messages_delivered": 8,
        "messages_duplicated": 1,
        "messages_reordered": 2,
        "stale_messages": 1,
        "latency_samples_ms": [10, 20, 30],
    })
    out = m.get_summary(2, 1, 7.0, {"NORMAL": 7.0, "DEGRADED": 0.0}, 0)
    for key in (
        "task_completion_rate", "makespan", "average_waiting_time",
        "average_route_length", "conflict_count", "collision_count",
        "deadlock_count", "deadlock_recovery_time",
        "failure_detection_time", "task_reassignment_time",
        "messages_sent", "messages_dropped", "stale_messages",
        "messages_delivered", "messages_duplicated", "messages_reordered",
        "network_latency_ms", "network_latency_p95_ms",
    ):
        assert key in out
    assert out["task_completion_rate"] == 50.0
    assert out["messages_dropped"] == 2
    assert out["packet_loss_rate"] == 20.0


def test_phase17_network_counters_match_authoritative_transport():
    sim = SimulationEngine(seed=17, time_step=0.1)
    sim.reset(robot_count=2, task_count=0)
    sim.network_sim.send_message("R1", "R2", {"type": "PING"}, 0.0, latency=0.2)
    telemetry = sim.get_telemetry()
    net = telemetry["network"]
    metrics = telemetry["metrics"]
    assert metrics["messages_sent"] == net["messages_sent"]
    assert metrics["messages_dropped"] == net["messages_dropped"]
    assert metrics["messages_delivered"] == net["messages_delivered"]
    assert metrics["messages_duplicated"] == net["messages_duplicated"]
    assert metrics["messages_reordered"] == net["messages_reordered"]


def test_phase17_resilience_duration_is_current_through_telemetry():
    sim = SimulationEngine(seed=17, time_step=1.0)
    sim.reset(robot_count=1, task_count=0)
    sim.clock.current_time = 2.0
    sim.state_machine.transition(ResilienceState.DEGRADED, 2.0, "test")
    sim.clock.current_time = 5.0
    telemetry = sim.get_telemetry()
    assert telemetry["resilience"]["state_durations"]["NORMAL"] == 2.0
    assert telemetry["resilience"]["state_durations"]["DEGRADED"] == 3.0
    assert telemetry["metrics"]["degraded_duration"] == 3.0


def test_phase17_metrics_snapshot_restores_transport_counters():
    m = MetricsCollector()
    m.sync_network_metrics({
        "messages_sent": 4, "messages_dropped": 1, "messages_delivered": 3,
        "messages_duplicated": 2, "messages_reordered": 1, "stale_messages": 1,
        "latency_samples_ms": [5.0, 15.0],
    })
    snap = m.snapshot_dict()
    restored = MetricsCollector()
    restored.restore_snapshot(snap)
    assert restored.snapshot_dict() == snap
