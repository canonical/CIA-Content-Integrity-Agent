"""
HTTPClient: Shared HTTP client with retry, caching, and request tracing.
ENGINEER A: Implement this service.
"""

class HTTPClient:
    """Wrapper around requests with caching and retry logic."""

    def __init__(self, cache=None):
        self.cache = cache

    def request(self, method: str, url: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement HTTP client")

    def head(self, url: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement HEAD request")

    def get(self, url: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement GET request")

    def is_link_alive(self, url: str) -> bool:
        raise NotImplementedError("Engineer A: Implement link alive check")
