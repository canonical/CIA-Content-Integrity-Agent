"""
Tests for GoogleDocsClient.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_docs_client import GoogleDocsClient


TEST_DOC_ID = "16_W5PIiK4mg2b5IYyAzmQvwMf7GA6yLiVOkzZ21nPP4"
TEST_DOC_URL = f"https://docs.google.com/document/d/{TEST_DOC_ID}/edit"


def test_extracts_doc_id_from_url():
    client = GoogleDocsClient()
    assert client._load_credentials() is None  # no env var set
    result = client.get_document_info(TEST_DOC_URL)
    assert result == {}


def test_invalid_url_returns_empty():
    client = GoogleDocsClient()
    result = client.get_document_info("not-a-google-docs-url")
    assert result == {}


def test_no_credentials_returns_empty():
    client = GoogleDocsClient()
    result = client.get_document_info(TEST_DOC_URL)
    assert result == {}


def test_real_document_requires_env_var():
    if not os.environ.get("GOOGLE_SERVICE_ACCOUNT_INFO"):
        print("\n  SKIP: GOOGLE_SERVICE_ACCOUNT_INFO not set — add it to .env to run real-doc test")
        return
    client = GoogleDocsClient()
    result = client.get_document_info(TEST_DOC_URL)
    assert "doc_id" in result
    assert result["doc_id"] == TEST_DOC_ID
    assert "title" in result
    assert "last_modified" in result
    assert "body" in result
    assert isinstance(result["body"], dict)
    print(f"  Title: {result['title']}")
    print(f"  Last modified: {result['last_modified']}")
    print(f"  Body content sections: {len(result.get('body', {}).get('content', []))}")


if __name__ == "__main__":
    print("test_extracts_doc_id_from_url:", end=" ")
    test_extracts_doc_id_from_url()
    print("PASS")
    print("test_invalid_url_returns_empty:", end=" ")
    test_invalid_url_returns_empty()
    print("PASS")
    print("test_no_credentials_returns_empty:", end=" ")
    test_no_credentials_returns_empty()
    print("PASS")
    print("test_real_document_requires_env_var:", end=" ")
    test_real_document_requires_env_var()
    print("DONE")
