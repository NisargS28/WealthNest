# Phase 04 — Import Preview & User Confirmation

Status: **PLANNED**

## Objective
Design the user interface flow for uploading a CAS PDF, presenting a high-level import preview, and prompting for manual adjustments or confirmations before committing data.

## Why this phase exists
PDF extraction is subject to text positioning quirks and rounding limits. Allowing the user to preview detected folios, transactions, and holdings *before* saving them ensures data integrity.

## Scope
- Upload CAS workflow.
- Render parsed metadata, detected members, and funds.
- Flag validation warnings (e.g. NAV mismatches) explicitly.
- Allow user confirmation of ambiguous fields (e.g. confirming whether an un-labelled transaction is an SIP or lump-sum).
- Commit confirmed data to database storage.

## Tasks
- [ ] Design mock screens for ingestion preview.
- [ ] Build API endpoints delivering parser results to the frontend.
- [ ] Create UI component displaying transaction tallies (purchases, reversals, stamp duty, others).
- [ ] Implement confirmation forms for folio ownership and manual inputs.
- [ ] Connect confirmation workflow to database commit script.

## Input
A successful parse payload from `cas-parser`.

## Output
Confirmed, structured entries persisted in database tables.

## Validation
User must explicitly approve folios containing validation warnings before final submission.
