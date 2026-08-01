# FTS5 Standalone Table Pattern

Standalone FTS5 tables (no `content=` parameter) are simpler and more flexible than externally-synced tables. The key rule: **use `DELETE FROM ftstable WHERE rowid = ?`**, never the `INSERT INTO ft(ft, rowid) VALUES('delete', ?)` syntax — that only works on external-content tables.

## Schema DDL

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    content,          -- Searchable field (e.g. turn content)
    session_title,    -- Another searchable field
    tokenize='porter unicode61'
);
```

No `content=` parameter — this is a standalone table. SQLite stores the content directly.

## INSERT Trigger

```sql
CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, content, session_title)
    VALUES (new.rowid, new.content, COALESCE(
        (SELECT title FROM sessions WHERE id = new.session_id), ''
    ));
END;
```

Key: the trigger must populate ALL FTS columns. Use `COALESCE` for nullable lookups.

## DELETE Trigger — critical difference from content-sync tables

```sql
CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
    DELETE FROM turns_fts WHERE rowid = old.rowid;
END;
```

**NOT** `INSERT INTO items_fts(items_fts, rowid, content, session_title) VALUES ('delete', ...)` — that syntax only works on `content=''` (external content) tables. On standalone tables it causes "SQL logic error".

## UPDATE Trigger

```sql
CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
    DELETE FROM items_fts WHERE rowid = old.rowid;
    INSERT INTO items_fts(rowid, content, session_title)
    VALUES (new.rowid, new.content, COALESCE(
        (SELECT title FROM sessions WHERE id = new.session_id), ''
    ));
END;
```

Delete the old entry first, then insert the new one. A single trigger can't atomically replace FTS entries — always do delete + insert.

## Cross-Table Title Sync Trigger

When the session title (or other parent table field synced into FTS) changes, all child FTS entries must be refreshed:

```sql
CREATE TRIGGER IF NOT EXISTS sessions_bu AFTER UPDATE OF title ON sessions BEGIN
    DELETE FROM items_fts WHERE rowid IN (
        SELECT rowid FROM items WHERE session_id = old.id
    );
    INSERT INTO items_fts(rowid, content, session_title)
    SELECT items.rowid, items.content, new.title
    FROM items WHERE items.session_id = old.id;
END;
```

Without this trigger, updating a parent's title leaves stale search data in FTS.

## Testing the pattern

```python
def test_fts_insert_syncs(db):
    """Insert should populate the FTS table."""
    # Create parent + child record
    db.execute("INSERT INTO sessions ... VALUES ('s1', 'test title', ...)")
    db.execute("INSERT INTO items ... VALUES ('i1', 's1', 0, 'user', 'hello world', ...)")
    db.commit()

    results = db.execute(
        "SELECT content FROM items_fts WHERE items_fts MATCH ?", ["hello"]
    ).fetchall()
    assert len(results) >= 1
    assert "hello world" in results[0]["content"]

def test_fts_delete_on_cascade(db):
    """Deleting parent should cascade and clean up FTS."""
    # ... create session with title ...
    db.execute("DELETE FROM sessions WHERE id = ?", (sid,))
    db.commit()
    # FTS entries are cleaned up by the cascade + items_ad trigger
    assert db.execute("SELECT COUNT(*) FROM items_fts").fetchone()[0] == 0

def test_search_across_session_title(db):
    """Search should match content AND session titles."""
    db.execute("INSERT INTO sessions ... VALUES ('s2', 'Python debugging', ...)")
    db.execute("INSERT INTO items ... VALUES ('t2', 's2', 0, 'user', 'help with this code', ...)")
    db.commit()

    results = db.execute(
        "SELECT session_title FROM items_fts WHERE items_fts MATCH ?", ["python"]
    ).fetchall()
    assert len(results) >= 1
    assert "Python debugging" in results[0]["session_title"]
```

## Pitfalls

- **`CREATE TRIGGER IF NOT EXISTS` does NOT update an existing trigger.** If you fix a trigger's syntax, you must `DROP` it first (or use a fresh DB, as temp-file test fixtures do). Running the same DDL again is a no-op for existing triggers — the old broken one persists.
- **Cascade deletes fire triggers on child rows.** When `DELETE FROM sessions` cascades to `items`, the `items_ad` trigger fires for each deleted item. This is correct behavior — the FTS cleanup happens automatically.
- **Standalone FTS tables can't use the 'delete' INSERT syntax.** See the DELETE trigger section above. This is the most common mistake — it looks right but fails with "SQL logic error" at runtime.
