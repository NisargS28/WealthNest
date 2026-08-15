from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.nav import NAVRecord


class NAVProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'mfapi')."""
        pass

    @abstractmethod
    def get_latest_nav(self, provider_scheme_code: int) -> NAVRecord:
        """Fetch the latest NAV for a specific scheme code."""
        pass
        
    @abstractmethod
    def get_scheme_master(self) -> List[Dict[str, Any]]:
        """
        Fetch the complete master list of schemes.
        Expected to return a list of dicts. Minimal required keys for MFapi:
        - schemeCode: int
        - schemeName: str
        - isinGrowth: Optional[str]
        - isinDivReinvestment: Optional[str]
        """
        pass
