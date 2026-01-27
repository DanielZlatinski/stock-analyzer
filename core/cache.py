import hashlib
import os
import pickle
from datetime import datetime, timedelta

from core.config import CACHE_DIR


class MemoryCache:
    """Lightweight in-memory cache for low-memory environments."""
    
    _store = {}  # Class-level to persist across requests
    MAX_SIZE = 20  # Limit cached items to save memory
    
    def __init__(self):
        pass
    
    def get(self, key, ttl_seconds):
        if key not in self._store:
            return None, None
        
        payload = self._store[key]
        stored_at = payload.get("stored_at")
        if stored_at is None:
            return None, None
        
        expires_at = stored_at + timedelta(seconds=ttl_seconds)
        if datetime.utcnow() > expires_at:
            del self._store[key]
            return None, None
        
        return payload.get("data"), stored_at
    
    def set(self, key, data):
        # Evict oldest if at capacity
        if len(self._store) >= self.MAX_SIZE:
            oldest_key = min(self._store.keys(), 
                           key=lambda k: self._store[k].get("stored_at", datetime.min))
            del self._store[oldest_key]
        
        payload = {
            "stored_at": datetime.utcnow(),
            "data": data,
        }
        self._store[key] = payload
        return payload["stored_at"]


class DiskCache:
    def __init__(self, base_dir=CACHE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path_for_key(self, key):
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return os.path.join(self.base_dir, f"{digest}.pkl")

    def get(self, key, ttl_seconds):
        path = self._path_for_key(key)
        if not os.path.exists(path):
            return None, None

        try:
            with open(path, "rb") as handle:
                payload = pickle.load(handle)
        except Exception:
            return None, None

        stored_at = payload.get("stored_at")
        if stored_at is None:
            return None, None

        expires_at = stored_at + timedelta(seconds=ttl_seconds)
        if datetime.utcnow() > expires_at:
            return None, None

        return payload.get("data"), stored_at

    def set(self, key, data):
        path = self._path_for_key(key)
        payload = {
            "stored_at": datetime.utcnow(),
            "data": data,
        }
        try:
            with open(path, "wb") as handle:
                pickle.dump(payload, handle)
        except Exception:
            pass  # Fail silently on disk issues
        return payload["stored_at"]


def get_cache():
    """Factory function to get appropriate cache based on environment."""
    if os.environ.get("LOW_MEMORY_MODE") == "1":
        return MemoryCache()
    return DiskCache()
