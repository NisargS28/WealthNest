Build a production-quality Python PDF parser for a **CAMS + KFintech Consolidated Account Statement (Detailed CAS)** used for my mutual-fund family portfolio application.

## Objective

The application will accept a password-protected or unprotected Detailed CAS PDF.

The parser's first responsibility is:

**Detailed CAS PDF → structured, normalized JSON**

The parser must extract mutual-fund portfolio and transaction information accurately enough that the resulting JSON can later be used by a portfolio calculation engine.

Do NOT build the dashboard, authentication system, MFapi integration, AI layer, or portfolio analytics yet.

Focus ONLY on the PDF ingestion and parsing pipeline.

---

## 1. Expected CAS structure

The Detailed CAS contains sections such as:

### Portfolio Summary

Typical columns:

* Mutual Fund
* Cost Value
* Market Value

### Fund/Folio sections

Each fund/folio may contain:

* Fund/AMC name
* Folio number
* PAN (do NOT store PAN)
* Registrar
* ISIN
* Scheme name
* Plan
* Option
* Nominee information
* Opening Unit Balance

### Transaction table

Typical columns:

* Date
* Transaction
* Amount (INR)
* Units
* Price (INR)
* Unit Balance

Example:

Date | Transaction | Amount | Units | Price | Unit Balance

13-Jun-2018 | Purchase - SIP | 1000.00 | 16.743 | 59.7249 | 16.743

15-Jul-2018 | Purchase - SIP - Instalment 2/67 | 1000.00 | 18.485 | 54.0984 | 35.228

15-Jul-2018 | Stamp Duty | 0.05 | | | 35.228

The transaction table can continue across multiple pages.

---

## 2. Important privacy requirements

The CAS contains sensitive financial information.

The parser MUST NOT store:

* PAN
* Email
* Mobile number
* Address
* Bank account number
* Nominee name/details
* KYC information
* Any unnecessary personal information

The parser should only extract information required for portfolio reconstruction.

The target data should be:

* AMC
* Scheme name
* Folio number
* ISIN
* Registrar
* Transaction date
* Transaction type
* Transaction description
* Amount
* Units
* Price/NAV
* Unit balance

For development/testing, allow folio numbers to be masked or hashed.

Do not log sensitive information to console.

---

## 3. PDF password handling

Support password-protected PDFs.

The parser should NOT permanently store the password.

Provide a CLI option such as:

python parser.py --input cas.pdf --password "PASSWORD"

Also support an interactive password prompt:

python parser.py --input cas.pdf

If the PDF is encrypted and no password is supplied, ask the user for the password.

Do not write the password into logs, output JSON, cache files, or database records.

---

## 4. PDF extraction strategy

First determine whether the PDF contains an actual text layer.

Prefer extraction in this order:

1. PyMuPDF / fitz
2. pdfplumber
3. OCR fallback only when text extraction fails

Do NOT use OCR unnecessarily because the CAS appears to contain machine-readable text.

The parser must preserve:

* page number
* row order
* table order

because transaction chronology is important.

---

## 5. Detect fund sections

The parser must identify when a new mutual-fund/folio section begins.

For each section identify:

```text
AMC
Scheme Name
Folio Number
ISIN
Registrar
Plan
Option
```

Do not assume the fund section occurs only once.

The same scheme may appear under multiple folios.

Example:

```text
Motilal Oswal Mutual Fund
Folio A
Scheme X

Motilal Oswal Mutual Fund
Folio B
Scheme X
```

These must remain separate folios internally.

---

## 6. Parse transaction rows

Create a robust transaction parser.

Every transaction should contain:

```json
{
  "date": "YYYY-MM-DD",
  "transaction_type": "PURCHASE",
  "description": "Purchase - SIP - Instalment 2/67",
  "amount": 1000.00,
  "units": 18.485,
  "nav": 54.0984,
  "unit_balance": 35.228,
  "page_number": 2
}
```

Normalize dates to:

YYYY-MM-DD

Normalize numeric values:

* Remove commas
* Remove currency symbols
* Convert to float/Decimal
* Preserve precision where necessary

Use Decimal rather than binary floating point for financial calculations.

---

## 7. Transaction classification

Create a transaction classification layer.

At minimum support:

### Purchase

Examples:

* Purchase
* Purchase - SIP
* Purchase - SIP - Instalment
* Systematic Investment
* Systematic Investment New Purchase

Normalize to:

PURCHASE

with a subtype such as:

* SIP
* LUMP_SUM
* SYSTEMATIC

### Redemption

Normalize to:

REDEMPTION

### Switch In

Normalize to:

SWITCH_IN

### Switch Out

Normalize to:

SWITCH_OUT

### Dividend / IDCW

Normalize appropriately.

### Dividend Reinvestment

Normalize to:

DIVIDEND_REINVESTMENT

### Stamp Duty

Normalize to:

STAMP_DUTY

### Other charges/adjustments

Normalize to:

OTHER

IMPORTANT:

Do not treat every row containing an amount as an investment transaction.

For example:

```text
Stamp Duty
```

must NOT increase units.

---

## 8. Preserve the original transaction description

Always keep both:

```text
transaction_type
description
```

Example:

```json
{
  "transaction_type": "PURCHASE",
  "subtype": "SIP",
  "description": "Purchase - SIP - Instalment 26/67"
}
```

The original description is important for future debugging.

---

## 9. Unit-balance validation

The parser must perform validation.

For normal purchase transactions:

```text
previous_unit_balance + units ≈ new_unit_balance
```

For redemption/switch-out:

```text
previous_unit_balance - units ≈ new_unit_balance
```

Allow a small tolerance for rounding.

For example:

```text
tolerance = 0.001
```

Do NOT silently modify values to make them match.

Instead generate validation warnings.

Example:

```json
{
  "validation": {
    "unit_balance_match": true,
    "difference": 0.000
  }
}
```

---

## 10. Transaction NAV validation

Where both amount and units exist:

```text
calculated_nav = amount / units
```

Compare it against the extracted `nav`.

Do not overwrite the extracted NAV.

Generate:

```json
{
  "nav_validation": {
    "calculated_nav": 54.0984,
    "reported_nav": 54.0984,
    "difference": 0.0000,
    "match": true
  }
}
```

Use Decimal and an appropriate tolerance.

Remember:

**Price/Unit from the CAS should be treated as the transaction price/NAV for that transaction.**

Do not infer purchase NAV from the calendar date when the CAS already provides transaction price.

---

## 11. SIP detection

The parser should detect possible SIP patterns but should NOT automatically assume future SIPs.

From transaction descriptions such as:

```text
Purchase - SIP - Instalment 15/67
Purchase - SIP - Instalment 16/67
Purchase - SIP - Instalment 17/67
```

extract:

```json
{
  "is_sip": true,
  "sip_installment_number": 17,
  "sip_total_installments": 67
}
```

Also analyze dates to identify possible frequency:

* Monthly
* Quarterly
* Other

But label this as:

```text
detected_sip_pattern
```

not as an active SIP.

The application will later ask the user during Import Preview whether the SIP is still active.

---

## 12. Import Preview data

Generate a separate summary suitable for an Import Preview UI.

Example:

```json
{
  "import_preview": {
    "funds_detected": 4,
    "folios_detected": 5,
    "transactions_detected": 143,
    "purchase_transactions": 100,
    "redemption_transactions": 5,
    "switch_transactions": 3,
    "other_transactions": 35,
    "sip_patterns_detected": 3
  }
}
```

For each detected SIP:

```json
{
  "scheme": "Example Flexi Cap Fund",
  "amount": 1000.00,
  "frequency": "MONTHLY",
  "detected_day": 15,
  "last_installment": 67,
  "status": "REQUIRES_USER_CONFIRMATION"
}
```

Do NOT create future transactions.

---

## 13. Output JSON structure

Use a normalized structure similar to:

```json
{
  "statement": {
    "statement_type": "CAS_DETAILED",
    "period_start": "2017-01-01",
    "period_end": "2026-08-15"
  },

  "folios": [
    {
      "folio_number": "MASKED_OR_HASHED",
      "amc": "Example Mutual Fund",
      "registrar": "CAMS",
      "scheme_name": "Example Flexi Cap Fund",
      "isin": "INE000000000",
      "plan": "Regular",
      "option": "Growth",

      "transactions": [
        {
          "date": "2025-01-15",
          "transaction_type": "PURCHASE",
          "subtype": "SIP",
          "description": "Purchase - SIP - Instalment 15/67",
          "amount": 1000.00,
          "units": 8.123,
          "nav": 123.0949,
          "unit_balance": 500.123,
          "page_number": 3
        }
      ]
    }
  ],

  "import_preview": {
    "folios_detected": 1,
    "funds_detected": 1,
    "transactions_detected": 1,
    "sip_patterns_detected": 1
  },

  "validation": {
    "errors": [],
    "warnings": []
  }
}
```

---

## 14. Error handling

The parser must NOT silently lose rows.

If a transaction cannot be parsed, put it into:

```json
{
  "unparsed_transactions": []
}
```

Example:

```json
{
  "page": 4,
  "raw_text": "...",
  "reason": "Unable to parse amount/units"
}
```

The application should report:

```text
143 transactions detected
140 parsed successfully
3 require review
```

Never silently discard financial transactions.

---

## 15. Testing

Create automated tests.

Include test cases for:

* Single fund
* Multiple funds
* Multiple folios
* SIP transactions
* Lump-sum purchases
* Redemption
* Switch
* Stamp duty
* Dividend/IDCW
* Transactions spanning multiple pages
* Repeated table headers
* Blank units/price fields
* Password-protected PDF
* Invalid password
* OCR fallback
* Decimal precision
* Unit-balance validation

Create fixtures using anonymized CAS data.

Do NOT commit the real CAS or real financial information to Git.

---

## 16. Project structure

Create a clean structure:

```text
cas-parser/
│
├── app/
│   ├── parser/
│   │   ├── pdf_reader.py
│   │   ├── section_detector.py
│   │   ├── transaction_parser.py
│   │   ├── fund_parser.py
│   │   ├── transaction_classifier.py
│   │   ├── sip_detector.py
│   │   └── validator.py
│   │
│   ├── models/
│   │   ├── fund.py
│   │   ├── folio.py
│   │   └── transaction.py
│   │
│   └── main.py
│
├── tests/
│
├── sample_data/
│   └── README.md
│
├── output/
│   └── .gitkeep
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 17. CLI

Provide:

```bash
python -m app.main --input cas.pdf
```

and:

```bash
python -m app.main --input cas.pdf --password
```

Output:

```text
output/parsed_cas.json
```

Display a concise summary:

```text
CAS parsing completed.

Funds detected:       4
Folios detected:      5
Transactions:       143

Parsed:             140
Needs review:         3

SIP patterns:         3

Output:
output/parsed_cas.json
```

---

## 18. Technology requirements

Use Python 3.11+.

Prefer:

* PyMuPDF
* pdfplumber
* Pydantic
* Decimal
* pytest

Use OCR only as a fallback.

Keep the parser modular so the PDF extraction layer can later be replaced without changing the transaction/portfolio engine.

Do NOT add unnecessary dependencies.

---

## 19. Critical financial rules

The parser must follow these principles:

1. Never invent missing transaction data.
2. Never infer transaction NAV from the calendar date when Price/Unit exists in the CAS.
3. Never treat Stamp Duty or similar charges as units purchased.
4. Never automatically create future SIP transactions.
5. Never assume a detected SIP is still active.
6. Preserve original transaction descriptions.
7. Preserve page numbers for traceability.
8. Use Decimal for financial values.
9. Never silently drop an unrecognized transaction.
10. Keep parsing separate from portfolio calculations.
11. Keep parsing separate from MFapi.in integration.
12. Do not store unnecessary personal information.

---

## Final deliverable

Produce:

1. Complete Python implementation
2. requirements.txt
3. README with setup and usage
4. Unit tests
5. Sample anonymized JSON output
6. Explanation of the parsing architecture
7. Clear list of assumptions and limitations

The immediate success criterion is:

**Given a real CAMS + KFintech Detailed CAS PDF, the program must reliably extract all fund/folio transaction rows into normalized JSON without losing or silently modifying financial data.**

Do not build the dashboard or MFapi integration yet.
