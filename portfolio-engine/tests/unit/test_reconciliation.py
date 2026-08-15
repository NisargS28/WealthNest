from decimal import Decimal

from app.engine.folio import reconstruct_folio
from app.models.holding import ReconciliationStatus


def test_reconciliation_pass():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "0.000",
        "closing_unit_balance": "10.003",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "100.00",
                "units": "10.000",  # diff is 0.003
                "nav": "10.00"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    # 0.003 difference is within 0.005 tolerance
    assert holding.reconciliation.difference == Decimal("0.003")
    assert holding.reconciliation.status == ReconciliationStatus.PASS


def test_reconciliation_fail():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "0.000",
        "closing_unit_balance": "10.006",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "100.00",
                "units": "10.000",  # diff is 0.006
                "nav": "10.00"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    # 0.006 difference exceeds 0.005 tolerance
    assert holding.reconciliation.difference == Decimal("0.006")
    assert holding.reconciliation.status == ReconciliationStatus.FAIL
