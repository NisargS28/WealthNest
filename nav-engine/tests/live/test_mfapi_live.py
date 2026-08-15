import pytest
from app.provider.mfapi import MFAPIProvider

@pytest.mark.live
def test_mfapi_live_connection():
    """
    This test requires an active internet connection.
    It verifies that the actual MFapi.in endpoints work as expected.
    To run this test, use: pytest -m live
    """
    provider = MFAPIProvider(timeout=10)
    
    # Test 1: Fetch master list
    master_list = provider.get_scheme_master()
    assert isinstance(master_list, list)
    assert len(master_list) > 1000
    
    # Verify a known scheme exists
    known = next((s for s in master_list if "schemeCode" in s), None)
    assert known is not None
    assert "schemeName" in known
    
    # Test 2: Fetch latest NAV
    nav_record = provider.get_latest_nav(125497)
    assert nav_record.provider == "mfapi"
    assert nav_record.provider_scheme_code == 125497
    assert nav_record.nav > 0
    assert nav_record.nav_date is not None
    
    # Test 3: Search endpoint
    results = provider.search_schemes("Motilal Oswal Small Cap")
    assert len(results) > 0
    assert "schemeCode" in results[0]
    assert "schemeName" in results[0]
    
    # Test 4: Missing Scheme (expect ValueError on missing data list)
    with pytest.raises(ValueError, match="No NAV data found"):
        provider.get_latest_nav(99999999)
