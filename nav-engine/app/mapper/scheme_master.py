import os
import json
import logging
from datetime import datetime
from typing import Dict

from app.provider.base import NAVProvider

logger = logging.getLogger(__name__)


class SchemeMasterIndex:
    def __init__(self, provider: NAVProvider, cache_dir: str = "cache", max_age_days: int = 1):
        self.provider = provider
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, f"{provider.provider_name}_master.json")
        self.max_age_days = max_age_days
        
        self.by_isin: Dict[str, int] = {}
        self.by_name: Dict[str, int] = {}
        
        self._initialize()

    def _initialize(self):
        data = self._load_from_cache()
        if not data:
            logger.info(f"Downloading scheme master from {self.provider.provider_name}...")
            data = self.provider.get_scheme_master()
            self._save_to_cache(data)
            
        self._build_index(data)

    def _load_from_cache(self) -> list:
        if not os.path.exists(self.cache_file):
            return []
            
        try:
            mtime = os.path.getmtime(self.cache_file)
            age_days = (datetime.now().timestamp() - mtime) / (24 * 3600)
            
            if age_days > self.max_age_days:
                logger.info("Scheme master cache is stale.")
                return []
                
            with open(self.cache_file, "r") as f:
                logger.info("Loaded scheme master from cache.")
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load scheme master cache: {e}")
            return []

    def _save_to_cache(self, data: list):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        try:
            with open(self.cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Failed to save scheme master cache: {e}")

    def _build_index(self, data: list):
        for scheme in data:
            code = scheme.get("schemeCode")
            if not code:
                continue
                
            name = scheme.get("schemeName")
            if name:
                self.by_name[name.lower()] = code
                
            isin_growth = scheme.get("isinGrowth")
            if isin_growth:
                self.by_isin[isin_growth] = code
                
            isin_div = scheme.get("isinDivReinvestment")
            if isin_div:
                self.by_isin[isin_div] = code

    def get_by_isin(self, isin: str) -> int:
        return self.by_isin.get(isin)
        
    def get_by_exact_name(self, name: str) -> int:
        return self.by_name.get(name.lower())
