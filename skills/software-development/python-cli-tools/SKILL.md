---
name: python-cli-tools
description: "Build Python CLI tools with modular architecture, async sources, and Docker packaging"
version: 1.1.0
---

# Python CLI Tools

Class-level pattern for building Python CLI tools with a modular source system, async parallel execution, multiple output formats, and Docker containerization.

**See also:**
- `references/difference-clustering.md` — reusable algorithm for organic content categorization by differences rather than similarity.
- `references/docx-generation-pipeline.md` — document conversion with mermaid rendering, SVG embedding in DOCX, pre/post-process pattern, and round-trip ingestion.

## Architecture Pattern

```
project/
├── Dockerfile              # Multi-stage or single-stage slim build
├── docker-compose.yml      # Volume mounts, env vars
├── pyproject.toml          # Project config with [project.scripts]
├── src/
│   ├── main.py             # CLI entry point (click or argparse + rich)
│   ├── config.py           # pydantic-settings (env var prefix)
│   ├── models.py           # pydantic data models
│   ├── sources/
│   │   ├── base.py         # Abstract base: name, run(), timed_run()
│   │   ├── __init__.py     # SOURCE_REGISTRY dict
│   │   └── <domain>/       # e.g. email/, phone/, social/, web/
│   ├── reporters/          # Output formatters: json, markdown, table
│   └── utils/
│       └── async_runner.py # Semaphore-bounded concurrent execution
├── tests/
└── README.md
```

## Key Component Patterns

### Source System
- `BaseSource` ABC with `name` class attribute, `run()` abstract method, `timed_run()` wrapper
- Each source returns a `SourceResult` with status, data, duration
- `SOURCE_REGISTRY` dict in `__init__.py` maps names to classes
- `ReconRunner` iterates relevant sources per input type, runs them concurrently with `asyncio.gather()`

### CLI Entry Point
- Use `click` with `@click.group(invoke_without_command=True)` for flexible command structure
- Detect input type from options (`--email`, `--phone`, `--username` — mutually exclusive)
- Output routing based on `--format` flag (table/json/markdown)

### Docker Packaging
- Start from `python:3.11-slim` for minimal base
- Install non-root user before copying files (use `--chown=user:user`)
- Only copy `pyproject.toml` + `src/` — `.dockerignore` keeps build context small
- `ENTRYPOINT ["recon"]` + `CMD ["--help"]` for CLI container pattern

## Tree Data Model Pitfall — Double-Counting in Parent Nodes

When building CLI tools that operate on tree-structured data (cluster trees, file trees, org charts, taxonomy hierarchies), a common bug is **redundant data storage at every tree level**. Storing the same data (e.g., a list of descendant IDs) on both parent and child nodes causes any recursive `count()` / `total_pages()` / `size()` method to double-count every item as many times as it appears in ancestors.

### The Bug

```python
# BAD: parent keeps all descendant page_ids AND children exist
class ClusterNode(BaseModel):
    page_ids: list[str] = []     # ← holds ALL descendant IDs
    children: list[ClusterNode] = []

    def total_pages(self) -> int:
        return len(self.page_ids) + sum(c.total_pages() for c in self.children)
```

### The Fix

**Non-leaf nodes must NOT hold the same data as their descendants.** Clear `page_ids` (or equivalent) on any node that has children. Only leaf nodes carry the actual data items.

```python
def build_tree(items, ...) -> ClusterNode:
    node = ClusterNode(page_ids=items)
    # ... split logic, create node.children ...
    if node.children:
        node.page_ids = []  # ★ CRITICAL: pages live only at leaves
    return node

def total_pages(self) -> int:
    if not self.children:   # leaf
        return len(self.page_ids)
    return sum(c.total_pages() for c in self.children)
```

### Labeling Consequences

When non-leaf nodes lose their `page_ids`, labeling logic must collect tags from all descendant leaves recursively, not just from `node.page_ids`:

```python
all_page_ids: list[str] = []
def collect_leaves(n: ClusterNode) -> None:
    if n.page_ids:
        all_page_ids.extend(n.page_ids)
    for c in n.children:
        collect_leaves(c)
collect_leaves(node)
```

### When This Pattern Applies

Any CLI tool that builds a hierarchical categorization from flat items: clustering systems, wiki builders, taxonomy generators, org chart builders, decision tree tools.

## Library Integration Pitfalls (from experience)

### 3rd Party Python Libraries with Unstable APIs
- **holehe**: `from holehe.core import holehe` DOES NOT WORK. The module has `maincore()`, not a `holehe` function with importable API. **Use subprocess instead**: `subprocess.run([sys.executable, "-m", "holehe", email, "--no-color", "--only-used"], ...)`
- **sherlock-project**: `from sherlock_project import sherlock` may work but the API changes. **Use subprocess with `--json <path>` flag** for reliable output parsing: `subprocess.run([sys.executable, "-m", "sherlock_project", username, "--json", json_path, "--timeout", "15", "--print-found"], ...)`

### Rule: Prefer subprocess for fragile Python libraries
When a Python library's importable API is poorly documented or unstable, invoke it as a CLI subprocess instead. This is more robust because:
- Libraries' CLI interfaces are generally more stable than their Python APIs
- You get error messages that look like normal CLI errors
- You don't pollute your namespace with the library's imports

### Go Binary Integration in Docker
For tools like PhoneInfoga that ship as Go binaries:
```dockerfile
ADD https://github.com/owner/repo/releases/download/vX.Y.Z/tool_Linux_x86_64.tar.gz /tmp/tool.tar.gz
RUN tar xzf /tmp/tool.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/tool && \
    rm /tmp/tool.tar.gz && \
    tool version
```

### PhoneInfoga Output Parsing — Line-Wrapped URLs

PhoneInfoga's CLI output wraps long Google search URLs across multiple lines at terminal width. When capturing output via `subprocess.run(capture_output=True)`, the raw text contains literal `\n` bytes inside URL strings. This breaks both JSON serialization and text parsing.

**Fix:** Use regex to join continuation lines before extracting URLs:

```python
# First, remove newlines inside URLs by merging continuation lines
cleaned = re.sub(
    r"(https://www\.google\.com/search\?q=[^\s\"']+?)(\n\s*)([^\s\"']{10,})",
    r"\1\3",
    output,
)
# Then find all URLs in the cleaned text
urls = list(set(re.findall(r"https://www\.google\.com/search\?q=[^\s\"']+", cleaned)))
```

**Output structure to expect:**
```
Results for googlesearch
Social media:
    URL: https://www.google.com/search?q=site%3Afacebook.com+intext%3A%22...
    URL: https://www.google.com/search?q=site%3Atwitter.com+intext%3A%22...
Reputation:
    URL: https://www.google.com/search?q=site%3Awhosenumber.info+intext%3A%22...
...
Results for local
Raw local: 65755348
Local: (555) 123-4567
...
```

Parse by detecting scanner headers with `Results for (\w+)`, then extracting URLs under each.

### Ignorant (from megadose/ignorant)
- **Available on PyPI** as `ignorant`. No API key needed — uses forgotten-password flows to check if a phone number is registered on Amazon, Instagram, Snapchat, etc.
- **DO NOT use `python -m ignorant`** — the package has no `__main__.py`. Use the direct `ignorant` binary: `subprocess.run(["ignorant", "--only-used", "--no-color", country_code, local_number], ...)`
- Takes country code and local number as separate positional args: `ignorant --only-used +1 3365755348`
- Output format: `[+] amazon.com` / `[-] snapchat.com` / `[x] Rate limit` — parse with regex `r"\[\+\]\s*([a-zA-Z][a-zA-Z0-9._-]+\.[a-zA-Z]{2,})"`
- Works with `phoneinfoga`'s country code extraction logic as a shared helper

## JSON Output: Handle Piped Output Control Characters
When piping JSON from a Docker container, control characters (0x00-0x1F) can corrupt the output. Fixes:
- In reporter: sanitize strings with `re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)` before `json.dumps()`
- When reading piped output: `json.loads(raw, strict=False)` bypasses control character validation
- Save to file inside container and mount a volume for reliable output

## Phone Number Auto-Detection (Multi-Region Fallback)

When users provide bare numbers without a `+` prefix, try multiple default regions:

```python
DEFAULT_REGIONS = ["US", "FR", "GB", "DE", "CA", "AU", "JP", "BR", "IN", "IT", "ES", "NL"]

def _try_parse(query: str):
    # Strategy 1: without region (requires +)
    try:
        return phonenumbers.parse(query, None)
    except phonenumbers.NumberParseException:
        pass

    # Strategy 2: try each default region — accept first valid
    best = None
    for region in DEFAULT_REGIONS:
        try:
            num = phonenumbers.parse(query, region)
            if phonenumbers.is_valid_number(num):
                return num
            if best is None:
                best = num
        except phonenumbers.NumberParseException:
            continue

    # Strategy 3: extract digits and try top 3 regions
    if best is None:
        digits = "".join(c for c in query if c.isdigit())
        if len(digits) >= 7:
            for region in DEFAULT_REGIONS[:3]:
                try:
                    num = phonenumbers.parse(digits, region)
                    if best is None or phonenumbers.is_valid_number(num):
                        best = num
                except phonenumbers.NumberParseException:
                    continue
    return best
```

## Self-Hosted Service Integration (e.g. SearXNG)

When a CLI tool needs a supporting service (search engine, database, ML model server), run it as a separate Docker container and connect via a Docker network + environment variables.

### Pattern

1. **Add the service to docker-compose.yml** with explicit configuration:
```yaml
services:
  searxng:
    image: searxng/searxng:latest
    ports: ["18080:8080"]
    environment:
      - SEARXNG_BASE_URL=http://searxng:8080/
    volumes:
      - ./searxng/settings.yml:/etc/searxng/settings.yml:ro
    cap_add:
      - CAP_NET_RAW
    restart: unless-stopped

  recon:
    build: .
    depends_on:
      - searxng
    environment:
      - RECON_SEARCH_BACKEND=searxng
      - RECON_SEARXNG_URL=http://searxng:8080
```

2. **Config-driven backend selection** in `src/config.py`:
```python
search_backend: str = "duckduckgo"   # or "searxng"
searxng_url: str = "http://searxng:8080"
```

3. **Backend abstraction** with ABC + multiple implementations:
```python
class SearchBackend(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[SearchResult]: ...

class DuckDuckGoBackend(SearchBackend):
    async def search(self, query: str) -> list[SearchResult]:
        # Free, no auth, POST to lite.duckduckgo.com/lite/
        ...

class SearXNGBackend(SearchBackend):
    def __init__(self, base_url: str = "http://localhost:18080"):
        self.base_url = base_url

    async def search(self, query: str) -> list[SearchResult]:
        # GET /search?q=...&format=json with Accept: application/json
        ...
```

4. **Backend factory** in the source module:
```python
@staticmethod
def _get_backend() -> SearchBackend:
    if settings.search_backend.lower() == "searxng":
        return SearXNGBackend(settings.searxng_url)
    return DuckDuckGoBackend()
```

### SearXNG-Specific Setup

SearXNG requires a custom `settings.yml` to enable JSON format API access. The default Docker image disables it for security.

**`searxng/settings.yml`:**
```yaml
use_default_settings: true
server:
  secret_key: "your-secret-key-here"
  bind_address: "0.0.0.0"
  image_proxy: true
  limiter: false
search:
  formats:
    - html
    - json
```

Without these settings, SearXNG returns HTTP 403 for `/search?format=json` requests.

**API endpoint:** `GET /search?q=<query>&format=json&language=en-US`

**Response structure:**
```json
{
  "query": "...",
  "results": [{"title": "...", "url": "...", "content": "..."}],
  "unresponsive_engines": [["brave", "too many requests"]]
}
```

### Fallback Pattern

When the supporting service is unavailable, degrade gracefully:
```python
try:
    results = await backend.search(query)
except SearXNGError as e:
    # Fall back to DuckDuckGo or just return empty results
    backend = DuckDuckGoBackend()
    results = await backend.search(query)
```

### Dork Executor Pattern

For tools that generate search queries (dorks) and need real results:

1. **Generate dork queries** from input data (phone number, email, etc.) using multiple format variants
2. **Execute via configurable backend** (DDG Lite or SearXNG)
3. **Categorize results** (social_media, reputation, leaks, etc.)
4. **Deduplicate by URL** within each category
5. **Report only results found** — the user wants matching outputs, not raw dork URLs

```python
def _generate_dorks(number: str) -> list[dict]:
    """Generate search queries across format variants and platforms."""
    formats = [digits, f"+1{digits}", f"{digits[:3]}-{digits[3:6]}-{digits[6:]}", ...]
    for fmt in formats:
        for site in ["facebook.com", "twitter.com"]:
            queries.append({"category": "social_media", "query": f'site:{site} "{fmt}"'})
        ...
    return queries
```

## Report Output: Results-Only Preference

When the user says "I want the final results, no need to provide all the dorks, only the matching outputs": the markdown reporter should show counts (not raw URLs) for intermediate data like generated search queries. A bullet list of category → count is enough:

```
**45 Google dork queries generated across 5 categories**
- Social Media: 4 queries
- Reputation & Caller ID: 6 queries
```

The actual matching results (found pages, profiles, mentions) get full detail with titles, URLs, and snippets. This keeps the report actionable.

**Rule of thumb for markdown reports:** If a source produced intermediate/generated data (dork URLs, queries, etc.), summarize it with counts. If it produced actual findings (search results, registered platforms, validated data), show the full detail.

## Report Model Population Pattern

After all sources run, map raw `SourceResult` data into typed model sections. This is the bridge between the generic source system and the structured output:

```python
@staticmethod
def _populate_report(report: ReconReport, results: list) -> None:
    for r in results:
        if r.status != "success":
            continue
        d = r.data

        if r.source_name == "phoneinfoga" and d:
            # Store dork URLs and categories as-is
            report.phoneinfoga_data = PhoneInfogaData(...)

        elif r.source_name == "ignorant" and d:
            # Merge into existing phone section to enrich output
            if report.phone is None:
                report.phone = PhoneRecon(raw=report.query)
            report.phone.registered_services = d.get("registered", [])
```

Key principle: **some sources populate their own section, others enrich an existing section**. Ignorant results enrich the phone section's `registered_services` field rather than creating a separate section. This keeps the output model clean.

## Four-Place Registration for New Sources

When adding a new source, update ALL four locations:

1. `sources/__init__.py` — add import + SOURCE_REGISTRY entry
2. `utils/async_runner.py` — add to the `_sources_for_type()` mapping
3. `main.py` — add to descriptions dict in `list-sources` command
4. `reporters/markdown_reporter.py` — if the source produces rich data that needs its own section in markdown output, add a `_add_<source>_section()` function and call it from `_add_source_detail_sections()`

Forgetting any one means the source either won't load, won't run for the right input type, won't appear in `list-sources`, or its data will be invisible in markdown reports.

### Markdown Reporter Pattern for Rich Sources

The markdown reporter uses a dispatch pattern for sources that produce data beyond the typed model:

```python
def _add_source_detail_sections(lines, report):
    for sr in report.source_results:
        if sr.status != "success" or not sr.data:
            continue
        if sr.source_name == "phoneinfoga":
            _add_phoneinfoga_section(lines, sr.data)
        elif sr.source_name == "messenger_check":
            _add_messenger_section(lines, sr.data)
        elif sr.source_name == "ignorant":
            _add_ignorant_section(lines, sr.data)

def _add_phoneinfoga_section(lines, data):
    # Renders dork categories with clickable search links
    # Uses data.get("dork_categories", {}) - a dict of category->[urls]
    # Shows first 4 URLs per category with "... and N more" overflow
    ...

def _add_messenger_section(lines, data):
    # Renders direct links (WhatsApp, Telegram, Signal, Viber)
    # Uses data.get("links", {}) and data.get("messengers", {})
    ...
```

**Pitfall:** The typed model sections (email, phone, social, web) are populated by `_populate_report()` in the async_runner. Sources like phoneinfoga and messenger_check produce data that fits in neither the typed model NOR the dump-every-source-results section. They need dedicated renderers in the markdown reporter. When you forget this, the data is in the JSON output but invisible in markdown — exactly what happened with the first version of Profile Recon.

## Verification

```bash
# Test help
docker run --rm <image> --help

# Test each input type
docker run --rm <image> --email test@example.com --quiet
docker run --rm <image> --phone "+15551234567" --quiet
docker run --rm <image> --username "testuser" --quiet

# List sources — verify ALL registered sources appear with descriptions
docker run --rm <image> list-sources

# Inspect JSON output for derived data flows (e.g. ignorant → phone.registered_services)
docker run --rm <image> --phone "+15551234567" --quiet --format json | python3 -c "
import sys, json; d = json.loads(sys.stdin.read(), strict=False)
for sr in d['source_results']:
    print(f\"{sr['source_name']}: {sr['status']}\")
"

# Check source results map correctly to typed sections
docker run --rm <image> --phone "+15551234567" --quiet --format json | python3 -c "
import sys, json; d = json.loads(sys.stdin.read(), strict=False)
print('Phone services:', d.get('phone', {}).get('registered_services', []))
"
```
