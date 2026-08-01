# CLI Companion Tool Pattern

Add a standalone CLI alongside your MCP server so users can query and import without an MCP client.

## Architecture

```python
# src/<package>/cli.py
import argparse, sys, json
from pathlib import Path
from <package>.db import init_db, get_db_path, ...  # Reuse all existing DB modules

def _get_conn():
    return init_db(get_db_path())

def cmd_list(args):
    db = _get_conn()
    sessions = list_sessions(db, limit=args.limit)
    for s in sessions:
        print(f"{s.id[:24]} {s.title[:50]}")

def main():
    parser = argparse.ArgumentParser(prog="<name>")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list", help="List items")
    p.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    {"list": cmd_list}[args.command](args)
```

## Key rules

1. **No code duplication** — CLI calls the same `db/` functions as the MCP server. Never duplicate business logic.
2. **Argparse only** — stdlib, zero extra dependencies. Save click/etc. for projects that already have it.
3. **Invoke as module** — `python -m <package>.cli <command>` (not `python -m <package>` which runs the server).
4. **Same config** — `get_db_path()` reads the same env vars as the server. The DB is always shared.
5. **Human-readable output** — tables and formatted text, not raw JSON. JSON is for the MCP server.
6. **Test via subprocess** — `subprocess.run([sys.executable, "-m", "<package>.cli", "cmd"])` in tests.

## Test pattern

```python
def _run(*args, **env):
    cmd = [sys.executable, "-m", "<package>.cli", *args]
    return subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, **env})

class TestCLI:
    def test_help(self):
        r = _run("--help")
        assert r.returncode == 0
        for cmd in ["list", "get", "search"]:
            assert cmd in r.stdout

    def test_list_empty(self, db_path):
        r = _run("list")
        assert "No items" in r.stdout
```

## When to add

- The MCP server has >2 CRUD tools and a user might want quick lookups without an MCP client
- The project already has a working `db/` package — the CLI is just a thin presentation layer
