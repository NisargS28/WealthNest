import pytest
from datetime import date
from decimal import Decimal
from app.parser.validator import Validator
from app.models.folio import Folio, Registrar
from app.models.transaction import Transaction, TransactionType

def test_nav_validation_rounding():
    validator = Validator()
    
    # Mock a folio with the transaction from CAS_02 that was failing with NAV mismatch
    tx = Transaction(
        date=date(2021, 1, 20),
        transaction_type=TransactionType.PURCHASE,
        description="Systematic Investment Purchase - 32/136",
        amount=Decimal("999.95"),
        units=Decimal("1.349"),
        nav=Decimal("741.2772"),
        unit_balance=Decimal("1.349"),
        page_number=1
    )
    
    folio = Folio(
        folio_number="21562170 / 0",
        amc="SBI",
        registrar=Registrar.CAMS,
        scheme_name="SBI Small Cap Fund",
        opening_unit_balance=Decimal("0.000"),
        transactions=[tx]
    )
    
    # In the old code, calc=999.95/1.349 = 741.2528. Reported is 741.2772. Diff is 0.0244.
    # Because unit tolerance was 0.01, it failed.
    # In the new code, amount = 999.95, expected amount = 1.349 * 741.2772 = 999.9829
    # Diff is 0.0329. The nav_monetary_tolerance is 0.5. So it should match!
    
    warnings = validator.validate(folio)
    
    assert len(warnings) == 0
    assert tx.validation.nav_validation.match is True
    # Verify the difference recorded is the monetary difference
    assert tx.validation.nav_validation.difference == round(Decimal("0.0329"), 4)

def test_unit_balance_with_reversal():
    validator = Validator()
    
    tx1 = Transaction(
        date=date(2024, 8, 20),
        transaction_type=TransactionType.PURCHASE,
        description="Systematic Investment Purchase",
        amount=Decimal("999.95"),
        units=Decimal("0.588"),
        nav=Decimal("1700.00"),
        unit_balance=Decimal("98.859"),
        page_number=1
    )
    
    # A reversal will have negative amount and negative units
    tx2 = Transaction(
        date=date(2024, 9, 20),
        transaction_type=TransactionType.REVERSAL,
        description="Systematic Investment Purchase - (Reversal)",
        amount=Decimal("-999.95"),
        units=Decimal("-0.588"),
        nav=Decimal("1701.0185"),
        unit_balance=Decimal("98.271"), # Unit balance goes down by 0.588
        page_number=1
    )
    
    folio = Folio(
        folio_number="123",
        amc="Test",
        registrar=Registrar.CAMS,
        scheme_name="Test",
        opening_unit_balance=Decimal("98.271"), # Before tx1
        transactions=[tx1, tx2]
    )
    
    warnings = validator.validate(folio)
    
    assert len(warnings) == 0
    assert tx1.validation.unit_balance_match is True
    assert tx2.validation.unit_balance_match is True
