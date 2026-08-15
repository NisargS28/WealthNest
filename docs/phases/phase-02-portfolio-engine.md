# Phase 02 — Portfolio Reconstruction Engine

Status: **IN PROGRESS**

## Objective
Develop the core portfolio engine that takes normalized transaction history and reconstructs holding states, computing cumulative invested amounts, outstanding unit balances, and reconciling closing balances.

## Why this phase exists
A list of transactions is only raw historical data. To evaluate net worth, track performance, or analyze allocation, we need a deterministic engine that acts as a state machine processing cash flows, purchases, redemptions, switches, and stamp duty chronologically.

## Scope
- Convert transaction sequences into active `Holding` records.
- Track total invested cost basis.
- Handle buy, sell, switch, and reversal events chronologically.
- Reconcile closing units against the stated CAS unit balances.
- Ensure folio-level holdings remain separate internally.

## Tasks
- [ ] Implement holding model structure mapping `amc`, `scheme_name`, `units`, and `invested_value`.
- [ ] Build the chronological state processor applying transaction logic.
- [ ] Incorporate REVERSAL logic to correctly subtract units and cost basis.
- [ ] Integrate stamp duty treatment (increases invested cost but doesn't add extra units).
- [ ] Add folio-level balance reconciliation checks.
- [ ] Write engine unit and integration tests.

## Technical Design
The Engine will process a list of transactions chronologically:
- **PURCHASE / SWITCH_IN**: `units_held += tx.units`, `invested_value += tx.amount`.
- **REDEMPTION / SWITCH_OUT**: `ratio = tx.units / units_held`, `invested_value -= (ratio * invested_value)`, `units_held -= tx.units`. (FIFO/Weighted Cost basis tracking).
- **REVERSAL**: `units_held += tx.units`, `invested_value += tx.amount` (since both are negative, this correctly subtracts them).
- **STAMP_DUTY**: `invested_value += tx.amount` (units remain unchanged).

## Input
A normalized `Statement` JSON (from Phase 01).

## Output
A structured portfolio holdings representation detailing active funds, folios, units, and cumulative cost.

## Validation
Calculated closing units must match the CAS-reported balance inside a strict tolerance (`0.001` units).

## Tests
Integration tests verifying holdings calculations across various mock transaction scenarios (e.g. purchases followed by switches, stamp duties, and mandate failures resulting in reversals).

## Known Limitations
Cost basis tracking might require user configuration if historical acquisition details are incomplete.

## Decisions
- Keep folios separate internally even when the same scheme appears in multiple folios.
- Reversals must be processed explicitly rather than mutating past records.
```
