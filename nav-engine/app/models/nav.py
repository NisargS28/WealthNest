from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class MappingStatus(str, Enum):
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class SchemeMapping(BaseModel):
    cas_scheme_name: str
    amc: str
    cas_isin: Optional[str]
    cas_scheme_code: Optional[str]
    provider: str                    # e.g., "mfapi"
    provider_scheme_code: Optional[int]
    match_method: Optional[str]      # e.g., "ISIN", "NAME_SEARCH", "FUZZY"
    status: MappingStatus


class NAVRecord(BaseModel):
    provider: str
    provider_scheme_code: int
    nav: Decimal                     # Never float
    nav_date: date
    fetched_at: datetime


class NAVStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NAV_UNAVAILABLE = "NAV_UNAVAILABLE"
    SCHEME_UNMATCHED = "SCHEME_UNMATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    API_ERROR = "API_ERROR"
    STALE_DATA = "STALE_DATA"


class ValuedHolding(BaseModel):
    scheme_name: str
    amc: str
    total_units: Decimal
    folios: List[str]
    mapping: SchemeMapping
    nav_record: Optional[NAVRecord]
    nav_status: NAVStatus
    current_value: Optional[Decimal]    # None if NAV unavailable
    nav_date: Optional[date]
    fetched_at: Optional[datetime]


class ValuationSummary(BaseModel):
    schemes_total: int
    schemes_valued: int
    schemes_unmatched: int
    schemes_error: int
    total_current_value: Decimal              # sum of all successfully valued schemes
    unavailable_value_schemes: int            # count of schemes that could not be valued


class ValuationResult(BaseModel):
    source_file: str
    generated_at: datetime
    valued_holdings: List[ValuedHolding]
    summary: ValuationSummary
