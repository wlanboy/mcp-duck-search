# MCP Duck Search

Ein MCP-Server (Model Context Protocol) auf Basis von [FastMCP](https://gofastmcp.com), der LLM-Modellen die Internetsuche über [DuckDuckGo](https://duckduckgo.com/) ermöglicht — optimiert fuer Code-, Fehler- und Dokumentationssuche.

## Tools

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         MCP Duck Search Server                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
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
│                               ▼                                          │
│                      ┌────────────────┐                                  │
│                      │   DuckDuckGo   │                                  │
│                      │   Search API   │                                  │
│                      └────────────────┘                                  │
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

```
┌──────────────┐     MCP (stdio)     ┌──────────────────┐     HTTPS     ┌──────────────┐
│              │ ──────────────────▶  │                  │ ────────────▶ │              │
│  LLM Studio  │     Tool Call        │  MCP Duck Search │    Query      │  DuckDuckGo  │
│  (Client)    │ ◀──────────────────  │  (Server)        │ ◀──────────── │              │
│              │     Ergebnisse       │                  │  Resultate    │              │
└──────────────┘                      └──────────────────┘               └──────────────┘
```

1. Das LLM erkennt, dass es eine Internetsuche braucht
2. Es ruft das passende Tool via MCP auf (z.B. `search_error` bei einem Fehler)
3. Der MCP-Server sucht über DuckDuckGo und gibt die Ergebnisse zurueck
4. Das LLM verarbeitet die Ergebnisse und antwortet dem Nutzer

## Voraussetzungen

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
uv sync
```

## Server starten

### Stdio-Transport (Standard fuer MCP-Clients)

```bash
uv run python main.py
```

### SSE-Transport (HTTP-Server via Uvicorn)

```bash
uv run uvicorn main:mcp.sse_app --host 0.0.0.0 --port 8000
```

## MCP-Client Konfiguration

### Stdio (LM Studio / Claude Desktop)

```json
{
  "mcpServers": {
    "duck-search": {
      "command": "uv",
      "args": ["run", "--directory", "/pfad/zu/mcp-duck-search", "python", "main.py"]
    }
  }
}
```

### SSE (HTTP)

```json
{
  "mcpServers": {
    "duck-search": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```
