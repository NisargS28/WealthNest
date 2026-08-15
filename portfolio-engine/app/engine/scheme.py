from decimal import Decimal
from typing import List, Dict, Tuple

from app.models.holding import FolioHolding, SchemeHolding


def aggregate_by_scheme(folio_holdings: List[FolioHolding]) -> List[SchemeHolding]:
    """
    Aggregates folio holdings by scheme name and ISIN.
    """
    # Key: (scheme_name, isin, amc)
    # Value: [list of FolioHoldings]
    groups: Dict[Tuple[str, str, str], List[FolioHolding]] = {}
    
    for holding in folio_holdings:
        # Default to empty string for ISIN if None, to ensure tuple hashability and proper grouping
        key = (holding.scheme_name, holding.isin or "", holding.amc)
        if key not in groups:
            groups[key] = []
        groups[key].append(holding)
        
    scheme_holdings: List[SchemeHolding] = []
    
    for (scheme_name, isin_val, amc), group in groups.items():
        total_units = sum((f.calculated_closing_units for f in group), Decimal("0"))
        folios = [f.folio_number for f in group]
        
        scheme_holdings.append(
            SchemeHolding(
                scheme_name=scheme_name,
                isin=isin_val if isin_val else None,
                amc=amc,
                total_units=total_units,
                folios=folios
            )
        )
        
    return scheme_holdings
