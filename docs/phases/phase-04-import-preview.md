# Phase 04: Import Preview & Portfolio Persistence

## Objectives
- Introduce a SQLite database for permanent persistence of family members, portfolios, folios, and transactions.
- Implement the `web-engine` backend orchestrator using FastAPI to run the `cas-parser` → `portfolio-engine` → `nav-engine` pipeline.
- Implement a Next.js (React + TypeScript) frontend to provide a beautiful, sleek interface for uploading CAS PDFs and visualizing portfolios.
- Implement an Import Preview with warnings, validations, and deduplication logic before committing transactions to the database.

## Architecture

**Stack**:
- **Frontend**: Next.js 14, React, custom Vanilla CSS (Dark Mode/Glassmorphism).
- **Backend**: FastAPI, SQLAlchemy, SQLite, Pydantic.
- **Engines**: Uses Python `v0.1`, `v0.2`, `v0.3` libraries programmatically.

### Data Model
- `family_members`: Pre-seeded family members.
- `portfolios`: Represents a portfolio belonging to a member.
- `import_sessions`: State machine for CAS processing (`UPLOADED` → `PREVIEW_READY` → `CONFIRMED`).
- `folios` & `transactions`: Permanent records stored post-confirmation.
- `valuations` & `nav_records`: Refreshable snapshots of market value.

### Workflows

1. **Upload**: User selects a member and uploads a CAS PDF (`/import`).
2. **Processing**: Backend runs all three engines in a background task.
3. **Preview**: Frontend polls until `PREVIEW_READY` and displays the Import Preview (`/import/[id]/preview`).
4. **Validation**: Deduplication checks and parsing warnings are displayed. User must acknowledge duplicate risks.
5. **Confirmation**: Confirmed imports write immutable transactions to SQLite.
6. **Viewing**: Users can view the Member Portfolio (`/portfolio/[id]`) and the aggregated Family View (`/family`).

## Completion Status
- ✅ Backend REST API implemented (13 endpoints)
- ✅ SQLite schema created using SQLAlchemy ORM
- ✅ Deduplication fingerprint logic `(folio, date, type, amount, units, desc)`
- ✅ Frontend routing and UI components implemented
- ✅ Premium dark-mode aesthetics with Google Fonts (Outfit) and glassmorphism.
