import logging
import os
import re

import httpx
from bs4 import BeautifulSoup
from fastmcp import FastMCP
from ddgs import DDGS
from markdownify import markdownify as _to_markdown

from config import CODE_SITES

logger = logging.getLogger(__name__)

_SEARXNG_URL = os.environ.get("SEARXNG_URL", "").rstrip("/")

mcp = FastMCP("duck-search")


def _site_query(query: str, sites: tuple[str, ...]) -> str:
    """Build a search query scoped to specific sites."""
    site_filter = " OR ".join(f"site:{s}" for s in sites)
    return f"{query} ({site_filter})"


def _search(query: str, max_results: int, categories: str = "general") -> list[dict]:
    """Route a search to SearXNG or DuckDuckGo depending on SEARXNG_URL."""
    if _SEARXNG_URL:
        try:
            params = {"q": query, "format": "json", "categories": categories}
            with httpx.Client(follow_redirects=True, timeout=15) as client:
                response = client.get(f"{_SEARXNG_URL}/search", params=params)
                response.raise_for_status()
            results = response.json().get("results", [])[:max_results]
            return [
                {"title": r.get("title", ""), "href": r.get("url", ""), "body": r.get("content", "")}
                for r in results
            ]
        except Exception as exc:
            logger.warning("SearXNG nicht erreichbar (%s: %s) → Fallback auf DuckDuckGo", type(exc).__name__, exc)
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for anything that is not a programming question
    (use search_code for those). Returns short snippets only — you MUST
    call fetch_page on the best result's href before answering; never
    answer from the snippet body alone.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).
    """
    return _search(query, max_results)


@mcp.tool()
def search_code(
    query: str,
    language: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for anything programming-related: code, errors, docs, dependencies.
    Use this instead of web_search for programming questions. Returns short
    snippets only — you MUST call fetch_page on the best result's href
    before answering; never answer from the snippet body alone.

    Args:
        query: The programming-related query, e.g. "python read csv file" or
               "ModuleNotFoundError: No module named 'foo'".
        language: Optional language/framework to prepend, e.g. "python".
        max_results: Maximum number of results to return (default 5).
    """
    full_query = f"{language} {query}".strip() if language else query
    return _search(_site_query(full_query, CODE_SITES), max_results)


_STRIP_TAGS = ["script", "style", "head", "nav", "footer", "header", "noscript"]


@mcp.tool()
def fetch_page(url: str, max_chars: int = 8000) -> str:
    """Load a web page and return its content as Markdown.

    Use this after web_search or search_code: pick the best result's URL
    and pass it here to load and show the full page to the user.

    Args:
        url: The URL of the page to fetch.
        max_chars: Maximum number of characters to return (default 8000).

    Returns:
        The page content converted to Markdown, or an error message.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mcp-duck-search/1.0)"}
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Error fetching page: {exc}"

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        import json as _json
        try:
            return f"```json\n{_json.dumps(response.json(), indent=2, ensure_ascii=False)}\n```"[:max_chars]
        except Exception:
            return response.text[:max_chars]
    if content_type and not any(t in content_type for t in ("text/html", "text/plain")):
        return f"Unsupported content type: {content_type}"
    if "text/plain" in content_type:
        return response.text[:max_chars]

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    markdown = _to_markdown(str(soup), heading_style="ATX")
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return markdown[:max_chars]
