import pytest
import json
from decimal import Decimal
from app.valuation.engine import ValuationEngine
from app.mapper.scheme_mapper import SchemeMapper
from app.models.nav import NAVRecord, NAVStatus
from app.cache.nav_cache import NAVCache
from datetime import datetime, date

class MockProviderIntegration:
    def __init__(self):
        self.provider_name = "mfapi"
        
    def get_latest_nav(self, code):
        navs = {
            100: Decimal("137.94580"),
            101: Decimal("199.03"),
            102: Decimal("16.9087"),
            103: Decimal("59.86"),
            104: Decimal("1300.5"), # Flexi Cap
            105: Decimal("12.5"),   # Energy
            106: Decimal("350.0")   # Multicap
        }
        if code in navs:
            return NAVRecord(
                provider="mfapi", provider_scheme_code=code,
                nav=navs[code], nav_date=date.today(), fetched_at=datetime.now()
            )
        raise ValueError("Unknown scheme")

class MockMasterIntegration:
    def get_by_isin(self, isin):
        mapping = {
            "INF209K01LF3": 100,
            "INF205K01BC9": 101,
            "INF247L01BV9": 102,
            "INF582M01BY1": 103,
            "INF090I01239": 104,
            "INF109KC15W9": 105,
            "INF277KA1703": 106
        }
        return mapping.get(isin)
        
    def get_by_exact_name(self, name):
        return None

def test_integration_cas_01():
    provider = MockProviderIntegration()
    master = MockMasterIntegration()
    mapper = SchemeMapper(provider, master)
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    engine = ValuationEngine(provider, mapper, cache)
    
    with open("../portfolio-engine/output/portfolio_reconstructed_cas_01.json") as f:
        reconstructed = json.load(f)
        
    result = engine.value_portfolio(reconstructed)
    
    assert result.summary.schemes_total == 4
    assert result.summary.schemes_valued == 4
    assert result.summary.schemes_unmatched == 0
    assert result.summary.unavailable_value_schemes == 0
    
    # 1412.890 * 137.94580 + 125.603 * 199.03 + 6998.416 * 16.9087 + 417.620 * 59.86 = approx 363233.86
    # Motilal: 6998.416 * 16.90870 = 118334.12
    # Invesco: 125.603 * 199.0300 = 24998.765 -> 24998.77
    # Union: 417.620 * 59.8600 = 24998.733 -> 24998.73
    # Aditya Birla: 1412.890 * 137.94580 = 194902.24
    
    # Check Aditya Birla was mapped successfully using the newly extracted ISIN
    ab = next(h for h in result.valued_holdings if "Aditya Birla" in h.scheme_name)
    assert ab.mapping.match_method == "ISIN"
    assert ab.current_value is not None

def test_integration_cas_02():
    provider = MockProviderIntegration()
    master = MockMasterIntegration()
    mapper = SchemeMapper(provider, master)
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    engine = ValuationEngine(provider, mapper, cache)
    
    with open("../portfolio-engine/output/portfolio_reconstructed_cas_02.json") as f:
        reconstructed = json.load(f)
        
    result = engine.value_portfolio(reconstructed)
    
    assert result.summary.schemes_total == 3
    assert result.summary.schemes_valued == 3
    assert result.summary.schemes_unmatched == 0
