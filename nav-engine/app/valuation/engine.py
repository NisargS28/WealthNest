import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any

from app.models.nav import (
    ValuationResult, ValuedHolding, ValuationSummary,
    NAVStatus, MappingStatus
)
from app.provider.base import NAVProvider
from app.mapper.scheme_mapper import SchemeMapper
from app.cache.nav_cache import NAVCache

logger = logging.getLogger(__name__)


class ValuationEngine:
    def __init__(self, provider: NAVProvider, mapper: SchemeMapper, cache: NAVCache, stale_days: int = 5):
        self.provider = provider
        self.mapper = mapper
        self.cache = cache
        self.stale_days = stale_days

    def value_portfolio(self, reconstructed_portfolio: Dict[str, Any]) -> ValuationResult:
        source_file = reconstructed_portfolio.get("source_file", "unknown")
        scheme_holdings = reconstructed_portfolio.get("scheme_holdings", [])
        
        valued_holdings: List[ValuedHolding] = []
        
        total_schemes = len(scheme_holdings)
        schemes_valued = 0
        schemes_unmatched = 0
        schemes_error = 0
        total_value = Decimal("0")
        unavailable_value = 0

        for holding in scheme_holdings:
            scheme_name = holding["scheme_name"]
            amc = holding["amc"]
            isin = holding.get("isin")
            total_units = Decimal(str(holding["total_units"]))
            folios = holding.get("folios", [])
            
            # 1. Map scheme
            mapping = self.mapper.map_scheme(scheme_name, amc, isin)
            
            if mapping.status in (MappingStatus.UNMATCHED, MappingStatus.AMBIGUOUS):
                schemes_unmatched += 1
                unavailable_value += 1
                valued_holdings.append(ValuedHolding(
                    scheme_name=scheme_name,
                    amc=amc,
                    total_units=total_units,
                    folios=folios,
                    mapping=mapping,
                    nav_record=None,
                    nav_status=NAVStatus.SCHEME_UNMATCHED,
                    current_value=None,
                    nav_date=None,
                    fetched_at=None
                ))
                continue
                
            # 2. Fetch NAV
            nav_record = None
            nav_status = NAVStatus.AVAILABLE
            current_value = None
            
            provider_code = mapping.provider_scheme_code
            
            # Check cache
            nav_record = self.cache.get_latest(self.provider.provider_name, provider_code)
            
            if not nav_record:
                try:
                    nav_record = self.provider.get_latest_nav(provider_code)
                    self.cache.set(nav_record)
                except Exception as e:
                    logger.warning(f"Error fetching NAV for {provider_code}: {e}")
                    nav_status = NAVStatus.API_ERROR
                    schemes_error += 1
                    
            if nav_record:
                # Check for staleness
                age_days = (datetime.now().date() - nav_record.nav_date).days
                if age_days > self.stale_days:
                    nav_status = NAVStatus.STALE_DATA
                    
                current_value = total_units * nav_record.nav
                total_value += current_value
                schemes_valued += 1
            else:
                if nav_status != NAVStatus.API_ERROR:
                    nav_status = NAVStatus.NAV_UNAVAILABLE
                unavailable_value += 1

            valued_holdings.append(ValuedHolding(
                scheme_name=scheme_name,
                amc=amc,
                total_units=total_units,
                folios=folios,
                mapping=mapping,
                nav_record=nav_record,
                nav_status=nav_status,
                current_value=current_value,
                nav_date=nav_record.nav_date if nav_record else None,
                fetched_at=nav_record.fetched_at if nav_record else None
            ))

        self.cache.save()

        summary = ValuationSummary(
            schemes_total=total_schemes,
            schemes_valued=schemes_valued,
            schemes_unmatched=schemes_unmatched,
            schemes_error=schemes_error,
            total_current_value=total_value,
            unavailable_value_schemes=unavailable_value
        )
        
        return ValuationResult(
            source_file=source_file,
            generated_at=datetime.now(),
            valued_holdings=valued_holdings,
            summary=summary
        )
