# ResilientEdge ROS 2 Data Contract — Phase 7 Preparation

This document defines the transport boundary only. It does **not** implement ROS 2 and does not require ROS 2 or Gazebo on the current Windows machine.

## Adapter boundary

`core/interfaces/robot_interface.py` defines `RobotInterface` with:

- `get_state()`
- `send_command()`
- `publish_intent()`
- `get_position()`
- `get_battery()`
- `stop()`
- `resume()`

Current implementation: `SimulatedRobotAdapter`.

Future implementation: `ROS2RobotAdapter`.

The coordination engine must depend on the interface, not a ROS 2 transport.

## Future message concepts

| Concept | Required fields |
|---|---|
| RobotState | robot_id, position, orientation, velocity, battery, state, communication_status |
| RobotIntent | robot_id, target, path, timestamp, priority |
| Task | task_id, pickup, destination, priority, assigned_robot, status |
| Command | robot_id, command, target, timestamp |
| FleetEvent | event_id, timestamp, event_type, robot_id, payload |
| Fault | fault_id, type, target, start_time, duration, parameters |
| Telemetry | robot state + odometry + sensor/obstacle state |

## Proposed future topics

- `/fleet/robot_states`
- `/fleet/robot_intents`
- `/fleet/tasks`
- `/fleet/commands`
- `/fleet/events`
- `/amr_<id>/odom`
- `/amr_<id>/scan`
- `/amr_<id>/status`
- `/amr_<id>/cmd_vel`

These are contract targets, not fake ROS endpoints.

## Gazebo mapping

The current simulator already exposes the core state required for future Gazebo integration:

- x/y position
- orientation
- velocity
- odometry-equivalent state
- obstacle state
- battery
- robot state

LiDAR and IMU remain future physical/sensor adapters.
