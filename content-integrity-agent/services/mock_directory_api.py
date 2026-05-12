"""
MockDirectoryAPI: Resolves email → full user record.
ENGINEER B: Implement this service.
"""

class MockDirectoryAPI:
    """Mock directory service for user lookups."""

    def __init__(self, fixtures_path: str = "fixtures/directory.json"):
        self.fixtures_path = fixtures_path

    def lookup_user(self, email: str):
        raise NotImplementedError("Engineer B: Implement mock Directory API")
