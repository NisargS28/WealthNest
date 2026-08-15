# Phase 09 — Automated Portfolio Refresh

Status: **PLANNED**

## Objective
Establish scheduled background tasks to refresh Net Asset Value (NAV) details and recalculate portfolio valuations daily.

## Why this phase exists
Investments change value daily. Users need to see up-to-date performance summaries when they open the dashboard, rather than manual, on-demand valuations.

## Scope
- Scheduled cron/worker tasks.
- Batch fetching NAV details for active funds.
- Valuation recalculation pipelines.
- API rate-limiting compliance.
- Stale data detection and last-updated timestamps.

## Tasks
- [ ] Implement celery or standard cron worker process structure.
- [ ] Design bulk API fetching routines for mapped schemes.
- [ ] Build valuation update triggers.
- [ ] Add visual "Last Updated" timestamp indicator on the dashboard.

## Input
List of active scheme codes and their current cache state.

## Output
Updated database valuation logs showing current holdings net values.

## Validation
Audit cron run results to confirm zero failed updates or uncaught rate-limiting exceptions.
