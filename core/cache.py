import hashlib
import os
import pickle
from datetime import datetime, timedelta

from core.config import CACHE_DIR


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

        with open(path, "rb") as handle:
            payload = pickle.load(handle)

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
        with open(path, "wb") as handle:
            pickle.dump(payload, handle)
        return payload["stored_at"]
