"""Live Market Data Fetch — Task 02 (technical test PDF + question2.md)."""

from __future__ import annotations

import json
import logging
import math
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import yfinance as yf

# --- constants (question2.md Step 7 & 9: no magic strings in fetch logic) ---
ASSET_BTC = "BTC"
ASSET_NIFTY = "NIFTY"
ASSET_GOLD = "GOLD"

CURRENCY_USD = "USD"
CURRENCY_INR = "INR"

PROVIDER_COINGECKO = "coingecko"
PROVIDER_YFINANCE = "yfinance"

COINGECKO_SIMPLE_PRICE_BASE = (
    "https://api.coingecko.com/api/v3/simple/price"
)
HTTP_TIMEOUT_SEC = 20
USER_AGENT = "timecell-intern-problem2/1.0"

IST = timezone(timedelta(hours=5, minutes=30))

# Step 5: minimum column widths; table widens if content needs it.
_TABLE_MIN_ASSET_COL = 8
_TABLE_MIN_PRICE_COL = 12
_TABLE_MIN_CURRENCY_COL = 8

# Step 7: one row per asset; main loop only iterates this list.
MARKET_ASSETS: list[dict[str, Any]] = [
    {
        "display_name": ASSET_BTC,
        "quote_currency": CURRENCY_USD,
        "provider": PROVIDER_COINGECKO,
        "coin_id": "bitcoin",
        "vs_currency": "usd",
    },
    {
        "display_name": ASSET_NIFTY,
        "quote_currency": CURRENCY_INR,
        "provider": PROVIDER_YFINANCE,
        "yahoo_ticker": "^NSEI",
    },
    {
        "display_name": ASSET_GOLD,
        "quote_currency": CURRENCY_USD,
        "provider": PROVIDER_YFINANCE,
        "yahoo_ticker": "GC=F",
    },
]

TABLE_PRICE_UNAVAILABLE = "N/A"

logging.basicConfig(level=logging.WARNING, format="%(message)s")
log = logging.getLogger(__name__)


def _configure_stdout_utf8() -> None:
    """Reconfigure stdout to UTF-8 so Unicode box-drawing renders on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


@dataclass(frozen=True)
class PriceRow:
    """Single row: display name, formatted price (or N/A), quote currency."""

    asset: str
    price_display: str
    currency: str


def ist_timestamp_label() -> str:
    """Return local IST wall time as YYYY-MM-DD HH:MM:SS (no trailing IST)."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _log_fetch_failure(display_name: str, exc: BaseException) -> None:
    """Step 6: explicit [ERROR] line so failures are visible, not silent skips."""
    log.error(
        "[ERROR] Failed to fetch %s: %s - %s",
        display_name,
        type(exc).__name__,
        exc,
    )


def _coingecko_simple_price(coin_id: str, vs_currency: str) -> float:
    """
    CoinGecko simple price; raises on non-200, bad JSON, or missing keys.
    Step 6: network / 429 surface as urllib HTTPError / URLError.
    """
    query = urllib.parse.urlencode({"ids": coin_id, "vs_currencies": vs_currency})
    url = f"{COINGECKO_SIMPLE_PRICE_BASE}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    try:
        return float(payload[coin_id][vs_currency])
    except (KeyError, TypeError, ValueError) as e:
        raise KeyError(f"missing rate for {coin_id}/{vs_currency}") from e


def _yahoo_last_close(ticker: str) -> float:
    """Latest non-NaN close from yfinance; raises if empty or invalid."""
    hist = yf.Ticker(ticker).history(period="5d")
    if hist.empty or "Close" not in hist.columns:
        raise ValueError(f"no price history for {ticker!r}")
    last = hist["Close"].dropna().iloc[-1]
    val = float(last)
    if math.isnan(val):
        raise ValueError(f"close is NaN for {ticker!r}")
    return val


def _price_row_from_config(cfg: dict[str, Any]) -> PriceRow:
    """
    Fetch one configured asset. On any failure: log and return N/A (Step 6).
    """
    name = str(cfg["display_name"])
    quote = str(cfg["quote_currency"])
    provider = cfg["provider"]
    try:
        if provider == PROVIDER_COINGECKO:
            raw = _coingecko_simple_price(
                str(cfg["coin_id"]),
                str(cfg["vs_currency"]),
            )
            return PriceRow(name, f"{raw:,.2f}", quote)
        if provider == PROVIDER_YFINANCE:
            raw = _yahoo_last_close(str(cfg["yahoo_ticker"]))
            return PriceRow(name, f"{raw:,.2f}", quote)
        raise ValueError(f"unknown provider: {provider!r}")
    except Exception as e:  # noqa: BLE001 — per spec, never crash the script
        _log_fetch_failure(name, e)
        return PriceRow(name, TABLE_PRICE_UNAVAILABLE, quote)


def collect_price_rows() -> tuple[list[PriceRow], str]:
    """Run all MARKET_ASSETS; failures become N/A rows."""
    ts = ist_timestamp_label()
    rows = [_price_row_from_config(cfg) for cfg in MARKET_ASSETS]
    return rows, ts


def _table_column_widths(
    headers: tuple[str, str, str],
    body: list[tuple[str, str, str]],
) -> tuple[int, int, int]:
    """Column widths with Step 5 minimums."""
    h0, h1, h2 = headers
    return (
        max(_TABLE_MIN_ASSET_COL, len(h0), *(len(r[0]) for r in body)),
        max(_TABLE_MIN_PRICE_COL, len(h1), *(len(r[1]) for r in body)),
        max(_TABLE_MIN_CURRENCY_COL, len(h2), *(len(r[2]) for r in body)),
    )


def _format_table_line(
    asset: str,
    price: str,
    currency: str,
    w_asset: int,
    w_price: int,
    w_currency: int,
) -> str:
    """One bordered row: left asset/currency, right-aligned price string."""
    return (
        f"│ {asset:<{w_asset}} │ {price:>{w_price}} │ "
        f"{currency:<{w_currency}} │"
    )


def print_asset_table(rows: list[PriceRow], fetched_at_ist: str) -> None:
    """Unicode box table + IST headline (PDF + question2.md Step 5)."""
    headers: tuple[str, str, str] = ("Asset", "Price", "Currency")
    body = [(r.asset, r.price_display, r.currency) for r in rows]
    w0, w1, w2 = _table_column_widths(headers, body)

    top = f"┌{'─' * (w0 + 2)}┬{'─' * (w1 + 2)}┬{'─' * (w2 + 2)}┐"
    sep = f"├{'─' * (w0 + 2)}┼{'─' * (w1 + 2)}┼{'─' * (w2 + 2)}┤"
    bot = f"└{'─' * (w0 + 2)}┴{'─' * (w1 + 2)}┴{'─' * (w2 + 2)}┘"

    print(f"Asset Prices — fetched at {fetched_at_ist} IST")
    print(top)
    print(_format_table_line(headers[0], headers[1], headers[2], w0, w1, w2))
    print(sep)
    for a, p, c in body:
        print(_format_table_line(a, p, c, w0, w1, w2))
    print(bot)


def main() -> None:
    _configure_stdout_utf8()
    rows, ts = collect_price_rows()
    print_asset_table(rows, ts)


if __name__ == "__main__":
    main()
