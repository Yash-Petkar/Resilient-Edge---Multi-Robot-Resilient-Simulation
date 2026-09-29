"""Role permissions shared by the FastAPI authorization middleware."""

from typing import Optional

ROLE_PERMISSIONS = {
    "OBSERVER": frozenset({"read", "audit_read"}),
    "VIEWER": frozenset({"read"}),
    "OPERATOR": frozenset(
        {
            "read",
            "simulation_control",
            "task_dispatch",
            "fault_injection",
            "recovery",
            "experiments",
        }
    ),
    "ADMIN": frozenset(
        {
            "read",
            "simulation_control",
            "task_dispatch",
            "fault_injection",
            "recovery",
            "experiments",
            "settings",
            "database_admin",
            "user_admin",
            "destructive",
            "audit_read",
        }
    ),
}


def permission_for_request(method: str, path: str) -> Optional[str]:
    """Map mutating endpoints to their minimum role capability."""
    normalized_path = path.removeprefix("/api").rstrip("/") or "/"
    if normalized_path.startswith("/auth/"):
        return None
    if normalized_path.startswith("/admin/users"):
        return "user_admin"
    if normalized_path.startswith("/admin/audit"):
        return "audit_read"
    if method.upper() in {"GET", "HEAD", "OPTIONS"} or normalized_path in {
        "/snapshot/save",
        "/backup",
    }:
        return "read"
    if normalized_path in {"/settings"}:
        return "settings"
    if normalized_path in {"/database/clear"}:
        return "database_admin"
    if normalized_path in {"/snapshot/restore", "/backup/restore"}:
        return "destructive"
    if normalized_path.startswith("/database/"):
        return "database_admin"
    if normalized_path.startswith("/experiments/") or normalized_path == "/scenarios/run":
        return "experiments"
    if normalized_path.startswith("/faults/") or normalized_path == "/faults":
        return "fault_injection"
    if normalized_path.startswith("/tasks/") or normalized_path == "/tasks":
        return "task_dispatch"
    if normalized_path.startswith("/robots/") or normalized_path in {
        "/controls/clock",
        "/simulation/start",
        "/simulation/pause",
        "/simulation/step",
        "/simulation/reset",
    }:
        return "recovery" if normalized_path.startswith("/robots/") else "simulation_control"
    return "destructive"


def role_allows(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())
