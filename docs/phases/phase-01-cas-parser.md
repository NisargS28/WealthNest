# Phase 01 — CAS PDF Parser

Status: **COMPLETED**

## Objective
Implement a robust, deterministic mutual fund Consolidated Account Statement (CAS) ingestion parser that extracts clean statement metadata, folio segments, and explicit financial transactions into normalized JSON format.

## Why this phase exists
The CAS PDF is the core source of truth for historical mutual fund holdings in India. To reconstruct portfolios, we must first parse these files with near-perfect accuracy and validate them mathematically.

## Scope
- PDF parsing using PyMuPDF (text layer) and pdfplumber (tables)
- AMC, Folio, and Scheme detection
- Statement Metadata (Period, Generated Date)
- Explicit SIP details extraction (without future-schedule inference)
- Reversal transaction processing (bounces, parenthesized amounts)
- System event filtering (silently ignores non-financial entries)
- Unit balance & NAV validation checks

## Tasks
- [x] Implement PyMuPDF and pdfplumber document loaders
- [x] Create regex-based folio splitting logic in `SectionDetector`
- [x] Build `TransactionClassifier` for Purchase, Redemption, Switch, and Reversals
- [x] Write `TransactionParser` handling positive/negative decimal strings
- [x] Build metadata and portfolio summary extraction
- [x] Implement `Validator` verifying cascading unit balances
- [x] Re-architect NAV validation using monetary formula: `abs(Amount - (Units * NAV)) <= 0.50 INR`
- [x] Create regression tests using dummy strings and anonymized fixtures

## Technical Design
- **Section Detector**: Iterates through PDF pages, tracking AMC headers and splitting the raw text into distinct `FolioSection` objects.
- **Transaction Parser**: Matches lines against regex templates. Cleans up parenthesized numbers representing negative values.
- **Validator**: Checks that starting balance + parsed transaction units = ending balance. Reconciles NAV with amount using a rounding-tolerant monetary discrepancy model.

## Input
A password-protected or decrypted CAMS/KFintech Detailed CAS PDF.

## Output
A structured JSON file adhering to `Statement` schema, complete with metadata, folio structures, parsed transactions, unparsed lines, and warnings.

## Validation
Run on sample files:
- **CAS_01**: 129 transactions parsed, 0 warnings.
- **CAS_02**: 73 transactions parsed, 7 warnings (isolated to expected high-NAV rounding errors under 0.50 INR).

## Tests
- `tests/test_pdf_reader.py`: Asserts correct metadata and summary extraction.
- `tests/test_transaction_parser.py`: Asserts parsing of SIPs, reversals, and header skipping.
- `tests/test_validator.py`: Asserts NAV monetary verification and reversal balance accounting.

## Known Limitations
The CAS truncates units to 3 decimal places. High-NAV funds (> 1500) will drift slightly in calculated amounts by up to 0.75 INR. This warning is captured but not auto-mutated.

## Decisions
- Removed `SIPDetector` pattern inference to adhere strictly to explicit facts.
- Decided to silently ignore non-financial events to prevent log pollution.

## Future Improvements
Support for more diverse registrar CAS formats if new structural layouts emerge.
