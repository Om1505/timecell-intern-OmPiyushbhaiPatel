"""What Would Ruin You? — Crash Scenario Simulator (Task 04 main CLI)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from display import (
    print_custom_scenario_prompt,
    print_danger_highlight,
    print_header,
    print_llm_insight,
    print_portfolio_summary,
    print_running_message,
    print_scenario_table,
    print_warn,
)
from llm_insight import get_assumption_insight
from sample_portfolio import PRESETS
from scenarios import DEFAULT_CRASH_PCT, DEFAULT_SCENARIO_KEY, SCENARIO_ORDER, SCENARIOS

log = logging.getLogger(__name__)

RUIN_THRESHOLD_MONTHS = 12
ALLOCATION_TOLERANCE_PCT = 0.01
CROR_INR = 10_000_000.0
LAKH_INR = 100_000.0
RUNWAY_ROUND_DECIMALS = 1
LOSS_PCT_ROUND_DECIMALS = 1


def format_inr(value: float) -> str:
    """
    Format INR amounts readably: crore, lakh, or thousands with grouping.
    """
    if value != value:  # NaN
        return "₹—"
    av = abs(value)
    sign = "-" if value < 0 else ""
    if av >= CROR_INR:
        return f"{sign}₹{av / CROR_INR:.2f} Cr"
    if av >= LAKH_INR:
        return f"{sign}₹{av / LAKH_INR:.2f} L"
    return f"{sign}₹{av:,.0f}"


def normalize_portfolio(
    portfolio: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """
    Return a portfolio copy with allocations scaled to sum to 100%, and warnings.

    ``expected_crash_pct`` from Task 01 shape is preserved but not used in
    scenario simulation (historical ``asset_crashes`` drive outcomes).
    """
    warnings: list[str] = []
    out = deepcopy(portfolio)
    assets = out.get("assets") or []
    total_alloc = sum(float(a["allocation_pct"]) for a in assets)
    if total_alloc <= 0:
        warnings.append("Portfolio has zero total allocation; cannot normalize.")
        return out, warnings
    if abs(total_alloc - 100.0) > ALLOCATION_TOLERANCE_PCT:
        warnings.append(
            f"Allocations sum to {total_alloc:.1f}% — scaled to 100% for simulation."
        )
        scale = 100.0 / total_alloc
        for a in assets:
            a["allocation_pct"] = float(a["allocation_pct"]) * scale
    return out, warnings


def _crash_pct_for_asset(
    asset_name: str,
    scenario: dict[str, Any],
) -> tuple[float, bool]:
    """
    Return (crash_decimal, used_default) for ``asset_name`` in ``scenario``.

    Matching is case-insensitive against ``asset_crashes`` keys. Missing keys
    use ``DEFAULT_CRASH_PCT``. Custom scenarios require every asset to be
    present after prompts — still applies default if omitted.
    """
    crashes: dict[str, float] = scenario["asset_crashes"]
    lower_map = {k.upper(): v for k, v in crashes.items()}
    key = asset_name.strip().upper()
    if key in lower_map:
        return float(lower_map[key]), False
    return DEFAULT_CRASH_PCT, True


def compute_scenario_outcome(
    portfolio: dict[str, Any],
    scenario: dict[str, Any],
    *,
    scenario_key: str,
) -> dict[str, Any]:
    """
    Compute post-crash value, runway, ruin test, and dominant loss contributor
    for one named scenario.
    """
    normalized, _ = normalize_portfolio(portfolio)
    total_value = float(normalized["total_value_inr"])
    monthly = float(normalized["monthly_expenses_inr"])
    assets = normalized["assets"]

    post_total = 0.0
    per_asset_loss: dict[str, float] = {}
    used_default_assets: list[str] = []

    for asset in assets:
        name = str(asset["name"])
        alloc_pct = float(asset["allocation_pct"])
        pre = total_value * (alloc_pct / 100.0)
        crash_pct, used_default = _crash_pct_for_asset(name, scenario)
        if used_default:
            used_default_assets.append(name)
        post_piece = pre * (1.0 + crash_pct)
        post_total += post_piece
        loss = pre - post_piece
        per_asset_loss[name] = per_asset_loss.get(name, 0.0) + loss

    value_lost = total_value - post_total
    loss_pct = (value_lost / total_value * 100.0) if total_value > 0 else 0.0

    if monthly <= 0:
        runway = float("inf")
    else:
        runway = round(post_total / monthly, RUNWAY_ROUND_DECIMALS)

    ruin_test = "PASS" if runway >= RUIN_THRESHOLD_MONTHS else "FAIL"

    killing_asset: str | None = None
    killing_loss = 0.0
    for aname, loss in per_asset_loss.items():
        if killing_asset is None or loss > killing_loss + 1e-9:
            killing_loss = loss
            killing_asset = aname

    killing_used_default = False
    if killing_asset is not None:
        killing_used_default = killing_asset.upper() in {
            x.upper() for x in used_default_assets
        }

    has_btc = any(str(a["name"]).strip().upper() == "BTC" for a in assets)
    note_2008_btc = scenario_key == "2008_gfc" and has_btc

    return {
        "scenario_key": scenario_key,
        "scenario_name": str(scenario["name"]),
        "year": scenario.get("year"),
        "post_crash_value_inr": post_total,
        "value_lost_inr": value_lost,
        "loss_pct": round(loss_pct, LOSS_PCT_ROUND_DECIMALS),
        "runway_months": runway,
        "ruin_test": ruin_test,
        "killing_asset": killing_asset,
        "killing_asset_loss_inr": killing_loss if killing_loss >= 0 else 0.0,
        "killing_asset_used_default_crash": killing_used_default,
        "used_default_crash_assets": used_default_assets,
        "btc_2008_inactive_note": note_2008_btc,
    }


def find_most_dangerous_scenario(results: list[dict[str, Any]]) -> str:
    """
    Return the human-readable scenario name that is most dangerous:

    - Among ``FAIL`` rows, lowest ``runway_months`` wins.
    - If all ``PASS``, lowest ``runway_months`` among all rows.
    """
    if not results:
        return ""

    fails = [r for r in results if r["ruin_test"] == "FAIL"]
    pool = fails if fails else results

    def runway_key(r: dict[str, Any]) -> float:
        v = float(r["runway_months"])
        return v if v != float("inf") else float("inf")

    worst = min(pool, key=runway_key)
    return str(worst["scenario_name"])


def get_result_by_scenario_name(
    results: list[dict[str, Any]], scenario_name: str
) -> dict[str, Any] | None:
    for r in results:
        if r["scenario_name"] == scenario_name:
            return r
    return None


def run_all_scenarios(
    portfolio: dict[str, Any],
    *,
    include_custom: bool = False,
    custom_asset_crashes: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Run every scenario in ``SCENARIO_ORDER``, optionally appending ``custom``
    populated with ``custom_asset_crashes``.
    """
    out: list[dict[str, Any]] = []
    for key in SCENARIO_ORDER:
        out.append(
            compute_scenario_outcome(
                portfolio, SCENARIOS[key], scenario_key=key
            )
        )
    if include_custom and custom_asset_crashes is not None:
        custom_scen = deepcopy(SCENARIOS[DEFAULT_SCENARIO_KEY])
        custom_scen["asset_crashes"] = {
            k.upper(): float(v) for k, v in custom_asset_crashes.items()
        }
        out.append(
            compute_scenario_outcome(
                portfolio, custom_scen, scenario_key=DEFAULT_SCENARIO_KEY
            )
        )
    return out


def load_portfolio_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[error] Could not read portfolio file: {path} ({e})", file=sys.stderr)
        sys.exit(1)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[error] Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    return data


def is_cash_only_indestructible(portfolio: dict[str, Any]) -> bool:
    """True when every holding is CASH after normalization (edge-case banner)."""
    normalized, _ = normalize_portfolio(portfolio)
    assets = normalized.get("assets") or []
    if not assets:
        return False
    for a in assets:
        if str(a["name"]).strip().upper() != "CASH":
            return False
    return True


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")

    parser = argparse.ArgumentParser(
        description=(
            "What Would Ruin You? — stress a Task-01-shaped portfolio against "
            "historical crashes."
        )
    )
    parser.add_argument(
        "--portfolio",
        type=Path,
        default=None,
        help="Path to portfolio JSON (overrides --preset when set)",
    )
    parser.add_argument(
        "--preset",
        choices=sorted(PRESETS.keys()),
        default="demo",
        help="Built-in portfolio preset when --portfolio is omitted",
    )
    parser.add_argument(
        "--custom",
        action="store_true",
        help="Prompt for per-asset crash %% and append a Custom scenario row",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Gemini assumption insight (no API key required)",
    )
    args = parser.parse_args()

    if args.portfolio is not None:
        portfolio = load_portfolio_json(args.portfolio)
    else:
        portfolio = deepcopy(PRESETS[args.preset])

    norm_warnings = normalize_portfolio(portfolio)[1]
    for w in norm_warnings:
        print_warn(w)

    print_header()
    print_portfolio_summary(portfolio, format_inr=format_inr)

    custom_map: dict[str, float] | None = None
    if args.custom:
        names = [str(a["name"]) for a in portfolio.get("assets", [])]
        custom_map = print_custom_scenario_prompt(names)

    print_running_message(historical=len(SCENARIO_ORDER), with_custom=args.custom)

    results = run_all_scenarios(
        portfolio,
        include_custom=args.custom,
        custom_asset_crashes=custom_map,
    )
    print_scenario_table(results, format_inr=format_inr)

    if is_cash_only_indestructible(portfolio):
        print_warn(
            "This portfolio is boring but indestructible — 100% CASH across holdings."
        )

    most_name = find_most_dangerous_scenario(results)
    most_res = get_result_by_scenario_name(results, most_name)
    if most_res:
        print_danger_highlight(most_name, most_res, format_inr=format_inr)

    if not args.no_llm:
        if most_res is None:
            most_res = results[-1] if results else {}
        insight = get_assumption_insight(portfolio, most_name, most_res or {})
        print_llm_insight(insight)


if __name__ == "__main__":
    main()
