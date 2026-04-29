"""Portfolio Risk Calculator — Task 01 ."""

from __future__ import annotations

import sys

BAR_CHAR = "█"


def _bar_character_for_terminal() -> str:
    """
    Prefer full block ``█``. Try UTF-8 stdout (common on modern Windows); else fall back to ``#``.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        BAR_CHAR.encode(encoding)
    except UnicodeEncodeError:
        return "#"
    return BAR_CHAR


def _compute_risk_metrics(portfolio: dict, crash_multiplier: float) -> dict:
    """
    Core metrics with crash severity scaled by ``crash_multiplier`` (1.0 = full crash, 0.5 = moderate).

    ``expected_crash_pct`` is multiplied by ``crash_multiplier`` before post-crash value and
    largest-risk scoring (same formulas as the base task).
    """
    total_value_inr = float(portfolio["total_value_inr"])
    monthly_expenses_inr = float(portfolio["monthly_expenses_inr"])
    assets = portfolio["assets"]

    post_crash_value = 0.0
    largest_risk_asset = None
    max_risk_score = -1.0
    concentration_warning = False

    # Per-asset crash impact, concentration, and risk score (allocation × |effective crash|).
    for asset in assets:
        alloc = float(asset["allocation_pct"])
        crash_pct = float(asset["expected_crash_pct"])
        name = asset["name"]

        effective_crash_pct = crash_pct * crash_multiplier

        asset_value = (alloc / 100.0) * total_value_inr
        crashed_value = asset_value * (1 + effective_crash_pct / 100.0)
        post_crash_value += crashed_value

        risk_score = alloc * abs(effective_crash_pct)
        if risk_score > max_risk_score:
            max_risk_score = risk_score
            largest_risk_asset = name

        if alloc > 40:
            concentration_warning = True

    if not assets:
        largest_risk_asset = None

    # Runway: guard zero monthly expenses (infinite runway if anything left after crash).
    if monthly_expenses_inr == 0:
        runway_months = float("inf") if post_crash_value > 0 else 0.0
    else:
        runway_months = post_crash_value / monthly_expenses_inr

    if runway_months != float("inf"):
        runway_months = round(runway_months, 2)

    ruin_test = "PASS" if runway_months > 12 else "FAIL"

    return {
        "post_crash_value": post_crash_value,
        "runway_months": runway_months,
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
    }


def compute_risk_metrics(portfolio: dict) -> dict:
    """
    Full (severe) crash scenario: each asset uses 100% of ``expected_crash_pct``.

    Expected portfolio keys: total_value_inr, monthly_expenses_inr, assets (list of dicts
    with name, allocation_pct, expected_crash_pct).
    """
    return _compute_risk_metrics(portfolio, crash_multiplier=1.0)


def compute_both_crash_scenarios(portfolio: dict) -> dict[str, dict]:
    """
    Bonus: full crash vs moderate crash (each asset loses 50% of expected crash magnitude).

    Returns two result dicts with the same keys as ``compute_risk_metrics``.
    """
    return {
        "full_crash": _compute_risk_metrics(portfolio, crash_multiplier=1.0),
        "moderate_crash": _compute_risk_metrics(portfolio, crash_multiplier=0.5),
    }


def print_crash_scenarios_side_by_side(portfolio: dict) -> None:
    """Print full vs moderate scenario metrics side by side (Bonus / PDF)."""
    scenarios = compute_both_crash_scenarios(portfolio)
    full = scenarios["full_crash"]
    mod = scenarios["moderate_crash"]
    labels = [
        ("post_crash_value", "post_crash_value"),
        ("runway_months", "runway_months"),
        ("ruin_test", "ruin_test"),
        ("largest_risk_asset", "largest_risk_asset"),
        ("concentration_warning", "concentration_warning"),
    ]
    label_width = 22
    print(f"{'':{label_width}} {'FULL CRASH':{label_width}} {'MODERATE (50%)':{label_width}}")
    print("-" * (label_width * 3 + 2))
    for key, _ in labels:
        full_value = full[key]
        moderate_value = mod[key]
        print(f"{key:{label_width}} {str(full_value):{label_width}} {str(moderate_value):{label_width}}")


def print_allocation_bar_chart(portfolio: dict, max_bar_width: int = 40) -> None:
    """
    Bonus: CLI bar chart of allocation breakdown (PDF: no external plotting libraries).

    Each row: ``NAME | <block bar> | NN%`` using only built-ins and Unicode block ``█``.
    Bar length: ``int((allocation_pct / 100) * max_bar_width)`` per question1.md Step 6.
    """
    assets = portfolio["assets"]
    name_width = max((len(str(asset["name"])) for asset in assets), default=0)
    name_width = max(name_width, 8)

    print("\nAllocation (CLI bar chart)")
    print("-" * (name_width + 3 + max_bar_width + 3 + 6))

    bar_symbol = _bar_character_for_terminal()

    for asset in assets:
        name = str(asset["name"])
        allocation_pct = float(asset["allocation_pct"])
        bar_length = int((allocation_pct / 100.0) * max_bar_width)
        bar_segment = bar_symbol * bar_length + " " * (max_bar_width - bar_length)
        pct_label = allocation_pct
        if pct_label == int(pct_label):
            pct_str = f"{int(pct_label)}%"
        else:
            pct_str = f"{pct_label:g}%"

        print(f"{name:{name_width}} | {bar_segment} | {pct_str}")


def example_portfolio_from_spec() -> dict:
    """The portfolio from the technical test PDF (Step 7 manual check)."""
    return {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC", "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD", "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH", "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }

if __name__ == "__main__":

    demo = example_portfolio_from_spec()
    print("\nRisk metrics (full crash):")
    for key, value in compute_risk_metrics(demo).items():
        print(f"  {key}: {value}")

    print()
    print_crash_scenarios_side_by_side(demo)
    print_allocation_bar_chart(demo)
