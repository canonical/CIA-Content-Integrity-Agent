"""
MockDirectoryAPI: Resolves email → full user record.
"""
import json
import os


class MockDirectoryAPI:
    """Mock directory service for user lookups."""

    def __init__(self, fixtures_path: str = "fixtures/directory.json"):
        self.fixtures_path = fixtures_path
        self._users = {}
        self._load_fixtures()

    def _load_fixtures(self):
        path = self.fixtures_path
        if not os.path.isfile(path):
            alt = os.path.join("content-integrity-agent", path)
            if os.path.isfile(alt):
                path = alt
            else:
                return
        with open(path, "r") as fh:
            data = json.load(fh)
        for user in data.get("users", []):
            self._users[user["email"]] = user

    def lookup_user(self, email: str) -> dict:
        return self._users.get(email, self._users.get("ops-team@canonical.com", {}))
