from decimal import Decimal

from app.engine.folio import reconstruct_folio
from app.models.holding import ReconciliationStatus


def test_purchase_units_increase():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "0.000",
        "closing_unit_balance": "10.000",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "100.00",
                "units": "10.000",
                "nav": "10.00"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.opening_units == Decimal("0.000")
    assert holding.calculated_closing_units == Decimal("10.000")
    assert holding.gross_purchases == Decimal("100.00")
    assert holding.net_cash_flow == Decimal("100.00")
    assert holding.reconciliation.status == ReconciliationStatus.PASS


def test_redemption_units_decrease():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "20.000",
        "closing_unit_balance": "10.000",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "REDEMPTION",
                "amount": "150.00",
                "units": "10.000",
                "nav": "15.00"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("10.000")
    assert holding.gross_redemptions == Decimal("150.00")
    assert holding.net_cash_flow == Decimal("-150.00")
    assert holding.reconciliation.status == ReconciliationStatus.PASS


def test_switch_in_switch_out():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "10.000",
        "closing_unit_balance": "15.000",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "SWITCH_IN",
                "amount": "100.00",
                "units": "10.000"
            },
            {
                "date": "2023-02-01",
                "transaction_type": "SWITCH_OUT",
                "amount": "50.00",
                "units": "5.000"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("15.000")
    assert holding.gross_purchases == Decimal("100.00")
    assert holding.gross_redemptions == Decimal("50.00")
    assert holding.net_cash_flow == Decimal("50.00")


def test_reversal_logic():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "10.000",
        "closing_unit_balance": "9.412",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "REVERSAL",
                "amount": "-10.00",
                "units": "-0.588"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("9.412")
    assert holding.gross_reversals == Decimal("-10.00")
    assert holding.net_cash_flow == Decimal("-10.00")


def test_stamp_duty_no_unit_impact():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "10.000",
        "closing_unit_balance": "10.000",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "STAMP_DUTY",
                "amount": "0.50",
                "units": "0.000"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("10.000")
    assert holding.stamp_duty == Decimal("0.50")
    assert holding.net_cash_flow == Decimal("0.00")


def test_multiple_transactions_ordered():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "0.000",
        "closing_unit_balance": "14.412",
        "transactions": [
            {
                "date": "2023-02-01",
                "transaction_type": "PURCHASE",
                "amount": "50.00",
                "units": "5.000"
            },
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "100.00",
                "units": "10.000"
            },
            {
                "date": "2023-03-01",
                "transaction_type": "REVERSAL",
                "amount": "-5.00",
                "units": "-0.588"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("14.412")
    assert holding.gross_purchases == Decimal("150.00")
    assert holding.gross_reversals == Decimal("-5.00")
    assert holding.net_cash_flow == Decimal("145.00")


def test_opening_nonzero_balance():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "55.443",
        "closing_unit_balance": "65.443",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "100.00",
                "units": "10.000"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("65.443")
    assert holding.reconciliation.status == ReconciliationStatus.PASS


def test_decimal_precision():
    folio_data = {
        "folio_number": "123",
        "amc": "Test AMC",
        "registrar": "CAMS",
        "scheme_name": "Test Scheme",
        "opening_unit_balance": "0.000",
        "closing_unit_balance": "0.333",
        "transactions": [
            {
                "date": "2023-01-01",
                "transaction_type": "PURCHASE",
                "amount": "3.33",
                "units": "0.333"
            }
        ]
    }
    
    holding = reconstruct_folio(folio_data)
    
    assert holding.calculated_closing_units == Decimal("0.333")
    assert holding.reconciliation.difference == Decimal("0.000")
