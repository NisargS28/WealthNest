import pytest
from datetime import date
from decimal import Decimal
from app.parser.pdf_reader import PdfReader

def test_extract_statement_metadata_and_summary():
    reader = PdfReader("dummy.pdf")
    
    # Simulate first page text from CAS PDF
    text = """
Consolidated Account Statement
01-Jan-2017 To 15-Aug-2026
Some other text...

PORTFOLIO SUMMARY
Aditya Birla Sun Life Mutual Fund 98,000.00               194,902.24
Invesco Mutual Fund 25,000.00               24,998.77
MOTILAL OSWAL MUTUAL FUND 80,000.00               118,334.11
Total 2,03,000.00 3,38,235.12
"""
    
    reader._extract_statement_metadata(text)
    
    assert reader.statement_metadata["period_start"] == date(2017, 1, 1)
    assert reader.statement_metadata["period_end"] == date(2026, 8, 15)
    assert reader.statement_metadata["generated_date"] == date(2026, 8, 15)
    
    assert len(reader.portfolio_summary) == 3
    assert reader.portfolio_summary[0] == {
        "amc": "Aditya Birla Sun Life Mutual Fund",
        "cost_value": "98000.00",
        "market_value": "194902.24"
    }
    assert reader.portfolio_summary[2] == {
        "amc": "MOTILAL OSWAL MUTUAL FUND",
        "cost_value": "80000.00",
        "market_value": "118334.11"
    }
