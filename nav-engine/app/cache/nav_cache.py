import json
import os
import logging
from typing import Optional
from datetime import datetime, date
from pydantic import TypeAdapter

from app.models.nav import NAVRecord

logger = logging.getLogger(__name__)


class NAVCache:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "nav_cache.json")
        self._cache = {}  # type: dict[str, NAVRecord]
        self._load()

    def _get_key(self, provider: str, provider_scheme_code: int, nav_date: Optional[date] = None) -> str:
        # If nav_date is None, we store it under a 'latest' key
        date_str = nav_date.isoformat() if nav_date else "latest"
        return f"{provider}:{provider_scheme_code}:{date_str}"

    def _load(self):
        if not os.path.exists(self.cache_file):
            return
            
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                
            adapter = TypeAdapter(NAVRecord)
            for k, v in data.items():
                self._cache[k] = adapter.validate_python(v)
            logger.info(f"Loaded {len(self._cache)} NAV records from cache.")
        except Exception as e:
            logger.warning(f"Failed to load NAV cache: {e}")

    def save(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            
        try:
            # Pydantic v2 serialization
            data = {k: v.model_dump(mode='json') for k, v in self._cache.items()}
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._cache)} NAV records to cache.")
        except Exception as e:
            logger.warning(f"Failed to save NAV cache: {e}")

    def get_latest(self, provider: str, provider_scheme_code: int) -> Optional[NAVRecord]:
        """
        Get the latest NAV from cache, but only if it was fetched today.
        (Otherwise we want to hit the API again to get a fresher one).
        """
        key = self._get_key(provider, provider_scheme_code, None)
        record = self._cache.get(key)
        if record:
            # Check if it was fetched today
            if record.fetched_at.date() == datetime.now().date():
                return record
        return None
        
    def get_historical(self, provider: str, provider_scheme_code: int, nav_date: date) -> Optional[NAVRecord]:
        key = self._get_key(provider, provider_scheme_code, nav_date)
        return self._cache.get(key)

    def set(self, record: NAVRecord):
        # Store by explicit date
        date_key = self._get_key(record.provider, record.provider_scheme_code, record.nav_date)
        self._cache[date_key] = record
        
        # Also store as 'latest'
        latest_key = self._get_key(record.provider, record.provider_scheme_code, None)
        # Only overwrite latest if the new record is actually newer or same date
        existing_latest = self._cache.get(latest_key)
        if not existing_latest or record.nav_date >= existing_latest.nav_date:
            self._cache[latest_key] = record
