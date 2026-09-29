
from core.networking.network_sim import NetworkSimulator
from core.networking.adapter import LocalP2PCommunicationAdapter
from core.simulation.engine import SimulationEngine


def test_phase16_real_latency_uses_transport_queue():
    net = NetworkSimulator(seed=7)
    assert net.send_message("R1", "R2", {"type": "PING"}, 0.0, latency=1.0)
    assert net.get_network_metrics()["in_flight_count"] == 1
    assert net.poll_delivered(0.5) == []
    delivered = net.poll_delivered(1.0)
    assert len(delivered) == 1
    assert delivered[0].sender == "R1"
    assert delivered[0].recipient == "R2"
    assert delivered[0].delivered_time == 1.0


def test_phase16_partition_is_real_delivery_isolation():
    net = NetworkSimulator(seed=1)
    groups = ({"R1", "R2"}, {"R3"})
    assert not net.send_message(
        "R1", "R3", {"type": "PING"}, 0.0,
        is_partitioned=True, partition_groups=groups
    )
    assert net.total_dropped == 1
    assert net.in_flight_messages == []
    assert net.send_message(
        "R1", "R2", {"type": "PING"}, 0.0,
        is_partitioned=True, partition_groups=groups, latency=0.001
    )
    assert len(net.poll_delivered(0.001)) == 1


def test_phase16_duplication_creates_distinct_transport_messages():
    net = NetworkSimulator(seed=2)
    assert net.send_message(
        "R1", "R2", {"type": "STATE"}, 0.0,
        latency=0.0, duplication_rate=1.0
    )
    messages = net.poll_delivered(1.0)
    assert len(messages) == 2
    assert len({m.message_id for m in messages}) == 2
    assert sum(m.is_duplicate for m in messages) == 1
    assert net.total_duplicated == 1


def test_phase16_reordering_is_seeded_and_observable():
    def run(seed):
        net = NetworkSimulator(seed=seed)
        net.send_message("R1", "R2", {"seq": 1}, 0.0, latency=0.0, reorder_rate=1.0)
        net.send_message("R1", "R2", {"seq": 2}, 0.0, latency=0.0, reorder_rate=0.0)
        return [m.payload["seq"] for m in net.poll_delivered(1.0)]

    first = run(42)
    second = run(42)
    assert first == second
    assert first == [2, 1]


def test_phase16_snapshot_restores_in_flight_transport():
    net = NetworkSimulator(seed=42)
    net.send_message("R1", "R2", {"type": "PING"}, 0.0, latency=2.0)
    snapshot = net.to_dict()

    restored = NetworkSimulator(seed=999)
    restored.from_dict(snapshot)
    assert restored.get_network_metrics()["in_flight_count"] == 1
    assert restored.poll_delivered(1.0) == []
    assert len(restored.poll_delivered(2.0)) == 1


def test_phase16_adapter_does_not_bypass_transport():
    net = NetworkSimulator(seed=42)
    adapter = LocalP2PCommunicationAdapter(net)
    adapter.register("R1")
    adapter.register("R2")
    assert adapter.send("R1", "R2", {"type": "PING"}, 0.0)
    assert net.get_network_metrics()["in_flight_count"] == 1
    assert adapter.pump_all(0.0)["R2"] == []
    assert len(adapter.pump_all(1.0)["R2"]) == 1


def test_phase16_engine_reset_clears_transport_state():
    sim = SimulationEngine(seed=42, time_step=0.1)
    sim.reset(robot_count=2, task_count=0)
    sim.p2p.configure(latency=5.0)
    sim.network_sim.send_message("R1", "R2", {"type": "PING"}, 0.0, latency=5.0)
    assert sim.network_sim.get_network_metrics()["in_flight_count"] == 1
    sim.reset(robot_count=2, task_count=0)
    metrics = sim.network_sim.get_network_metrics()
    assert metrics["in_flight_count"] == 0
    assert metrics["messages_sent"] == 0
