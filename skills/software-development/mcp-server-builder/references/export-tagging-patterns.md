# Export Registry & Auto-Tagging Patterns

## Export Registry (mirrors the adaptor pattern for output)

When your MCP server stores data that users want to reconstruct in multiple formats, use the same registry pattern as adaptors — but for output instead of input.

```python
# src/<package>/exporters.py
from abc import ABC, abstractmethod
from <package>.db.models import Session  # or whatever your data model is

class BaseExporter(ABC):
    @abstractmethod
    def export(self, data) -> str: ...

class ExportRegistry:
    def __init__(self):
        self._exporters: dict[str, type[BaseExporter]] = {}

    def register(self, name: str) -> callable:
        def decorator(cls):
            self._exporters[name] = cls
            return cls
        return decorator

    def list(self) -> list[str]:
        return list(self._exporters.keys())

    def export(self, name: str, data) -> str:
        cls = self._exporters.get(name)
        if cls is None:
            raise ValueError(f"Unknown format '{name}'. Supported: {', '.join(self.list())}")
        return cls().export(data)

EXPORT_REGISTRY = ExportRegistry()
register = EXPORT_REGISTRY.register

@register("markdown")
class MarkdownExporter(BaseExporter):
    def export(self, session) -> str:
        # ... format as markdown ...
```

### Key differences from adaptor pattern

| Aspect | Adaptors (input) | Exporters (output) |
|--------|-----------------|-------------------|
| Direction | raw text → structured model | structured model → formatted text |
| Interface | `detect()` + `parse()` | `export()` only |
| Auto-detect | Yes, via confidence scoring | No (user picks format) |
| Error on unknown | Returns None | Raises ValueError with supported list |

## Auto-Tagging Heuristic

On imports, automatically tag sessions with their origin information. This lets users filter without manual tagging.

```python
# src/<package>/tagging.py
def build_tags(imported, adaptor_name: str) -> list[str]:
    existing = set(imported.tags or [])
    new_tags = []

    agent_tag = f"agent:{adaptor_name}"
    if agent_tag not in existing:
        new_tags.append(agent_tag)

    if imported.model:
        model_tag = f"model:{imported.model}"
        if model_tag not in existing:
            new_tags.append(model_tag)

    return new_tags
```

### Integration point

Append auto-tags to any existing tags in the `SessionCreate` call:

```python
SessionCreate(
    ...
    tags=imported.tags + build_tags(imported, adaptor_name),
)
```

This applies to both full imports and block imports.
