"""Simple provider response cache (in-memory; DB-backed records optional)."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any

from packages.contracts.providers import ProviderName, ProviderRequest, ProviderResponse


@dataclass
class CacheEntry:
    response: ProviderResponse
    expires_at: float


class ProviderCache:
    """Thread-safe TTL cache keyed by provider + request fingerprint."""

    def __init__(self, default_ttl_seconds: int = 300) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._entries: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def make_key(provider: ProviderName, request: ProviderRequest) -> str:
        payload = {
            "provider": provider.value,
            "query": request.query.strip().lower(),
            "geography": request.geography,
            "language": request.language,
            "limit": request.limit,
            "metadata": request.metadata,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"{provider.value}:{digest}"

    def get(self, key: str) -> ProviderResponse | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self.misses += 1
                return None
            if entry.expires_at < time.time():
                del self._entries[key]
                self.misses += 1
                return None
            self.hits += 1
            cached = entry.response.model_copy(deep=True)
            cached.cached = True
            return cached

    def set(
        self,
        key: str,
        response: ProviderResponse,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        with self._lock:
            self._entries[key] = CacheEntry(
                response=response.model_copy(deep=True),
                expires_at=time.time() + ttl,
            )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "size": len(self._entries),
                "hits": self.hits,
                "misses": self.misses,
                "default_ttl_seconds": self.default_ttl_seconds,
            }
