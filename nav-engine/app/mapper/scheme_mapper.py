import logging
import difflib
from typing import Dict, Any

from app.models.nav import SchemeMapping, MappingStatus
from app.provider.base import NAVProvider
from app.mapper.scheme_master import SchemeMasterIndex

logger = logging.getLogger(__name__)


class SchemeMapper:
    def __init__(self, provider: NAVProvider, master_index: SchemeMasterIndex):
        self.provider = provider
        self.master = master_index

    def map_scheme(self, scheme_name: str, amc: str, isin: str = None, scheme_code: str = None) -> SchemeMapping:
        """
        Maps a CAS scheme to a provider scheme code based on priority:
        1. ISIN
        2. Name Search
        3. Fuzzy match fallback
        """
        base_mapping = {
            "cas_scheme_name": scheme_name,
            "amc": amc,
            "cas_isin": isin,
            "cas_scheme_code": scheme_code,
            "provider": self.provider.provider_name,
            "provider_scheme_code": None,
            "match_method": None,
            "status": MappingStatus.UNMATCHED
        }

        # Priority 1: ISIN
        if isin:
            code = self.master.get_by_isin(isin)
            if code:
                base_mapping.update({
                    "provider_scheme_code": code,
                    "match_method": "ISIN",
                    "status": MappingStatus.MATCHED
                })
                return SchemeMapping(**base_mapping)

        # Priority 2: Exact name in master
        code = self.master.get_by_exact_name(scheme_name)
        if code:
            base_mapping.update({
                "provider_scheme_code": code,
                "match_method": "EXACT_NAME",
                "status": MappingStatus.MATCHED
            })
            return SchemeMapping(**base_mapping)

        # Priority 3: API Search
        # Strip some common words that confuse the API search
        clean_name = scheme_name.replace(" - ", " ").replace(" Growth", "").replace(" Regular Plan", "")
        # But we must be careful not to strip too much, the user specifically mentioned fallback to name match.
        # Let's search with the first 4 words of the scheme name to ensure we get candidates
        search_query = " ".join(scheme_name.split()[:5])
        
        try:
            results = getattr(self.provider, "search_schemes", lambda x: [])(search_query)
        except Exception as e:
            logger.warning(f"Search API failed for {scheme_name}: {e}")
            results = []

        if not results:
            return SchemeMapping(**base_mapping)

        if len(results) == 1:
            base_mapping.update({
                "provider_scheme_code": results[0]["schemeCode"],
                "match_method": "NAME_SEARCH",
                "status": MappingStatus.MATCHED
            })
            return SchemeMapping(**base_mapping)

        # Priority 4: Fuzzy match against search results
        best_match = None
        best_ratio = 0.0
        
        for res in results:
            ratio = difflib.SequenceMatcher(None, scheme_name.lower(), res["schemeName"].lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = res
                
        # Handle ambiguous results (e.g. if two options have identical ratio, though unlikely)
        # We just rely on best_ratio.
        
        if best_ratio >= 0.85:
            base_mapping.update({
                "provider_scheme_code": best_match["schemeCode"],
                "match_method": "FUZZY",
                "status": MappingStatus.MATCHED
            })
        elif best_ratio >= 0.60:
            base_mapping.update({
                "provider_scheme_code": best_match["schemeCode"],
                "match_method": "FUZZY",
                "status": MappingStatus.REQUIRES_REVIEW
            })
        else:
            # Ratios below 0.60 are rejected
            pass

        return SchemeMapping(**base_mapping)
