# Task 03 — AI-Powered Portfolio Explainer

This folder contains `Problem3.py` for the Timecell intern technical test (**AI-Powered Portfolio Explainer**): it sends a **structured prompt** (including Task 01 metrics) to **Google Gemini**, prints the **raw model text**, then prints **parsed JSON** fields required by the brief. Optional **tone** modes and a **critic** second call match the official bonus items.

## What the PDF requires

- **Input:** a **portfolio dictionary** with the **same shape as Task 01**: `total_value_inr`, `monthly_expenses_inr`, `assets` (each asset: `name`, `allocation_pct`, `expected_crash_pct`).
- **Behavior:** call an **LLM API**; the **prompt must live in your code** (see `build_prompt`); the script must work for **different portfolios** (CLI JSON file or built-in demos), not a single hardcoded story baked only into the prompt.
- **Output content** from the model (then validated / displayed):
  1. **3–4 sentences** — plain-English **summary** of risk level  
  2. **One** specific **doing_well** point  
  3. **One** specific **change_needed** plus **why**  
  4. **verdict** — exactly **`Aggressive`**, **`Balanced`**, or **`Conservative`**
- **Printing:** **`RAW API RESPONSE`** and **`STRUCTURED OUTPUT`** must appear **separately** (two sections).
- **README:** document **prompt approach**, what you tried, what worked, what you changed (this file + comments in `Problem3.py`).

**Allowed:** any Python 3.10+ libraries; **API key must not be committed** — use an environment variable.

## Setup

1. Create a free key at [Google AI Studio](https://aistudio.google.com) (**Get API key**).
2. Install the client library:

```bash
pip install google-generativeai
```

3. Set the key (examples):

- **Windows (cmd):** `set GEMINI_API_KEY=your_key_here`  
- **Windows (PowerShell):** `$env:GEMINI_API_KEY="your_key_here"`  
- **macOS/Linux:** `export GEMINI_API_KEY=your_key_here`

Optional: **`GEMINI_MODEL`** — override the default if your project uses another id ([model list](https://ai.google.dev/gemini-api/docs/models)). Default in code is **`gemini-3.1-flash-lite-preview`** (Gemini 3.1 Flash Lite on the AI Studio usage dashboard). If you see **429 / quota limit 0** for `gemini-2.0-flash`, switch to this default or another model row that shows non-zero limits in your dashboard.

## How to run

From the repo root or this folder:

```bash
# Default: PDF-style example portfolio from Task 01 spec
python Problem3.py

# Built-in demo by name: spec | conservative | concentrated
python Problem3.py --demo conservative

# All three built-in portfolios (good for prompt iteration)
python Problem3.py --demo-all

# Your own portfolio JSON file
python Problem3.py --portfolio path/to/portfolio.json

# Bonus: tone (beginner default, per PDF non-expert client)
python Problem3.py --tone experienced

# Bonus: second LLM call that critiques the first explanation
python Problem3.py --critic
```

## Code layout (what evaluators score under “structure”)

| Piece | Role |
|--------|------|
| `format_portfolio_for_prompt` / `format_metrics_for_prompt` | Turn the live dict + Task 01 metrics into prompt text |
| `build_prompt` | Persona, data, metrics, tone instructions, **JSON-only** contract |
| `call_gemini` | API configuration and `generate_content` only |
| `parse_explainer_response` / `_extract_json_object` | Parse and **validate** `verdict` |
| `build_critic_prompt` + second `call_gemini` | Optional critic pass |

Task 01 math is reused by **loading** `Problem1/Problem1.py` at runtime (`compute_risk_metrics`), so the LLM sees **`post_crash_value`**, **`runway_months`**, **`ruin_test`**, **`largest_risk_asset`**, **`concentration_warning`** — as recommended in `question3.md` Step 3.E.

## Prompt design (what we optimized for)

**First instinct (weak):** “Explain this portfolio’s risk” with no format → rambling text, wrong verdict labels, missing fields.

**What we changed (stronger):**

1. **Persona** — friendly, honest advisor for an **Indian non-expert** (PDF tone).
2. **Grounding** — portfolio **formatted from the actual dict** + **computed metrics** so the model cannot ignore runway / ruin / concentration.
3. **JSON-only** response with **fixed keys** (`summary`, `doing_well`, `change_needed`, `verdict`) — reliable `json.loads` and marking.
4. **Verdict constraint** — exactly one of three capitalized tokens; parser **rejects** anything else so bad output is visible, not silently passed through.
5. **Tone bonus** — `beginner` / `experienced` / `expert` blocks adjust vocabulary and depth (`TONE_INSTRUCTIONS`).

**Critic bonus:** a **separate** system-style instruction (`build_critic_prompt`) and a **second** raw response block — chaining calls without mixing parse logic into the API layer.

*(After your own runs, paste a real **raw vs structured** snippet into this README or your Loom notes — the PDF asks for that reflection.)*

## AI usage (honest log)

If you used Cursor, Copilot, or another assistant, say **what you asked**, **what you verified by hand** (prompt wording, JSON keys, Gemini safety blocks), and **what you own** in review (e.g. metric injection, parsing, CLI).

## Troubleshooting

- **`Set GEMINI_API_KEY`** — key missing from the environment.
- **429 / quota (`ResourceExhausted`, limit 0 for a model)** — your project has no free-tier quota on that model (e.g. `gemini-2.0-flash`). Use **`gemini-3.1-flash-lite-preview`** (script default) or another model that shows non-zero limits in AI Studio.
- **Parse error** — model returned prose or markdown despite instructions; check **RAW** output; tighten the prompt or set **`GEMINI_MODEL`** to a current Flash / Flash-Lite id.
- **`FileNotFoundError` for Problem1.py** — run from the repo layout where `Problem1/Problem1.py` exists next to `Problem3/`.
