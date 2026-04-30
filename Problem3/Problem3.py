"""AI-Powered Portfolio Explainer — Task 03 (technical test PDF + question3.md)."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Any, Literal

import warnings

from google.api_core import exceptions as google_api_exceptions
from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd or parents if you configure it
# Library shows a FutureWarning on import; keep CLI output clean.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import google.generativeai as genai

# --- Gemini (question3.md Step 5): key from environment only ---
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
# Gemini 3.1 Flash Lite (AI Studio free tier often has quota here while 2.0-flash
# shows limit 0). Override with GEMINI_MODEL if your project uses another id.
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite-preview"

ALLOWED_VERDICTS = frozenset({"Aggressive", "Balanced", "Conservative"})
Tone = Literal["beginner", "experienced", "expert"]

log = logging.getLogger(__name__)


def _configure_stdout_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def _load_compute_risk_metrics():
    """Load ``compute_risk_metrics`` from sibling Task 01 module (question3.md Step 3.E)."""
    root = Path(__file__).resolve().parent.parent
    path = root / "Problem1" / "Problem1.py"
    if not path.is_file():
        raise FileNotFoundError(f"Expected Problem1.py at {path}")
    spec = spec_from_file_location("timecell_problem1", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.compute_risk_metrics


compute_risk_metrics = _load_compute_risk_metrics()


def portfolio_from_spec() -> dict[str, Any]:
    """Example portfolio from the technical test (aggressive / crypto-heavy)."""
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


def portfolio_conservative_demo() -> dict[str, Any]:
    """Mostly cash and gold — should read more conservative."""
    return {
        "total_value_inr": 5_000_000,
        "monthly_expenses_inr": 50_000,
        "assets": [
            {"name": "CASH", "allocation_pct": 55, "expected_crash_pct": 0},
            {"name": "GOLD", "allocation_pct": 25, "expected_crash_pct": -15},
            {"name": "NIFTY50", "allocation_pct": 20, "expected_crash_pct": -40},
        ],
    }


def portfolio_concentrated_demo() -> dict[str, Any]:
    """Edge case: 100% single high-drawdown asset."""
    return {
        "total_value_inr": 2_000_000,
        "monthly_expenses_inr": 100_000,
        "assets": [
            {"name": "BTC", "allocation_pct": 100, "expected_crash_pct": -80},
        ],
    }


DEMO_PORTFOLIOS: dict[str, dict[str, Any]] = {
    "spec": portfolio_from_spec(),
    "conservative": portfolio_conservative_demo(),
    "concentrated": portfolio_concentrated_demo(),
}


def format_portfolio_for_prompt(portfolio: dict[str, Any]) -> str:
    """Human-readable block from the live dict (PDF: not hardcoded prompt text)."""
    lines: list[str] = []
    lines.append(
        f"Total value (INR): {portfolio['total_value_inr']:,}"
    )
    lines.append(
        f"Monthly expenses (INR): {portfolio['monthly_expenses_inr']:,}"
    )
    lines.append("Holdings:")
    for a in portfolio["assets"]:
        lines.append(
            f"  - {a['name']}: {a['allocation_pct']}% allocation, "
            f"model crash {a['expected_crash_pct']}%"
        )
    return "\n".join(lines)


def format_metrics_for_prompt(metrics: dict[str, Any]) -> str:
    """Task 01 metrics as context for the LLM (question3.md Step 3.E)."""
    rm = metrics["runway_months"]
    runway = "infinity" if rm == float("inf") else str(rm)
    return (
        f"- post_crash_value_inr: {metrics['post_crash_value']:,.2f}\n"
        f"- runway_months: {runway}\n"
        f"- ruin_test: {metrics['ruin_test']}\n"
        f"- largest_risk_asset: {metrics['largest_risk_asset']}\n"
        f"- concentration_warning: {metrics['concentration_warning']}"
    )


TONE_INSTRUCTIONS: dict[Tone, str] = {
    "beginner": (
        "Use short sentences, little jargon, and brief analogies where helpful. "
        "Explain what a 'crash scenario' means in plain language. Be kind but honest."
    ),
    "experienced": (
        "Use standard portfolio vocabulary (allocation, drawdown, runway, "
        "concentration). Skip basic definitions; be direct and concrete."
    ),
    "expert": (
        "Use precise risk language (tail risk, severity of drawdowns, ruin "
        "probability framing). Be concise and technical; assume finance fluency."
    ),
}


def build_prompt(
    portfolio: dict[str, Any],
    metrics: dict[str, Any],
    *,
    tone: Tone = "beginner",
) -> str:
    """
    Full prompt: persona, data, Task 01 metrics, tone, JSON-only reply
    (question3.md Steps 3–4, 7).
    """
    pf = format_portfolio_for_prompt(portfolio)
    mf = format_metrics_for_prompt(metrics)
    tone_line = TONE_INSTRUCTIONS[tone]
    return f"""You are a friendly but honest financial advisor speaking to a \
non-expert Indian client.

Portfolio DATA:
{pf}

Computed severe-crash metrics (same assumptions as Task 01 — use these numbers \
in your explanation when relevant):
{mf}

AUDIENCE / DEPTH:
Tone mode: {tone}.
{tone_line}

YOUR TASK:
Explain this portfolio's risk in plain English. You MUST return ONLY valid JSON \
with exactly these keys and no others:
  "summary" — string, exactly 3 to 4 sentences on overall risk level.
  "doing_well" — string, ONE specific strength tied to this portfolio.
  "change_needed" — string, ONE specific change the investor should consider \
and WHY (include the reason in the same string).
  "verdict" — string, EXACTLY one of: Aggressive, Balanced, Conservative \
(capitalize as shown). No other verdict text.

Rules:
- Base claims on the DATA and metrics above; do not invent holdings.
- The verdict must be exactly one of the three allowed words.
- Output ONLY the JSON object, no markdown fences, no commentary."""


def build_critic_prompt(
    structured: dict[str, Any],
    portfolio: dict[str, Any],
    metrics: dict[str, Any],
) -> str:
    """Optional second call: critique the first explanation (question3.md Step 8)."""
    return f"""You are a senior financial analyst reviewing an AI draft for factual \
rigor and missing risks.

PORTFOLIO CONTEXT:
{format_portfolio_for_prompt(portfolio)}

METRICS CONTEXT:
{format_metrics_for_prompt(metrics)}

DRAFT JSON EXPLANATION:
{json.dumps(structured, indent=2)}

Write a short critique (plain text, not JSON): flag inaccuracies, overstated \
claims, missing risks, or unclear advice. Be specific and practical."""


def call_gemini(prompt: str, *, model_name: str) -> str:
    """Single Gemini ``generate_content`` call; returns raw text (Step 4: API only)."""
    api_key = os.environ.get(GEMINI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(
            f"Set {GEMINI_API_KEY_ENV} to your Google AI Studio API key "
            "(see question3.md Step 5)."
        )
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    try:
        response = model.generate_content(prompt)
    except google_api_exceptions.NotFound as e:
        raise RuntimeError(
            f"Gemini model {model_name!r} was not found or does not support "
            "generateContent for this API key. Set env GEMINI_MODEL to a current "
            f"id (default in repo: {DEFAULT_GEMINI_MODEL!r}). Underlying error: {e}"
        ) from e
    except google_api_exceptions.ResourceExhausted as e:
        raise RuntimeError(
            "Gemini quota exceeded (429) for model "
            f"{model_name!r}. Pick a model with free-tier quota in AI Studio "
            "(this repo defaults to gemini-3.1-flash-lite-preview), set "
            "GEMINI_MODEL accordingly, or wait for reset. "
            f"Details: {e}"
        ) from e
    try:
        text = response.text
    except ValueError:
        # Blocked or empty candidates — surface what we have.
        text = str(response)
    return text.strip()


def _extract_json_object(raw: str) -> str:
    """Strip optional ```json fences; take outermost {{ ... }} slice."""
    s = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", s, re.IGNORECASE)
    if fence:
        s = fence.group(1).strip()
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    return s[start : end + 1]


def parse_explainer_response(raw: str) -> dict[str, Any]:
    """
    Parse JSON fields; validate verdict (question3.md Step 6).
    On failure, raises ValueError — caller prints raw and handles.
    """
    blob = _extract_json_object(raw)
    data = json.loads(blob)
    for key in ("summary", "doing_well", "change_needed", "verdict"):
        if key not in data:
            raise KeyError(f"Missing key {key!r} in JSON.")
    verdict = str(data["verdict"]).strip()
    if verdict not in ALLOWED_VERDICTS:
        raise ValueError(
            f"verdict must be one of {sorted(ALLOWED_VERDICTS)}, got {verdict!r}"
        )
    return {
        "summary": str(data["summary"]).strip(),
        "doing_well": str(data["doing_well"]).strip(),
        "change_needed": str(data["change_needed"]).strip(),
        "verdict": verdict,
    }


def explain_portfolio(
    portfolio: dict[str, Any],
    *,
    tone: Tone = "beginner",
    model_name: str | None = None,
    with_critic: bool = False,
) -> None:
    """Orchestrate metrics → prompt → API → print raw vs structured (+ critic)."""
    model = model_name or os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    metrics = compute_risk_metrics(portfolio)
    prompt = build_prompt(portfolio, metrics, tone=tone)

    print("=== RAW API RESPONSE (explainer) ===\n")
    raw = call_gemini(prompt, model_name=model)
    print(raw)
    print()

    print("=== STRUCTURED OUTPUT ===\n")
    structured: dict[str, Any] | None = None
    try:
        structured = parse_explainer_response(raw)
        print(json.dumps(structured, indent=2, ensure_ascii=False))
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        log.warning("Could not parse structured JSON: %s", e)
        print(f"(Parse error: {e})\nSee raw response above.")

    if not with_critic or structured is None:
        return

    crit_prompt = build_critic_prompt(structured, portfolio, metrics)
    print("\n=== RAW API RESPONSE (critic) ===\n")
    crit_raw = call_gemini(crit_prompt, model_name=model)
    print(crit_raw)
    print()


def load_portfolio_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    _configure_stdout_utf8()

    parser = argparse.ArgumentParser(
        description="AI Portfolio Explainer (Timecell Task 03).",
    )
    parser.add_argument(
        "--portfolio",
        type=Path,
        help="Path to JSON file with keys total_value_inr, monthly_expenses_inr, assets",
    )
    parser.add_argument(
        "--demo",
        choices=sorted(DEMO_PORTFOLIOS.keys()),
        help="Use a built-in demo portfolio instead of --portfolio",
    )
    parser.add_argument(
        "--demo-all",
        action="store_true",
        help="Run all built-in demos sequentially (question3.md Step 10)",
    )
    parser.add_argument(
        "--tone",
        choices=("beginner", "experienced", "expert"),
        default="beginner",
        help="Explanation depth (bonus; default beginner per PDF non-expert client)",
    )
    parser.add_argument(
        "--critic",
        action="store_true",
        help="Second LLM call to critique the first explanation (bonus)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Gemini model id (default: env GEMINI_MODEL or {DEFAULT_GEMINI_MODEL})",
    )
    args = parser.parse_args()

    if args.demo_all:
        for name in ("spec", "conservative", "concentrated"):
            print(f"\n########## DEMO: {name} ##########\n")
            explain_portfolio(
                DEMO_PORTFOLIOS[name],
                tone=args.tone,
                model_name=args.model,
                with_critic=args.critic,
            )
        return

    if args.portfolio is not None:
        portfolio = load_portfolio_json(args.portfolio)
    elif args.demo is not None:
        portfolio = DEMO_PORTFOLIOS[args.demo]
    else:
        portfolio = DEMO_PORTFOLIOS["spec"]

    explain_portfolio(
        portfolio,
        tone=args.tone,
        model_name=args.model,
        with_critic=args.critic,
    )

if __name__ == "__main__":
    main()
