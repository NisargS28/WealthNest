# Phase 03 — NAV/Data Integration

Status: **PLANNED**

## Objective
Integrate external market data providers to fetch latest and historical Net Asset Value (NAV) details, mapping them to scheme codes and ISINs safely.

## Why this phase exists
To calculate current valuation, profit/loss, and portfolio analytics (XIRR/CAGR), we must merge the user's transaction cost basis with the latest active market valuations.

## Scope
- Integrate external NAV feeds (starting with planned source `MFapi.in`).
- Implement scheme code mapping to ISIN/AMC nomenclature.
- Fetch and cache NAV details locally to prevent rate limiting.
- Gracefully handle API outages and missing data feeds.

## Tasks
- [ ] Design the market data API client layer.
- [ ] Build mapping registry linking CAS scheme strings/ISINs to MFapi scheme codes.
- [ ] Implement caching mechanism for daily NAV.
- [ ] Add fallback mechanism (e.g., utilize last reported CAS NAV if API is offline).
- [ ] Write data fetcher unit tests.

## Technical Design
The NAV module will act as a separate, isolated data provider layer. The transaction database is the immutable truth; NAV data is fetched on demand and cached. 
```
Transaction Data (Truth) ──┐
                           ├─► Valuation Calculator ─► Current Portfolio State
External NAV Cache ────────┘
```

## Input
ISIN or scheme code from parsed transactions.

## Output
Live or historical NAV (Decimal) for valuation calculation.

## Validation
Confirm fetched valuations reconcile logically against the portfolio summary cost/market values in the statement metadata.

## Known Limitations
`MFapi.in` is a free, public service in India and might suffer from rate limiting or downtime. The design must accommodate alternative providers (e.g., AMFI raw text scrapers or commercial feeds) without rewriting core logic.

## Decisions
- Treat external market data feeds as non-authoritative overlays; never write API values directly into historical transaction tables.
