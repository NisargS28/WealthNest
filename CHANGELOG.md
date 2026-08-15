# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-08-15
### Added
- **NAV & Market Data Integration**: `nav-engine/` module added to integrate with MFapi.in.
- **Scheme Mapping**: Advanced scheme matching prioritizing ISIN > Exact Name > Name Search > Fuzzy Matching.
- **Valuation Engine**: Computes current market values using precise Decimal arithmetic.
- **NAV Caching**: Prevents redundant API requests per scheme per day, preserving API boundaries.
- **Testing**: Added unit, integration, and live provider tests for the valuation engine.

### Fixed
- **ISIN Extraction**: Updated CAS Parser regex (`fund_parser.py`) to correctly extract ISINs when placed on a separate newline (fixing Aditya Birla ISIN miss).

## [0.2.0] — 2026-08-15
### Added
- **Portfolio Reconstruction Engine**: Introduced a deterministic engine completely independent from the CAS parser.
- **Folio Holdings**: Computes and reconciles the closing unit balance for every folio using strict Decimal arithmetic.
- **Cash Flow Semantics**: Accurately tracks separate totals for `gross_purchases`, `gross_redemptions`, `gross_reversals`, `stamp_duty`, and computes a `net_cash_flow`. Reversals naturally subtract from running balances as signed by the parser.
- **Scheme Aggregation**: Groups folios matching identical AMC and scheme names, aggregating their total units while preserving distinct folio structures underneath.
- **Reconciliation Engine**: Validates unit balances against the CAS-stated balances with a rigid `0.005` tolerance, producing explicit `PASS`/`FAIL` markers.
- **Comprehensive Testing**: Created 13+ unit and integration tests verifying purchase, redemption, switch, and stamp duty semantics, achieving 100% PASS on all folios from `CAS_01` and `CAS_02`.

---

## [0.1.0] — 2026-08-15
### Added
- **Core Ingestion PDF Engine**: Implemented `PdfReader` leveraging PyMuPDF for document parsing and metadata extraction, combined with `pdfplumber` for robust transaction table parsing.
- **Statement Metadata Extraction**: Parser extracts `period_start`, `period_end`, and `generated_date` from the overall statement dates at the top of the CAS.
- **Folio Segmentation**: Added `SectionDetector` to parse individual folios, registrar details (CAMS/KFintech), scheme descriptions, and scheme codes separately.
- **Strict Fact Extraction**: Re-engineered parser to only extract explicit SIP data present in the text (e.g. `Instalment 28/299`). Removed active future SIP schedule inference from the parser.
- **System Event Silencing**: Added logic to automatically detect and discard non-financial system events (bank mandate approvals, KYC updates, etc.) silently, preventing pollution in `unparsed_transactions`.
- **SIP Reversal Processing**: Added `REVERSAL` transaction type. Implemented parser support for accounting parentheses representation, converting `(999.95)` to `Decimal("-999.95")`.
- **Validation Suite**: Implemented cascading unit balance checks and NAV-to-Amount reconciliation.
- **Reconciled Rounding Errors**: Shifted validation to evaluated monetary variance equation: `abs(Amount - (Units * NAV)) <= 0.50 INR`. This successfully reduced validation warnings in CAS_02 from 67 down to 7 (with remaining warnings isolated to precision loss from high-NAV 3-decimal unit roundings).
- **Regression Suite**: Created comprehensive test suite for pdf metadata, transaction parsing, and unit validation.
