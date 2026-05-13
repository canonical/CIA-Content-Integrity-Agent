import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from services.google_doc_fetcher import GoogleDocFetcher
from utils.cache import SimpleCache


SA_INFO = json.dumps({
    "client_email": "test@test.iam.gserviceaccount.com",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----",
    "token_uri": "https://oauth2.googleapis.com/token",
})

MOCK_DOC_RESPONSE = {
    "body": {
        "content": [
            {
                "paragraph": {
                    "elements": [
                        {"textRun": {"content": "Use sentence case for headings.\n"}}
                    ]
                }
            },
            {
                "paragraph": {
                    "elements": [
                        {"textRun": {"content": "CTAs must start with a verb.\n"}}
                    ]
                }
            },
        ]
    }
}


def _make_fetcher(cache_dir=None):
    if cache_dir is None:
        cache_dir = tempfile.mkdtemp()
    cache = SimpleCache(cache_dir=cache_dir)
    return GoogleDocFetcher(service_account_info=SA_INFO, cache=cache, cache_ttl=300)


@patch("services.google_doc_fetcher.requests.post")
@patch("services.google_doc_fetcher.requests.get")
@patch("services.google_doc_fetcher.jwt.encode")
def test_get_document_text(mock_jwt, mock_get, mock_post):
    mock_jwt.return_value = "fake-jwt"
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"access_token": "tok", "expires_in": 3600}),
    )
    mock_get.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value=MOCK_DOC_RESPONSE),
    )

    fetcher = _make_fetcher()
    text = fetcher.get_document_text("doc123")

    assert "Use sentence case for headings." in text
    assert "CTAs must start with a verb." in text
    mock_get.assert_called_once()


@patch("services.google_doc_fetcher.requests.post")
@patch("services.google_doc_fetcher.requests.get")
@patch("services.google_doc_fetcher.jwt.encode")
def test_caching(mock_jwt, mock_get, mock_post):
    mock_jwt.return_value = "fake-jwt"
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"access_token": "tok", "expires_in": 3600}),
    )
    mock_get.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value=MOCK_DOC_RESPONSE),
    )

    cache_dir = tempfile.mkdtemp()
    fetcher = _make_fetcher(cache_dir=cache_dir)
    fetcher.get_document_text("doc_caching")
    fetcher.get_document_text("doc_caching")

    assert mock_get.call_count == 1


@patch("services.google_doc_fetcher.requests.post")
@patch("services.google_doc_fetcher.jwt.encode")
def test_api_failure_returns_empty(mock_jwt, mock_post):
    mock_jwt.return_value = "fake-jwt"
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"access_token": "tok", "expires_in": 3600}),
    )

    fetcher = _make_fetcher()
    with patch("services.google_doc_fetcher.requests.get", side_effect=Exception("down")):
        text = fetcher.get_document_text("doc_fail")

    assert text == ""


@patch("services.google_doc_fetcher.requests.post")
@patch("services.google_doc_fetcher.requests.get")
@patch("services.google_doc_fetcher.jwt.encode")
def test_extract_text_empty_doc(mock_jwt, mock_get, mock_post):
    mock_jwt.return_value = "fake-jwt"
    mock_post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"access_token": "tok", "expires_in": 3600}),
    )
    mock_get.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"body": {"content": []}}),
    )

    fetcher = _make_fetcher()
    text = fetcher.get_document_text("empty_doc")
    assert text == ""
