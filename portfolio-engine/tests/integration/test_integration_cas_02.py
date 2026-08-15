import os

from app.engine.loader import load_parsed_cas
from app.engine.folio import reconstruct_folio
from app.models.holding import ReconciliationStatus

def test_integration_cas_02():
    filepath = "cas-parser/output/parsed_cas_02.json"
    if not os.path.exists(filepath):
        return
        
    cas_data = load_parsed_cas(filepath)
    
    folios_raw = cas_data.get("folios", [])
    assert len(folios_raw) == 3
    
    folio_holdings = []
    for folio_raw in folios_raw:
        holding = reconstruct_folio(folio_raw)
        assert holding.reconciliation.status == ReconciliationStatus.PASS
        folio_holdings.append(holding)
        
    # Check Franklin Flexi Cap folio (has opening balance and reversals)
    franklin = next(f for f in folio_holdings if "Franklin India Flexi Cap Fund" in f.scheme_name)
    assert str(franklin.opening_units) == "55.443"
    assert str(franklin.gross_reversals) == "-1999.90"
    assert str(franklin.cas_closing_units) == "113.926"
    assert str(franklin.calculated_closing_units) == "113.926"
