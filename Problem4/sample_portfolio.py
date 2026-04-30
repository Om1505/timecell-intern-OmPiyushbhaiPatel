"""Sample portfolios for Task 04 demos and tests."""

from __future__ import annotations

from typing import Any

DEMO_PORTFOLIO: dict[str, Any] = {
    "name": "Demo HNI Portfolio — 1 Crore INR",
    "total_value_inr": 10_000_000,
    "monthly_expenses_inr": 80_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
        {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}

CASH_HEAVY_PORTFOLIO: dict[str, Any] = {
    "name": "Conservative — 90% Cash",
    "total_value_inr": 5_000_000,
    "monthly_expenses_inr": 50_000,
    "assets": [
        {"name": "CASH", "allocation_pct": 90, "expected_crash_pct": 0},
        {"name": "GOLD", "allocation_pct": 10, "expected_crash_pct": -15},
    ],
}

BTC_HEAVY_PORTFOLIO: dict[str, Any] = {
    "name": "Aggressive — 70% BTC",
    "total_value_inr": 20_000_000,
    "monthly_expenses_inr": 200_000,
    "assets": [
        {"name": "BTC", "allocation_pct": 70, "expected_crash_pct": -80},
        {"name": "NIFTY50", "allocation_pct": 20, "expected_crash_pct": -40},
        {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
    ],
}

PRESETS: dict[str, dict[str, Any]] = {
    "demo": DEMO_PORTFOLIO,
    "cash_heavy": CASH_HEAVY_PORTFOLIO,
    "btc_heavy": BTC_HEAVY_PORTFOLIO,
}
