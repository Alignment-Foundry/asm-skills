# MCP Search Enhancement Patterns

Optional search features for MCP servers with SQLite FTS5. Both are designed as zero-cost opt-ins — existing callers are unaffected when the parameters are omitted.

## Recency-Boosted BM25 Ranking

BM25 relevance alone doesn't favour newer results. For conversation stores, search logs, or any content with a temporal dimension, a gentle recency boost improves result quality.

### SQL Formula

```sql
SELECT ..., rank as bm25_score,
       (julianday('now') - julianday(s.created_at)) as days_old
FROM ...
WHERE turns_fts MATCH ?
ORDER BY rank - (1.0 / (1.0 + MAX(days_old, 0))) * 0.5
LIMIT ? OFFSET ?
```

**How it works:**
- `rank` is the FTS5 BM25 score (negative values, closer to 0 = better match)
- `1.0 / (1.0 + MAX(days_old, 0))` — recency boost factor: 1.0 for brand new, 0.5 for 1 day old, 0.09 for 10 days old
- `* 0.5` — keeps it a gentle tiebreaker (max boost of 0.5, a fraction of typical BM25 spread)
- **Subtraction** from rank (not addition) because BM25 rank is negative — subtracting improves the score for newer results
- `MAX(days_old, 0)` clamps negative values (future dates, clock skew) to 0

### Python Integration

```python
def search_sessions(db, query, *, context_window=0, limit=20, offset=0):
    safe_query = _fts_escape(query)
    sql = """
        SELECT ..., rank as bm25_score,
               (julianday('now') - julianday(s.created_at)) as days_old
        FROM turns_fts
        JOIN turns t ON t.rowid = turns_fts.rowid
        JOIN sessions s ON s.id = t.session_id
        WHERE turns_fts MATCH ?
        ORDER BY rank - (1.0 / (1.0 + MAX(days_old, 0))) * 0.5
        LIMIT ? OFFSET ?
    """
    rows = db.execute(sql, [safe_query, limit, offset]).fetchall()
    return [
        SearchResult(
            score=float(r["bm25_score"]),  # Note: column renamed from 'score'
            ...
        ) for r in rows
    ]
```

**Note:** When adding the recency column, rename the select from `rank as score` to `rank as bm25_score` to avoid confusion with the final ranked order.

## Search Result Context Windowing

When a user searches and finds a match, they typically want to see the surrounding turns too — not just the matched turn in isolation.

### Data Model

```python
class SearchResult(BaseModel):
    session_id: str
    title: str
    agent: str
    match_snippet: str = ""
    score: float = 0.0
    matched_turn_id: str | None = None
    context_turns: list[dict] = Field(default_factory=list)  # ±N turns
```

### Fetch Function

```python
def _fetch_context_turns(db, session_id, matched_turn_id, context_window):
    """Fetch ±N turns around the matched turn for context."""
    if not matched_turn_id:
        return []

    row = db.execute(
        "SELECT turn_index FROM turns WHERE id = ?", (matched_turn_id,)
    ).fetchone()
    if row is None:
        return []

    idx = row["turn_index"]
    start = max(0, idx - context_window)
    end = idx + context_window + 1  # exclusive end

    rows = db.execute(
        """SELECT turn_index as idx, role, content
           FROM turns WHERE session_id = ? AND turn_index >= ? AND turn_index < ?
           ORDER BY turn_index""",
        (session_id, start, end),
    ).fetchall()

    return [
        {
            "turn_index": r["idx"],
            "role": r["role"],
            "content": r["content"],
            "is_match": r["idx"] == idx,  # Client can highlight this turn
        }
        for r in rows
    ]
```

### Integration Pattern

```python
def search_sessions(db, query, *, context_window=0, ...):
    results = _search_with_query(db, query, ...)

    if context_window > 0 and results:
        for r in results:
            r.context_turns = _fetch_context_turns(
                db, r.session_id, r.matched_turn_id, context_window
            )

    return results
```

The `context_window` parameter defaults to 0, so existing callers get exactly the same behaviour. When a caller passes `context_window=2`, each result includes up to 2 turns before and 2 turns after the matched turn.

### MCP Tool Input Schema

```python
Tool(
    name="search",
    description="...",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "context_window": {
                "type": "integer",
                "description": "Include ±N turns around the match for context (default: 0).",
                "default": 0,
            },
            ...
        },
    },
)
```

## Testing

```python
def test_search_context_window(db):
    """Search with context_window returns surrounding turns."""
    results = search_sessions(db, "pytest", context_window=1)
    assert len(results) >= 1
    assert len(results[0].context_turns) >= 1
    # Context turns have is_match flag
    match_count = sum(
        1 for t in results[0].context_turns if t.get("is_match")
    )
    assert match_count >= 1

def test_search_no_context(db):
    """Default behaviour (no context_window) returns no context turns."""
    results = search_sessions(db, "pytest")
    assert all(len(r.context_turns) == 0 for r in results)

def test_recency_boost(db):
    """Recency boost ranks newer sessions higher for similar relevance."""
    # Arrange: create old session + new session with same text match
    old_session = create_session(..., title="Old Session")
    db.execute("UPDATE sessions SET created_at = ? WHERE id = ?",
               (seven_days_ago_iso, old_session.id))
    new_session = create_session(..., title="New Session")

    # Act
    results = search_sessions(db, "match_text")

    # Assert
    new_idx = next(i for i, r in enumerate(results) if "New" in r.title)
    old_idx = next(i for i, r in enumerate(results) if "Old" in r.title)
    assert new_idx < old_idx
```

## Calling Conventions (MCP)

For MCP tools, pass `context_window` as an integer parameter:

```bash
# Search with context
printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_sessions","arguments":{"query":"hello","context_window":2}}}'

# Search with model filter
printf '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_sessions","arguments":{"query":"","model":"claude-sonnet-4"}}}'
```
