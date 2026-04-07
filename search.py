import logging
import os
import re
from html.parser import HTMLParser

import httpx
from fastmcp import FastMCP
from ddgs import DDGS

from config import CODE_SITES, DOCS_SITES, ERROR_SITES, MAVEN_SITES, SPRING_SITES

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


def _search_news(query: str, max_results: int) -> list[dict]:
    """Route a news search to SearXNG or DuckDuckGo depending on SEARXNG_URL."""
    if _SEARXNG_URL:
        return _search(query, max_results, categories="news")
    with DDGS() as ddgs:
        return list(ddgs.news(query, max_results=max_results))


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the internet using DuckDuckGo. Use this tool for general-purpose
    queries that do not fit a more specific tool: current events, comparisons,
    product information, or anything that is not a code example, error message,
    official docs lookup, or Spring Boot question. Prefer the specialised
    search_* tools whenever the topic matches their scope, because they return
    higher-quality results by restricting to trusted sites.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results with title, href, and body.
    """
    return _search(query, max_results)


@mcp.tool()
def search_code(
    query: str,
    language: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for code examples, solutions, and programming documentation.

    Use this tool when you need to find code snippets, API usage examples,
    or programming how-tos. Results are scoped to developer sites like
    GitHub, MDN, and official docs.

    Args:
        query: The code-related search query (e.g. "python read csv file",
               "react useEffect cleanup").
        language: Optional programming language to prepend to the query
                  (e.g. "python", "javascript", "rust").
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results from developer-focused sites.
    """
    full_query = f"{language} {query}".strip() if language else query
    return _search(_site_query(full_query, CODE_SITES), max_results)


@mcp.tool()
def search_error(
    error_message: str,
    language: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for solutions to error messages, exceptions, and stack traces.

    Use this tool when encountering an error message or exception.
    Pass the core error message (without file paths or line numbers).
    Results are scoped to sites where developers discuss and resolve errors.

    Args:
        error_message: The error message or exception text
                       (e.g. "TypeError: Cannot read properties of undefined",
                        "ModuleNotFoundError: No module named 'foo'").
        language: Optional programming language or framework context
                  (e.g. "python", "spring boot", "react").
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results with potential fixes and explanations.
    """
    quoted_error = f'"{error_message}"'
    full_query = f"{language} {quoted_error}".strip() if language else quoted_error
    return _search(_site_query(full_query, ERROR_SITES), max_results)


@mcp.tool()
def search_docs(
    library: str,
    topic: str = "",
    site: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for official documentation of a library, framework, or tool.

    Use this tool when you need to look up API references, configuration
    options, or usage guides for a specific technology. Results are scoped
    to common documentation platforms (ReadTheDocs, MDN, pkg.go.dev, etc.).

    Args:
        library: The library or framework name (e.g. "fastapi", "react", "spring boot").
        topic: Optional specific topic within the docs (e.g. "routing", "middleware").
        site: Optional specific documentation site to restrict results to
              (e.g. "fastapi.tiangolo.com", "docs.djangoproject.com").
              If omitted, searches across common documentation platforms.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of documentation search results.
    """
    query = f"{library} {topic}".strip()
    sites = (site,) if site else DOCS_SITES
    return _search(_site_query(query, sites), max_results)


@mcp.tool()
def search_spring_boot(
    query: str,
    version: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for Spring Boot guides, configurations, and best practices.

    Use this tool for anything related to the Spring ecosystem: Spring Boot,
    Spring Security, Spring Data, Spring Cloud, etc. Results are scoped to
    spring.io, Baeldung, and other trusted Spring resources.

    Args:
        query: The Spring-related search query (e.g. "custom auto-configuration",
               "JPA repository pagination", "WebClient timeout").
        version: Optional Spring Boot version to narrow results
                 (e.g. "3.4", "3.3").
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results from Spring-focused sites.
    """
    parts = ["spring boot"]
    if version:
        parts.append(version)
    parts.append(query)
    full_query = " ".join(parts)
    return _search(_site_query(full_query, SPRING_SITES), max_results)


@mcp.tool()
def search_maven(
    artifact: str,
    group_id: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for Maven / Gradle dependencies on Maven Central and MVN Repository.

    Use this tool when you need to find a Java or Kotlin library, check the
    latest version of an artifact, or look up Gradle plugin coordinates.

    Args:
        artifact: The artifact name or search term
                  (e.g. "spring-boot-starter-web", "jackson-databind").
        group_id: Optional Maven group ID to narrow results
                  (e.g. "org.springframework.boot", "com.fasterxml.jackson.core").
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results from Maven Central and related sites.
    """
    parts = []
    if group_id:
        parts.append(group_id)
    parts.append(artifact)
    return _search(_site_query(" ".join(parts), MAVEN_SITES), max_results)


@mcp.tool()
def web_search_news(query: str, max_results: int = 5) -> list[dict]:
    """Search for recent news articles using DuckDuckGo.

    Use this tool when the user asks about current events, breaking news,
    recent announcements, or any time-sensitive topic where publication date
    matters (e.g. "latest React release", "what happened with X yesterday").
    For timeless technical questions use web_search or the search_* tools instead.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of news results with title, url, body, date, and source.
    """
    return _search_news(query, max_results)


class _TextExtractor(HTMLParser):
    """Strip HTML tags and collect visible text, skipping non-content elements."""

    _SKIP_TAGS = {"script", "style", "head", "nav", "footer", "header", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_startendtag(self, tag: str, attrs: object) -> None:
        pass  # self-closing tags have no content; do not touch _skip_depth

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            stripped = data.strip()
            if stripped:
                self.parts.append(stripped)


@mcp.tool()
def fetch_page(url: str, max_chars: int = 8000) -> str:
    """Fetch and extract the plain-text content of a web page.

    Use this tool after web_search or search_* to read the full content
    of a result page for deeper analysis — for example to read an article,
    inspect a changelog, or study documentation in detail.

    Args:
        url: The URL of the page to fetch.
        max_chars: Maximum number of characters to return (default 8000).

    Returns:
        The extracted plain text of the page, or an error message.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; mcp-duck-search/1.0)"}
    try:
        with httpx.Client(follow_redirects=True, timeout=15) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Error fetching page: {exc}"

    content_type = response.headers.get("content-type", "")
    if content_type and not any(t in content_type for t in ("text/html", "text/plain")):
        return f"Unsupported content type: {content_type}"

    parser = _TextExtractor()
    parser.feed(response.text)
    text = "\n".join(parser.parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:max_chars]
