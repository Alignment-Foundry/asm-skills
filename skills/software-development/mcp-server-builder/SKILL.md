---
name: mcp-server-builder
description: "Use when building a new MCP (Model Context Protocol) server from scratch. Provides architecture pattern, server setup, DB layer, testing, and Dockerfile — derived from the {private-repo-convo-label} project."
version: 1.1.0
author: Alpha
license: MIT
metadata:
  hermes:
    tags: [mcp, servers, python, sqlite, protocol]
    related_skills: [efficient-operation, plan, test-driven-development]
---

# MCP Server Builder

## Overview

Build a Model Context Protocol (MCP) server using the `mcp` Python SDK. This skill captures the canonical pattern from the {private-repo-convo-label} project — a modular, testable MCP server with SQLite persistence, FTS5 search, Pydantic models, and Docker deployment.

The pattern is: **one server.py file** for all MCP wiring (tool listing + tool dispatch), **one db/ package** for persistence (schema, models, CRUD, search), and **one tests/ directory** with unit tests + MCP client integration tests.

## When to Use

- Building a new MCP server from scratch (stdio transport, Python SDK)
- Adding MCP tool support to an existing CLI/data project
- Teaching the canonical MCP server structure

**Don't use for:** wrapping an existing HTTP API as MCP (use a lightweight reverse proxy instead). Don't use for non-Python MCP servers.

## Architecture Pattern

```
<project-name>/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── __main__.py       # Entry: async def main() -> run_stdio()
│   ├── server.py          # MCP server: Server(), list_tools(), call_tool()
│   ├── config.py          # pydantic-settings (env var config)
│   └── db/
│       ├── __init__.py    # Re-export everything
│       ├── models.py      # Pydantic data models (input types, result types)
│       ├── schema.py      # SQLite DDL + init_db() function
│       ├── sessions.py    # CRUD operations (create, get, list, delete)
│       └── search.py      # FTS5 search layer (optional)
├── tests/
│   ├── __init__.py
│   ├── test_db.py         # Unit tests for DB layer
│   ├── test_server.py     # Integration tests via MCP ClientSession
│   └── test_cli.py        # Tests for CLI companion (if applicable)
└── Dockerfile
```

### Extended tree — multi-phase MCP project (Phases 2-4 extras)

```
├── docker-compose.yml       # Sidecar deployment alongside other MCP servers
├── src/
│   ├── cli.py               # Standalone CLI (argparse) — ad-hoc queries without MCP
│   ├── exporters.py         # Export registry — reconstruct stored data in multiple formats
│   ├── tagging.py           # Auto-tagging heuristics on import
│   └── adaptors/            # Import pipeline — pluggable format detectors/parsers
└── tests/
    └── fixtures/            # Sample input files for integration tests
```

### Task-first workflow (write tasks before code)

Each phase starts with task files in `ai-docs/tasks/TNNN-*.md`. Every task has:
- A **goal** (one sentence)
- **Acceptance criteria** as `[ ]` checkboxes
- **Implementation notes** with file paths

One task = one logical change = one incremental commit. No code without a task file.

### pyproject.toml — Dependencies

```toml
[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.scripts]
<cli-name> = "<package>.__main__:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["src"]
```

## MCP Server Setup

### server.py — Core Pattern

```python
"""MCP server for <project>."""

from __future__ import annotations

import json  # ← module-level, NOT inline — see pitfall #1
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

server = Server("<server-name>")

# ── Tool Registration ────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="<tool_name>",
            description="<clear one-line description>",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "..."},
                    "param2": {"type": "integer", "default": 20},
                },
                "required": ["param1"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "<tool_name>":
        # ... business logic ...
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    raise ValueError(f"Unknown tool: {name}")

# ── Stdio Entry ───────────────────────────────────────────────────────────────────

async def run_stdio() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())
```

### config.py — pydantic-settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    my_db_path: str = ""
    model_config = {"env_prefix": ""}

settings = Settings()
```

### __main__.py — CLI Entry

```python
import asyncio, logging, sys
from my_package.server import run_stdio

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

def main():
    asyncio.run(run_stdio())

if __name__ == "__main__":
    main()
```

## SQLite Database Layer

### schema.py — DDL + init_db

```python
import sqlite3, os
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS items (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""

def get_default_db_path() -> str:
    home = Path.home()
    db_dir = home / ".<project>"
    db_dir.mkdir(parents=True, exist_ok=True)
    return str(db_dir / "store.db")

def get_db_path(override: str | None = None) -> str:
    if override:
        return override
    env_path = os.environ.get("<PROJECT>_DB_PATH")
    return env_path or get_default_db_path()

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn
```

### models.py — Pydantic Models

Use Pydantic v2 with `BaseModel`, `Field`, `field_validator`. Use UUIDv4 strings for all IDs:

```python
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
```

### FTS5 for Search (optional)

Create a virtual table for full-text search in `schema.py`:

```python
SCHEMA_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    content,
    title,
    tokenize='porter unicode61'
);
"""
```

Use triggers to keep FTS in sync:
```sql
CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, content, title)
    VALUES (new.rowid, new.content, '...');
END;
```

**⚠️ Critical FTS5 detail:** Use `DELETE FROM items_fts WHERE rowid = ?` for deletes, NOT the `INSERT INTO ft(ft, rowid) VALUES('delete', ?)` syntax (that's only for external-content tables). See `references/fts5-standalone-pattern.md` for the complete working standalone FTS5 setup with all triggers (INSERT, DELETE, UPDATE, cross-table title sync).

### Internal helper pattern for CRUD

Always use `conn.row_factory = sqlite3.Row` for dict-like access. Use `contextlib` or explicit connection passing. Never use an ORM — raw SQLite is simpler and adequate for single-process MCP servers.

## Testing

### Unit tests (test_db.py)

```python
import os, tempfile, pytest, sqlite3
from my_package.db import init_db

@pytest.fixture
def db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = init_db(path)
    yield conn
    conn.close()
    os.unlink(path)
```

### MCP integration tests (test_server.py)

```python
import json, os, tempfile
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.fixture
async def client():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "my_package"],
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

@pytest.mark.asyncio
async def test_list_tools(client: ClientSession):
    result = await client.list_tools()
    tool_names = [t.name for t in result.tools]
    assert "my_tool" in tool_names

@pytest.mark.asyncio
async def test_call_tool(client: ClientSession):
    result = await client.call_tool("my_tool", {"param": "value"})
    data = json.loads(result.content[0].text)
    assert "expected_field" in data
```

**Note:** The `stdio_client` fixture produces teardown noise (`RuntimeError: Attempted to exit cancel scope...`) from the MCP SDK's async context manager. This is harmless — the tests themselves pass correctly. Use `--tb=short` to suppress the noise.

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -e . && \
    rm -rf /root/.cache/pip

USER appuser

# Stdio transport — pipe into the MCP client
CMD ["python", "-m", "my_package"]
```

## Tool Design Conventions

1. **Snake case tool names** — e.g. `store_session`, `get_item`, `search_records`
2. **Clear descriptions** — they're what MCP clients show users. "Store a new session with turns and tags" > "Store session"
3. **JSON Schema input types** — use raw dicts for `inputSchema`, not Pydantic model schemas. MCP clients expect raw JSON Schema.
4. **`default` for optional params** — set sensible defaults (e.g. `limit: 20` for list operations)
5. **Return structured JSON** — always `json.dumps(result, indent=2)` wrapped in `TextContent`
6. **Return error strings for not-found** — don't raise exceptions for missing entities; return `"Session not found: {id}"` as text

## Adaptor / Registry Pattern (Optional)

When the MCP server needs to handle multiple input formats (import pipelines, format detection), use a variant of the registry pattern:

```
adaptors/
├── __init__.py   # Imports all adaptors so they self-register, exports REGISTRY
├── base.py       # BaseAdaptor ABC + AdaptorRegistry singleton + register decorator
├── format_a.py   # @register("format_a") class FormatAAdaptor(BaseAdaptor): ...
├── format_b.py   # @register("format_b") ...
```

**Key design decisions:**

1. **ABC with two methods** — `detect(raw_text) -> float` (confidence 0.0-1.0) and `parse(raw_text) -> ImportedSession`. Each adaptor scores text and only parses when confidence > threshold.

2. **Self-registering via decorator** — `@register("name")` on the class, combined with a bare import of the module in `__init__.py` (`import adaptors.format_a  # noqa: F401`). No wiring changes needed to add a format.

3. **Auto-detect** — `REGISTRY.detect(text)` iterates all registered adaptors, returns (name, instance) of the highest scorer above 0.5 threshold, or None.

4. **Explicit override** — tool callers can pass an explicit adaptor name, bypassing detection.

**When to use:** your MCP server accepts free-form input that could be in multiple formats (session imports, document ingestion, data format conversion).

**When to skip:** single-format servers, or servers where the format is always known in advance.

See the `{private-repo-convo}` project at `{projects}/{private-repo-convo}/src/{private-repo-convo}/adaptors/` for a complete reference implementation with Hermes, Claude, and ChatGPT adaptors.

## Search Enhancement Patterns (Optional)

When your MCP server includes FTS5 search, two optional enhancements improve result quality for temporal data (conversations, logs, documents):

1. **Recency-boosted BM25 ranking** — gently favours newer results when relevance is similar. Formula: `ORDER BY rank - (1.0 / (1.0 + days_old)) * 0.5`
2. **Result context windowing** — include ±N turns around the matched turn with an `is_match` flag for client-side highlighting.

Both are zero-cost opt-ins (default 0 — existing callers unaffected). See `references/search-enhancements.md` for the full implementation, SQL formulas, Python integration, and test patterns.

### CLI Companion (Optional)

Add a standalone CLI for ad-hoc queries without an MCP client. Reuses the same `db/` modules — zero duplication. Uses stdlib argparse. See `references/cli-companion-pattern.md` for the full pattern.

### Export Registry & Auto-Tagging (Optional)

When your server exports stored data in multiple formats, mirror the adaptor registry for output. Same pattern, reversed direction. Auto-tag imported data with origin metadata. See `references/export-tagging-patterns.md` for both patterns.

### Import Block / Partial Import (Optional)

When your server accepts multi-turn transcripts and users want only a subset, add an `import_block` tool that:
1. Parses with the same adaptor as full import
2. Slices `turns[turn_start:turn_end]` (0-based, exclusive end)
3. Optionally expands with a `context_window` (±N turns clamped to bounds)
4. Creates a new session with just the sliced turns

The context window expansion formula: `window_start = max(0, turn_start - context_window)` and `window_end = min(total, turn_end + context_window)`.

## Config via Environment Variables

Use `pydantic-settings` with `env_prefix=""` so env vars like `MYAPP_DB_PATH="/custom/path.db"` override defaults. Document env vars in the skill's `.hermes.md` Runbook section.

## Common Pitfalls

1. **Inline `import json` in `call_tool()` causes runtime scoping errors** — Never put `import json` (or any import) inside the `call_tool()` function body. Python treats it as a local variable, shadowing the module-level `import json`. If a code path before the inline import (like another tool handler) references `json`, you'll get `UnboundLocalError: cannot access local variable 'json' where it is not associated with a value`. Always put `import json` at the top of `server.py`.
2. **`python -m my_package` fails with "No module named __main__"** — Always create `__main__.py` before any server test, since the integration test spawns the server via `python -m`.
3. **FTS5 delete syntax on regular tables** — For regular FTS5 tables (no `content=` parameter), use `DELETE FROM ftstable WHERE rowid = ?` to remove entries, NOT `INSERT INTO ftstable(ftstable, rowid) VALUES('delete', ?)` (that syntax is only for external-content tables).
4. **MCP fixture teardown noise** — `stdio_client` + `ClientSession` produces cancel-scope errors during teardown. All tests pass correctly. Use `--tb=short` or `pytest -W ignore::RuntimeWarning`.
5. **`inputSchema` as raw dicts** — Don't pass Pydantic model `schema()` output directly. Hand-write the JSON Schema dicts for clarity and MCP client compatibility.
6. **Setting `content=` on FTS5 tables** — If you don't need external content sync, just omit the `content=` parameter for a standard FTS5 table.
7. **Missing `asyncio_mode = "auto"`** — Without this in `pyproject.toml`, async tests won't auto-await coroutines and will silently pass without testing anything.
8. **`session_id` collisions** — Always use UUIDv4 strings for IDs (stdlib `uuid.uuid4()`). Never use auto-increment integers — they break cross-instance sync.

## Verification Checklist

- [ ] `python -c "import my_package"` succeeds
- [ ] `python -m my_package` starts the MCP server (stdio)
- [ ] `pytest tests/ -v --tb=short` — all tests pass (ignore fixture teardown noise)
- [ ] `docker build -t <name> .` succeeds
- [ ] `docker run --rm <name>` starts the server (verify via MCP client)
- [ ] Every tool has a clear `description` field in its `Tool()` definition
- [ ] All tool names use snake_case
- [ ] Optional input params have sensible `default` values
- [ ] Config is settable via env vars (pydantic-settings)
- [ ] SQLite uses WAL mode + foreign_keys=ON
- [ ] UUIDv4 for all primary keys
- [ ] `.hermes.md` Runbook section filled with run/test/build/dependencies info
