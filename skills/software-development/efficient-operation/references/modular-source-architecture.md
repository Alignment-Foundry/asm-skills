# Modular Source Architecture Pattern

A reusable pattern for building CLI tools that run parallel lookups against multiple backends (OSINT, monitoring, scanning, enrichment, etc.).

## Core Components

### 1. BaseSource (abstract base)

```python
class BaseSource(ABC):
    name: str = "base"

    @abstractmethod
    async def run(self, query: str, **kwargs) -> SourceResult:
        ...

    async def timed_run(self, query: str, **kwargs) -> SourceResult:
        start = time.monotonic()
        try:
            result = await self.run(query, **kwargs)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except Exception as e:
            return SourceResult(
                source_name=self.name, status="error", error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )
```

Key: `timed_run()` wraps `run()` with timing + error handling — subclasses only implement `run()`.

### 2. SourceResult (pydantic model)

```python
class SourceResult(BaseModel):
    source_name: str
    status: str  # "success", "error", "skipped"
    data: dict = Field(default_factory=dict)
    error: str | None = None
    confidence: str = "unknown"
    duration_ms: int = 0
```

### 3. SOURCE_REGISTRY

```python
SOURCE_REGISTRY: dict[str, type] = {
    "holehe": HoleheSource,
    "domain": DomainSource,
    # Add new sources here — zero wiring changes needed
}
```

### 4. ReconRunner (async executor)

```python
class ReconRunner:
    def __init__(self, max_concurrency: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def run(self, query: str, input_type: InputType) -> ReconReport:
        source_names = self._sources_for_type(input_type)
        sources = [SOURCE_REGISTRY[name]() for name in source_names]
        tasks = [self._run_one(src, query) for src in sources]
        results = await asyncio.gather(*tasks)
        # Assemble report from results
        ...

    async def _run_one(self, src, query):
        async with self.semaphore:
            return await src.timed_run(query)
```

## Third-Party Library Integration

When a tool has its own CLI (holehe, sherlock, etc.):

```python
# Preferred: subprocess via asyncio.to_thread
async def run(self, query, **kwargs):
    result = await asyncio.to_thread(self._check, query)
    return result

def _check(self, email):
    result = subprocess.run(
        [sys.executable, "-m", "holehe", email, "--no-color"],
        capture_output=True, text=True, timeout=60,
    )
    # Parse output
    ...
```

**Why subprocess over direct import:**
- Avoids dependency on internal API stability
- Handles CLI-only tools with ArgumentParser
- Clean error isolation (subprocess crash doesn't take down main process)

## Adding a New Source

1. Create a class extending `BaseSource`
2. Set `name` attribute
3. Implement `async def run()`
4. Register in `SOURCE_REGISTRY`
5. Add to the runner's `_sources_for_type()` mapping

No other code changes needed — reporters iterate `source_results` generically.

## Docker Packaging

```dockerfile
FROM python:3.11-slim
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 app --ingroup app
WORKDIR /app
COPY --chown=app:app pyproject.toml src/ ./
RUN pip install --no-cache-dir -e .
USER app
ENTRYPOINT ["toolname"]
CMD ["--help"]
```
