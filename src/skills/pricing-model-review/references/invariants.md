# The Invariant Battery

Checks that must hold for any correct pricing model, what each one proves,
and the tolerance to demand. Any failure is a confirmed bug — no judgment
call needed. Runnable template: `scripts/invariant_checks.py` (the model
needs only a `price_fn(spot, strike, days, kind) -> {'fair_value',
'probability_itm'}` adapter).

## Structural invariants (any model, any measure)

| Check | Assert | Proves | Tolerance |
|---|---|---|---|
| Put-call parity | C − P = E[S] − K·DF | Both legs price off one consistent terminal distribution. For common-scenario engines (both legs average the same weighted scenario set) this holds EXACTLY — demand 1e-10, not "close". For risk-neutral models, C − P = S − K·e^{−rT}. | 1e-10 (analytic/scenario), 3 MC s.e. (simulation) |
| Call ↓ in strike, Put ↑ in strike | monotone across a strike grid | No sign errors, no unit errors in the payoff | exact (≤/≥) |
| ATM value ↑ in tenor | monotone across tenors | Time value exists; horizon units are consistent | exact for ATM European w/o dividends |
| Probabilities | 0 ≤ P(ITM) ≤ 1; P(call ITM)+P(put ITM) ≤ 1 (=1 iff P(S=K)=0) | Probability code isn't mislabeled (ITM vs OTM inversions happen) | exact |
| Non-negative values | all fair values ≥ 0 | payoff floors applied | exact |
| Intrinsic floor at T→0 | price(days→min) → intrinsic | expiry limit handled | model-specific small tolerance |

## Measure invariants (risk-neutral models only)

| Check | Assert | Proves | Tolerance |
|---|---|---|---|
| Martingale | E[S_T] = S0·e^{rT} in the simulation | The drift (incl. any jump/dividend compensator) is right. THE canonical MC bug. Quote the MC standard error with the result. | 3 s.e. at large n_paths; run at high jump intensity too — compensator bugs scale with λ |
| Parameter limits | λ→0 ⇒ plain BS; σ_jump→0 & μ_jump→0 ⇒ BS; vol→0 ⇒ discounted intrinsic/forward | Each model component switches off cleanly; catches series-weight and compensator errors | 1e-9 vs analytic BS |
| MC vs closed form | same params, agree within MC error | The two internal implementations share one measure (their disagreement WAS the bug in the origin repo, mislabeled "jump premium") | 3 s.e., several strikes and both types |

## Data-facing probes

| Check | Assert | Proves |
|---|---|---|
| Degenerate ramp probe | On a monotone +X/session series: every call P(ITM)=1, every put value 0 | Return construction and payoff signs are wired right — if this doesn't hold, units/horizons are broken. (Doubles as: never let such a file be the default dataset.) |
| Known-vol synthetic | Price on a simulated series with known σ; compare ATM value to BS(σ) scaled for measure | End-to-end unit round-trip: data → returns → distribution → price |
| Unfitted guard | price() before fit() raises | No silent default-parameter pricing |
| Refit-on-change | mutate the data (or supply an equal-length different window), re-call the one-shot API | The fit cache keys on content, not identity |

## What agreement does NOT prove

Cross-entry-point agreement (four wrappers returning bit-identical values)
is a WIRING test: it proves the wrappers share one engine, and nothing about
whether that engine is correct. Say so explicitly in any report. The same
applies to external libraries: matching QuantLib to 1e-10 validates the
implementation of a formula, not the model (see gotchas §5.5).

## Reference implementation

`validate_pricing.py` in the research repo implements this battery for the
empirical model (Part A), the wiring test (Part B, labeled as such), and the
market comparison (Part C) — use it as the pattern.
