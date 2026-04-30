"""Terminal presentation for the crash scenario simulator (Rich only)."""

from __future__ import annotations

import math
import sys
from typing import Any, Callable

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scenarios import DEFAULT_CRASH_PCT

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (OSError, ValueError):
        pass

console = Console()

_BAR_WIDTH = 32

COLOR_GREEN = {"CASH", "GOLD", "BONDS"}
COLOR_YELLOW = {"NIFTY50", "NIFTY"}
COLOR_RED = {"BTC", "ETH"}


def _asset_style(name: str) -> str:
    u = name.strip().upper()
    if u in COLOR_GREEN:
        return "green"
    if u in COLOR_YELLOW:
        return "yellow"
    if u in COLOR_RED:
        return "red"
    return "white"


def print_warn(message: str) -> None:
    """Print a non-fatal warning line."""
    console.print(f"[yellow]⚠ {message}[/yellow]")


def print_header() -> None:
    """Print the Task 04 title banner."""
    title = Text()
    title.append(
        "╔══════════════════════════════════════════════════════════════╗\n",
        style="bold",
    )
    title.append(
        "║         WHAT WOULD RUIN YOU? — Crash Scenario Simulator      ║\n",
        style="bold cyan",
    )
    title.append(
        "║                    Timecell.ai · Task 04                     ║\n",
        style="dim",
    )
    title.append(
        "╚══════════════════════════════════════════════════════════════╝",
        style="bold",
    )
    console.print(title)
    console.print()


def print_running_message(*, historical: int, with_custom: bool) -> None:
    """Tell the user how many scenarios are simulating."""
    suffix = " + 1 custom scenario" if with_custom else ""
    console.print(
        f"\n[bold]Running {historical} historical crash scenarios{suffix}...[/bold]\n"
    )


def print_portfolio_summary(
    portfolio: dict[str, Any],
    *,
    format_inr: Callable[[float], str],
) -> None:
    """Rich panel: headline values and per-asset allocation bars."""
    name = str(portfolio.get("name", "Portfolio"))
    total = float(portfolio["total_value_inr"])
    monthly = float(portfolio["monthly_expenses_inr"])
    assets = portfolio.get("assets") or []
    alloc_sum = sum(float(a["allocation_pct"]) for a in assets)
    scale = 100.0 / alloc_sum if alloc_sum else 0.0

    body_parts: list[str] = [
        f"[bold]Portfolio:[/bold] {name}\n",
        f"Total Value : {format_inr(total)}   |   Monthly Expenses: {format_inr(monthly)}\n",
        "\n[bold]Assets:[/bold]\n",
    ]

    for asset in assets:
        raw_pct = float(asset["allocation_pct"])
        pct = raw_pct * scale if alloc_sum else 0.0
        value = total * (pct / 100.0)
        filled = max(0, min(_BAR_WIDTH, int(round((pct / 100.0) * _BAR_WIDTH))))
        bar_plain = "█" * filled + "░" * (_BAR_WIDTH - filled)
        nm = str(asset["name"])
        style = _asset_style(nm)
        amt = format_inr(value)
        body_parts.append(
            f"  [{style}]{nm:<8}[/{style}]  [{style}]{bar_plain}[/{style}]  "
            f"{pct:5.1f}%   {amt}\n"
        )

    console.print(
        Panel.fit("".join(body_parts).rstrip(), title="Holdings", border_style="dim")
    )


def _format_runway(months: float) -> str:
    if months == float("inf") or math.isinf(months):
        return "∞"
    return f"{months:>{5}.1f} mo"


def _risk_cell(res: dict[str, Any]) -> str:
    ka = res.get("killing_asset")
    if not ka:
        return "—"
    star = "*" if res.get("killing_asset_used_default_crash") else ""
    return f"{ka}{star}"


def print_scenario_table(
    results: list[dict[str, Any]],
    *,
    format_inr: Callable[[float], str],
) -> None:
    """Sort and print PASS/FAIL-coloured scenario rows."""

    def runway_val(r: dict[str, Any]) -> float:
        v = float(r["runway_months"])
        return v if not math.isinf(v) else float("inf")

    fails = [r for r in results if r["ruin_test"] == "FAIL"]
    oks = [r for r in results if r["ruin_test"] == "PASS"]
    fails.sort(key=runway_val)
    oks.sort(key=runway_val, reverse=True)
    ordered = fails + oks

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold")
    table.add_column("Scenario", overflow="fold")
    table.add_column("Post-Crash", justify="right")
    table.add_column("Lost", justify="right")
    table.add_column("Loss%", justify="right")
    table.add_column("Runway", justify="right")
    table.add_column("Ruin Test", justify="center")
    table.add_column("Biggest Risk", overflow="fold")

    footnotes: list[str] = []

    for res in ordered:
        is_fail = res["ruin_test"] == "FAIL"
        row_style = "bold red" if is_fail else "green"

        post = float(res["post_crash_value_inr"])
        lost = float(res["value_lost_inr"])
        loss_pct = float(res["loss_pct"])
        rw = float(res["runway_months"])

        table.add_row(
            Text(str(res["scenario_name"]), style=row_style),
            Text(format_inr(post), style=row_style),
            Text(format_inr(lost), style=row_style),
            Text(f"{loss_pct:.1f}%", style=row_style),
            Text(_format_runway(rw), style=row_style),
            Text(res["ruin_test"], style=row_style),
            Text(_risk_cell(res), style=row_style),
        )

        defaults = res.get("used_default_crash_assets") or []
        if defaults:
            footnotes.append(
                f"* default {abs(int(round(DEFAULT_CRASH_PCT * 100)))}% drawdown applied: "
                f"{', '.join(sorted(defaults))}"
            )
        if res.get("btc_2008_inactive_note"):
            footnotes.append(
                "2008 GFC: BTC treated as 0% move (not a listed macro asset then)."
            )

    console.print(table)
    seen: set[str] = set()
    for line in footnotes:
        if line not in seen:
            seen.add(line)
            console.print(f"[dim]{line}[/dim]")


def print_danger_highlight(
    most_dangerous: str,
    result: dict[str, Any],
    *,
    format_inr: Callable[[float], str],
) -> None:
    """Highlight the single worst scenario for the portfolio."""
    ka = result.get("killing_asset") or "—"
    kl = float(result.get("killing_asset_loss_inr") or 0.0)
    rw = float(result["runway_months"])
    rw_s = "∞" if rw == float("inf") or math.isinf(rw) else f"{rw:.1f}"

    body = (
        f"[bold red]⚠  MOST DANGEROUS SCENARIO:[/bold red] {most_dangerous}\n"
        f"Runway: {rw_s} months — Biggest threat: {ka} "
        f"(lost {format_inr(kl)})\n"
        f'[italic]"This is the scenario most likely to end you."[/italic]'
    )
    console.print()
    console.print(
        Panel.fit(
            body,
            border_style="red",
            title="[bold red]Risk focus[/bold red]",
        )
    )


def print_llm_insight(insight_text: str) -> None:
    """Render Gemini / fallback insight in a framed panel."""
    console.print()
    console.print(
        Panel.fit(
            insight_text.strip(),
            title="🧠 The Assumption You'd Need To Be Wrong About",
            border_style="magenta",
        )
    )


def print_custom_scenario_prompt(asset_names: list[str]) -> dict[str, float]:
    """
    Interactively collect crash percentages (negative for declines) per asset.

    Accepts values like -60 (meaning -60%) or -0.6 (already a decimal fraction).
    Returns upper-cased keys mapped to decimal fractions (e.g. -0.60).
    """
    console.print(
        Panel.fit(
            "Enter expected price moves as percent (e.g. -60 for -60%) "
            "or as decimals (-0.60). Positive numbers mean appreciation.",
            title="Custom scenario",
            border_style="blue",
        )
    )
    out: dict[str, float] = {}
    for raw in asset_names:
        name = raw.strip()
        while True:
            try:
                s = console.input(
                    f"Crash / move for [bold]{name}[/bold] (% or decimal): "
                ).strip()
                val = float(s)
            except ValueError:
                console.print("[red]Invalid number — try again.[/red]")
                continue
            if abs(val) > 1.0 + 1e-9:
                val = val / 100.0
            out[name.upper()] = float(val)
            break
    return out
