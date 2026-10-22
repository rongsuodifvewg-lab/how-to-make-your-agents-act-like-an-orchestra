"""Budgeted evidence memory with lexical retrieval and provenance."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryItem:
    item_id: str
    text: str
    evidence_id: str
    scope: str
    tokens: int


class EvidenceMemory:
    def __init__(self) -> None:
        self.items: list[MemoryItem] = []
        self.compression_log: list[dict[str, object]] = []

    def add(self, text: str, evidence_id: str, scope: str = "task") -> str:
        item_id = hashlib.sha256(f"{evidence_id}:{text}".encode()).hexdigest()[:16]
        tokens = max(1, len(text.split()))
        self.items.append(MemoryItem(item_id, text, evidence_id, scope, tokens))
        return item_id

    @staticmethod
    def _terms(text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))

    def retrieve(self, query: str, token_budget: int, scope: str | None = None) -> list[MemoryItem]:
        query_terms = self._terms(query)
        candidates = [item for item in self.items if scope is None or item.scope == scope]
        ranked = sorted(candidates, key=lambda item: (len(query_terms & self._terms(item.text)), item.evidence_id), reverse=True)
        selected: list[MemoryItem] = []
        used = 0
        for item in ranked:
            if used + item.tokens > token_budget:
                continue
            selected.append(item)
            used += item.tokens
        self.compression_log.append({"query": query, "candidate_count": len(candidates), "selected_ids": [x.item_id for x in selected], "token_budget": token_budget})
        return selected
