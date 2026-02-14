from fastmcp import FastMCP
from ddgs import DDGS

mcp = FastMCP("duck-search")

CODE_SITES = (
    "github.com",
    "dev.to",
    "developer.mozilla.org",
    "docs.python.org",
    "learn.microsoft.com",
    "medium.com",
    "reddit.com/r/programming",
    "reddit.com/r/learnprogramming",
)

ERROR_SITES = (
    "github.com/issues",
    "github.com/discussions",
    "reddit.com",
    "bugs.python.org",
    "github.com/spring-projects/spring-boot/issues",
    "github.com/spring-projects/spring-framework/issues",
    "github.com/spring-cloud",
)

SPRING_SITES = (
    "spring.io",
    "docs.spring.io",
    "github.com/spring-projects",
    "github.com/spring-cloud",
    "spring.io/projects/spring-cloud",
    "cloud.spring.io",
    "reflectoring.io",
    "thorben-janssen.com",
    "vladmihalcea.com",
    "piotrminkowski.com",
)


def _site_query(query: str, sites: tuple[str, ...]) -> str:
    """Build a DuckDuckGo query scoped to specific sites."""
    site_filter = " OR ".join(f"site:{s}" for s in sites)
    return f"{query} ({site_filter})"


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the internet using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of search results with title, href, and body.
    """
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


@mcp.tool()
def search_code(
    query: str,
    language: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for code examples, solutions, and programming documentation.

    Use this tool when you need to find code snippets, API usage examples,
    or programming how-tos. Results are scoped to developer sites like
    StackOverflow, GitHub, MDN, and official docs.

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
    with DDGS() as ddgs:
        return list(ddgs.text(
            _site_query(full_query, CODE_SITES),
            max_results=max_results,
        ))


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
    full_query = f"{language} {error_message}".strip() if language else error_message
    with DDGS() as ddgs:
        return list(ddgs.text(
            _site_query(f'"{full_query}"', ERROR_SITES),
            max_results=max_results,
        ))


@mcp.tool()
def search_docs(
    library: str,
    topic: str = "",
    max_results: int = 5,
) -> list[dict]:
    """Search for official documentation of a library, framework, or tool.

    Use this tool when you need to look up API references, configuration
    options, or usage guides for a specific technology.

    Args:
        library: The library or framework name (e.g. "fastapi", "react", "spring boot").
        topic: Optional specific topic within the docs (e.g. "routing", "middleware").
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of documentation search results.
    """
    query = f"{library} {topic} documentation".strip()
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


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
    with DDGS() as ddgs:
        return list(ddgs.text(
            _site_query(full_query, SPRING_SITES),
            max_results=max_results,
        ))


@mcp.tool()
def web_search_news(query: str, max_results: int = 5) -> list[dict]:
    """Search for recent news articles using DuckDuckGo.

    Args:
        query: The search query string.
        max_results: Maximum number of results to return (default 5).

    Returns:
        A list of news results with title, url, body, date, and source.
    """
    with DDGS() as ddgs:
        return list(ddgs.news(query, max_results=max_results))


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9900, path="/sse")
