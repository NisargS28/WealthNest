# Phase 05 — Family Portfolio Model

Status: **PLANNED**

## Objective
Establish the relational models and aggregation logic required to group individual portfolios under a unified family structure while preserving distinct asset ownership.

## Why this phase exists
A centralized family view requires mapping independent portfolios to individual family members, then aggregating them into a consolidated family-level model.

## Scope
- Create family profile containers.
- Add family members (Mother, Father, Brother, Self).
- Assign parsed folios to specific family members.
- Maintain separate holding structures per member.
- Combine member holdings to present a unified household allocation.

## Tasks
- [ ] Create database schemas for `Family` and `FamilyMember`.
- [ ] Establish relationships linking `Folio` to `FamilyMember`.
- [ ] Build aggregation algorithms combining holdings by asset class, AMC, and fund type.
- [ ] Implement access controls preventing member visibility mismatch.

## Technical Design
```
       Family (Aggregation Layer)
        ├── Father (Member)
        │    ├── Folio A (SBI)
        │    └── Folio B (HDFC)
        └── Mother (Member)
             └── Folio C (ICICI)
```

## Input
Confirmed holdings across multiple family member portfolios.

## Output
An aggregated holdings state reflecting combined family-level allocations.

## Validation
Aggregated totals must exactly equal the sum of constituent member portfolios.
