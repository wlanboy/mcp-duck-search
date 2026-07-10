import pytest
from unittest.mock import MagicMock, patch

import httpx

import search
from search import (
    _search,
    _site_query,
    fetch_page,
    search_code,
    web_search,
)

web_search_fn = web_search
search_code_fn = search_code


FAKE_RESULTS = [
    {"title": "Example", "href": "https://example.com", "body": "A test result."},
]


def test_site_query():
    result = _site_query("python async", ("github.com", "dev.to"))
    assert result == "python async (site:github.com OR site:dev.to)"


@patch("search.DDGS")
def test_web_search(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = web_search_fn("python async")

    mock_ddgs.text.assert_called_once_with("python async", max_results=5)
    assert results == FAKE_RESULTS


@patch("search.DDGS")
def test_web_search_custom_max(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = web_search_fn("python async", max_results=3)

    mock_ddgs.text.assert_called_once_with("python async", max_results=3)
    assert results == FAKE_RESULTS


@patch("search.DDGS")
def test_search_code(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_code_fn("read csv", language="python")

    call_args = mock_ddgs.text.call_args
    assert "python read csv" in call_args[0][0]
    assert results == FAKE_RESULTS


@patch("search.DDGS")
def test_search_code_error_message(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_code_fn("ModuleNotFoundError: No module named 'foo'", language="python")

    call_args = mock_ddgs.text.call_args
    query = call_args[0][0]
    assert "python" in query
    assert "ModuleNotFoundError" in query
    assert results == FAKE_RESULTS


@patch("search.DDGS")
def test_search_code_without_language(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_code_fn("spring-boot-starter-web dependency")

    call_args = mock_ddgs.text.call_args
    query = call_args[0][0]
    assert "spring-boot-starter-web dependency" in query
    assert results == FAKE_RESULTS


@patch("search.httpx.Client")
def test_fetch_page_html(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "text/html; charset=utf-8"}
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://example.com")

    assert "Hello world" in result


@patch("search.httpx.Client")
def test_fetch_page_json(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "application/json; charset=utf-8"}
    mock_response.json.return_value = {"version": "1.0", "items": ["a", "b"]}
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://api.example.com/data.json")

    assert '"version"' in result
    assert '"1.0"' in result
    assert "Unsupported content type" not in result


@patch("search.httpx.Client")
def test_fetch_page_unsupported_content_type(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "application/pdf"}
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://example.com/file.pdf")

    assert "Unsupported content type" in result
    assert "application/pdf" in result


@patch("search.httpx.Client")
def test_fetch_page_http_error(mock_client_cls):
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.side_effect = httpx.HTTPError("connection failed")

    result = fetch_page("https://example.com")

    assert "Error fetching page" in result


FAKE_SEARXNG_RESPONSE = {
    "results": [
        {"title": "Example", "url": "https://example.com", "content": "A test result."},
    ]
}


@patch("search.httpx.Client")
def test_search_uses_searxng_when_url_set(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = FAKE_SEARXNG_RESPONSE
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    with patch.object(search, "_SEARXNG_URL", "http://searxng:8080"):
        results = _search("python async", max_results=5)

    mock_client_cls.get.assert_called_once()
    call_kwargs = mock_client_cls.get.call_args
    assert "http://searxng:8080/search" in call_kwargs[0][0]
    assert results == [{"title": "Example", "href": "https://example.com", "body": "A test result."}]


@patch("search.DDGS")
@patch("search.httpx.Client")
def test_search_falls_back_to_ddgs_on_searxng_error(mock_client_cls, mock_ddgs):
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.side_effect = httpx.HTTPError("connection refused")

    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    with patch.object(search, "_SEARXNG_URL", "http://searxng:8080"):
        results = _search("python async", max_results=5)

    mock_ddgs.text.assert_called_once()
    assert results == FAKE_RESULTS


@patch("search.DDGS")
@patch("search.httpx.Client")
def test_search_falls_back_to_ddgs_and_logs_warning(mock_client_cls, mock_ddgs, caplog):
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.side_effect = httpx.HTTPError("connection refused")

    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    with patch.object(search, "_SEARXNG_URL", "http://searxng:8080"):
        import logging
        with caplog.at_level(logging.WARNING, logger="search"):
            results = _search("python async", max_results=5)

    assert any("SearXNG" in r.message for r in caplog.records)
    assert results == FAKE_RESULTS


@pytest.mark.integration
def test_search_spring_ai_docs_integration():
    """Integration test: real DuckDuckGo search for Spring AI documentation."""
    from ddgs import DDGS

    with DDGS() as ddgs:
        results = list(ddgs.text("spring ai documentation", max_results=3))

    if not results:
        pytest.skip("DuckDuckGo returned no results (package may be outdated, try: uv add ddgs)")

    assert len(results) > 0
    for result in results:
        assert "title" in result
        assert "href" in result
        assert "body" in result
