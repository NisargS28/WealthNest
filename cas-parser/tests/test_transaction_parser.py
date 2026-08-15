import pytest
from datetime import date
from decimal import Decimal
from app.parser.transaction_parser import TransactionParser
from app.models.transaction import TransactionType, SubType
from app.models.statement import UnparsedTransaction

def test_system_events_handling():
    parser = TransactionParser()
    unparsed = []
    
    # Simulate multi-line system event
    lines = [
        ("26-Jun-2018 ***One Time Mandate Acceptance from BankORIENTAL BANK OF", 1),
        ("COMMERCE$**6826***", 1),
        ("27-Jun-2018 Purchase 1,000.00 10.0 100.0 100.0", 1) # A valid transaction after it
    ]
    
    txs = parser.parse_transactions(lines, unparsed)
    
    assert len(unparsed) == 0
    assert len(txs) == 1
    assert txs[0].transaction_type == TransactionType.PURCHASE
    assert txs[0].date == date(2018, 6, 27)

def test_false_positive_header_skipping():
    parser = TransactionParser()
    unparsed = []
    
    lines = [
        ("01-Jan-2017 To 15-Aug-2026 Date Transaction Amount Units Price Unit (INR) (INR) Balance", 1),
        ("27-Jun-2018 Purchase 1,000.00 10.0 100.0 100.0", 1)
    ]
    
    txs = parser.parse_transactions(lines, unparsed)
    
    assert len(unparsed) == 0
    assert len(txs) == 1
    assert txs[0].date == date(2018, 6, 27)

def test_explicit_sip_extraction():
    parser = TransactionParser()
    unparsed = []
    
    lines = [
        ("15-Jan-2019 Purchase - SIP - Instalment 8/67 1,000.00 19.401 51.5440 148.043", 1),
        ("15-Feb-2019 Systematic Investment Existing Folio with SIP (1) 999.95 91.757 10.8978 187.023", 1)
    ]
    
    txs = parser.parse_transactions(lines, unparsed)
    
    assert len(txs) == 2
    
    # First should have extracted installments
    assert txs[0].is_sip is True
    assert txs[0].sip_installment_number == 8
    assert txs[0].sip_total_installments == 67
    
    # Second has no explicit installments, should be SIP but None
    assert txs[1].is_sip is True
    assert txs[1].sip_installment_number is None
    assert txs[1].sip_total_installments is None

def test_systematic_investment_purchase():
    parser = TransactionParser()
    unparsed = []
    
    lines = [
        ("20-Jan-2021 Systematic Investment Purchase - 32/136 999.95 1.349 741.2772 56.792", 1)
    ]
    
    txs = parser.parse_transactions(lines, unparsed)
    
    assert len(unparsed) == 0
    assert len(txs) == 1
    assert txs[0].transaction_type == TransactionType.PURCHASE
    assert txs[0].subtype == SubType.SIP
    assert txs[0].is_sip is True
    assert txs[0].sip_installment_number == 32
    assert txs[0].sip_total_installments == 136

def test_reversal_parsing():
    parser = TransactionParser()
    unparsed = []
    
    lines = [
        ("20-Sep-2024 Systematic Investment Purchase - (Reversal) - Instalment No 76 (999.95) (0.588) 1,701.0185 98.271", 1)
    ]
    
    txs = parser.parse_transactions(lines, unparsed)
    
    assert len(unparsed) == 0
    assert len(txs) == 1
    assert txs[0].transaction_type == TransactionType.REVERSAL
    assert txs[0].subtype == SubType.SIP
    assert txs[0].amount == Decimal("-999.95")
    assert txs[0].units == Decimal("-0.588")
    assert txs[0].nav == Decimal("1701.0185")
