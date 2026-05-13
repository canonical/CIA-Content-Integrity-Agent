"""
GoogleDocsClient: Reads Google Docs via service account authentication.
Falls back gracefully when no credentials are configured.
"""
import json
import os
import re
import time

import jwt
import requests


class GoogleDocsClient:
    """Reads Google Docs metadata and structured content via REST APIs."""

    SCOPES = [
        "https://www.googleapis.com/auth/documents.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    TOKEN_URI = "https://oauth2.googleapis.com/token"

    def __init__(self):
        self._credentials = self._load_credentials()
        self._token = None
        self._token_expiry = 0

    def _load_credentials(self):
        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_INFO", "")
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def _build_jwt(self):
        creds = self._credentials
        now = int(time.time())
        payload = {
            "iss": creds["client_email"],
            "scope": " ".join(self.SCOPES),
            "aud": self.TOKEN_URI,
            "iat": now,
            "exp": now + 3600,
        }
        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "kid": creds["private_key_id"],
        }
        return jwt.encode(payload, creds["private_key"], algorithm="RS256", headers=headers)

    def _get_access_token(self):
        if not self._credentials:
            return None
        now = int(time.time())
        if self._token and now < self._token_expiry - 60:
            return self._token
        assertion = self._build_jwt()
        resp = requests.post(
            self.TOKEN_URI,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = now + data.get("expires_in", 3600)
        return self._token

    def get_document_info(self, doc_url: str) -> dict:
        match = re.search(r"/d/([^/]+)", doc_url)
        if not match:
            return {}
        doc_id = match.group(1)

        token = self._get_access_token()
        if not token:
            return {}

        auth = {"Authorization": f"Bearer {token}"}

        try:
            drive_resp = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{doc_id}",
                params={"fields": "name,modifiedTime"},
                headers=auth,
                timeout=15,
            )
            drive_resp.raise_for_status()
            drive_data = drive_resp.json()
        except Exception:
            return {}

        try:
            docs_resp = requests.get(
                f"https://docs.googleapis.com/v1/documents/{doc_id}",
                headers=auth,
                timeout=15,
            )
            docs_resp.raise_for_status()
            docs_data = docs_resp.json()
        except Exception:
            return {}

        return {
            "doc_id": doc_id,
            "title": drive_data.get("name", ""),
            "last_modified": drive_data.get("modifiedTime", ""),
            "body": docs_data.get("body", {}),
        }
