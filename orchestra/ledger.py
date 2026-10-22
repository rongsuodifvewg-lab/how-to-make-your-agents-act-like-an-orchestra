"""Append-only, hash-chained execution ledger."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .schema import TraceEvent, TypedMessage


class Ledger:
    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    @property
    def last_hash(self) -> str:
        return self.events[-1].digest() if self.events else "GENESIS"

    def append(self, event_type: str, task_id: str, decision: str, payload: dict[str, Any]) -> TraceEvent:
        sequence = len(self.events)
        # The fixture ledger is deterministic: wall-clock timing belongs in a
        # separate telemetry field and must not change the evidence hash.
        event = TraceEvent(event_type, task_id, decision, payload, sequence, timestamp_ms=sequence, previous_hash=self.last_hash)
        self.events.append(event)
        return event

    def record_message(self, message: TypedMessage) -> TraceEvent:
        return self.append("message", message.task_id, message.next_action, message.as_dict())

    def verify_chain(self) -> bool:
        previous = "GENESIS"
        for index, event in enumerate(self.events):
            if event.sequence != index or event.previous_hash != previous:
                return False
            previous = event.digest()
        return True

    def export(self) -> list[dict[str, Any]]:
        return [asdict(event) | {"digest": event.digest()} for event in self.events]
