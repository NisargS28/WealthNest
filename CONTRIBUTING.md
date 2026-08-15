# Contributing to WealthNest

Thank you for your interest in contributing to WealthNest! Please follow these guidelines to set up your environment, write tests, and maintain clean standards.

---

## Development Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/NisargS28/WealthNest.git
   cd WealthNest
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   Install the project and development dependencies:
   ```bash
   pip install -e .[dev]
   ```

---

## Running the Parser

You can run the ingestion parser from the command line by providing a CAS PDF and a password:

```bash
python -m app.main --input path/to/your/sanitized_cas.pdf --password "your_password" --output output/parsed_cas.json
```

If the PDF does not require a password, simply omit the `--password` flag.

---

## Running Tests

We use `pytest` for unit and regression testing. Run tests using:

```bash
pytest tests
```

---

## How to Add CAS Fixtures & Regression Tests

To maintain parsing accuracy:
1. **Anonymize First**: Ensure the test PDF contains only fake names, dummy folio numbers, and fake bank details.
2. **Place in Tests**: Place the sanitized PDF or transaction strings under the appropriate folder.
3. **Write Unit Tests**: 
   - Add metadata/summary tests in `tests/test_pdf_reader.py`.
   - Add transaction/SIP/reversal parsing tests in `tests/test_transaction_parser.py`.
   - Add balance/NAV validation tests in `tests/test_validator.py`.

---

## Coding Conventions

- **Linting**: Keep code formatted using `black` (88 line-length limit).
- **Typing**: Use type hints (validated by `mypy`) for clarity, especially in Pydantic models.
- **Financial Arithmetic**: Always represent monetary amounts and unit counts using Python's `Decimal` type to avoid floating-point rounding errors.
- **No Silenced Warnings**: Validation failures must be populated in the root `Statement` model for UI rendering rather than silently ignored.
