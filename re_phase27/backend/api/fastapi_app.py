"""FastAPI backend application for ResilientEdge Windows and local deployment.
Authoritative source of truth for the ResilientEdge simulation engine.
"""
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Set
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from core.simulation.engine import SimulationEngine
from core.models.fault import FaultType
from backend.database.sqlite_db import ResilientEdgeDatabase
from backend.database.factory import persistence
from backend.database.worker import PersistenceWorker
from backend.auth import auth_service, AuthenticationError
from backend.api.permissions import permission_for_request, role_allows
from experiments.scenarios import SCENARIOS, run_scenario
from experiments.baseline import run_baseline_comparison

logger = logging.getLogger("resilientedge.api")

# Authoritative simulation instance
sim = SimulationEngine(seed=42, time_step=0.1)
db = ResilientEdgeDatabase()
persistence_worker = PersistenceWorker(persistence)
active_fastapi_role = "ADMIN"
current_run_id = None

# Initialize default fleet and tasks
sim.reset(robot_count=3, task_count=6)
import uuid
current_run_id = str(uuid.uuid4())
persistence_worker.submit("create_simulation", {"simulation_id": "resilientedge", "name": "ResilientEdge", "status": "RUNNING", "config": {"seed": sim.seed, "time_step": sim.clock.time_step}})
persistence_worker.submit("create_simulation_run", {"run_id": current_run_id, "simulation_id": "resilientedge", "name": "ResilientEdge Run", "status": "RUNNING", "config": {"seed": sim.seed, "time_step": sim.clock.time_step}})

# Active WebSocket telemetry clients.
# Each client gets its own bounded queue so a slow browser cannot block the
# authoritative simulation loop or other clients.
connected_websockets: Set[WebSocket] = set()
_websocket_queues: Dict[WebSocket, asyncio.Queue] = {}
_websocket_sender_tasks: Dict[WebSocket, asyncio.Task] = {}
telemetry_sequence: int = 0
latest_telemetry: Optional[Dict[str, Any]] = None
sim_loop_task: Optional[asyncio.Task] = None
is_running_loop: bool = True


def _telemetry_envelope(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add transport metadata while preserving the authoritative telemetry shape."""
    global telemetry_sequence
    telemetry_sequence += 1
    envelope = dict(data)
    envelope["message_type"] = "TELEMETRY"
    envelope["sequence"] = telemetry_sequence
    envelope["server_timestamp"] = time.time()
    return envelope


async def _send_queued_telemetry(ws: WebSocket, queue: asyncio.Queue):
    while True:
        payload = await queue.get()
        await ws.send_text(json.dumps(payload))


async def _enqueue_telemetry(ws: WebSocket, payload: Dict[str, Any]):
    queue = _websocket_queues.get(ws)
    if queue is None:
        return
    if queue.full():
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        pass


async def broadcast_telemetry(data: Dict[str, Any]):
    """Publish authoritative telemetry without blocking the simulation loop."""
    global latest_telemetry
    payload = _telemetry_envelope(data)
    latest_telemetry = payload
    for ws in list(connected_websockets):
        await _enqueue_telemetry(ws, payload)


async def _remove_websocket(ws: WebSocket):
    connected_websockets.discard(ws)
    _websocket_queues.pop(ws, None)
    task = _websocket_sender_tasks.pop(ws, None)
    if task and task is not asyncio.current_task():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def background_simulation_loop():
    """Independent background simulation loop.
    Simulation advances at a constant rate regardless of whether 0, 1, or 10 WebSocket clients are connected.
    """
    global is_running_loop
    logger.info("Starting background simulation loop at 10Hz...")
    while is_running_loop:
        try:
            # Advance authoritative simulation step
            telemetry = sim.step()

            # Persistence runs off the simulation thread; cloud/database outages cannot stop the loop.
            if sim.clock.tick_count % 10 == 0:
                persistence_worker.submit("sync_telemetry", telemetry, run_id=current_run_id)
            # Always publish into the authoritative latest-snapshot cache. With
            # no clients this is O(1); with clients it feeds their bounded queues.
            await broadcast_telemetry(telemetry)

            # Sleep interval scaled by time_scale
            interval = sim.clock.time_step / max(0.1, sim.clock.time_scale)
            await asyncio.sleep(interval)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background simulation loop: {e}")
            await asyncio.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sim_loop_task, is_running_loop
    is_running_loop = True
    sim_loop_task = asyncio.create_task(background_simulation_loop())
    yield
    is_running_loop = False
    if sim_loop_task:
        sim_loop_task.cancel()
        try:
            await sim_loop_task
        except asyncio.CancelledError:
            pass
    for ws in list(connected_websockets):
        await _remove_websocket(ws)
    if current_run_id:
        persistence_worker.submit("update_simulation_run", current_run_id, {"status": "COMPLETED", "end_time": time.time(), "final_metrics": sim.get_telemetry().get("metrics", {})})


app = FastAPI(
    title="ResilientEdge Authoritative Telemetry API",
    description="Multi-robot resilience simulation, coordination, fault injection, and telemetry API",
    version="1.0.0",
    lifespan=lifespan,
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "Invalid request", "errors": exc.errors()})


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_auth_and_permissions(request: Request, call_next):
    public_paths = {
        "/health", "/api/health",
        "/auth/login", "/api/auth/login",
        "/auth/refresh", "/api/auth/refresh",
        "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc",
    }
    if request.method.upper() == "OPTIONS" or request.url.path in public_paths:
        return await call_next(request)
    try:
        if os.getenv('DEMO_MODE', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}:
            demo_role = (request.headers.get('x-demo-role') or '').strip().upper()
            if demo_role in {'ADMIN', 'OPERATOR', 'OBSERVER', 'VIEWER'} and not request.headers.get('authorization'):
                from backend.auth import AuthUser
                user = AuthUser(
                    id=None,
                    email='demo@resilientedge.local',
                    role=demo_role,
                    full_name=f'Demo {"Administrator" if demo_role == "ADMIN" else demo_role.title()}',
                    local=True,
                )
            else:
                user = auth_service.authenticate_header(request.headers.get('authorization'))
        else:
            user = auth_service.authenticate_header(request.headers.get('authorization'))
    except AuthenticationError as exc:
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    request.state.user = user
    permission = permission_for_request(request.method, request.url.path)
    if permission is not None and not role_allows(user.role, permission):
        return JSONResponse(status_code=403, content={"detail": f"Role {user.role} cannot perform {permission}"})
    return await call_next(request)


# Request schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class RoleUpdateRequest(BaseModel):
    role: str

class UserStatusRequest(BaseModel):
    is_active: bool

class TaskCreateRequest(BaseModel):
    pickup: List[int]
    delivery: List[int]
    priority: int = 1
    deadline: float = 300.0


class FaultCreateRequest(BaseModel):
    type: str
    target: str
    duration: float = 30.0
    start_time: Optional[float] = None
    parameters: Optional[Dict[str, Any]] = None


class ScenarioRunRequest(BaseModel):
    scenario_id: str
    seed: int = 42


class ClockControlRequest(BaseModel):
    action: str  # pause, resume, step, reset
    scale: Optional[float] = None
    robot_count: Optional[int] = 3
    task_count: Optional[int] = 6


class SettingsRequest(BaseModel):
    time_step: Optional[float] = None
    time_scale: Optional[float] = None
    seed: Optional[int] = None
    telemetry_interval: Optional[float] = None
    default_robot_count: Optional[int] = None
    log_level: Optional[str] = None


class TaskAssignRequest(BaseModel):
    robot_id: Optional[str] = None


# -------------------------------------------------------------
# Endpoints (Supporting both root and /api prefixed routes)
# -------------------------------------------------------------

@app.get("/health")
@app.get("/api/health")
def get_health():
    persistence_status = persistence.get_persistence_status()
    return {
        "status": "ONLINE",
        "system": "ResilientEdge",
        "version": "1.0.0",
        "sim_time": round(sim.clock.current_time, 2),
        "active_robots": len(sim.robots),
        "is_paused": sim.clock.is_paused,
        "provider": persistence_status.get("provider"),
        "connected": persistence_status.get("connected", persistence_status.get("status") == "online" and persistence_status.get("database") == "sqlite"),
        "database": persistence_status.get("database"),
        "database_status": persistence_status.get("status"),
        "storage_mode": persistence_status.get("storage_mode") or persistence_status.get("mode"),
        "persistence": persistence_status,
        "websocket": "connected" if connected_websockets else "idle",
        "demo_mode": os.getenv('DEMO_MODE', 'false').strip().lower() in {'1', 'true', 'yes', 'on'},
    }


@app.get("/database/status")
@app.get("/api/database/status")
def get_database_status():
    return persistence.get_persistence_status()


@app.get("/robots")
@app.get("/api/robots")
def get_robots():
    return [r.to_dict() for r in sim.robots.values()]


@app.get("/robots/{robot_id}")
@app.get("/api/robots/{robot_id}")
def get_robot(robot_id: str):
    r = sim.robots.get(robot_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found")
    return r.to_dict()


@app.post("/robots/{robot_id}/pause")
@app.post("/api/robots/{robot_id}/pause")
def pause_robot(robot_id: str):
    try:
        robot = sim.pause_robot(robot_id)
        return robot.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/robots/{robot_id}/resume")
@app.post("/api/robots/{robot_id}/resume")
def resume_robot(robot_id: str):
    try:
        robot = sim.resume_robot(robot_id)
        return robot.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/robots/{robot_id}/reset")
@app.post("/api/robots/{robot_id}/reset")
def reset_robot(robot_id: str):
    try:
        robot = sim.reset_robot(robot_id)
        return robot.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/robots/{robot_id}/reassign")
@app.post("/api/robots/{robot_id}/reassign")
def reassign_robot(robot_id: str):
    try:
        res = sim.reassign_robot(robot_id)
        if res.get("status") == "NO_ELIGIBLE_ROBOT":
            raise HTTPException(status_code=409, detail=res["error"])
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
@app.get("/api/tasks")
def get_tasks():
    return [t.to_dict() for t in sim.tasks.values()]


@app.post("/tasks")
@app.post("/api/tasks")
def create_task(req: TaskCreateRequest, request: Request):
    tid = f"T{len(sim.tasks) + 1:02d}"
    task = sim.add_task(
        task_id=tid,
        pickup=tuple(req.pickup),
        delivery=tuple(req.delivery),
        priority=req.priority,
        deadline=req.deadline,
    )
    auth_service.audit(request.state.user,"TASK_ACTION","task",tid,{"task_id":tid,"operation":"create"})
    return task.to_dict()


@app.post("/tasks/{task_id}/assign")
@app.post("/api/tasks/{task_id}/assign")
def assign_task_route(task_id: str, req: TaskAssignRequest, request: Request):
    try:
        t = sim.assign_task(task_id, req.robot_id)
        auth_service.audit(request.state.user,"TASK_ACTION","task",task_id,{"task_id":task_id,"operation":"assign"})
        return t.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tasks/{task_id}/reassign")
@app.post("/api/tasks/{task_id}/reassign")
def reassign_task_route(task_id: str, request: Request):
    try:
        res = sim.reassign_task(task_id)
        if res.get("status") == "NO_ELIGIBLE_ROBOT":
            raise HTTPException(status_code=409, detail=res["error"])
        auth_service.audit(request.state.user,"TASK_ACTION","task",task_id,{"task_id":task_id,"operation":"reassign"})
        return res
    except ValueError as e:
        message = str(e)
        if "not found" in message:
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=409 if "Cannot reassign" in message else 400, detail=message)


@app.post("/tasks/{task_id}/cancel")
@app.post("/api/tasks/{task_id}/cancel")
def cancel_task_route(task_id: str, request: Request):
    try:
        t = sim.cancel_task(task_id)
        auth_service.audit(request.state.user,"TASK_ACTION","task",task_id,{"task_id":task_id,"operation":"cancel"})
        return t.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/incidents")
@app.get("/api/incidents")
def get_incidents():
    return [inc.to_dict() for inc in sim.incidents[-50:]]


@app.get("/faults")
@app.get("/api/faults")
def get_faults():
    return [f.to_dict() for f in sim.fault_engine.active_faults.values()]


@app.post("/faults")
@app.post("/api/faults")
def inject_fault(req: FaultCreateRequest, request: Request):
    try:
        ftype = FaultType(req.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid fault type: {req.type}")

    start_time = sim.clock.current_time if req.start_time is None else float(req.start_time)
    if start_time > sim.clock.current_time:
        fault = sim.fault_engine.schedule_fault(
            fault_type=ftype,
            target=req.target,
            start_time=start_time,
            duration=req.duration,
            parameters=req.parameters or {},
        )
    else:
        fault = sim.fault_engine.inject_fault(
            fault_type=ftype,
            target=req.target,
            start_time=start_time,
            duration=req.duration,
            parameters=req.parameters or {},
        )
    auth_service.audit(request.state.user,"FAULT_INJECTED","fault",fault.fault_id,{"fault_id":fault.fault_id,"fault_type":req.type,"target":req.target})
    return fault.to_dict()


@app.delete("/faults/{fault_id}")
@app.delete("/api/faults/{fault_id}")
def clear_fault(fault_id: str, request: Request):
    f = sim.fault_engine.clear_fault(fault_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fault not found")
    auth_service.audit(request.state.user,"FAULT_RESOLVED","fault",fault_id,{"fault_id":fault_id})
    return {"status": "CLEARED", "fault_id": fault_id}


@app.post("/faults/clear-all")
@app.post("/api/faults/clear-all")
def clear_all_faults(request: Request):
    cleared = sim.fault_engine.clear_all()
    # Reset any failed robot health back to nominal
    for r in sim.robots.values():
        if r.state == "FAILED":
            r.state = "IDLE"
            r.health = 1.0
    auth_service.audit(request.state.user,"FAULTS_CLEARED","fault",None,{"cleared_count":len(cleared)})
    return {"cleared_count": len(cleared)}


@app.get("/metrics")
@app.get("/api/metrics")
def get_metrics():
    return sim.get_telemetry()["metrics"]


@app.get("/scenarios")
@app.get("/api/scenarios")
def get_scenarios():
    return [
        {
            "id": s.scenario_id,
            "name": s.name,
            "description": s.description,
            "robot_count": s.robot_count,
            "task_count": s.task_count,
            "duration": s.duration,
        }
        for s in SCENARIOS.values()
    ]


@app.post("/scenarios/run")
@app.post("/api/scenarios/run")
def execute_scenario(req: ScenarioRunRequest, request: Request):
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Configure global simulation to match scenario
    sim.reset(robot_count=SCENARIOS[req.scenario_id].robot_count, task_count=SCENARIOS[req.scenario_id].task_count)
    SCENARIOS[req.scenario_id].setup_fn(sim)

    # Also run isolated evaluation for benchmark database
    result = run_scenario(req.scenario_id, seed=req.seed)
    persistence.save_experiment({
        "experiment_id": f"exp_{req.scenario_id}_{int(sim.clock.current_time)}",
        "scenario": req.scenario_id,
        "seed": req.seed,
        "robot_count": len(result["robots"]),
        "task_count": result["metrics"]["total_tasks"],
        "start_time": time.time(),
        "end_time": time.time(),
        "status": "COMPLETED",
        "metrics": result["metrics"],
    })
    auth_service.audit(request.state.user,"EXPERIMENT_STARTED","experiment",req.scenario_id,{"scenario_id":req.scenario_id,"seed":req.seed})
    return result


@app.get("/experiments")
@app.get("/api/experiments")
def get_experiments():
    return persistence.get_experiment_results(50)


@app.post("/controls/clock")
@app.post("/api/controls/clock")
def control_clock(req: ClockControlRequest, request: Request):
    action = req.action.lower()
    if action == "pause":
        sim.clock.pause()
    elif action == "resume":
        sim.clock.resume()
    elif action == "step":
        sim.clock.pause()
        sim.force_step()
    elif action == "reset":
        sim.reset(robot_count=req.robot_count or 3, task_count=req.task_count or 6)

    if req.scale is not None and req.scale > 0:
        sim.clock.time_scale = req.scale

    audit_actions = {
        "pause": "SIMULATION_PAUSED",
        "resume": "SIMULATION_STARTED",
        "step": "SIMULATION_STEPPED",
        "reset": "SIMULATION_RESET",
    }
    action_name = audit_actions.get(action)
    if action_name:
        metadata = {"simulation_time": round(sim.clock.current_time, 2)}
        if action == "reset":
            metadata.update({"robot_count": req.robot_count or 3, "task_count": req.task_count or 6})
        if req.scale is not None and req.scale > 0:
            metadata["time_scale"] = req.scale
        auth_service.audit(request.state.user, action_name, "simulation", current_run_id, metadata)

    return {
        "is_paused": sim.clock.is_paused,
        "time_scale": sim.clock.time_scale,
        "sim_time": round(sim.clock.current_time, 2),
    }


@app.post("/simulation/start")
@app.post("/api/simulation/start")
def simulation_start(request: Request):
    sim.clock.resume()
    auth_service.audit(request.state.user,"SIMULATION_STARTED","simulation",current_run_id,{"simulation_time":round(sim.clock.current_time,2)})
    return {"status": "RUNNING", "is_paused": False, "sim_time": round(sim.clock.current_time, 2)}


@app.post("/simulation/pause")
@app.post("/api/simulation/pause")
def simulation_pause(request: Request):
    sim.clock.pause()
    auth_service.audit(request.state.user,"SIMULATION_PAUSED","simulation",current_run_id,{"simulation_time":round(sim.clock.current_time,2)})
    return {"status": "PAUSED", "is_paused": True, "sim_time": round(sim.clock.current_time, 2)}


@app.post("/simulation/step")
@app.post("/api/simulation/step")
def simulation_step(request: Request):
    sim.clock.pause()
    telemetry = sim.force_step()
    auth_service.audit(request.state.user,"SIMULATION_STEPPED","simulation",current_run_id,{"simulation_time":round(sim.clock.current_time,2)})
    return {"status": "STEPPED", "is_paused": True, "sim_time": round(sim.clock.current_time, 2), "telemetry": telemetry}


@app.post("/simulation/reset")
@app.post("/api/simulation/reset")
def simulation_reset(request: Request, robot_count: int = 3, task_count: int = 6):
    sim.reset(robot_count=robot_count, task_count=task_count)
    auth_service.audit(request.state.user,"SIMULATION_RESET","simulation",current_run_id,{"robot_count":robot_count,"task_count":task_count})
    return {"status": "RESET", "is_paused": False, "sim_time": round(sim.clock.current_time, 2)}


@app.get("/simulation/state")
@app.get("/api/simulation/state")
def get_simulation_state():
    return {
        "clock": sim.clock.to_dict(),
        "robots_count": len(sim.robots),
        "tasks_count": len(sim.tasks),
        "active_faults_count": len(sim.fault_engine.active_faults),
        "resilience_state": sim.state_machine.current_state.value,
    }


@app.get("/baseline")
@app.get("/api/baseline")
def get_baseline_comparison():
    # Run comparative benchmark for S06 or retrieve reference
    base_comp = run_baseline_comparison("S06", seed=sim.seed)
    return base_comp


@app.get("/settings")
@app.get("/api/settings")
def get_settings():
    return {
        "time_step": sim.clock.time_step,
        "time_scale": sim.clock.time_scale,
        "seed": sim.seed,
        "telemetry_interval": 0.1,
        "default_robot_count": len(sim.robots),
        "log_level": "INFO",
    }


@app.post("/settings")
@app.post("/api/settings")
def set_settings(req: SettingsRequest, request: Request):
    try:
        updated = sim.update_settings(req.model_dump(exclude_none=True))
        safe={k:v for k,v in req.model_dump(exclude_none=True).items() if k not in {"password","password_hash","token","refresh_token","secret"}}
        auth_service.audit(request.state.user,"SETTINGS_CHANGED","settings",None,safe)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/backup")
@app.get("/api/backup")
@app.post("/snapshot/save")
@app.post("/api/snapshot/save")
def export_snapshot():
    return sim.save_snapshot()


@app.post("/backup/restore")
@app.post("/api/backup/restore")
@app.post("/snapshot/restore")
@app.post("/api/snapshot/restore")
def restore_snapshot_route(snapshot: Dict[str, Any]):
    try:
        sim.restore_snapshot(snapshot)
        return {"status": "RESTORED", "sim_time": round(sim.clock.current_time, 2)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to restore snapshot: {e}")


@app.post("/auth/login")
@app.post("/api/auth/login")
def auth_login(payload: LoginRequest):
    try:
        user, access_token, refresh_token = auth_service.authenticate(str(payload.email), payload.password)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}}
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

@app.post("/auth/refresh")
@app.post("/api/auth/refresh")
def auth_refresh(payload: RefreshRequest):
    try:
        access_token, refresh_token = auth_service.refresh(payload.refresh_token)
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

@app.post("/auth/logout")
@app.post("/api/auth/logout")
def auth_logout(request: Request):
    token=request.headers.get("authorization","").split(" ",1)[1].strip() if request.headers.get("authorization","").lower().startswith("bearer ") else ""
    auth_service.logout(token)
    return {"status":"SIGNED_OUT"}

@app.get("/auth/me")
@app.get("/api/auth/me")
def get_auth_me(request: Request):
    user = request.state.user
    return {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name, "local": user.local}

@app.get("/admin/users")
@app.get("/api/admin/users")
def admin_users(request: Request):
    return {"users": persistence.sqlite.list_users()}

@app.patch("/admin/users/{user_id}/role")
@app.patch("/api/admin/users/{user_id}/role")
def admin_change_role(user_id: str, payload: RoleUpdateRequest, request: Request):
    role=payload.role.upper()
    if role not in {"ADMIN","OPERATOR","OBSERVER","VIEWER"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    target=persistence.sqlite.get_user_by_id(user_id)
    if not target: raise HTTPException(status_code=404, detail="User not found")
    if target.get("role")=="ADMIN" and role!="ADMIN" and persistence.sqlite.count_admins()<=1:
        raise HTTPException(status_code=409, detail="The last administrator cannot be removed")
    persistence.sqlite.update_user_role(user_id,role)
    auth_service.audit(request.state.user,"ROLE_CHANGED","user",user_id,{"old_role":target.get("role"),"new_role":role})
    return {"status":"UPDATED","id":user_id,"role":role}

@app.patch("/admin/users/{user_id}/status")
@app.patch("/api/admin/users/{user_id}/status")
def admin_change_user_status(user_id: str, payload: UserStatusRequest, request: Request):
    target=persistence.sqlite.get_user_by_id(user_id)
    if not target: raise HTTPException(status_code=404, detail="User not found")
    if not payload.is_active and target.get("role") == "ADMIN" and persistence.sqlite.count_admins() <= 1:
        raise HTTPException(status_code=409, detail="The last administrator cannot be disabled")
    persistence.sqlite.set_user_active(user_id, payload.is_active)
    auth_service.audit(request.state.user, "USER_ENABLED" if payload.is_active else "USER_DISABLED", "user", user_id, {"is_active":payload.is_active})
    return {"status":"UPDATED","id":user_id,"is_active":payload.is_active}

@app.get("/admin/audit")
@app.get("/api/admin/audit")
def admin_audit(request: Request, limit: int = 200):
    return {"logs": persistence.sqlite.get_audit_logs(min(max(limit,1),500))}

@app.post("/auth/switch-role")
@app.post("/api/auth/switch-role")
def switch_auth_role():
    raise HTTPException(status_code=410, detail="Role switching is disabled; role comes from the authenticated profile.")

@app.get("/database/stats")
@app.get("/api/database/stats")
def get_database_stats():
    return persistence.get_stats()

@app.get("/database/robots")
@app.get("/api/database/robots")
def get_database_robots():
    return persistence.get_robots()

@app.get("/database/tasks")
@app.get("/api/database/tasks")
def get_database_tasks():
    return persistence.get_tasks()

@app.get("/database/incidents")
@app.get("/api/database/incidents")
def get_database_incidents(limit: int = 50):
    return persistence.get_incidents(limit=limit)

@app.get("/database/events")
@app.get("/api/database/events")
def get_database_events(limit: int = 50):
    return persistence.get_decision_events(limit=limit)

@app.post("/database/clear")
@app.post("/api/database/clear")
def clear_database(request: Request):
    try:
        persistence.clear_all()
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    auth_service.audit(request.state.user,"DATABASE_CLEAR","database",None,{"status":"cleared"})
    return {"status": "CLEARED"}


@app.post("/experiments/run")
@app.post("/api/experiments/run")
def api_experiment_run(payload: Dict[str, Any], request: Request):
    from experiments.runner import run_experiment
    try:
        scenario_id = payload.get("scenario_id", "S01")
        config = payload.get("config", "resilient")
        seed = int(payload.get("seed", 42))
        runs = int(payload.get("runs", 1))
        result = run_experiment(
            scenario=scenario_id,
            config=config,
            seed=seed,
            runs=runs,
            robots=payload.get("robots"),
            tasks=payload.get("tasks"),
            duration=payload.get("duration"),
            output=payload.get("output"),
            persist=True,
        )
        auth_service.audit(
            request.state.user,
            "EXPERIMENT_STARTED",
            "experiment",
            scenario_id,
            {"scenario_id": scenario_id, "config": config, "seed": seed, "runs": runs},
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/experiments/compare")
@app.post("/api/experiments/compare")
def api_experiment_compare(payload: Dict[str, Any], request: Request):
    from experiments.runner import compare
    try:
        scenario_id = payload.get("scenario_id", "S03")
        seed = int(payload.get("seed", 42))
        runs = int(payload.get("runs", 5))
        result = compare(scenario_id, seed, runs, robots=payload.get("robots"), tasks=payload.get("tasks"), duration=payload.get("duration"))
        auth_service.audit(request.state.user, "EXPERIMENT_STARTED", "experiment", scenario_id, {"scenario_id": scenario_id, "operation": "compare", "seed": seed, "runs": runs})
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/experiments/history")
@app.get("/api/experiments/history")
def api_experiment_history():
    return persistence.get_experiment_results(100)

@app.post("/experiments/monte-carlo")
@app.post("/api/experiments/monte-carlo")
def api_monte_carlo(payload: Dict[str, Any], request: Request):
    from experiments.monte_carlo import run_monte_carlo
    sc_id = payload.get("scenario_id", "S06")
    runs = payload.get("num_runs", 10)
    seed = payload.get("start_seed", 100)
    result = run_monte_carlo(sc_id, num_runs=int(runs), start_seed=int(seed))
    auth_service.audit(request.state.user, "EXPERIMENT_STARTED", "experiment", sc_id, {"scenario_id": sc_id, "operation": "monte_carlo", "num_runs": int(runs), "start_seed": int(seed)})
    return result

@app.post("/experiments/parameter-sweep")
@app.post("/api/experiments/parameter-sweep")
def api_parameter_sweep(payload: Dict[str, Any], request: Request):
    from experiments.parameter_sweep import run_parameter_sweep
    p_type = payload.get("param_type", "robot_count")
    vals = payload.get("values")
    seed = payload.get("seed", 42)
    result = run_parameter_sweep(p_type, values=vals, seed=int(seed))
    auth_service.audit(request.state.user, "EXPERIMENT_STARTED", "experiment", p_type, {"operation": "parameter_sweep", "param_type": p_type, "values": vals, "seed": int(seed)})
    return result

# -------------------------------------------------------------
# WebSocket Telemetry
# -------------------------------------------------------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """Persistent authoritative telemetry stream."""
    token = websocket.query_params.get("access_token")
    demo_role = (websocket.query_params.get("demo_role") or '').strip().upper()
    demo_mode = os.getenv('DEMO_MODE', 'false').strip().lower() in {'1', 'true', 'yes', 'on'}
    try:
        if not token and demo_mode and demo_role in {'ADMIN', 'OPERATOR', 'OBSERVER', 'VIEWER'}:
            pass
        else:
            auth_service.authenticate_token(token)
    except AuthenticationError:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await websocket.accept()
    connected_websockets.add(websocket)
    queue: asyncio.Queue = asyncio.Queue(maxsize=8)
    _websocket_queues[websocket] = queue
    sender = asyncio.create_task(_send_queued_telemetry(websocket, queue))
    _websocket_sender_tasks[websocket] = sender

    # Reconnect semantics: immediately deliver the newest authoritative state.
    snapshot = latest_telemetry
    if snapshot is None:
        snapshot = _telemetry_envelope(sim.get_telemetry())
        globals()["latest_telemetry"] = snapshot
    await _enqueue_telemetry(websocket, snapshot)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue
            if data.get("type") == "PING":
                await websocket.send_json({
                    "type": "PONG",
                    "server_timestamp": time.time(),
                })
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("Telemetry WebSocket closed: %s", exc)
    finally:
        await _remove_websocket(websocket)
