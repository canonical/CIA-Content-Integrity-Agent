import requests
from urllib.parse import urlparse
from utils.cache import SimpleCache
from utils.decorators import retry


class HTTPClient:
    DEFAULT_TIMEOUT = 15
    USER_AGENT = "ContentIntegrityBot/1.0 (+https://canonical.com; bot@canonical.com)"

    def __init__(self, cache=None, timeout: int = DEFAULT_TIMEOUT):
        self.cache = cache or SimpleCache()
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def _should_cache(self, url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        return any(
            domain in netloc
            for domain in ("localhost", "127.0.0.1", "canonical.com")
        ) or not netloc

    def request(self, method: str, url: str, use_cache: bool = True, **kwargs) -> str:
        if use_cache and method.upper() in ("GET", "HEAD"):
            cached = self.cache.get(url)
            if cached is not None:
                return cached

        @retry(max_attempts=3, backoff_factor=1.0, jitter=True)
        def _do_request():
            resp = self.session.request(
                method, url, timeout=kwargs.pop("timeout", self.timeout), **kwargs
            )
            resp.raise_for_status()
            return resp

        try:
            resp = _do_request()
            text = resp.text
            if use_cache and method.upper() in ("GET", "HEAD") and self._should_cache(url):
                self.cache.set(url, text)
            return text
        except Exception:
            raise

    def head(self, url: str, **kwargs) -> requests.Response:
        try:
            @retry(max_attempts=2, backoff_factor=0.5, jitter=True)
            def _do_head():
                return self.session.head(
                    url, timeout=kwargs.pop("timeout", self.timeout), **kwargs
                )
            return _do_head()
        except Exception:
            raise

    def get(self, url: str, **kwargs) -> str:
        return self.request("GET", url, **kwargs)

    def is_link_alive(self, url: str) -> bool:
        try:
            resp = self.session.head(url, timeout=5, allow_redirects=True)
            return resp.status_code < 400
        except Exception:
            return False
