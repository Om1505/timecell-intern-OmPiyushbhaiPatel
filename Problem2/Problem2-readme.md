# Task 02 — Live Market Data Fetch

This folder contains `Problem2.py` for the Timecell intern technical test (**Live Market Data Fetch**). It pulls live quotes for three configured assets, prints an IST-stamped Unicode box table, and **never exits early** because of a single failed provider.

## What the PDF asks for

Per the technical test brief: at least **one Indian stock/index** and **one crypto**, **free public APIs only**, a **formatted table** (asset, price, currency, fetch time in IST), and **graceful errors** — log failures and continue.

## Approach

**Asset config (`MARKET_ASSETS`)**  
All instruments are declared once as dictionaries (`question2.md` Step 7): display name, quote currency, provider id (`coingecko` or `yfinance`), and provider-specific fields (`coin_id` / `vs_currency`, or `yahoo_ticker`). The main path only iterates this list.

**Data sources**  
- **CoinGecko** — `simple/price` for spot crypto (e.g. `bitcoin` vs `usd`). No API key.  
- **yfinance** — Yahoo Finance for **NIFTY 50** (`^NSEI`, INR) and **gold futures** (`GC=F`, USD per troy oz). No API key.

**Timestamp**  
IST via `timezone(timedelta(hours=5, minutes=30))` and headline format  
`Asset Prices — fetched at YYYY-MM-DD HH:MM:SS IST` (`question2.md` Step 4).

**Table**  
Manual Unicode box drawing with f-string column padding (Step 5): comma thousands and two decimals for numeric prices (`f"{value:,.2f}"`).

**Error handling (8 pts)**  
Each asset is fetched inside `_price_row_from_config`: exceptions are **logged** with  
`[ERROR] Failed to fetch <Asset>: <ExceptionType> - <message>`  
and the row still appears with **`N/A`** in the price column so the script **does not crash** and the evaluators still see three rows (`question2.md` Step 6).  
yfinance empty history or **NaN** closes raise before formatting; CoinGecko network or **HTTP errors** (including rate limits) surface as exceptions and the same logging path applies. There is no bare `except:` or silent `pass`.

## How to run

Requires **Python 3.10+** and:

```bash
pip install yfinance
python Problem2.py
```

(Run from this folder or pass the full path to `Problem2.py`.)

## Testing error handling (Step 8)

Before submitting, force at least one failure and confirm you see an `[ERROR]` line and **`N/A`** in the table while the other rows still populate. For example:

- Temporarily set `"coin_id": "not-a-real-coin"` for the BTC entry in `MARKET_ASSETS`, or  
- Set `"yahoo_ticker": "FAKEASSETINVALID"` on the NIFTY or GOLD row.

Revert the config after the test.

**Note:** PDF sample output shows GOLD as `INR/g`; this solution follows `question2.md` / Yahoo **`GC=F`** as **USD** per contract unit.

## AI usage (honest log)

Per the test rubric, document how AI tools were used (if applicable).

- **Tool:** e.g. Cursor + AI assistant, local `question2.md` guide.  
- **What you should own:** You can explain each function, why `MARKET_ASSETS` is data-driven, how IST is computed, and how failures become logged `N/A` rows without stopping the run.
