import pytest
from unittest.mock import patch, MagicMock
from main import web_search, search_code, search_error, search_docs, search_spring_boot, _site_query

web_search_fn = web_search
search_code_fn = search_code
search_error_fn = search_error
search_docs_fn = search_docs
search_spring_boot_fn = search_spring_boot


FAKE_RESULTS = [
    {"title": "Example", "href": "https://example.com", "body": "A test result."},
]


def test_site_query():
    result = _site_query("python async", ("github.com", "dev.to"))
    assert result == "python async (site:github.com OR site:dev.to)"


@patch("main.DDGS")
def test_web_search(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = web_search_fn("python async")

    mock_ddgs.text.assert_called_once_with("python async", max_results=5)
    assert results == FAKE_RESULTS


@patch("main.DDGS")
def test_web_search_custom_max(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = web_search_fn("python async", max_results=3)

    mock_ddgs.text.assert_called_once_with("python async", max_results=3)
    assert results == FAKE_RESULTS


@patch("main.DDGS")
def test_search_code(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_code_fn("read csv", language="python")

    call_args = mock_ddgs.text.call_args
    assert "python read csv" in call_args[0][0]
    assert results == FAKE_RESULTS


@patch("main.DDGS")
def test_search_error(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_error_fn("ModuleNotFoundError", language="python")

    call_args = mock_ddgs.text.call_args
    assert "python ModuleNotFoundError" in call_args[0][0]
    assert results == FAKE_RESULTS


@patch("main.DDGS")
def test_search_docs(mock_ddgs):
    mock_ddgs.return_value.__enter__ = MagicMock(return_value=mock_ddgs)
    mock_ddgs.return_value.__exit__ = MagicMock(return_value=False)
    mock_ddgs.text.return_value = FAKE_RESULTS

    results = search_docs_fn("fastapi", topic="routing")

    mock_ddgs.text.assert_called_once_with("fastapi routing documentation", max_results=5)
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
