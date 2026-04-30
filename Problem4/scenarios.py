"""Named historical crash scenarios for the Task 04 simulator."""

from __future__ import annotations

from typing import Any

# When an asset is absent from a scenario's ``asset_crashes``, assume this move.
DEFAULT_CRASH_PCT = -0.20

# Order used for CLI table and "Running N scenarios..." messaging.
SCENARIO_ORDER: list[str] = [
    "2008_gfc",
    "2020_covid",
    "2022_crypto_winter",
    "2013_taper_tantrum",
]

DEFAULT_SCENARIO_KEY = "custom"

SCENARIOS: dict[str, dict[str, Any]] = {
    "2008_gfc": {
        "name": "2008 Global Financial Crisis",
        "year": 2008,
        "description": "Lehman Brothers collapse. Global markets froze.",
        "source": "NIFTY fell ~60%, Gold +25%, BTC did not exist",
        "asset_crashes": {
            "BTC": 0.0,
            "NIFTY50": -0.60,
            "GOLD": 0.05,
            "CASH": 0.0,
            "ETH": 0.0,
            "REALESTATE": -0.30,
            "BONDS": 0.10,
            "USDINR": -0.25,
        },
        "btc_existed": False,
    },
    "2020_covid": {
        "name": "2020 COVID Crash",
        "year": 2020,
        "description": "Pandemic panic. Markets crashed in 6 weeks.",
        "source": "NIFTY fell ~38%, BTC fell ~50%, Gold +10%",
        "asset_crashes": {
            "BTC": -0.50,
            "NIFTY50": -0.38,
            "GOLD": 0.10,
            "CASH": 0.0,
            "ETH": -0.55,
            "REALESTATE": -0.10,
            "BONDS": 0.05,
            "USDINR": -0.05,
        },
        "btc_existed": True,
    },
    "2022_crypto_winter": {
        "name": "2022 Crypto Winter",
        "year": 2022,
        "description": "Terra/LUNA collapse. BTC fell 77%. Equities largely flat.",
        "source": "BTC -77%, ETH -80%, NIFTY flat, Gold flat",
        "asset_crashes": {
            "BTC": -0.77,
            "NIFTY50": -0.05,
            "GOLD": 0.0,
            "CASH": 0.0,
            "ETH": -0.80,
            "REALESTATE": 0.0,
            "BONDS": -0.10,
            "USDINR": -0.03,
        },
        "btc_existed": True,
    },
    "2013_taper_tantrum": {
        "name": "2013 Taper Tantrum India",
        "year": 2013,
        "description": "Fed signals tapering. INR crashed, capital flight from India.",
        "source": "NIFTY -20%, INR -20% vs USD, Gold rose in INR terms",
        "asset_crashes": {
            "BTC": -0.50,
            "NIFTY50": -0.10,
            "GOLD": 0.15,
            "CASH": 0.0,
            "ETH": 0.0,
            "REALESTATE": -0.05,
            "BONDS": -0.15,
            "USDINR": -0.20,
        },
        "btc_existed": True,
    },
    "custom": {
        "name": "Custom User-Defined Scenario",
        "year": None,
        "description": "User defines crash % per asset",
        "source": "User input",
        "asset_crashes": {},
        "btc_existed": True,
    },
}
