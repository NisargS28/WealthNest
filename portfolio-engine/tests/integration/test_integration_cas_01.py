import os

from app.engine.loader import load_parsed_cas
from app.engine.folio import reconstruct_folio
from app.engine.scheme import aggregate_by_scheme
from app.models.holding import ReconciliationStatus

def test_integration_cas_01():
    # Path is relative to project root since pytest is run from there
    filepath = "cas-parser/output/parsed_cas_01.json"
    if not os.path.exists(filepath):
        # Allow test to be skipped if file is missing (e.g. running outside full repo)
        return
        
    cas_data = load_parsed_cas(filepath)
    
    folios_raw = cas_data.get("folios", [])
    assert len(folios_raw) == 5
    
    folio_holdings = []
    for folio_raw in folios_raw:
        holding = reconstruct_folio(folio_raw)
        assert holding.reconciliation.status == ReconciliationStatus.PASS
        folio_holdings.append(holding)
        
    scheme_holdings = aggregate_by_scheme(folio_holdings)
    
    # Motilal Oswal Small Cap Fund appears in two folios and should aggregate
    motilal = next(s for s in scheme_holdings if "Motilal Oswal Small Cap Fund" in s.scheme_name)
    assert len(motilal.folios) == 2
    # 4730.983 + 2267.433 = 6998.416
    assert str(motilal.total_units) == "6998.416"
