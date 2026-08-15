from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    REDEMPTION = "REDEMPTION"
    SWITCH_IN = "SWITCH_IN"
    SWITCH_OUT = "SWITCH_OUT"
    DIVIDEND = "DIVIDEND"
    DIVIDEND_REINVESTMENT = "DIVIDEND_REINVESTMENT"
    STAMP_DUTY = "STAMP_DUTY"
    REVERSAL = "REVERSAL"
    OTHER = "OTHER"


class SubType(str, Enum):
    SIP = "SIP"
    LUMP_SUM = "LUMP_SUM"
    SYSTEMATIC = "SYSTEMATIC"


class NavValidation(BaseModel):
    calculated_nav: Decimal
    reported_nav: Decimal
    difference: Decimal
    match: bool


class TransactionValidation(BaseModel):
    unit_balance_match: bool
    unit_balance_difference: Optional[Decimal] = None
    nav_validation: Optional[NavValidation] = None


class Transaction(BaseModel):
    date: date
    transaction_type: TransactionType
    subtype: Optional[SubType] = None
    description: str
    amount: Optional[Decimal] = None
    units: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    unit_balance: Optional[Decimal] = None
    page_number: int
    is_sip: bool = False
    sip_installment_number: Optional[int] = None
    sip_total_installments: Optional[int] = None
    validation: Optional[TransactionValidation] = None
