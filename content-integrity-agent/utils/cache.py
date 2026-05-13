"""
SimpleCache: In-memory + file-backed cache for HTTP responses.
ENGINEER A: Implement this utility.
"""

class SimpleCache:
    """In-memory key-value cache with optional file persistence."""

    def __init__(self, ttl_seconds: int = 3600, cache_dir: str = ".cache"):
        self.ttl = ttl_seconds
        self.cache_dir = cache_dir

    def get(self, url: str):
        raise NotImplementedError("Engineer A: Implement cache get")

    def set(self, url: str, value):
        raise NotImplementedError("Engineer A: Implement cache set")
