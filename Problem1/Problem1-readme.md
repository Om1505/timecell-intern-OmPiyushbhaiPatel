# Task 01 — Portfolio Risk Calculator

This folder contains `Problem1.py`: a small pure-Python module for the Timecell intern technical test (Portfolio Risk Calculator).

## Approach

**Core metrics (`compute_risk_metrics`)**  
For each asset we take its share of `total_value_inr`, apply the crash as `value × (1 + expected_crash_pct/100)`, and sum for `post_crash_value`. `runway_months` is `post_crash_value / monthly_expenses_inr` (rounded to two decimals when finite). `ruin_test` is `PASS` only when runway is **strictly** greater than 12 months. `largest_risk_asset` is the name with the highest `allocation_pct × |expected_crash_pct|`. `concentration_warning` is `True` if any single position is **strictly** above 40% of the portfolio.

**Edge cases**  
Zero allocation contributes nothing to value and risk score. If `monthly_expenses_inr` is zero, runway is modeled as infinity when post-crash value is positive (so ruin test follows from comparing infinity to 12). Empty `assets` yields zero post-crash value and `largest_risk_asset` of `None`. Allocations do not need to sum to 100%; each slice is computed independently.

**Bonus 1 — moderate crash**  
`_compute_risk_metrics(portfolio, crash_multiplier)` scales each `expected_crash_pct` before applying the same formulas (`1.0` = full crash, `0.5` = half the crash magnitude). `compute_both_crash_scenarios` returns full and moderate dicts; `print_crash_scenarios_side_by_side` prints them in aligned columns.

**Bonus 2 — CLI bar chart**  
`print_allocation_bar_chart` prints each asset as `NAME | █… | NN%` with bar length `int((allocation_pct / 100) × max_bar_width)` (default width 40). Only the Python standard library and a Unicode block character are used—no plotting packages. On Windows, the script attempts `stdout` UTF-8 reconfigure so `█` renders; if the active encoding still cannot encode it, bars use `#` so printing never crashes.

**Testing**  
Run the module as a script to execute a small demo:

```bash
python Problem1.py
```

## AI usage (honest log)

Per the rubric, this documents **how** AI was used—not to hide it.

- **Tool:** Cursor with an integrated AI assistant (Claude), plus repo-local guides in `question1.md`.
- **Prompts (paraphrased):**  
  - Implement `compute_risk_metrics` exactly from the spec and `question1.md`, including edge cases (zero expenses, zero allocation, empty assets).  
  - Refactor with a `crash_multiplier` helper for the moderate-crash bonus; keep `compute_risk_metrics` as the public full-crash API.  
  - Add a CLI allocation bar chart with no third-party libraries, following Step 6 formatting.  
  - Add executable checks for the Step 7 numeric example and a short task README with an AI usage section.
- **What the model got right:** Straight-line translation of formulas; side-by-side scenario printing; bar chart structure; splitting core logic into `_compute_risk_metrics`.
- **What I verified or adjusted:** Re-read the PDF for strict vs non-strict inequalities (`runway > 12`, allocation `> 40` for concentration); chose explicit naming and comments for clarity; ensured moderate scenario matches “50% of crash magnitude” on the sample (e.g. post-crash total ₹78,50,000).
- **What I own:** I can explain every line in review: how effective crash affects value and risk score, why infinity is used for zero expenses, and how bar width maps from percentages.

