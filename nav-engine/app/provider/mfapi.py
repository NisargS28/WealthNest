import requests
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any

from app.models.nav import NAVRecord
from app.provider.base import NAVProvider


class MFAPIProvider(NAVProvider):
    BASE_URL = "https://api.mfapi.in"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    @property
    def provider_name(self) -> str:
        return "mfapi"

    def get_latest_nav(self, provider_scheme_code: int) -> NAVRecord:
        url = f"{self.BASE_URL}/mf/{provider_scheme_code}/latest"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        
        # MFapi returns HTTP 200 with empty 'data' array if scheme is not found or has no NAV
        if not data.get("data"):
            raise ValueError(f"No NAV data found for scheme {provider_scheme_code}")
            
        latest = data["data"][0]
        date_str = latest["date"]  # "DD-MM-YYYY"
        nav_str = latest["nav"]
        
        nav_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        nav_value = Decimal(nav_str)
        
        return NAVRecord(
            provider=self.provider_name,
            provider_scheme_code=provider_scheme_code,
            nav=nav_value,
            nav_date=nav_date,
            fetched_at=datetime.now()
        )

    def get_scheme_master(self) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/mf"
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()

    def search_schemes(self, query: str) -> List[Dict[str, Any]]:
        """
        Specific to MFapi. Used as fallback by mapper if ISIN is unavailable.
        Returns: [{"schemeCode": int, "schemeName": str}, ...]
        """
        url = f"{self.BASE_URL}/mf/search"
        response = self.session.get(url, params={"q": query}, timeout=self.timeout)
        response.raise_for_status()
        
        return response.json()
