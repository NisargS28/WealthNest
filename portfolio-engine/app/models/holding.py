from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class ReconciliationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class FolioReconciliation(BaseModel):
    cas_closing_units: Optional[Decimal]
    calculated_closing_units: Decimal
    difference: Optional[Decimal]
    status: ReconciliationStatus


class FolioHolding(BaseModel):
    folio_number: str
    amc: str
    registrar: str
    scheme_name: str
    scheme_code: Optional[str] = None
    isin: Optional[str] = None
    plan: Optional[str] = None
    option: Optional[str] = None
    
    opening_units: Decimal
    calculated_closing_units: Decimal
    cas_closing_units: Optional[Decimal] = None
    
    # Cash-flow breakdown (explicit, no ambiguous "invested_amount")
    gross_purchases: Decimal       # sum of all PURCHASE & SWITCH_IN & DIVIDEND_REINVESTMENT amounts (positive)
    gross_redemptions: Decimal     # sum of all REDEMPTION & SWITCH_OUT amounts (positive)
    gross_reversals: Decimal       # sum of all REVERSAL amounts (negative, as-signed by parser)
    stamp_duty: Decimal            # sum of |STAMP_DUTY amounts|
    net_cash_flow: Decimal         # gross_purchases + gross_redemptions + gross_reversals + stamp_duty(technically maybe we do not want stamp duty here, but user asked for net_cash_flow. Let's strictly do gross_purchases - gross_redemptions + gross_reversals - stamp_duty ? Actually, if it's cash flow *into* the fund: gross_purchases + gross_reversals. Let's document exactly what we mean.)
    
    reconciliation: FolioReconciliation


class SchemeHolding(BaseModel):
    scheme_name: str
    isin: Optional[str] = None
    amc: str
    total_units: Decimal           # sum of calculated_closing_units across folios
    folios: List[str]              # list of folio_numbers contributing to this scheme


class ReconciliationSummary(BaseModel):
    folios_processed: int
    folios_passed: int
    folios_failed: int
    unit_tolerance: Decimal


class PortfolioReconstruction(BaseModel):
    source_file: str
    generated_at: datetime
    folios: List[FolioHolding]
    scheme_holdings: List[SchemeHolding]
    reconciliation_summary: ReconciliationSummary
