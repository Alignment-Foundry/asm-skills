# SQLite FTS5 Patterns for CLI Tools

When building a CLI/MCP tool that needs full-text search across structured data, SQLite's built-in FTS5 is the zero-infrastructure choice — no external search service, no API keys, works offline.

## Standalone vs Content-Sync Tables

Two ways to use FTS5:

### Standalone (preferred for cross-table search)

Create the FTS5 table WITHOUT a `content=` parameter. This gives full control over columns and avoids the column-mapping issues of content-sync:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
    content,       -- searchable column
    session_title, -- another searchable column
    tokenize='porter unicode61'
);
```

**Manage manually with triggers.** Use regular `DELETE` + `INSERT` (not the special 'delete' insert syntax):

```sql
-- Insert
CREATE TRIGGER IF NOT EXISTS turns_ai AFTER INSERT ON turns BEGIN
    INSERT INTO turns_fts(rowid, content, session_title)
    VALUES (new.rowid, new.content,
            COALESCE((SELECT title FROM sessions WHERE id = new.session_id), ''));
END;

-- Delete — use regular DELETE, NOT INSERT INTO fts(fts) VALUES('delete')
CREATE TRIGGER IF NOT EXISTS turns_ad AFTER DELETE ON turns BEGIN
    DELETE FROM turns_fts WHERE rowid = old.rowid;
END;

-- Update = delete old + insert new
CREATE TRIGGER IF NOT EXISTS turns_au AFTER UPDATE ON turns BEGIN
    DELETE FROM turns_fts WHERE rowid = old.rowid;
    INSERT INTO turns_fts(rowid, content, session_title)
    VALUES (new.rowid, new.content,
            COALESCE((SELECT title FROM sessions WHERE id = new.session_id), ''));
END;
```

### Content-Sync (not recommended for cross-table)

```sql
-- Mirrors the source table's columns. Uses 'delete' insert syntax.
CREATE VIRTUAL TABLE ft USING fts5(content, content='source_table', content_rowid='rowid');
-- Delete uses: INSERT INTO ft(ft, rowid) VALUES('delete', rowid);
```

**Why standalone is better for CLI tools:**
- You control the column schema — can include data from JOINs (e.g., session title in a turns FTS index)
- No content-sync column-name mismatch errors
- `INSERT INTO ft(ft, rowid) VALUES('delete', rowid)` syntax is ONLY for contentless/external-content tables. Using it on a standalone table causes `SQL logic error` errors.
- Regular `DELETE FROM ft WHERE rowid = ?` always works on standalone tables

## Search Queries

```sql
-- Basic match
SELECT content FROM turns_fts WHERE turns_fts MATCH ?

-- Highlighted snippets
SELECT snippet(turns_fts, 0, '<mark>', '</mark>', '...', 60) as match_snippet
FROM turns_fts WHERE turns_fts MATCH ?
ORDER BY rank
LIMIT ? OFFSET ?
```

- `rank` is the BM25 relevance score (built into FTS5, lower = more relevant)
- `snippet()` args: column_index (0-based), open tag, close tag, ellipsis, max_length

## Joining Back to Source Tables

FTS5 `rowid` matches the source table's `rowid` (not your primary key). Join on that:

```sql
SELECT s.id, s.title, snippet(turns_fts, 0, '<mark>', '</mark>', '...', 60)
FROM turns_fts
JOIN turns t ON t.rowid = turns_fts.rowid
JOIN sessions s ON s.id = t.session_id
WHERE turns_fts MATCH ?
ORDER BY rank
LIMIT ? OFFSET ?
```

## Filtered Search (FTS + structured filters)

Add WHERE extra conditions after the FTS match:

```sql
SELECT s.*, rank
FROM turns_fts
JOIN turns t ON t.rowid = turns_fts.rowid
JOIN sessions s ON s.id = t.session_id
WHERE turns_fts MATCH ?
  AND s.agent = ?
  AND s.created_at >= ?
ORDER BY rank
```

## CASCADE Delete with FTS Triggers

When a parent row is deleted with `ON DELETE CASCADE`, child rows' triggers fire automatically. The `turns_ad` trigger handles FTS cleanup — no manual FTS management needed in your delete logic:

```python
def delete_session(db, session_id):
    # Just delete the parent. Cascade + triggers handle the rest.
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
    return db.execute("SELECT changes() as cnt").fetchone()["cnt"] > 0
```

## Checking Delete Success

`db.total_changes` is cumulative — it counts ALL changes since the connection opened, not just the last statement. Use `SELECT changes()` instead:

```python
db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
db.commit()
deleted = db.execute("SELECT changes() as cnt").fetchone()["cnt"] > 0
```

## Using COALESCE in Triggers

When a trigger references a JOINed value (e.g., session title in a turns trigger), the session might not have a title yet. Use `COALESCE` for a safe fallback:

```sql
COALESCE((SELECT title FROM sessions WHERE id = new.session_id), '')
```

## Cross-Table FTS Trigger for Title Updates

When a session title changes, re-sync ALL turns in that session:

```sql
CREATE TRIGGER IF NOT EXISTS sessions_bu AFTER UPDATE OF title ON sessions BEGIN
    DELETE FROM turns_fts WHERE rowid IN (
        SELECT rowid FROM turns WHERE session_id = old.id
    );
    INSERT INTO turns_fts(rowid, content, session_title)
    SELECT turns.rowid, turns.content, new.title
    FROM turns WHERE turns.session_id = old.id;
END;
```

## FTS Query Sanitization

Bare special characters in FTS queries (`^ * ( ) " ~ + -`) can cause syntax errors. For simple queries (no AND/OR/NOT operators), clean them:

```python
import re

def fts_escape(query: str) -> str:
    if not query.strip():
        return query
    # If it already has boolean operators, pass through (advanced query)
    if re.search(r'\b(AND|OR|NOT)\b', query, re.IGNORECASE):
        return query
    # Wrap in double quotes if it contains special chars
    if re.search(r'[()"*^~+]', query):
        clean = re.sub(r'[()"*^~+]', ' ', query)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return f'"{clean}"'
    return query
```

## Common Pitfalls

1. **Using 'delete' insert syntax on a standalone FTS5 table** → `sqlite3.OperationalError: SQL logic error`. Use `DELETE FROM fts WHERE rowid = ?` instead.
2. **Using `content='turns'` when you need columns from another table** → FTS5 mirrors the source table's columns; you can't add session_title to a turns-synced FTS table. Use standalone instead.
3. **`CREATE TRIGGER IF NOT EXISTS` won't replace a bad trigger** — if you created the wrong trigger in a previous run, the `IF NOT EXISTS` silently skips it. Drop and recreate, or use a fresh database for tests.
4. **Forgetting to use `PRAGMA foreign_keys=ON`** — every connection that needs FK enforcement must set this. It's per-connection, not stored in the DB file. WAL mode is also per-connection but can be stored in the journal_mode pragma (WAL persists to the DB file).
5. **`db.total_changes` is cumulative** — use `SELECT changes()` for per-operation row counts.
