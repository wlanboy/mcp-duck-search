from unittest.mock import MagicMock, patch

import httpx
import pytest

import search
from config import CODE_SITES
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


@patch("search.httpx.Client")
def test_fetch_page_plain_text(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.text = "<p>not parsed</p>"
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://example.com/readme.txt")

    assert result == "<p>not parsed</p>"


@patch("search.httpx.Client")
def test_fetch_page_invalid_json_returns_raw_text(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.side_effect = ValueError("invalid json")
    mock_response.text = "{broken"
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://api.example.com/data.json")

    assert result == "{broken"


@patch("search.httpx.Client")
def test_fetch_page_strips_boilerplate_tags(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = (
        "<html><head><title>T</title></head><body>"
        "<nav>Menu</nav><script>alert(1)</script><style>p{}</style>"
        "<h1>Title</h1><p>Content</p>\n\n\n\n<p>More</p>"
        "<footer>Footer</footer></body></html>"
    )
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://example.com")

    assert "# Title" in result
    assert "Content" in result
    for removed in ("Menu", "alert", "p{}", "Footer"):
        assert removed not in result
    assert "\n\n\n" not in result


@patch("search.httpx.Client")
def test_fetch_page_truncates_to_max_chars(mock_client_cls):
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = f"<p>{'x' * 500}</p>"
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    result = fetch_page("https://example.com", max_chars=100)

    assert len(result) == 100


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


@patch("search.httpx.Client")
def test_search_searxng_respects_max_results_and_categories(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"title": f"R{i}", "url": f"https://example.com/{i}", "content": ""} for i in range(10)]
    }
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    with patch.object(search, "_SEARXNG_URL", "http://searxng:8080"):
        results = _search("python async", max_results=3, categories="it")

    params = mock_client_cls.get.call_args[1]["params"]
    assert params == {"q": "python async", "format": "json", "categories": "it"}
    assert [r["title"] for r in results] == ["R0", "R1", "R2"]


@patch("search.DDGS")
@patch("search.httpx.Client")
def test_search_falls_back_to_ddgs_on_invalid_searxng_json(mock_client_cls, mock_ddgs):
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("invalid json")
    mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_client_cls)
    mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
    mock_client_cls.get.return_value = mock_response

    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    with patch.object(search, "_SEARXNG_URL", "http://searxng:8080"):
        results = _search("python async", max_results=5)

    assert results == FAKE_RESULTS


@patch("search.DDGS")
def test_search_code_scopes_query_to_code_sites(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    search_code_fn("read csv")

    query = mock_ddgs.text.call_args[0][0]
    assert query == _site_query("read csv", CODE_SITES)


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
