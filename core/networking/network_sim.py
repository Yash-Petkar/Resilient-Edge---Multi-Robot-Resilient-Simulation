"""Deterministic message-transport simulation for ResilientEdge.

Phase 16 makes inter-robot communication pass through an explicit transport
queue. Packet loss, latency, jitter, duplication, reordering and partitions
affect delivery rather than merely producing telemetry.
"""
import ast
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any


@dataclass
class NetworkMessage:
    sender: str
    recipient: str
    payload: Dict[str, Any]
    send_time: float
    deliver_time: float
    message_id: str = ""
    is_duplicate: bool = False
    status: str = "PENDING"
    delivered_time: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.message_id:
            # Backward-compatible deterministic fallback for restored/legacy messages.
            self.message_id = f"legacy-{self.sender}-{self.recipient}-{self.send_time:.6f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "send_time": self.send_time,
            "deliver_time": self.deliver_time,
            "is_duplicate": self.is_duplicate,
            "status": self.status,
            "delivered_time": self.delivered_time,
        }


class NetworkSimulator:
    """Authoritative deterministic transport boundary between simulated robots."""

    def __init__(self, seed: int = 42):
        self.seed = int(seed)
        self.random = random.Random(seed)
        self.in_flight_messages: List[NetworkMessage] = []
        self.total_sent = 0
        self.total_dropped = 0
        self.total_delivered = 0
        self.total_duplicated = 0
        self.total_reordered = 0
        self.total_stale = 0
        self._next_message_id = 1
        self.current_latency = 0.012
        self.current_loss_rate = 0.001
        self.current_jitter = 0.002
        self.current_duplication_rate = 0.0
        self.current_reorder_rate = 0.0
        self.is_partitioned = False
        self.partition_groups: Optional[Tuple[set, set]] = None
        self.latency_samples_ms: List[float] = []

    def _new_id(self) -> str:
        message_id = f"msg_{self._next_message_id:08d}"
        self._next_message_id += 1
        return message_id

    @staticmethod
    def _crosses_partition(sender: str, recipient: str,
                           partition_groups: Optional[Tuple[set, set]]) -> bool:
        if not partition_groups:
            return False
        group_a, group_b = partition_groups
        return (sender in group_a and recipient in group_b) or (
            sender in group_b and recipient in group_a
        )

    def send_message(
        self,
        sender: str,
        recipient: str,
        payload: Dict[str, Any],
        current_time: float,
        loss_rate: float = 0.0,
        latency: float = 0.01,
        jitter: float = 0.0,
        duplication_rate: float = 0.0,
        reorder_rate: float = 0.0,
        is_partitioned: bool = False,
        partition_groups: Optional[Tuple[set, set]] = None,
    ) -> bool:
        """Queue a message after applying transport conditions.

        ``True`` means accepted into the transport queue. ``False`` means the
        message was dropped before delivery (loss or partition).
        """
        self.total_sent += 1
        self.current_latency = float(latency)
        self.current_loss_rate = float(loss_rate)
        self.current_jitter = float(jitter)
        self.current_duplication_rate = float(duplication_rate)
        self.current_reorder_rate = float(reorder_rate)
        self.is_partitioned = bool(is_partitioned)
        self.partition_groups = partition_groups

        sender, recipient = str(sender), str(recipient)
        if is_partitioned and self._crosses_partition(sender, recipient, partition_groups):
            self.total_dropped += 1
            return False

        effective_loss = max(0.0, min(1.0, float(loss_rate)))
        if effective_loss and self.random.random() < effective_loss:
            self.total_dropped += 1
            return False

        jitter_offset = self.random.uniform(-jitter, jitter) if jitter > 0 else 0.0
        applied_latency = max(0.001, float(latency) + jitter_offset)

        # Reordering is modeled by adding a deterministic, seeded delay to the
        # selected message. The delivery queue remains the sole source of truth.
        if reorder_rate > 0.0 and self.random.random() < float(reorder_rate):
            applied_latency += self.random.uniform(0.1, 0.5)
            self.total_reordered += 1

        self.latency_samples_ms.append(applied_latency * 1000.0)
        deliver_time = float(current_time) + applied_latency
        msg = NetworkMessage(
            sender=sender,
            recipient=recipient,
            payload=dict(payload),
            send_time=float(current_time),
            deliver_time=deliver_time,
            message_id=self._new_id(),
        )
        self.in_flight_messages.append(msg)

        if duplication_rate > 0.0 and self.random.random() < float(duplication_rate):
            self.total_duplicated += 1
            dup_msg = NetworkMessage(
                sender=sender,
                recipient=recipient,
                payload=dict(payload),
                send_time=float(current_time),
                deliver_time=deliver_time + self.random.uniform(0.02, 0.08),
                message_id=self._new_id(),
                is_duplicate=True,
            )
            self.in_flight_messages.append(dup_msg)

        return True

    def poll_delivered(self, current_time: float) -> List[NetworkMessage]:
        """Remove and return all messages whose simulated delivery time elapsed.

        Delivery is sorted by delivery timestamp, with message ID as a stable
        tie-breaker. This makes same-time delivery deterministic.
        """
        due = [m for m in self.in_flight_messages if m.deliver_time <= current_time]
        self.in_flight_messages = [m for m in self.in_flight_messages if m.deliver_time > current_time]
        due.sort(key=lambda m: (m.deliver_time, m.message_id))
        for msg in due:
            msg.status = "DELIVERED"
            msg.delivered_time = float(current_time)
        self.total_delivered += len(due)
        return due

    def configure(
        self,
        *,
        loss_rate: Optional[float] = None,
        latency: Optional[float] = None,
        jitter: Optional[float] = None,
        duplication_rate: Optional[float] = None,
        reorder_rate: Optional[float] = None,
        is_partitioned: Optional[bool] = None,
        partition_groups: Optional[Tuple[set, set]] = None,
    ) -> None:
        """Configure persistent transport conditions for direct simulator use."""
        values = {
            "loss_rate": self.current_loss_rate if loss_rate is None else loss_rate,
            "latency": self.current_latency if latency is None else latency,
            "jitter": self.current_jitter if jitter is None else jitter,
            "duplication_rate": self.current_duplication_rate if duplication_rate is None else duplication_rate,
            "reorder_rate": self.current_reorder_rate if reorder_rate is None else reorder_rate,
            "is_partitioned": self.is_partitioned if is_partitioned is None else is_partitioned,
        }
        for name in ("loss_rate", "duplication_rate", "reorder_rate"):
            if not 0.0 <= float(values[name]) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        for name in ("latency", "jitter"):
            if float(values[name]) < 0:
                raise ValueError(f"{name} must be non-negative")
        self.current_loss_rate = float(values["loss_rate"])
        self.current_latency = float(values["latency"])
        self.current_jitter = float(values["jitter"])
        self.current_duplication_rate = float(values["duplication_rate"])
        self.current_reorder_rate = float(values["reorder_rate"])
        self.is_partitioned = bool(values["is_partitioned"])
        self.partition_groups = partition_groups

    def get_network_metrics(self) -> Dict[str, Any]:
        return {
            "latency_ms": round(self.current_latency * 1000.0, 1),
            "packet_loss_rate": round(self.current_loss_rate, 4),
            "jitter_ms": round(self.current_jitter * 1000.0, 1),
            "messages_sent": self.total_sent,
            "messages_dropped": self.total_dropped,
            "messages_delivered": self.total_delivered,
            "messages_duplicated": self.total_duplicated,
            "messages_reordered": self.total_reordered,
            "stale_messages": self.total_stale,
            "in_flight_count": len(self.in_flight_messages),
            "is_partitioned": self.is_partitioned,
            "partition_groups": [sorted(g) for g in self.partition_groups] if self.partition_groups else [],
            "latency_samples_ms": list(self.latency_samples_ms[-1000:]),
        }

    def reset(self):
        self.in_flight_messages.clear()
        self.total_sent = self.total_dropped = self.total_delivered = 0
        self.total_duplicated = self.total_reordered = self.total_stale = 0
        self.current_latency = 0.012
        self.current_loss_rate = 0.001
        self.current_jitter = 0.002
        self.current_duplication_rate = 0.0
        self.current_reorder_rate = 0.0
        self.is_partitioned = False
        self.partition_groups = None
        self.latency_samples_ms.clear()
        self.random.seed(self.seed)
        self._next_message_id = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "next_message_id": self._next_message_id,
            "total_sent": self.total_sent,
            "total_dropped": self.total_dropped,
            "total_delivered": self.total_delivered,
            "total_duplicated": self.total_duplicated,
            "total_reordered": self.total_reordered,
            "total_stale": self.total_stale,
            "current_latency": self.current_latency,
            "current_loss_rate": self.current_loss_rate,
            "current_jitter": self.current_jitter,
            "current_duplication_rate": self.current_duplication_rate,
            "current_reorder_rate": self.current_reorder_rate,
            "is_partitioned": self.is_partitioned,
            "partition_groups": [sorted(g) for g in self.partition_groups] if self.partition_groups else [],
            "latency_samples_ms": list(self.latency_samples_ms[-1000:]),
            "in_flight_messages": [m.to_dict() for m in self.in_flight_messages],
            "random_state": repr(self.random.getstate()),
        }

    def from_dict(self, data: Dict[str, Any]):
        self.seed = int(data.get("seed", self.seed))
        self._next_message_id = int(data.get("next_message_id", 1))
        self.total_sent = int(data.get("total_sent", 0))
        self.total_dropped = int(data.get("total_dropped", 0))
        self.total_delivered = int(data.get("total_delivered", 0))
        self.total_duplicated = int(data.get("total_duplicated", 0))
        self.total_reordered = int(data.get("total_reordered", 0))
        self.total_stale = int(data.get("total_stale", 0))
        self.current_latency = float(data.get("current_latency", 0.012))
        self.current_loss_rate = float(data.get("current_loss_rate", 0.001))
        self.current_jitter = float(data.get("current_jitter", 0.002))
        self.current_duplication_rate = float(data.get("current_duplication_rate", 0.0))
        self.current_reorder_rate = float(data.get("current_reorder_rate", 0.0))
        self.is_partitioned = bool(data.get("is_partitioned", False))
        pg = data.get("partition_groups")
        self.partition_groups = (set(pg[0]), set(pg[1])) if pg and len(pg) == 2 else None
        self.latency_samples_ms = [float(v) for v in data.get("latency_samples_ms", [])][-1000:]
        random_state = data.get("random_state")
        if random_state:
            try:
                self.random.setstate(ast.literal_eval(random_state))
            except (ValueError, SyntaxError, TypeError) as exc:
                raise ValueError("invalid network random_state in snapshot") from exc
        self.in_flight_messages = [
            NetworkMessage(
                sender=m["sender"], recipient=m["recipient"], payload=m.get("payload", {}),
                send_time=float(m.get("send_time", 0.0)),
                deliver_time=float(m.get("deliver_time", 0.0)),
                message_id=str(m.get("message_id", "")),
                is_duplicate=bool(m.get("is_duplicate", False)),
                status=str(m.get("status", "PENDING")),
                delivered_time=(float(m["delivered_time"]) if m.get("delivered_time") is not None else None),
            )
            for m in data.get("in_flight_messages", [])
        ]
        # Legacy snapshots may not contain the next ID.
        if self.in_flight_messages and self._next_message_id <= 1:
            nums = []
            for m in self.in_flight_messages:
                match = __import__("re").search(r"msg_(\d+)$", m.message_id)
                if match:
                    nums.append(int(match.group(1)))
            if nums:
                self._next_message_id = max(nums) + 1
