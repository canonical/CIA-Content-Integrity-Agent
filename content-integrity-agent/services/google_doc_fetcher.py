"""
GoogleDocFetcher: Fetches Google Doc content using service account authentication.
Uses pyjwt + requests (no google-api-python-client dependency).
"""

import json
import logging
import time

import jwt
import requests

from utils.cache import SimpleCache

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_DOCS_API = "https://docs.googleapis.com/v1/documents"
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


class GoogleDocFetcher:
    """Fetches Google Doc content via service account auth."""

    def __init__(self, service_account_info: str, cache=None, cache_ttl: int = 3600):
        self.service_account_info = json.loads(service_account_info)
        self.cache = cache or SimpleCache()
        self.cache_ttl = cache_ttl
        self._access_token = None
        self._token_expiry = 0

    def _get_access_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expiry - 60:
            return self._access_token

        sa = self.service_account_info
        payload = {
            "iss": sa["client_email"],
            "scope": " ".join(SCOPES),
            "aud": GOOGLE_TOKEN_URL,
            "iat": int(now),
            "exp": int(now) + 3600,
        }
        token_jwt = jwt.encode(payload, sa["private_key"], algorithm="RS256")

        resp = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": token_jwt,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        self._access_token = data["access_token"]
        self._token_expiry = now + int(data.get("expires_in", 3600))
        return self._access_token

    def get_document_text(self, doc_id: str) -> str:
        cache_key = f"gdoc:{doc_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            token = self._get_access_token()
            resp = requests.get(
                f"{GOOGLE_DOCS_API}/{doc_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            resp.raise_for_status()
            doc = resp.json()
            text = self._extract_text(doc)
            self.cache.set(cache_key, text)
            return text
        except Exception as e:
            logger.error("Failed to fetch Google Doc %s: %s", doc_id, e)
            return ""

    def _extract_text(self, doc: dict) -> str:
        body = doc.get("body", {})
        content = body.get("content", [])
        parts = []
        for element in content:
            paragraph = element.get("paragraph")
            if paragraph:
                for elem in paragraph.get("elements", []):
                    text_run = elem.get("textRun")
                    if text_run:
                        parts.append(text_run.get("content", ""))
        return "".join(parts)
