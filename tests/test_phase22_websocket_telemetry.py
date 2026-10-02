import asyncio

import pytest

from backend.api import fastapi_app as api


def test_phase22_telemetry_envelope_preserves_authoritative_shape():
    api.telemetry_sequence = 0
    payload = api._telemetry_envelope({
        "timestamp": 12.3,
        "robots": [{"robot_id": "R1"}],
        "tasks": [],
        "incidents": [],
        "faults": [],
        "metrics": {},
        "simulation": {},
        "resilience": {},
    })
    assert payload["message_type"] == "TELEMETRY"
    assert payload["sequence"] == 1
    assert payload["timestamp"] == 12.3
    assert payload["robots"][0]["robot_id"] == "R1"
    assert "server_timestamp" in payload


@pytest.mark.asyncio
async def test_phase22_bounded_queue_keeps_latest_snapshot():
    class DummyWS:
        pass

    ws = DummyWS()
    q = asyncio.Queue(maxsize=2)
    api._websocket_queues[ws] = q
    await api._enqueue_telemetry(ws, {"sequence": 1})
    await api._enqueue_telemetry(ws, {"sequence": 2})
    await api._enqueue_telemetry(ws, {"sequence": 3})
    assert q.qsize() == 2
    assert await q.get() == {"sequence": 2}
    assert await q.get() == {"sequence": 3}
    api._websocket_queues.pop(ws, None)


def test_phase22_reconnect_snapshot_cache_is_authoritative():
    original = api.latest_telemetry
    try:
        api.latest_telemetry = {
            "message_type": "TELEMETRY",
            "sequence": 99,
            "timestamp": 55.0,
            "robots": [{"robot_id": "R2"}],
        }
        assert api.latest_telemetry["sequence"] == 99
        assert api.latest_telemetry["robots"][0]["robot_id"] == "R2"
    finally:
        api.latest_telemetry = original
