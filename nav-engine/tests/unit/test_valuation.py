import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from app.models.nav import MappingStatus, NAVRecord, NAVStatus, SchemeMapping
from app.valuation.engine import ValuationEngine
from app.cache.nav_cache import NAVCache

class MockMapper:
    def map_scheme(self, name, amc, isin=None, scheme_code=None):
        if "Unmatched" in name:
            return SchemeMapping(
                cas_scheme_name=name, amc=amc, cas_isin=isin, cas_scheme_code=scheme_code,
                provider="mock", provider_scheme_code=None, match_method=None, status=MappingStatus.UNMATCHED
            )
        return SchemeMapping(
            cas_scheme_name=name, amc=amc, cas_isin=isin, cas_scheme_code=scheme_code,
            provider="mock", provider_scheme_code=100, match_method="ISIN", status=MappingStatus.MATCHED
        )

class MockProvider:
    def __init__(self):
        self.provider_name = "mock"
    
    def get_latest_nav(self, code):
        if code == 999:
            raise ValueError("API Error")
        if code == 888:
            return NAVRecord(
                provider="mock", provider_scheme_code=code,
                nav=Decimal("15.5"), nav_date=date(2000, 1, 1), fetched_at=datetime.now()
            )
        return NAVRecord(
            provider="mock", provider_scheme_code=code,
            nav=Decimal("10.0"), nav_date=date.today(), fetched_at=datetime.now()
        )

def test_valuation_engine_success():
    mapper = MockMapper()
    provider = MockProvider()
    # Cache with in-memory persistence, but don't save to file by mocking save
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    
    engine = ValuationEngine(provider, mapper, cache)
    
    reconstructed = {
        "source_file": "dummy.json",
        "scheme_holdings": [
            {"scheme_name": "Scheme A", "amc": "AMC A", "total_units": "100.0"},
            {"scheme_name": "Scheme B", "amc": "AMC B", "total_units": "50.5"}
        ]
    }
    
    result = engine.value_portfolio(reconstructed)
    assert result.summary.schemes_total == 2
    assert result.summary.schemes_valued == 2
    assert result.summary.total_current_value == Decimal("1505.0")  # (100 * 10) + (50.5 * 10)
    assert result.summary.unavailable_value_schemes == 0

def test_valuation_engine_unmatched():
    mapper = MockMapper()
    provider = MockProvider()
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    
    engine = ValuationEngine(provider, mapper, cache)
    reconstructed = {
        "scheme_holdings": [
            {"scheme_name": "Unmatched Scheme", "amc": "AMC", "total_units": "10.0"}
        ]
    }
    
    result = engine.value_portfolio(reconstructed)
    assert result.summary.schemes_unmatched == 1
    assert result.summary.schemes_valued == 0
    assert result.summary.unavailable_value_schemes == 1
    assert result.valued_holdings[0].nav_status == NAVStatus.SCHEME_UNMATCHED
    assert result.valued_holdings[0].current_value is None

def test_valuation_engine_stale_data():
    mapper = MockMapper()
    provider = MockProvider()
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    
    engine = ValuationEngine(provider, mapper, cache)
    
    # 888 returns year 2000 date
    mapper.map_scheme = lambda n, a, i=None: SchemeMapping(
        cas_scheme_name=n, amc=a, cas_isin=i, cas_scheme_code=None, provider="mock", provider_scheme_code=888, match_method="ISIN", status=MappingStatus.MATCHED
    )
    
    reconstructed = {
        "scheme_holdings": [
            {"scheme_name": "Stale Scheme", "amc": "AMC", "total_units": "100.0"}
        ]
    }
    
    result = engine.value_portfolio(reconstructed)
    assert result.summary.schemes_valued == 1
    assert result.valued_holdings[0].nav_status == NAVStatus.STALE_DATA
    # Value is still calculated even if stale
    assert result.valued_holdings[0].current_value == Decimal("1550.0")

def test_valuation_engine_api_error():
    mapper = MockMapper()
    provider = MockProvider()
    cache = NAVCache(cache_dir="dummy")
    cache.save = lambda: None
    
    engine = ValuationEngine(provider, mapper, cache)
    
    # 999 throws API error
    mapper.map_scheme = lambda n, a, i=None: SchemeMapping(
        cas_scheme_name=n, amc=a, cas_isin=i, cas_scheme_code=None, provider="mock", provider_scheme_code=999, match_method="ISIN", status=MappingStatus.MATCHED
    )
    
    reconstructed = {
        "scheme_holdings": [
            {"scheme_name": "Error Scheme", "amc": "AMC", "total_units": "100.0"}
        ]
    }
    
    result = engine.value_portfolio(reconstructed)
    assert result.summary.schemes_error == 1
    assert result.summary.schemes_valued == 0
    assert result.summary.unavailable_value_schemes == 1
    assert result.valued_holdings[0].nav_status == NAVStatus.API_ERROR
    assert result.valued_holdings[0].current_value is None
