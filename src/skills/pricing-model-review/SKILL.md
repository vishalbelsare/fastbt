---
name: pricing-model-review
description: Decisive framework for evaluating any pricing or valuation model (options, derivatives, fair-value engines) before trusting its output. Five phases — identify the claim, desk-read the math as implemented, run the invariant battery, verify every finding by running code, benchmark against market prices with a null baseline. Use when reviewing/auditing a pricing model, asking "is this model correct", or before wiring model output into a trading decision. For judging STRATEGY RETURNS use statistical-testing instead; this skill judges PRICING MODELS.
metadata:
  version: "1.0.0"
  origin: "Distilled from the Aug 2026 four-model review in the research repo (QUANT_CRITIQUE.md)"
---

# Pricing Model Review

Canonical copy: `.claude/skills/pricing-model-review/` in the research repo;
the `~/.claude/skills/` copy is an install. Edit the repo copy first.

## Purpose

Answer: **"Can this model's numbers be trusted, and for what?"** — decisively,
with every claim either reproduced numerically or verified against the code,
and with the market (not another library, not the model's own docs) as the
final judge.

## Core rules

1. **Docs describe intent; only code is evidence.** Review the math as
   implemented, never as documented. (A methodology doc in the origin repo
   described a weighting scheme the code did not perform.)
2. **No finding without verification.** Every finding is tagged
   `[verified-by-run]` (numeric reproduction, numbers quoted) or
   `[desk-verified]` (unambiguous from the code). A finding that fails
   verification is DROPPED, not hedged. The cautionary exemplar: a "missing
   Hastings correction" in an MH sampler looked like a clear bug — running it
   showed a second error (missing prior Jacobian) exactly cancelled it; the
   naive one-sided "fix" would have *introduced* bias.
3. **The market judges models; libraries judge implementations.** Agreement
   with QuantLib/BS means "same formula", never "right model".
4. **Level beats correlation.** All sane option models correlate ~0.95 with
   market cross-sectionally (moneyness and tenor dominate). The
   model/market ratio and its residuals are the evidence; r is not.

## The five phases

### Phase 0 — Identify the claim

Before reading any code, force answers to:
- What does the model claim to output — a **risk-neutral price** (drift r,
  discounted) or a **real-world expected payoff** (historical drift, no
  discount)? These differ by the risk premium and are not comparable to each
  other, only to market.
- Day count: trading days (252) or calendar (365)? What do *callers* pass?
- Units: fractional or percent returns? Per contract or per lot?
- What data does it assume (columns, sort order, source), and what does it
  silently do when that data is missing?

A model whose owner cannot answer these fails the review at phase 0.
(Origin example: an empirical model's "10% underpricing" was a measure
property — real-world payoff vs VRP-bearing market prices — not a bug.)

### Phase 1 — Desk read

Read every pricing-relevant file, formula by formula, walking
`references/gotchas.md` (the failure-mode catalog: measure/conventions,
statistics, simulation, plumbing, evaluation traps — each with a detection
method and a real observed example). Output: candidate findings with
`file:line`. Do not trust variable names ("closed_form", "probability_otm",
"per_lot") — check what the code computes.

### Phase 2 — Invariant battery

Run the checks in `references/invariants.md` (adapt
`scripts/invariant_checks.py` — the model only needs a
`price_fn(spot, strike, days, kind) -> {'fair_value','probability_itm'}`
adapter). Any failure is a confirmed bug. Headliners: put-call parity,
strike/tenor monotonicity, martingale check for risk-neutral MC, limit
reductions (λ→0 ⇒ BS, T→0 ⇒ intrinsic), degenerate-data probe.

### Phase 3 — Verify-by-run

For each candidate finding from phases 1-2, write the smallest script that
reproduces it and quote the observed numbers (e.g. "E[S_T]/forward = 0.896
vs predicted 0.896 from the missing compensator"). Scratch scripts only —
never modify the code under review during the review.

### Phase 4 — External benchmark

Per `references/benchmark-protocol.md`:
1. **Null baseline first**: Black-Scholes at trailing realized vol. Any
   model that does not beat this adds nothing (in the origin review the null
   baseline was *closest* to market — 0.96 vs 0.90/0.89 for the
   sophisticated models).
2. **Market comparison** with the strict protocol: history strictly prior to
   each pricing date, calendar→trading-day conversion via the actual session
   calendar, raw data columns only, one calibration per date, and REPORT THE
   CALIBRATION-FALLBACK SHARE (a benchmark whose calibration silently fell
   back to defaults on 80% of dates is mislabeled as "calibrated").
3. Read results as ratio + residuals, per core rule 4.

### Phase 5 — Verdict

Per model, in this order: **What it does** (math as implemented, 2-3
sentences) / **Pros** (genuine strengths) / **Cons** (structural, method
level) / **Errors** (each tagged, with file:line and observed numbers) /
**Verdict** (trustable for what; what it would take to make it usable).
Mark which findings are new vs previously documented. Findings that don't
survive your own reading or runs get dropped, not hedged.

## Outputs

A review document (e.g. `QUANT_CRITIQUE.md` style) with the phase-5
structure per model, a cross-cutting section (shared conventions,
duplicated code, silent defaults), and a ranked what-to-fix-first list where
rank = information gained per unit effort.

## In the research repo specifically

Reuse the existing harness instead of rebuilding: `option_models/`
fit/price API, `validate_pricing.py` (invariants + market comparison),
`market_sample.py` (shared sample definition), `benchmark_merton.py`
(per-date-calibration benchmark pattern). Data rules: only
`vortex/nifty_full.vortex` and `vortex/monthly_nifty.vortex` raw columns are
trusted; daily data from the local Yahoo CSVs (`download_yahoo_daily.py`).
