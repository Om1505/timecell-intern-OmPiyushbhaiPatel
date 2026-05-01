# Timecell internship — technical solutions

**Walkthrough video:** [intern-timecell-OmPiyushbhaiPatel.mp4](https://drive.google.com/file/d/1hRlNaRFlLTX83GDfQV1PPus5A7Oq9OAj/view?usp=sharing)

This repo contains four tasks from the Timecell internship technical assignment. Each task lives in its own folder with runnable code and a detailed write-up.

---

## Problems overview

### Problem 1 — Portfolio Risk Calculator

Pure-Python crash stress test: post-crash value, runway in months, pass/fail vs a 12-month rule, concentration warning, moderate-crash variant, and a CLI allocation bar chart (stdlib only).

**Detailed explanation:** [Problem1/Problem1-readme.md](Problem1/Problem1-readme.md)

---

### Problem 2 — Live Market Data Fetch

Fetches live quotes for configured assets (e.g. crypto via CoinGecko, Indian index and commodities via yfinance), prints an IST-stamped table, and keeps going when any single fetch fails.

**Detailed explanation:** [Problem2/Problem2-readme.md](Problem2/Problem2-readme.md)

---

### Problem 3 — AI-Powered Portfolio Explainer

Sends portfolio + Task 1–style metrics to Google Gemini with an in-code prompt; prints raw model output and parsed structured fields (summary, strengths, changes, verdict), with optional tone and critic bonuses.

**Detailed explanation:** [Problem3/Problem3-readme.md](Problem3/Problem3-readme.md)

---

### Problem 4 — Crash Scenario Simulator (open problem)

CLI that stresses a portfolio against named historical crashes, ranks worst-case runway and “killing asset,” and optionally asks Gemini for the single assumption you’d need to be wrong about to survive the worst case—see [Problem4/Problem4-readme.md](Problem4/Problem4-readme.md) for motivation, setup (`GEMINI_API_KEY`), and AI usage notes.

**Detailed explanation:** [Problem4/Problem4-readme.md](Problem4/Problem4-readme.md)
