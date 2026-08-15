# Phase 06 — Portfolio Analytics

Status: **PLANNED**

## Objective
Implement financial math calculations to compute absolute returns, annualized growth rates (CAGR), and internal rate of return (XIRR) across individual and consolidated family portfolios.

## Why this phase exists
Evaluating the true performance of a portfolio requires standard investment metrics. In particular, because mutual funds involve recurring cash flows (SIPs, switches, redemptions), simple percentage gains are insufficient; we must calculate XIRR.

## Scope
- Absolute Profit/Loss (Current Value - Invested Value).
- Internal Rate of Return (XIRR) based on transaction cash flows.
- Compounded Annual Growth Rate (CAGR) for lump-sum holdings.
- Asset, Category, AMC, and concentration allocation metrics.

## Tasks
- [ ] Implement mathematical formula for XIRR using cash-flow sequences (e.g. Newton-Raphson method or standard finance libraries).
- [ ] Build CAGR utility functions.
- [ ] Add portfolio concentration calculators (e.g., top holdings allocation percentages).
- [ ] Test calculations against known financial benchmark datasets.

## Technical Design
All financial math will be implemented in a dedicated `analytics_engine.py` using Python's standard `math` and decimal-based algorithms to guarantee floating-point correctness.
- **XIRR**: Maps transactions as negative cash flows (purchases) and positive cash flows (redemptions, current valuation as terminal value) aligned with their exact dates.

## Input
Reconstructed transaction ledger and live NAV dataset.

## Output
An analytics summary object displaying XIRR, CAGR, absolute gain, and concentration metrics.

## Validation
XIRR calculations must reconcile exactly against MS Excel/Google Sheets XIRR functions within a 0.0001% tolerance.

## Known Limitations
Calculating XIRR on portfolios with complex histories containing dozens of micro-transactions (e.g. daily STP or minor dividend reinvestments) can be computationally heavy and requires optimized numerical solver loops.

## Decisions
- Clearly distinguish XIRR (internal rate of return) from simple percentage gains in UI screens.
