# Phase 10 — Advanced Analytics

Status: **FUTURE**

## Objective
Implement advanced investment analysis layers such as benchmark comparisons, risk metrics, goal tracking, and tax-oriented harvesting calculations.

## Why this phase exists
Once basic holdings and valuations are tracked, users need actionable, advanced tools to evaluate risk, optimize taxes (e.g. tracking short-term vs long-term capital gains), and measure progress against financial milestones.

## Scope
- Index benchmark tracking (e.g., comparing returns against Nifty 50 or custom blends).
- Portfolio risk calculations (Volatility, Drawdown, Sharpe ratio).
- Asset overlap checker (analyzing concentration across similar underlying stock holdings).
- Tax-harvesting alerts (calculating LTCG tax-free exemption limits).
- Goal-based milestone tracking.

## Tasks
- [ ] Design benchmark comparison modules.
- [ ] Build capital gains tax calculation engines based on local laws.
- [ ] Implement portfolio risk analytics models.
- [ ] Formulate asset overlap calculation engines.

## Technical Design
Calculations will be encapsulated inside optional modules to avoid bloating the core portfolio engine.
- **Tax Harvesting**: Evaluates purchased units holding periods (e.g. >365 days for Equity LTCG) and prompts selling/buying recommendations to maximize annual exemption limits.

## Validation
Tax calculations must match statutory financial calculation standards exactly.

## Known Limitations
All recommendations generated are purely mathematical/educational simulations and **do not constitute professional financial advice**.
