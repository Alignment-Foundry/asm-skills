---
name: markdown-publishing
description: >-
  Convert structured markdown (with mermaid diagrams, MARP slide decks, templates)
  to production-ready DOCX/PDF via pandoc + SVG embedding for Word-editable shapes.
version: 1.0.0
author: Alpha
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [document-conversion, markdown, mermaid, pandoc, docx, svg, marp]
    category: software-development
---

# Markdown Publishing

Class-level pattern for converting structured markdown content with diagrams,
slide decks, and style templates into production-ready DOCX and PDF documents.

**See also:** `references/docx-svg-embedding.md` — SVG-in-DOCX embedding via
`<asvg:svgBlip>` for Word-editable mermaid shapes.

## Pipeline Architecture

```
Input .md
  │
  ├─ MARP Detection ──────► Strip directives → clean markdown
  ├─ Mermaid Extraction ──► Render to PNG+SVG → Replace blocks with image refs
  ├─ Pandoc Conversion ───► DOCX/PDF (with --reference-doc for styles)
  ├─ SVG Embedding ───────► Post-process DOCX zip for editable shapes
  └─ Output .docx / .pdf
```

### Module Layout (Python)

```
project/
├── pyproject.toml          # [project.scripts] entry point
├── src/package/
│   ├── __init__.py         # __version__
│   ├── __main__.py         # Allow python -m
│   ├── cli.py              # argparse or click — subcommands: build, ingest, template, show
│   ├── converters.py       # Orchestrator pipeline (read → process → write)
│   ├── mermaid_handler.py  # Extract ```mermaid blocks, render to SVG/PNG
│   ├── marp_handler.py     # Detect/strip MARP frontmatter and directives
│   ├── template.py         # Pandoc reference-doc workflow, DOCX→MD round-trip
│   └── svg_embedder.py     # Post-process DOCX zip to embed SVG blips
├── templates/              # Pandoc reference .docx files
├── tests/
└── README.md
```

## Dependencies

| Library | Purpose | Installation |
|---------|---------|-------------|
| `mermaidx` | Python-native mermaid rendering (no Node/Puppeteer) | `pip install mermaidx` |
| `pypandoc-binary` | Bundled pandoc binary + Python wrapper | `pip install pypandoc-binary` |
| `python-docx` | DOCX creation and XML manipulation | `pip install python-docx` |
| `docxtpl` | Jinja2 templating for DOCX (optional) | `pip install docxtpl` |

## Mermaid Rendering Pipeline

### Extract mermaid blocks from markdown

```python
MERMAID_PATTERN = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
```

Each block gets assigned a SHA256 fingerprint for cross-format matching.

### Render to SVG and PNG

```python
from mermaidx import render as mermaid_render, svg_to_png

d = mermaid_render(code)
svg_content = d.svg()                  # SVG string
png_bytes = svg_to_png(svg, width=800) # PNG bytes
ascii_art = d.ascii()                  # Box-drawing ASCII (debugging)
```

**Why mermaidx over mermaid-cli:**
- No Node.js, no Puppeteer, no Chrome download
- Python-native (QuickJS-backed JS runtime)
- Supports 20+ diagram types: graph, flowchart, sequenceDiagram, classDiagram, erDiagram, stateDiagram, gantt, pie, timeline, mindmap, sankey, quadrantChart, etc.
- Output: `.svg()`, `.png()`, `.ascii()`, `.numpy()`, `.raw()`, `.save()`

### Alt-text fingerprinting for post-processing

When replacing mermaid blocks with image references, embed the fingerprint in
the alt text so downstream post-processors can identify which images originated
from mermaid:

```markdown
![Mermaid graph [fp:fd8d9893de5f9bfe]](mermaid-fd8d9893de5f9bfe.png)
```

Pandoc preserves alt text in the DOCX `docPr/@descr` attribute, making it
searchable during SVG embedding post-processing.

## Pandoc Template Workflow

### Reference-doc pattern (styles only)

1. **Init:** Export pandoc's default reference DOCX:
   ```bash
   pandoc -o reference.docx --print-default-data-file reference.docx
   ```
2. **Customize:** Open `reference.docx` in Word → modify Heading 1, Heading 2,
   Normal, colors, fonts, spacing, header/footer.
3. **Use:** Convert with styles applied:
   ```bash
   pandoc input.md --reference-doc=reference.docx -o output.docx
   ```

### Style inspection

Extract style names from a reference DOCX to see what's available:
```python
from docx import Document
doc = Document("reference.docx")
para_styles = [s.name for s in doc.styles if s.type == 1]   # paragraph
char_styles = [s.name for s in doc.styles if s.type == 2]   # character
```

Pandoc's default reference doc ships with ~31 paragraph styles (Heading 1-9,
Normal, Title, Subtitle, Compact, Captioned Figure, etc.) and ~17 character
styles (Verbatim Char, Heading 1 Char, Hyperlink, etc.).

## MARP Slide-Deck Handling

MARP (https://marp.app/) is a markdown presentation format.

### Detection signals

```python
# Frontmatter with marp: true
---
marp: true
theme: uncover
---

# Slide 1

---

## Slide 2
```

### Strip directives before pandoc conversion

1. Remove `marp: true` frontmatter block
2. Remove `theme:` frontmatter blocks  
3. Remove HTML-comment directives: `<!-- _class: lead -->`
4. Preserve `---` slide separators (pandoc renders them as horizontal rules)
5. Collapse multiple blank lines

## DOCX ↔ Markdown Round-Trip

### Direction: DOCX → Markdown (ingest / template ingestion)

```bash
pandoc input.docx -f docx -t markdown --wrap=preserve -o output.md
```

This preserves:
- Headings, lists, bold/italic, code, links
- Image references (as markdown with alt text)
- Table structure

**Pandoc exit code 63** means the DOCX couldn't be parsed — usually indicates
an unsupported Office extension (e.g. SVG blip elements added by
`--editable-mermaid`). Round-trip works on non-SVG-embedded DOCX.

### Finding the bundled pandoc binary

When using `pypandoc-binary`, the pandoc binary lives inside the package
but is not on PATH. Find it programmatically:

```python
import pypandoc
pandoc_path = pypandoc.get_pandoc_path()
# Returns: /path/to/venv/lib/.../pypandoc/files/pandoc
```

Use this when calling pandoc directly (e.g. ``--print-default-data-file``)
instead of through ``pypandoc.convert_text``.

### Fingerprint preservation

Mermaid fingerprints in alt text survive the round-trip, so re-converting the
ingested markdown produces the same images (same render cache keys).

## SVG Embedding for Word-Editable Mermaid Shapes

See `references/docx-svg-embedding.md` for the full technique.

**Quick summary:** When `--editable-mermaid` is enabled:
1. Mermaid blocks render to PNG (embedded in DOCX by pandoc) AND SVG
2. Post-processor unzips the DOCX, finds mermaid images by alt-text fingerprint
3. Adds SVG image parts to `word/media/`
4. Adds `<asvg:svgBlip>` DrawingML extension to each image's `<a:blip>`
5. Adds SVG content type to `[Content_Types].xml`
6. Rebuilds the zip

Result: Word 2016+ renders the SVG natively. Users right-click → "Convert to
Shapes" for fully editable nodes, edges, and labels.

## CLI Subcommand Pattern

Use argparse with subparsers for a clean multi-command interface:

```python
parser = argparse.ArgumentParser(prog="tool-name")
sub = parser.add_subparsers(dest="command", required=True)

# build — convert markdown → DOCX/PDF
build = sub.add_parser("build", help="Convert markdown → DOCX/PDF")
build.add_argument("input", type=Path)
build.add_argument("-o", "--output", type=Path)
build.add_argument("--template", "--reference-doc", dest="reference_doc", type=Path)
build.add_argument("--mermaid-theme", choices=["default", "dark", "neutral", "forest", "base"])
build.add_argument("--editable-mermaid", action="store_true")
build.add_argument("--to-pdf", action="store_true")
build.add_argument("--mermaid-width", type=int, default=800)

# ingest — DOCX → markdown
ingest = sub.add_parser("ingest", help="DOCX → markdown round-trip")
ingest.add_argument("input", type=Path)
ingest.add_argument("-o", "--output", type=Path)

# template — init / inspect
template = sub.add_parser("template", help="Template utilities")
tmpl_sub = template.add_subparsers(dest="template_cmd", required=True)
# template init — export default reference docx
# template inspect — list styles

# show — info / capabilities
show = sub.add_parser("show", help="Show project info")

def main(argv=None):
    args = parser.parse_args(argv)
    match args.command:
        case "build": _cmd_build(args)
        case "ingest": _cmd_ingest(args)
        case "template": _cmd_template(args)
        case "show": _cmd_show(args)
```

## Workflow: Session Closeout

When a build session produces working output (successful DOCX/PDF generation
verified), prefer to **push and review** rather than diving into the next feature:

1. Verify the output renders correctly (check file size, internal structure)
2. Commit and push to the remote
3. Present the deliverable for user review
4. Let the user decide when to start the next feature

This prevents scope creep in a single session and gives the user a clean
checkpoint to review before committing to the next direction.

## Pitfalls

- **pandoc renames images** — When converting markdown, pandoc assigns its own
  filenames (`rId9.png`, `rId13.png`) to embedded images. Never try to match
  by original filename in post-processing. Use alt-text fingerprinting instead.
- **SVG content type** — Adding .svg files to a DOCX without updating
  `[Content_Types].xml` with `Default Extension="svg" ContentType="image/svg+xml"`
  breaks the DOCX and pandoc returns exit code 63.
- **Pandoc 3.9 and SVG blips** — Pandoc's DOCX parser does NOT support the
  Office 2019 SVG extension (`<asvg:svgBlip>`). SVG-embedded DOCX works in
  Word but can't be re-ingested by pandoc. File under `known limitation`.
- **Tempfile cleanup** — Always wrap temporary directories in
  `tempfile.TemporaryDirectory()` + `try/finally` or `shutil.rmtree()`
  to avoid leaking temp dirs from failed conversions.
- **mermaidx backend** — Ensure the installed mermaidx has a working JS
  backend. `mermaidx.backends()` lists available ones. `quickjs` ships by
  default. Install `mermaidx[v8]` or `mermaidx[rust]` for alternatives.
- **Mermaid diagram type detection** — The first word of a mermaid code block
  is the diagram type. Validate it against a known list to detect malformed
  blocks early.
