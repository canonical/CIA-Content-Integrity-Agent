import hashlib
import json
import os
import time
from typing import Any, Optional


class SimpleCache:
    def __init__(self, ttl_seconds: int = 3600, cache_dir: str = ".cache"):
        self._memory = {}
        self.ttl = ttl_seconds
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _key_to_path(self, url: str) -> str:
        h = hashlib.sha256(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{h}.json")

    def get(self, url: str) -> Optional[Any]:
        if url in self._memory:
            entry = self._memory[url]
            if time.time() < entry["expires"]:
                return entry["value"]
            del self._memory[url]

        path = self._key_to_path(url)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    entry = json.load(f)
                if time.time() < entry["expires"]:
                    self._memory[url] = entry
                    return entry["value"]
                os.remove(path)
            except (json.JSONDecodeError, KeyError, OSError):
                pass
        return None

    def set(self, url: str, value: Any):
        entry = {
            "value": value,
            "expires": time.time() + self.ttl,
        }
        self._memory[url] = entry
        path = self._key_to_path(url)
        try:
            with open(path, "w") as f:
                json.dump(entry, f)
        except (OSError, TypeError):
            pass
