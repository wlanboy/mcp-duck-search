# MCP Duck Search

Ein MCP-Server (Model Context Protocol) auf Basis von [FastMCP](https://gofastmcp.com), der LLM-Modellen die Internetsuche ermöglicht — optimiert fuer Code-, Fehler- und Dokumentationssuche.

Als Such-Backend wird automatisch **SearXNG** verwendet, wenn die Umgebungsvariable `SEARXNG_URL` gesetzt ist, andernfalls **DuckDuckGo**.

## Tools

```txt
┌───────────────────────────────────────────────────────────────────────────┐
│                         MCP Duck Search Server                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ web_search   │  │ search_code  │  │ search_error │  │ search_spring │  │
│  │              │  │              │  │              │  │ _boot         │  │
│  │ Allgemeine   │  │ Code &       │  │ Fehler &     │  │ Spring Boot   │  │
│  │ Websuche     │  │ Beispiele    │  │ Exceptions   │  │ Ecosystem     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                 │                  │          │
│         │    ┌────────────┴──┐  ┌───────────┴──┐               │          │
│         │    │ search_docs   │  │ web_search_  │               │          │
│         │    │               │  │ news         │               │          │
│         │    │ Offizielle    │  │              │               │          │
│         │    │ Dokumentation │  │ Nachrichten  │               │          │
│         │    └───────┬───────┘  └──────┬───────┘               │          │
│         │            │                 │                       │          │
│         └────────────┴────────┬────────┴───────────────────────┘          │
│                               ▼                                           │
│          ┌──────────────────────────────────────────────┐                 │
│          │  Such-Backend (via SEARXNG_URL konfiguriert) │                 │
│          │                                              │                 │
│          │  SEARXNG_URL gesetzt  →  SearXNG (selfhosted)│                 │
│          │  SEARXNG_URL leer     →  DuckDuckGo          │                 │
│          └──────────────────────────────────────────────┘                 │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

| Tool | Beschreibung | Site-Filter |
|---|---|---|
| `web_search` | Allgemeine Websuche | Keine |
| `search_code` | Code-Beispiele & Programmierlösungen | GitHub, MDN, Dev.to, offizielle Docs |
| `search_error` | Fehler, Exceptions & Stack Traces | GitHub Issues/Discussions, Reddit, Bugtracker |
| `search_spring_boot` | Spring Boot Guides, Configs & Best Practices | spring.io, Baeldung, Reflectoring, GitHub Spring Projects |
| `search_docs` | Offizielle Dokumentation nachschlagen | Keine (findet alle Docs) |
| `web_search_news` | Aktuelle Nachrichten | Keine |

## Workflow

```txt
┌──────────────┐     MCP (stdio)      ┌──────────────────┐     HTTPS     ┌──────────────────┐
│              │ ──────────────────▶  │                  │ ────────────▶ │ SearXNG          │
│  LLM Studio  │     Tool Call        │  MCP Duck Search │    Query      │ (wenn SEARXNG_URL│
│  (Client)    │ ◀──────────────────  │  (Server)        │ ◀──────────── │ gesetzt)         │
│              │     Ergebnisse       │                  │  Resultate    ├──────────────────┤
└──────────────┘                      └──────────────────┘               │ DuckDuckGo       │
                                                                         │ (Fallback)       │
                                                                         └──────────────────┘
```

1. Das LLM erkennt, dass es eine Internetsuche braucht
2. Es ruft das passende Tool via MCP auf (z.B. `search_error` bei einem Fehler)
3. Der MCP-Server leitet die Suche an SearXNG (wenn `SEARXNG_URL` gesetzt) oder DuckDuckGo weiter
4. Das LLM verarbeitet die Ergebnisse und antwortet dem Nutzer

## Such-Backend

| Umgebungsvariable | Wert | Backend |
|---|---|---|
| `SEARXNG_URL` | nicht gesetzt | DuckDuckGo (Standard) |
| `SEARXNG_URL` | `http://your-searxng:8080` | SearXNG (selfhosted) |

SearXNG benötigt eine `settings.yml`, um das JSON-Format zu aktivieren (standardmäßig deaktiviert):

```yaml
# searxng/settings.yml
search:
  formats:
    - html
    - json
```

```bash
docker run -d --name searxng \
  -p 8880:8080 \
  -v ./searxng:/etc/searxng \
  searxng/searxng
```

> **Hinweis:** Redis ist optional. Für den lokalen Einsatz nicht notwendig.

## Voraussetzungen

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
uv lock --upgrade
uv sync
uv run pytest
uv run pyright
uv run ruff check

uv pip compile pyproject.toml -o requirements.txt
```

## Server starten

### Stdio-Transport (Standard fuer MCP-Clients)

```bash
uv run main.py
```

## MCP-Client Konfiguration

### Stdio (LM Studio / Claude Desktop)

```json
{
  "mcpServers": {
    "duck-search": {
      "command": "uv",
      "args": ["run", "--directory", "/pfad/zu/mcp-duck-search", "main.py"],
      "env": {
        "SEARXNG_URL": "http://gmk:8880"
      }
    }
  }
}
```

### SSE (HTTP)

`SEARXNG_URL` wird hier server-seitig konfiguriert (siehe Docker-Abschnitt).

```json
{
  "mcpServers": {
    "duck-search": {
      "url": "http://localhost:9900/sse"
    }
  }
}
```

## Docker

```bash
# Build
docker build -t mcp-duck-search .

# Run with duckduckgo backend
docker run --rm --name mcp-duck -p 9900:9900 mcp-duck-search

# Run with your own searxng backend
docker run --rm --name mcp-duck -p 9900:9900 -e SEARXNG_URL=http://gmk:8880 mcp-duck-search
```
