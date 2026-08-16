from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class FamilyMemberBase(BaseModel):
    id: str
    display_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreateFamilyMember(BaseModel):
    display_name: str


class PortfolioSummary(BaseModel):
    id: str
    member_id: str
    display_name: str
    created_at: datetime
    total_current_value: Optional[Decimal] = None
    last_valuation_date: Optional[date] = None
    folio_count: int
    transaction_count: int


class ImportSessionResponse(BaseModel):
    import_id: str
    status: str
    preview: Optional['ImportPreview'] = None
    error_message: Optional[str] = None


class ImportSummary(BaseModel):
    funds: int
    folios: int
    transactions: int
    total_current_value: Decimal
    nav_data_date: Optional[date] = None
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None


class TransactionBreakdown(BaseModel):
    purchases: int
    redemptions: int
    switches: int
    reversals: int
    stamp_duty: int
    other: int


class HoldingPreview(BaseModel):
    scheme_name: str
    amc: str
    isin: Optional[str] = None
    folios: List[str]
    total_units: Decimal
    nav: Optional[Decimal] = None
    nav_date: Optional[date] = None
    current_value: Optional[Decimal] = None
    nav_status: str
    mapping_method: Optional[str] = None


class ValidationWarning(BaseModel):
    folio: str
    transaction_date: date
    message: str


class ValidationSummary(BaseModel):
    parser_warnings: int
    reconciliation_warnings: int
    nav_errors: int
    unmatched_schemes: int
    stale_nav_schemes: int
    warnings: List[ValidationWarning] = []


class ImportPreview(BaseModel):
    import_id: str
    portfolio_owner: str
    status: str
    duplicate_risk: bool = False
    duplicate_message: Optional[str] = None
    summary: ImportSummary
    transaction_breakdown: TransactionBreakdown
    holdings: List[HoldingPreview]
    validation: ValidationSummary


class StoredHolding(BaseModel):
    scheme_name: str
    amc: str
    isin: Optional[str] = None
    total_units: Decimal
    current_value: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    nav_date: Optional[date] = None
    nav_status: str
    folios: List[str]


class StoredFolio(BaseModel):
    folio_number: str
    amc: str
    scheme_name: str
    isin: Optional[str] = None
    opening_units: Decimal
    cas_closing_units: Optional[Decimal] = None
    transaction_count: int


class ValuationDetail(BaseModel):
    portfolio_id: str
    generated_at: datetime
    total_current_value: Decimal
    holdings: List[StoredHolding]


class PortfolioDetail(BaseModel):
    id: str
    member_id: str
    display_name: str
    holdings: List[StoredHolding]
    folios: List[StoredFolio]
    valuation: Optional[ValuationDetail] = None


class TransactionView(BaseModel):
    id: str
    date: date
    transaction_type: str
    subtype: Optional[str] = None
    description: str
    amount: Optional[Decimal] = None
    units: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    unit_balance: Optional[Decimal] = None
    is_sip: bool

    class Config:
        from_attributes = True


class ConfirmImportRequest(BaseModel):
    acknowledge_duplicate: bool = False


class FamilyAggregate(BaseModel):
    total_value: Decimal
    member_summaries: List[PortfolioSummary]


class FamilyView(BaseModel):
    members: List[FamilyMemberBase]
    aggregate: FamilyAggregate

class HoldingDetail(BaseModel):
    id: str
    scheme_name: str
    folio_number: str
    amc_name: str
    category: Optional[str] = None
    invested: Decimal
    current_value: Decimal
    returns: Decimal
    nav: Decimal
    units: Decimal
    nav_date: Optional[date] = None

class AssetAllocation(BaseModel):
    name: str
    value: Decimal
    color: str

class ValuationHistory(BaseModel):
    month: str
    value: Decimal
    invested: Decimal

class DashboardResponse(BaseModel):
    total_value: Decimal
    total_invested: Decimal
    profit_loss: Decimal
    profit_percentage: Decimal
    portfolio_count: int
    recent_transactions: List[TransactionView]
    top_holdings: List[HoldingDetail]
    asset_allocation: List[AssetAllocation]
    pending_actions: int
    valuation_history: List[ValuationHistory]

ImportSessionResponse.model_rebuild()
