"""Formal Phase 3 experiment definitions and scenario configuration loading."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json

try:
    import yaml
except ImportError:  # pragma: no cover - requirements installs PyYAML
    yaml = None

ROOT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class ExperimentDefinition:
    experiment_id: str
    name: str
    description: str
    scenario_id: str
    version: str = "1.0"
    seed: int = 42
    robot_count: int = 3
    task_count: int = 6
    simulation_duration: float = 45.0
    configuration: Dict[str, Any] = field(default_factory=dict)
    fault_schedule: List[Dict[str, Any]] = field(default_factory=list)
    network_schedule: List[Dict[str, Any]] = field(default_factory=list)
    planner_configuration: Dict[str, Any] = field(default_factory=dict)
    recovery_configuration: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scenario_version: str = "1.0"
    algorithm_version: str = "1.0"
    configuration_version: str = "1.0"
    world: Dict[str, Any] = field(default_factory=dict)
    tasks_configuration: Dict[str, Any] = field(default_factory=dict)
    timing: Dict[str, Any] = field(default_factory=dict)
    expected_behavior: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load experiment configuration files")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_scenario_config(scenario_id: str) -> Dict[str, Any]:
    path = ROOT / "scenarios" / f"{scenario_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Scenario configuration not found: {path}")
    data = load_yaml(path)
    if data.get("scenario_id") != scenario_id:
        raise ValueError(f"Scenario file {path.name} has mismatched scenario_id")
    return data


def load_algorithm_config(name: str) -> Dict[str, Any]:
    path = ROOT / "configs" / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Experiment configuration not found: {path}")
    return load_yaml(path)


def validate_scenario_config(data: Dict[str, Any]) -> List[str]:
    """Return schema errors for an executable Phase 18 scenario."""
    required = ("scenario_id", "world", "robot_count", "tasks", "faults", "timing", "seed", "duration", "expected_behavior")
    errors = [f"missing required field: {k}" for k in required if k not in data]
    if "robot_count" in data and int(data["robot_count"]) < 1:
        errors.append("robot_count must be >= 1")
    if "tasks" in data and not isinstance(data["tasks"], dict):
        errors.append("tasks must be an object")
    elif "tasks" in data and int(data["tasks"].get("count", 0)) < 0:
        errors.append("tasks.count must be >= 0")
    if "duration" in data and float(data["duration"]) <= 0:
        errors.append("duration must be > 0")
    if "faults" in data and not isinstance(data["faults"], list):
        errors.append("faults must be a list")
    return errors


def validate_all_scenarios() -> Dict[str, List[str]]:
    """Validate every S01-S12 scenario before execution."""
    errors = {}
    for sid in [f"S{i:02d}" for i in range(1, 13)]:
        try:
            data = load_scenario_config(sid)
            issues = validate_scenario_config(data)
        except Exception as exc:
            issues = [str(exc)]
        if issues:
            errors[sid] = issues
    return errors


def build_definition(scenario_id: str, config_name: str, seed: int, robots: Optional[int] = None,
                     tasks: Optional[int] = None, duration: Optional[float] = None,
                     experiment_id: Optional[str] = None) -> ExperimentDefinition:
    scenario = load_scenario_config(scenario_id)
    algorithm = load_algorithm_config(config_name)
    rc = int(robots if robots is not None else scenario["robot_count"])
    tc = int(tasks if tasks is not None else scenario["task_count"])
    dur = float(duration if duration is not None else scenario["duration"])
    eid = experiment_id or f"EXP-{scenario_id}-{config_name.upper()}-{seed}"
    return ExperimentDefinition(
        experiment_id=eid,
        name=scenario["name"],
        description=scenario["description"],
        scenario_id=scenario_id,
        version=str(scenario.get("version", "1.0")),
        seed=int(seed),
        robot_count=rc,
        task_count=tc,
        simulation_duration=dur,
        configuration={"algorithm": config_name, **algorithm.get("configuration", {})},
        fault_schedule=list(scenario.get("fault_schedule", [])),
        network_schedule=list(scenario.get("network_schedule", [])),
        planner_configuration=dict(algorithm.get("planner_configuration", {})),
        recovery_configuration=dict(algorithm.get("recovery_configuration", {})),
        scenario_version=str(scenario.get("version", "1.0")),
        algorithm_version=str(algorithm.get("version", "1.0")),
        configuration_version=str(algorithm.get("configuration_version", "1.0")),
        world=dict(scenario.get("world", {})),
        tasks_configuration=dict(scenario.get("tasks", {})),
        timing=dict(scenario.get("timing", {})),
        expected_behavior=str(scenario.get("expected_behavior", "")),
    )
