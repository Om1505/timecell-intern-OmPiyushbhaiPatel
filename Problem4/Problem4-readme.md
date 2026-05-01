# Task 04 — What Would Ruin You? (Open Problem)

This folder implements the **Crash Scenario Simulator** CLI from the Timecell internship technical test: stress a Task-01-shaped portfolio against named historical crashes, highlight the worst case for runway vs expenses, and optionally ask Gemini for the single “assumption you’d need to be wrong about.”

### Section 1: What I Built

Most portfolio tools tell you how much you could make. Timecell asks a different question — what does failure look like? That line stuck with me.

So for Task 4, I wanted to build a failure detector. Something that takes your portfolio and runs it through real historical crashes — 2008, COVID, the crypto winter — and tells you plainly: here's the scenario that ruins you, and here's exactly why.

So it can give answer for most fearful question: will my portfolio survive if market crash like 2020 covid happens again? So it will give answer what happens to your portfolio in worst case situation.

Because the honest truth is, a portfolio that survives a crypto winter but gets wiped out by a 2008-style crash isn't balanced — it's just lucky so far.

I also added one LLM call that I think is the most interesting part — it tells you the single assumption you'd need to be wrong about for your portfolio to survive its worst-case scenario. That felt like something a real advisor would say.

This is a feature Timecell could ship tomorrow. That's why I built it.

`crash_simulator.py` is the entry point. It loads a portfolio (JSON file, or a built-in preset), **normalises allocations** if they do not sum to 100% (with a warning), runs four historical scenarios from `scenarios.py`, prints a **Rich** comparison table (pass/fail vs a **12-month runway** rule, post-crash value, loss, killing asset; default **−20%** moves for unknown asset names are marked with `*` and footnoted), highlights the **most dangerous** scenario, then—unless you pass **`--no-llm`**—calls **`llm_insight.py`** (Google **Gemini**, key via **`GEMINI_API_KEY`** / `.env`). There is **no** web UI and **no** charting libraries; output is terminal-only. **Custom mode** (`--custom`) prompts for per-asset moves and appends a **Custom User-Defined Scenario** row.

**Run (from this folder):**

```bash
pip install google-generativeai python-dotenv rich
python crash_simulator.py --no-llm
python crash_simulator.py --portfolio my_portfolio.json
python crash_simulator.py --preset btc_heavy
python crash_simulator.py --custom
```

Copy `.env.example` to `.env` and set `GEMINI_API_KEY` for the insight panel (the PDF positions Task 4 as the open problem; `question4.md` specifies Gemini for this layer).

### Section 2: Why I Chose This Idea

[Timecell.ai](https://timecell.ai) frames wealth work around **what failure looks like** before celebrating upside—the rubric literally asks for the assumption you’d have to be wrong about. A **failure detector** fits that better than a tracker: it ties each row to a **named historical regime** and a **source string**, so outputs stay **traceable** rather than vibes-based. For **HNI Indian** portfolios (INR base, NIFTY, gold, USDINR-style shocks in the scenario deck), the question “which past crisis ends you, and which line item did it?” is the conversation a family office or advisor actually needs before markets get choppy.

### Section 3: Why This Is Worth Building

**Who:** Private bankers, wealth advisors, and family-office CIOs who already have allocations but need a **repeatable stress narrative** for clients. **When:** Before volatility spikes, at **annual reviews**, or when a client adds a concentrated bet (e.g. crypto). **Decision:** It helps answer concrete allocation questions—“**Do I cut BTC before a risk-off episode?**”, “**Is my INR expense runway robust to a 2013-style INR shock?**”—with numbers attached, optional AI only for the closing “assumption” sentence so the table stays deterministic.

---

## AI usage (honest log)

Per the rubric, this documents **how** AI was used—not to hide it.

- **Tool:** Cursor with an integrated AI assistant (Claude), repo guide `question4.md`, and alignment with Task 01/03 patterns where helpful.
- **Prompts (paraphrased):**  
  - Implement Task 04 layout under `Problem4/` (`crash_simulator.py`, `scenarios.py`, `display.py`, `llm_insight.py`, `sample_portfolio.py`) per `question4.md`: historical scenario dict, runway/ruin/killing-asset math, Rich tables, CLI flags (`--portfolio`, `--preset`, `--custom`, `--no-llm`).  
  - Use **Gemini** (`GEMINI_API_KEY`, `gemini-3.1-flash-lite-preview`, `max_output_tokens=300`) for the assumption insight; graceful fallback if the key or SDK is missing.  
  - Handle edge cases: allocation normalisation, zero expenses → ∞ runway, 100% cash message, JSON load errors, default −20% for unknown asset keys, optional 2008/BTC footnote.
- **What the model got right:** End-to-end scaffolding, `rich` table sorting (FAIL first by runway), separation of display vs core logic, preset/sample portfolios.
- **What I verified or adjusted:** Chose **Gemini** for `llm_insight.py` as in `question4.md` FILE 4 (vs the older ANTHROPIC snippet in the `.env` example section of the same doc); rounded runway to one decimal; **ruin** rule **`runway >= 12`** per spec; confirmed math by hand on one scenario row; `.env.example` documents `GEMINI_API_KEY` (PDF not present in this workspace—requirements taken from `question4.md`).
- **What I own:** I can walk through `compute_scenario_outcome`, how **most dangerous** is chosen among FAIL then PASS, and how custom prompts feed the **custom** scenario row.
