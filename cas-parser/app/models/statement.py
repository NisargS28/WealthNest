from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.models.folio import Folio


class StatementMetadata(BaseModel):
    statement_type: str = "CAS_DETAILED"
    statement_id: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    generated_date: Optional[date] = None
    extraction_method: str = "PyMuPDF+pdfplumber"


class PortfolioSummaryRow(BaseModel):
    amc: str
    cost_value: Decimal
    market_value: Decimal


class ImportPreview(BaseModel):
    funds_detected: int = 0
    folios_detected: int = 0
    transactions_detected: int = 0
    purchase_transactions: int = 0
    redemption_transactions: int = 0
    switch_transactions: int = 0
    stamp_duty_transactions: int = 0
    reversal_transactions: int = 0
    other_transactions: int = 0


class ValidationWarning(BaseModel):
    folio: str
    transaction_date: date
    message: str


class ValidationSummary(BaseModel):
    errors: List[str] = []
    warnings: List[ValidationWarning] = []


class UnparsedTransaction(BaseModel):
    page: int
    raw_text: str
    reason: str


class Statement(BaseModel):
    statement: StatementMetadata = StatementMetadata()
    portfolio_summary: List[PortfolioSummaryRow] = []
    folios: List[Folio] = []
    import_preview: ImportPreview = ImportPreview()
    unparsed_transactions: List[UnparsedTransaction] = []
    validation: ValidationSummary = ValidationSummary()
