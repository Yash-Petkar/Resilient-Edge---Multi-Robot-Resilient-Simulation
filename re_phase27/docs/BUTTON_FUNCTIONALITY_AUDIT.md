# ResilientEdge Button & Control Functionality Audit

| Button / Control | Frontend Handler | API / Endpoint | Backend Effect | Simulation Effect | Telemetry Effect | Status |
|---|---|---|---|---|---|---|
| **TopBar: Play/Resume** | `onClockAction('resume')` | `POST /api/controls/clock` or `POST /api/simulation/start` | Resumes simulation loop timer | `clock.resume()` enables world and robot motion | `clock.is_paused` = `false`, timestamp ticks | **PASS** |
| **TopBar: Pause** | `onClockAction('pause')` | `POST /api/controls/clock` or `POST /api/simulation/pause` | Pauses simulation loop timer | `clock.pause()` halts movement, drains, timers | `clock.is_paused` = `true`, timestamp freezes | **PASS** |
| **TopBar: Step** | `onClockAction('step')` | `POST /api/controls/clock` or `POST /api/simulation/step` | Invokes single step | `clock.force_step()` executes exactly one Δt | Advances clock by Δt (+0.1s) and updates | **PASS** |
| **TopBar: Reset** | `onClockAction('reset')` | `POST /api/controls/clock` or `POST /api/simulation/reset` | Resets simulation fleet and tasks | `sim.reset()` restores initial world and positions | Clock resets to 0.0s, faults clear, robots home | **PASS** |
| **TopBar: Time Scale** | `onClockAction('...', scale)` | `POST /api/controls/clock` | Updates loop time scale multiplier | Sets `clock.time_scale` (0.5x, 1x, 2x, 5x, 10x) | Accelerates/decelerates simulation ticks | **PASS** |
| **TopBar: Settings** | `onOpenSettings()` | UI Modal open | Renders settings dialog | None (config input) | Opens modal | **PASS** |
| **Sidebar: Dashboard** | `onSelectTab('dashboard')` | Internal tab state | None | None | Renders grid overview layout | **PASS** |
| **Sidebar: Simulation** | `onSelectTab('simulation')` | Internal tab state | None | None | Renders maximized map viewport | **PASS** |
| **Sidebar: Fleet** | `onSelectTab('fleet')` | Internal tab state | None | None | Renders full fleet cards & stats | **PASS** |
| **Sidebar: Tasks** | `onSelectTab('tasks')` | Internal tab state | None | None | Renders task queue & dispatcher button | **PASS** |
| **Sidebar: Faults** | `onSelectTab('faults')` | Internal tab state | None | None | Renders chaos injection testbed | **PASS** |
| **Sidebar: Incidents** | `onSelectTab('incidents')` | Internal tab state | None | None | Renders incident audit stream & filters | **PASS** |
| **Sidebar: Recovery** | `onSelectTab('recovery')` | Internal tab state | None | None | Renders state machine analysis | **PASS** |
| **Sidebar: Experiments** | `onSelectTab('experiments')` | Internal tab state | None | None | Renders benchmark scenario suite | **PASS** |
| **Sidebar: Metrics** | `onSelectTab('metrics')` | Internal tab state | None | None | Renders real-time telemetry metrics | **PASS** |
| **Sidebar: Baseline** | `onSelectTab('baseline')` | Internal tab state | None | None | Renders resilient vs non-resilient chart | **PASS** |
| **Sidebar: Network** | `onSelectTab('network')` | Internal tab state | None | None | Renders network mesh latency monitor | **PASS** |
| **Sidebar: Database** | `onSelectTab('database')` | Internal tab state | None | None | Renders SQLite table counts | **PASS** |
| **Sidebar: Settings** | `onSelectTab('settings')` | Internal tab state | None | None | Renders backup & snapshot manager | **PASS** |
| **Robot: Pause** | `handleRobotAction('pause', id)` | `POST /api/robots/{id}/pause` | Sets robot state to PAUSED | Robot ceases motion; current task remains assigned; no fault generated | Telemetry shows robot state = PAUSED | **PASS** |
| **Robot: Resume** | `handleRobotAction('resume', id)` | `POST /api/robots/{id}/resume` | Resumes target robot only | Transitions robot to PLANNING/IDLE; recovers target-scoped fault if failed | Telemetry shows robot state = PLANNING/IDLE | **PASS** |
| **Robot: Reset** | `handleRobotAction('reset', id)` | `POST /api/robots/{id}/reset` | Resets target robot to home | Restores home pos, nominal health/battery, releases its reservations & task | Telemetry shows robot at home with 100% battery | **PASS** |
| **Robot: Reassign** | `handleRobotAction('reassign', id)` | `POST /api/robots/{id}/reassign` | Reassigns robot's active task | Finds best eligible replacement robot, plans path, transfers task | Task assigned_robot updates, replacement plans | **PASS** |
| **Task: Dispatch** | `handleDispatchTask(...)` | `POST /api/tasks` | Inserts task in queue | Allocator evaluates task for next available robot | Telemetry includes new task in list | **PASS** |
| **Task: Assign** | `onReassignTask(taskId, robotId)` | `POST /api/tasks/{id}/assign` | Assigns task to specified robot | Target robot starts path planning towards station | Telemetry updates task status to ASSIGNED | **PASS** |
| **Task: Cancel** | `onCancelTask(taskId)` | `POST /api/tasks/{id}/cancel` | Cancels task, frees robot | Robot returns to IDLE; cancels cell reservations | Telemetry sets status = CANCELLED | **PASS** |
| **Fault: Inject** | `handleInjectFault(...)` | `POST /api/faults` | Injects validated fault model | Engine applies hardware, environment, or network anomaly | Telemetry lists active fault; state updates | **PASS** |
| **Fault: Clear** | `handleClearFault(id)` | `DELETE /api/faults/{id}` | Clears targeted fault | Resolves anomaly from engine | Telemetry removes fault from active list | **PASS** |
| **Fault: Clear All** | `handleClearAllFaults()` | `POST /api/faults/clear-all` | Purges all active faults | Clears all faults and restores failed robot health | Telemetry shows 0 active faults | **PASS** |
| **Snapshot: Save** | `handleSaveSnapshot()` | `POST /api/snapshot/save` | Captures simulation state | Serializes clock, world, robots, tasks, faults, metrics | Returns full snapshot JSON download | **PASS** |
| **Snapshot: Restore** | `handleRestoreSnapshot(...)` | `POST /api/snapshot/restore` | Authoritatively restores state | Overwrites simulation world, clock, robots, tasks, faults | Telemetry updates immediately via WebSocket | **PASS** |
| **Scenario: Run** | `handleRunScenario(id)` | `POST /api/scenarios/run` | Executes benchmark scenario | Runs scenario, evaluates metrics, records to SQLite | Experiment output returned with completion metrics | **PASS** |
| **Map: Zoom In** | `setZoom(z + 0.15)` | Client canvas state | Transforms 2D canvas | Increases rendering scale | Map zooms in smoothly | **PASS** |
| **Map: Zoom Out** | `setZoom(z - 0.15)` | Client canvas state | Transforms 2D canvas | Decreases rendering scale | Map zooms out smoothly | **PASS** |
| **Map: Fit View** | `setZoom(1.0)` | Client canvas state | Resets scale & viewport | Centers map on canvas | Grid fits perfectly within container | **PASS** |
| **Map: Layers Toggle** | `toggleLayer(key)` | Client layer state | Filters rendering passes | Shows/hides robots, tasks, paths, reservations, obstacles | Selected elements render or hide conditionally | **PASS** |
