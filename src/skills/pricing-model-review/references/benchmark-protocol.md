# Market Benchmark Protocol

How to compare a pricing model against real traded prices so the result
means something. Generalized from the "Part C" methodology
(`validate_pricing.py` / `market_sample.py` in the research repo — reuse
those there; replicate this protocol elsewhere).

## 1. The null baseline comes first

Before benchmarking the model, benchmark **Black-Scholes at trailing
realized volatility** (e.g. 126-session window) on the identical sample.
This is the zero-sophistication reference: any model that does not beat it
adds nothing over "recent vol + lognormal". Humbling origin result: the
null baseline was CLOSEST to market (0.96 model/market) — ahead of both the
empirical distribution model (0.90) and calibrated Merton (0.89).

## 2. Sample construction

- **Quote**: one end-of-day quote per (date, expiry, strike, type) — last
  traded bar of the session. Caveat to state in the report: on illiquid
  strikes the last trade can be stale; volume>0 and price>0 filters are the
  floor, a bid/ask-aware or VWAP quote is the upgrade.
- **Raw data only**: filter and price off raw columns (traded price, volume,
  strike, expiry, underlying). Derived columns (IV, Greeks, exclusion
  flags) are not trusted inputs — if one seems necessary, flag it to the
  owner first.
- **Moneyness band**: near-the-money (e.g. ±500 pts) unless wings are the
  question; report bucket counts so thin buckets (N<50) aren't over-read.
- **Shared definition**: if two scripts claim "the same sample", they must
  import the same sample-construction code. Copy-paste + comment is how
  samples silently diverge.

## 3. No lookahead — the non-negotiables

- History for fitting/pricing is **strictly prior** to each quote date
  (`data.iloc[:pos]`, exclusive).
- **One calibration per date**, on that prior history only. Never fit once
  on the full period.
- Horizon = **trading days** via the actual session calendar (sessions
  strictly after trade date, up to and including expiry). Vendor `dte`
  columns are calendar days — coarse filter only, never the pricing horizon.
- **Report the calibration-fallback share.** If the calibration silently
  degrades to defaults on short histories, the benchmark must say what
  fraction of rows that affected ("calibrated per date" at 80% fallback is
  mislabeled).

## 4. Reading the results

- **Report**: N / mean market / mean model / median model-market ratio /
  median abs error, for ALL, calls, puts, and moneyness buckets.
- **Level, not correlation**: all sane models correlate ~0.95 with market
  cross-sectionally because moneyness and tenor dominate — r ≈ 0.95 is the
  entry fee, not evidence. The evidence is the RATIO (which vol level the
  model effectively runs) and the RESIDUALS (does deviation from the
  model's own baseline ratio predict anything?).
- **Ratio ≠ mispricing** for a real-world-measure model: its expected gap
  IS the risk premium. State each model's measure next to its ratio.
- Tenor-dependence: a ratio measured at one tenor (e.g. dte 5-7) does not
  extrapolate — the variance risk premium is term-structure dependent.
  Say which tenors the number covers.
- Comparative numbers from other runs must carry their run date; never
  hardcode a "same sample" cross-reference string that can silently
  desynchronize.

## 5. Library cross-checks (scoped)

QuantLib (or any reference library) belongs in the *implementation* checks:
match your BS/analytic engines to it at ~1e-10 under explicitly matched
conventions (day count, calendar, settlement, compounding) once, keep the
check in CI, and expect most "discrepancies" to be convention mismatches.
It has no standing in the market benchmark: two engines agreeing on the
same formula says nothing about whether the formula fits the market.
