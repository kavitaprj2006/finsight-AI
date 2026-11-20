"""
FinSight AI - Market Data Cache Manager
"""
import time
import json
import pickle
from pathlib import Path
from typing import Optional, Any
from app.config import settings
from app.core.logger import logger

class CacheManager:
    """Manages cached provider responses with TTL support."""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 3600):
        self.cache_dir = cache_dir or settings.CACHE_DIR
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache = {}

    def _get_key_path(self, key: str) -> Path:
        safe_key = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in key)
        return self.cache_dir / f"{safe_key}.cache"

    def get(self, key: str) -> Optional[Any]:
        # Check memory first
        now = time.time()
        if key in self._memory_cache:
            data, exp = self._memory_cache[key]
            if now < exp:
                return data
            else:
                del self._memory_cache[key]

        # Check disk
        path = self._get_key_path(key)
        if not path.exists():
            return None

        try:
            with open(path, "rb") as f:
                payload = pickle.load(f)
            if now < payload.get("expires_at", 0):
                self._memory_cache[key] = (payload["data"], payload["expires_at"])
                return payload["data"]
            else:
                path.unlink(missing_ok=True)
                return None
        except Exception as e:
            logger.warning(f"Failed to read cache for {key}: {e}")
            return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + ttl
        self._memory_cache[key] = (data, expires_at)

        path = self._get_key_path(key)
        try:
            with open(path, "wb") as f:
                pickle.dump({"data": data, "expires_at": expires_at}, f)
        except Exception as e:
            logger.warning(f"Failed to write cache for {key}: {e}")

    def clear(self):
        self._memory_cache.clear()
        for f in self.cache_dir.glob("*.cache"):
            try:
                f.unlink()
            except Exception:
                pass
        logger.info("Cache cleared.")

cache = CacheManager()
