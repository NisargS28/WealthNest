from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from app.models.transaction import Transaction


class Registrar(str, Enum):
    CAMS = "CAMS"
    KFINTECH = "KFINTECH"





class Folio(BaseModel):
    folio_number: str
    amc: str
    registrar: Registrar
    scheme_name: str
    scheme_code: Optional[str] = None
    isin: Optional[str] = None
    plan: Optional[str] = None
    option: Optional[str] = None
    opening_unit_balance: Decimal
    closing_unit_balance: Optional[Decimal] = None
    closing_nav: Optional[Decimal] = None
    closing_nav_date: Optional[date] = None
    total_cost_value: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    transactions: List[Transaction] = []
