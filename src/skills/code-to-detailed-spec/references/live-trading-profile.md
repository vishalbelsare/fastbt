# Live Trading Profile

Use this profile when the source implementation is a trading system or when the user asks to convert backtest code into live trading behavior.

Add or verify these requirements in the final spec:

- Submitted orders do not change strategy state until fills are confirmed.
- Entry and exit prices come from fills, not pre-submit quotes.
- Partial fills, rejected orders, cancellations, and timeouts require explicit handling.
- Missing option or market quotes block only quote-dependent decisions.
- Known open positions must still be flattened at mandatory exit times.
- Stale market data must not be treated as fresh.
- Re-entry counters increment only after confirmed closes.
- Lifecycle state must survive restarts or be reconstructable from persisted events.
- Audit events must include selections, order ids, fill ids, state transitions, skipped decisions, and forced exits.

Do not blindly preserve backtest-only mechanics if they are unsafe live. Preserve trading intent, then define the live-safe contract.
