"""Gemini-backed 'assumption you'd need to be wrong about' insight."""

from __future__ import annotations

import logging
import os
import warnings
from typing import Any

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"
MAX_OUTPUT_TOKENS = 300

_FALLBACK = (
    "[LLM insight unavailable — set a valid GEMINI_API_KEY "
    "(see .env.example) to see the assumption analysis.]"
)


def _asset_summary_lines(portfolio: dict[str, Any]) -> str:
    lines: list[str] = []
    total = float(portfolio["total_value_inr"])
    for a in portfolio.get("assets") or []:
        name = str(a["name"])
        pct = float(a["allocation_pct"])
        crash = float(a.get("expected_crash_pct", 0))
        slice_inr = total * (pct / 100.0)
        lines.append(
            f"- {name}: allocation {pct:.1f}%, slice ~₹{slice_inr:,.0f} INR, "
            f"user crash assumption {crash:+.1f}%"
        )
    return "\n".join(lines) if lines else "(no assets)"


def get_assumption_insight(
    portfolio: dict[str, Any],
    most_dangerous_scenario: str,
    scenario_result: dict[str, Any],
) -> str:
    """
    Call Gemini with the Task 04 system/user prompt; return plain text.

    On any failure (missing key, SDK error, network), returns a static fallback
    string so the CLI still finishes.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        try:
            import google.generativeai as genai
        except ImportError:
            log.warning("google-generativeai not installed; skipping LLM insight.")
            return _FALLBACK

    key = os.environ.get(GEMINI_API_KEY_ENV)
    if not key:
        log.warning("%s not set; skipping LLM insight.", GEMINI_API_KEY_ENV)
        return _FALLBACK

    total_v = float(portfolio["total_value_inr"])
    monthly = float(portfolio["monthly_expenses_inr"])
    post = float(scenario_result.get("post_crash_value_inr", 0))
    runway = scenario_result.get("runway_months", 0)
    if runway != float("inf"):
        try:
            runway_f = float(runway)
            runway_s = f"{runway_f:.1f}"
        except (TypeError, ValueError):
            runway_s = str(runway)
    else:
        runway_s = "∞"
    killing = scenario_result.get("killing_asset") or "—"
    killing_loss = float(scenario_result.get("killing_asset_loss_inr") or 0)
    year = scenario_result.get("year")
    year_s = str(year) if year is not None else "n/a"

    user_block = f"""Portfolio summary:
- Total value: {total_v:,.0f} INR
- Monthly expenses: {monthly:,.0f} INR
- Assets:
{_asset_summary_lines(portfolio)}

The scenario most likely to ruin this portfolio is: {most_dangerous_scenario} ({year_s})
Under this scenario:
- Post-crash value: {post:,.0f} INR
- Runway: {runway_s} months
- Biggest contributing loss: {killing} ({killing_loss:,.0f} INR lost)

Complete this sentence in 2–3 sentences:
"The assumption you would need to be wrong about for this portfolio to survive {most_dangerous_scenario} is..."

Then add one sentence: what single change to the portfolio allocation would most improve survival odds in this scenario?
"""

    prompt = (
        "You are a brutally honest financial risk advisor for high-net-worth Indian families.\n"
        "You speak like a CIO who has survived multiple market crashes — direct, clear, no hand-waving.\n"
        "Keep responses under 120 words.\n\n"
        f"{user_block}"
    )

    model_name = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": MAX_OUTPUT_TOKENS,
            },
        )
        try:
            text = response.text
        except ValueError:
            text = str(response)
        return (text or "").strip() or _FALLBACK
    except Exception as e:
        log.warning("Gemini call failed (%s): %s", type(e).__name__, e)
        return _FALLBACK
