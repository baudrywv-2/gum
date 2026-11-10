"""Provider usage / cost tracking (in-memory + optional DB persistence)."""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from packages.contracts.providers import (
    ProviderMode,
    ProviderName,
    ProviderUsageRecord,
)

# Rough placeholder unit costs for budget awareness (USD). Live rates TBD.
ESTIMATED_UNIT_COST_USD: dict[ProviderName, float] = {
    ProviderName.MOCK: 0.0,
    ProviderName.GOOGLE_ADS: 0.0,  # Google Ads API usually free; quota limited
    ProviderName.GOOGLE_TRENDS: 0.0,
    ProviderName.SERP: 0.005,
    ProviderName.X_API: 0.01,
    ProviderName.REDDIT: 0.0,
}


class UsageTracker:
    """Records provider calls for budgets, debugging, and later billing."""

    def __init__(self) -> None:
        self._records: list[ProviderUsageRecord] = []
        self._lock = threading.Lock()

    def record(
        self,
        *,
        provider: ProviderName,
        operation: str,
        mode: ProviderMode,
        units: int = 1,
        success: bool = True,
        cached: bool = False,
        query: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> ProviderUsageRecord:
        unit_cost = ESTIMATED_UNIT_COST_USD.get(provider, 0.0)
        # Cached / mock calls do not consume paid units.
        billable_units = 0 if cached or mode is ProviderMode.MOCK else units
        record = ProviderUsageRecord(
            provider=provider,
            operation=operation,
            mode=mode,
            units=billable_units,
            estimated_cost_usd=round(billable_units * unit_cost, 6),
            success=success,
            cached=cached,
            query=query,
            recorded_at=datetime.now(timezone.utc),
            details=details or {},
        )
        with self._lock:
            self._records.append(record)
        return record

    def list_records(self) -> list[ProviderUsageRecord]:
        with self._lock:
            return list(self._records)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            records = list(self._records)
        by_provider: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "units": 0, "estimated_cost_usd": 0.0, "cache_hits": 0}
        )
        for record in records:
            bucket = by_provider[record.provider.value]
            bucket["calls"] += 1
            bucket["units"] += record.units
            bucket["estimated_cost_usd"] = round(
                bucket["estimated_cost_usd"] + record.estimated_cost_usd, 6
            )
            if record.cached:
                bucket["cache_hits"] += 1
        return {
            "total_calls": len(records),
            "total_estimated_cost_usd": round(
                sum(r.estimated_cost_usd for r in records), 6
            ),
            "by_provider": dict(by_provider),
        }

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
