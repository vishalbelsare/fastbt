# Failure-Mode Catalog

Each entry: **symptom → how to detect → real observed example** (from the
Aug 2026 four-model review; magnitudes are what was actually measured).
Walk every entry against every pricing-relevant file during Phase 1.

---

## 1. Measure & conventions

**1.1 Real-world payoff sold as a price.** No risk-neutral drift, no
discounting — output is E_P[payoff], a lower bound on fair value, not a
price. *Detect:* look for drift adjustment and a discount factor; if absent,
the model output must never be compared to market as a mispricing signal.
*Example:* empirical model priced 10% below 3,760 traded options — entirely
the variance risk premium, not an error.

**1.2 MC drift missing the compensator.** Risk-neutral simulation of a
jump/dividend process needs the drift compensator (−λk for Merton jumps) or
E[S_T] ≠ S0·e^{rT}. *Detect:* simulate, compare E[S_T] to the forward; the
gap is exp(λkT)−1. *Example:* MC underpriced calls systematically;
E[S_T]/forward = 0.896 at λ=5, exactly the predicted compensator gap.

**1.3 Mixed discounting.** An adjusted rate used in d1/d2 but the raw rate
in the discount factor (or vice versa) — internally inconsistent even as an
approximation. *Detect:* trace every occurrence of r through one pricing
call. *Example:* a "closed form" used r−λk in d1/d2 but e^{−rT} discounting.

**1.4 Day-count mixing.** 252 trading days in one place, 365 calendar in
another; λ annualized on 252 but T passed as 30/365. *Detect:* grep for
252/365/annualize; table every conversion. *Example:* ~4% error in jump
intensity terms; a whole silo used T·365 against a 252-convention repo.

**1.5 Calendar dte fed to a trading-day engine.** The engine's horizon is
return periods (trading days); callers pass calendar days. *Detect:* check
what every call site passes, not what the engine expects. *Example:* +19.2%
ATM value at weekly tenor (7 calendar vs 5 trading), +7.2% at monthly.

**1.6 Percent vs fraction return units.** Two implementations, one uses
r*100. *Detect:* max|return| sanity check (fractional daily returns < 0.5).
*Example:* three coexisting conventions in one repo; unified, with an
explicit validation check.

**1.7 Per-lot vs per-contract.** Variables named `*_per_lot` holding
per-contract values; the same trade reported 75x apart by two scripts.
*Detect:* multiply through one example by hand; check the lot-size constant
is applied exactly once.

---

## 2. Statistical

**2.1 Overlapping windows.** `close/close.shift(h)` gives N observations of
which ~N/h are independent; every naive error bar is √h too tight.
*Detect:* any multi-period return built by shifting. *Example:* 316 raw
7-day observations, ~45 independent.

**2.2 Lookahead.** Scaler/cluster/parameters fitted on the full sample and
then used to label/score that same sample; backward-fill on time series;
labels aligned by front-truncation. *Detect:* for every fitted object, ask
"what dates went into the fit vs what dates it scores". *Example:* KMeans
regime labels at time t informed by data from t+1…T; a `.bfill()` in a
feature pipeline.

**2.3 Circular validation.** The model is conditioned on the very number it
then judges (posterior σ fit to the market price, then "market vs fair
value" verdicts). *Detect:* feed different market prices; if fair value
tracks the input, the verdict is vacuous. *Example:* market 600/800/1000 →
"fair value" 741/853/966.

**2.4 Truncated-sample moments.** Jump size σ estimated from only the
|r|>2.5σ tail — biased low; tail means average toward zero. *Detect:* any
moment computed on a thresholded subsample.

**2.5 Contaminated thresholds.** The 2.5σ jump threshold computed from a
std that includes the jumps — under-detects; and fixed k·σ thresholds flag
pure noise in long samples (~12 false "jumps" per 5,000 normal obs).
*Detect:* threshold derivation vs what it's applied to.

**2.6 ESS misread.** Kish effective sample size measures weight
concentration, not serial dependence — it does NOT correct for overlap.
*Detect:* any significance claim citing ESS on overlapping data.

**2.7 Horizon truncation at the data boundary.** Trading-day horizons
computed by counting sessions in a reference series undercount whenever the
expiry lies beyond the series' last date — the tail of the sample is priced
at too-short tenors and screens "cheap". *Detect:* spot-check a quote near
the data end; assert expiry ≤ last session before counting. *Example:* a
quote 3 trading days from expiry priced at horizon 1 (model/market 0.57);
1.9% of the benchmark sample affected.

**2.8 Cancelling error pairs.** Two individually wrong pieces that are
jointly consistent (asymmetric MH proposal without Hastings correction +
prior kernel without Jacobian — chain sampled the intended distribution
exactly). *Detect:* verify the pair END TO END numerically before "fixing"
either half; the one-sided fix introduces the bias.

---

## 3. Simulation

**3.1 Multi-event collapse.** `np.sum(f(x[i, step]))` over a SCALAR — n
Poisson events apply as one. Invisible at low intensity, catastrophic at
high. *Detect:* force high λ·dt; compare E[S_T] to compound-Poisson theory.
*Example:* deterministic +10% jumps, λ=20: coded 239 vs correct 819.

**3.2 Greeks from independent simulations.** Bump-and-revalue with fresh
random draws (worse: fewer paths for the bumps) — MC noise dominates the
second difference; gamma is meaningless. *Detect:* look for common random
numbers; for multiplicative models S_T = S0·M, reusing M is exact and free.

**3.3 Per-step simulation of European payoffs.** Sum of iid per-step log
increments ≡ one terminal draw; 252 steps is ~250x wasted RNG with zero
distributional difference. *Detect:* is anything path-dependent? If not,
one step.

**3.4 "Closed form" that isn't.** A function named closed_form computing a
different (simpler) formula than the model's actual solution. *Detect:*
check against the literature formula AND against the model's own MC; the
two internal implementations disagreeing is itself the bug signal.
*Example:* "Merton closed form" = drift-tweaked single BS, no Poisson
series — and its printed "Jump Premium" was actually the MC/CF measure
disagreement.

---

## 4. Data & plumbing

**4.1 Degenerate default data.** A committed toy series (e.g. +50/session
ramp, every return positive) as the silent default — every call prices 100%
ITM. *Detect:* run the pricer with defaults, look at P(ITM); probe with the
ramp deliberately (it's also a unit test: calls MUST be 100% ITM on it).

**4.2 cwd-relative paths.** `'../data.csv'` / bare filenames — behavior
depends on invocation directory; a same-named file elsewhere is silently
used. *Detect:* run entry points from a different cwd. *Fix pattern:*
anchor to `os.path.dirname(__file__)`.

**4.3 Silent synthetic fallback.** `except: <generate random data>` — a
broken load is indistinguishable from a real run. *Detect:* grep bare
except; break the data path on purpose and see if the run "succeeds".

**4.4 Silent calibration fallback.** Insufficient data → hardcoded defaults,
but `is_fitted=True` and no warning; "calibrated" output is fiction.
*Detect:* check every calibration branch sets a flag the caller can see;
benchmarks must report the fallback share. *Example:* a benchmark labeled
"calibrated per date" ran on fallback defaults for 80% of rows.

**4.5 Identity-keyed caches.** Fit-state keyed on `id(data)` — in-place
mutation keeps stale calibration; GC id-reuse in walk-forward loops silently
prices every window with the first window's parameters. *Detect:* mutate
the frame and re-call; key on content (length, index endpoints, value hash).

**4.6 Duplicated implementations.** The same math in 2+ places "kept in
sync" by comment — they drift, and their mutual agreement is then presented
as validation (it's a wiring test of one implementation). *Detect:* diff
the copies; extract the shared function.

**4.7 Hardcoded values that don't follow arguments.** Price-target tables,
strike-specific labels, recommendation strings pinned to one example while
the function takes parameters. *Detect:* call with different arguments and
read the output critically.

**4.8 Global warning suppression.** `warnings.filterwarnings('ignore')` at
module import — hides the model's own deprecation/copy warnings, mutates
global state for every importer. *Detect:* grep; remove and rerun.

---

## 5. Evaluation traps

**5.1 Verdicts from a lower-bound model.** "Overpriced/underpriced" strings
comparing a no-risk-premium expected payoff to market prices — systematically
anti-long/pro-short, i.e. it always recommends selling exactly the premium
whose tail-risk compensation the model cannot see. *Detect:* what measure
is the fair value in? Re-base verdicts on deviation from the model's known
baseline ratio, or delete them.

**5.2 Zeros printed as results.** A key mismatch (weights dict vs branch
names) making every portfolio return exactly 0 — reported as Sharpe 0.00.
*Detect:* any suspiciously round metric; assert non-degenerate
intermediates in backtests.

**5.3 Validation against synthetic returns.** Strategy weights "validated"
on seeded noise with one strategy handed +1%/day alpha — any weighting
favoring it wins by construction. *Detect:* trace what the returns being
weighted actually are.

**5.4 Hardcoded cross-references between reports.** "(other model on the
same sample: 0.90)" printed as a string — desynchronizes silently when
either side's filters change. *Detect:* shared sample definitions must be
shared CODE, and comparative numbers labeled with their run date.

**5.5 Library agreement as model validation.** "QuantLib agrees" proves the
formula is computed correctly, not that the model is right for the market.
Convention mismatches (day count, calendar, settlement) generate false
alarms; agreement generates false confidence. *Detect/frame:* library
cross-checks live in Phase 2 (implementation), never Phase 4 (model).
