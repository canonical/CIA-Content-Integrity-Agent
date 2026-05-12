"""
MockGoogleDocAPI: Returns document metadata including owner, title, last modified.
ENGINEER B: Implement this service.
"""

class MockGoogleDocAPI:
    """Mock service returning fixture-based copydoc metadata."""

    def __init__(self, fixtures_dir: str = "fixtures/copydocs"):
        self.fixtures_dir = fixtures_dir

    def get_document_info(self, doc_url: str):
        raise NotImplementedError("Engineer B: Implement mock Google Doc API")
