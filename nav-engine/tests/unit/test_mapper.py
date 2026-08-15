import pytest
from datetime import date
from decimal import Decimal
from app.models.nav import MappingStatus, NAVRecord
from app.mapper.scheme_mapper import SchemeMapper

class MockProvider:
    def __init__(self):
        self.provider_name = "mfapi"
        
    def search_schemes(self, query):
        if "Unique" in query:
            return [{"schemeCode": 100, "schemeName": "Unique Scheme Growth"}]
        elif "Ambiguous" in query:
            return [
                {"schemeCode": 101, "schemeName": "Ambiguous Scheme Growth"},
                {"schemeCode": 102, "schemeName": "Ambiguous Scheme Regular"}
            ]
        elif "Empty" in query:
            return []
        return []

class MockMaster:
    def get_by_isin(self, isin):
        if isin == "INF123456789": return 200
        return None
        
    def get_by_exact_name(self, name):
        if name == "exact match scheme": return 300
        return None

def test_mapper_isin_match():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    mapping = mapper.map_scheme("Some Scheme", "AMC", isin="INF123456789")
    assert mapping.status == MappingStatus.MATCHED
    assert mapping.match_method == "ISIN"
    assert mapping.provider_scheme_code == 200

def test_mapper_exact_name_match():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    mapping = mapper.map_scheme("exact match scheme", "AMC")
    assert mapping.status == MappingStatus.MATCHED
    assert mapping.match_method == "EXACT_NAME"
    assert mapping.provider_scheme_code == 300

def test_mapper_search_unique_match():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    mapping = mapper.map_scheme("Unique Scheme Growth", "AMC")
    assert mapping.status == MappingStatus.MATCHED
    assert mapping.match_method == "NAME_SEARCH"
    assert mapping.provider_scheme_code == 100

def test_mapper_search_unmatched():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    mapping = mapper.map_scheme("Empty Query Scheme", "AMC")
    assert mapping.status == MappingStatus.UNMATCHED
    assert mapping.provider_scheme_code is None

def test_mapper_fuzzy_requires_review():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    # query is Ambiguous Scheme Growth
    # the search returns 101 ("Ambiguous Scheme Growth") and 102 ("Ambiguous Scheme Regular")
    # the first one will perfectly match. Wait, fuzzy ratio for exact match is 1.0.
    mapping = mapper.map_scheme("Ambiguous Scheme Growth", "AMC")
    assert mapping.status == MappingStatus.MATCHED
    assert mapping.match_method == "FUZZY"
    assert mapping.provider_scheme_code == 101

def test_mapper_fuzzy_unmatched():
    provider = MockProvider()
    master = MockMaster()
    mapper = SchemeMapper(provider, master)
    
    # Force a very bad fuzzy match
    # Wait, the search mock above returns nothing for "Very Bad". So it goes to UNMATCHED.
    mapping = mapper.map_scheme("Very Bad Query", "AMC")
    assert mapping.status == MappingStatus.UNMATCHED
