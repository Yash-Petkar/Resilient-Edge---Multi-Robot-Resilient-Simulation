"""Phase 6: independent RobotAgent architecture tests."""
from core.agents.robot_agent import PeerState, RobotAgent
from core.models.robot import Robot, RobotState
from core.planning.astar import AStarPlanner
from core.simulation.engine import SimulationEngine


def make_agent(robot_id, position):
    return RobotAgent(
        Robot(robot_id=robot_id, position=position, state=RobotState.IDLE),
        planner=AStarPlanner(),
        priority=1,
    )


def test_three_independent_agents_have_independent_local_state():
    agents = {f"AMR-{i:02d}": make_agent(f"AMR-{i:02d}", (i, 0)) for i in range(1, 4)}
    assert len(agents) == 3
    assert len({id(a) for a in agents.values()}) == 3
    assert len({id(a.robot) for a in agents.values()}) == 3
    assert len({id(a.planner) for a in agents.values()}) == 3
    assert len({id(a.peer_table) for a in agents.values()}) == 3
    assert len({id(a.intent) for a in agents.values()}) == 3


def test_agent_intent_is_local():
    a1 = make_agent("AMR-01", (1, 0))
    a2 = make_agent("AMR-02", (2, 0))
    a1.set_intent([(1, 0), (1, 1), (1, 2)], timestamp=1.0)
    assert a1.intent.planned_path != a2.intent.planned_path
    assert a2.intent.intent == "IDLE"


def test_peer_table_is_local_and_does_not_mutate_peer_robot():
    a1 = make_agent("AMR-01", (1, 0))
    a2 = make_agent("AMR-02", (2, 0))
    peer = PeerState("AMR-02", (2, 0), 1.0, 90.0, 2, "MOVING", [(2, 0), (3, 0)], timestamp=1.0, sequence_number=1)
    a1.update_peer(peer)
    assert "AMR-02" in a1.peer_table
    assert "AMR-02" not in a2.peer_table
    a1.peer_table["AMR-02"].position = (99, 99)
    assert a2.robot.position == (2, 0)


def test_agent_local_path_planning_updates_only_its_intent():
    a1 = make_agent("AMR-01", (0, 0))
    a2 = make_agent("AMR-02", (5, 5))
    path = a1.plan_local_path((2, 0), set(), 8, 8, timestamp=2.0)
    assert path is not None
    assert a1.intent.planned_path == path
    assert a2.intent.intent == "IDLE"


def test_agent_communication_recovery_and_reservations_are_local():
    a1 = make_agent("AMR-01", (0, 0))
    a2 = make_agent("AMR-02", (1, 0))
    a1.set_communication_state("DEGRADED")
    a1.set_recovery_state("LOCAL_AUTONOMY")
    a1.record_reservation("res-1")
    a1.record_conflict("conf-1", {"type": "VERTEX"})
    assert a1.communication_state == "DEGRADED"
    assert a1.recovery_state == "LOCAL_AUTONOMY"
    assert a1.local_reservations == {"res-1"}
    assert "conf-1" in a1.local_conflicts
    assert a2.communication_state == "CONNECTED"
    assert a2.recovery_state == "NORMAL"
    assert not a2.local_reservations
    assert not a2.local_conflicts


def test_engine_creates_three_independent_agents():
    engine = SimulationEngine(seed=7)
    engine.reset(robot_count=3, task_count=0)
    assert set(engine.agents) == {"R1", "R2", "R3"}
    assert all(engine.robots[k] is engine.agents[k].robot for k in engine.agents)
    assert len({id(a) for a in engine.agents.values()}) == 3
    assert len({id(a.robot) for a in engine.agents.values()}) == 3


def test_one_agent_failure_does_not_mutate_other_agent_local_state():
    engine = SimulationEngine(seed=9)
    engine.reset(robot_count=3, task_count=0)
    a1, a2, a3 = (engine.agents[k] for k in ("R1", "R2", "R3"))
    a2.set_recovery_state("RECOVERY")
    a2.set_communication_state("DISCONNECTED")
    a2.robot.state = RobotState.FAILED
    assert a1.robot.state == RobotState.IDLE
    assert a3.robot.state == RobotState.IDLE
    assert a1.recovery_state == "NORMAL"
    assert a3.recovery_state == "NORMAL"
    assert a1.communication_state == "CONNECTED"
    assert a3.communication_state == "CONNECTED"
