# DOCX Generation Pipeline (Pre/Post-Process Pattern)

Building a CLI tool that converts markdown (with embedded diagrams) to styled
DOCX/PDF with editable vector shapes.  Core technique: **render before pandoc,
post-process after pandoc**.

## Pipeline Architecture

```
Input .md
  │
  ├─ Pre-processing ────── Extract mermaid/MARP blocks, render to images
  ├─ Pandoc conversion ─── Markdown → DOCX (with --reference-doc styles)
  ├─ Post-processing ───── SVG embed, shape injection, XML manipulation
  └─ Output .docx
```

The key insight: **pandoc is the engine, but external content (diagrams, vector
shapes) must be handled before and after its pass.**

## Library Choices

| Need | Library | Why |
|------|---------|-----|
| Mermaid rendering | `mermaidx` | Python-native (QuickJS backend) — no Node.js, no Puppeteer. Supports SVG, PNG, PDF, ASCII output. |
| DOCX read/write | `python-docx` | Standard Python library for Office OpenXML. No SVG support natively, but raw XML manipulation works. |
| Format conversion | `pypandoc-binary` | Bundles pandoc binary — no system install needed. Handles md↔docx, pdf, html, etc. |
| DOCX templating | `docxtpl` (available) | Jinja2-powered DOCX templates for complex document generation. |
| SVG rendering | `cairosvg` (optional) | Converts SVG to PNG/PDF with Cairo backend. Installable via pip in venv. |

## Pre-Processing: Mermaid Extraction

### Pattern

1. Scan markdown for ```` ```mermaid … ``` ```` blocks via regex
2. Render each block to PNG + SVG using `mermaidx`:
   ```python
   from mermaidx import render, svg_to_png
   d = render(code)
   svg = d.svg()          # SVG markup string
   png = svg_to_png(svg, width=800)  # PNG bytes
   ```
3. Replace the mermaid code block with an image reference:
   ```python
   image_ref = f"\n![Mermaid {diagram_type} [fp:{fingerprint}]]({output_path})\n"
   ```
4. The `[fp:<fingerprint>]` marker in alt-text is used by the post-processor
   to identify which images need SVG upgrades.

### Fingerprint Strategy

Use SHA-256 of the mermaid source code (truncated to 16 hex chars) as a
deterministic identifier:

```python
fingerprint = hashlib.sha256(code.encode()).hexdigest()[:16]
```

This allows the post-processor to match rendered images back to their source
code without needing the original file.

## Post-Processing: DOCX as a Zip Archive

A DOCX file is a standard ZIP archive containing XML files. The post-processing
pattern:

1. **Extract** the DOCX with `zipfile.ZipFile(docx_path, 'r').extractall(tmpdir)`
2. **Modify** XML files (`word/document.xml`, `word/_rels/document.xml.rels`,
   `[Content_Types].xml`)
3. **Rebuild** the zip: walk the temp dir and write all files back

### SVG Embedding (Word-Editable Shapes)

Word 2016+ supports SVG natively via the `<asvg:svgBlip>` DrawingML extension.
When rendered in Word, users can right-click → "Convert to Shapes" to get
native Word drawing objects.

**OpenXML structure for SVG blip:**

```xml
<a:blip r:embed="rId9">
  <a:extLst>
    <a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">
      <asvg:svgBlip r:embed="rIdSvg1" />
    </a:ext>
  </a:extLst>
</a:blip>
```

**Steps to add SVG to a DOCX:**

1. Write the SVG file to `word/media/<filename>.svg`
2. Add a relationship in `word/_rels/document.xml.rels`:
   ```xml
   <Relationship Id="rIdSvg1"
     Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
     Target="media/<filename>.svg" />
   ```
3. Register the SVG content type in `[Content_Types].xml`:
   ```xml
   <Default Extension="svg" ContentType="image/svg+xml" />
   ```
4. Find the target `<a:blip>` in `word/document.xml` (by matching the existing
   image's `r:embed` attribute) and add the `<a:extLst>` with the SVG blip
   extension.

**Namespace declarations needed in document.xml root:**

```xml
xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main"
```

### Finding Images by Alt-Text (Fingerprint Matching)

When post-processing, you need to find which images in the DOCX correspond to
your rendered mermaid diagrams. The `docPr/@descr` attribute preserves the
markdown alt-text:

```python
import re
FP_PATTERN = re.compile(r"\[fp:([a-f0-9]+)\]")

for inline in root.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"):
    docPr = inline.find("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr")
    descr = docPr.get("descr", "")
    m = FP_PATTERN.search(descr)
    if m:
        fp = m.group(1)  # match to your rendered fingerprint
        # Navigate to the a:blip from this inline to add SVG extension
```

### Navigation from docPr to a:blip (ElementTree)

`docPr.find("..")` returns `None` in Python's C-accelerated ElementTree.
Instead, iterate over `wp:inline` elements (which contain both `docPr` and the
picture structure) and navigate downward:

```python
inline → a:graphic → a:graphicData → pic:pic → pic:blipFill → a:blip
```

```python
graphic = inline.find("{http://schemas.openxmlformats.org/drawingml/2006/main}graphic")
graphic_data = graphic.find("{http://schemas.openxmlformats.org/drawingml/2006/main}graphicData")
pic = graphic_data.find("{http://schemas.openxmlformats.org/drawingml/2006/picture}pic")
blip_fill = pic.find("{http://schemas.openxmlformats.org/drawingml/2006/picture}blipFill")
blip = blip_fill.find("{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
```

## Template System (Pandoc Reference-DOCX)

Pandoc uses `--reference-doc=<template.docx>` to apply styles from a template.
The template must be a `.docx` with edited styles (Heading 1, Normal, etc.).

**Workflow:**

1. Export pandoc's default reference doc:
   ```
   pandoc -o reference.docx --print-default-data-file reference.docx
   ```
2. Open `reference.docx` in Word and edit styles (fonts, colors, spacing,
   headers/footers)
3. Pass it to the converter:
   ```
   pandoc input.md --reference-doc=reference.docx -o output.docx
   ```

`pypandoc.get_pandoc_path()` returns the bundled pandoc binary path.

## MARP Slide-Deck Support

MARP (https://marp.app/) is markdown-based presentation format with `---`
slide separators and HTML-comment directives.

**Detection heuristic:**
- YAML frontmatter containing `marp: true`
- Or: multiple `---` separators + HTML comment directives like `<!-- _class: lead -->`

**Stripping:** Remove `marp: true` frontmatter and `<!-- _class: ... -->`
directives. Preserve `---` slide separators as horizontal rules.

## Round-Trip (DOCX → Markdown)

Pandoc's reverse conversion works well for basic documents:
```python
import pypandoc
markdown = pypandoc.convert_file("input.docx", "markdown", extra_args=["--wrap=preserve"])
```

**Known limitation:** SVG-extended DOCX (with `<asvg:svgBlip>`) cannot be
re-parsed by pandoc 3.9 — it fails with exit code 63. The non-SVG version
round-trips cleanly.

## Known Pitfalls

- **pandoc renames image files** when embedding them. Don't rely on filenames
  matching. Use alt-text fingerprints instead.
- **`docPr.find("..")` does not work** in Python's ElementTree. Iterate over
  `wp:inline` / `wp:anchor` elements instead.
- **Namespace registration is required** before writing XML back:
  ```python
  ET.register_namespace("asvg", "http://schemas.microsoft.com/office/drawing/2016/SVG/main")
  ```
- **Content types must be updated** when adding new file types to a DOCX.
  SVG files require `<Default Extension="svg" ContentType="image/svg+xml" />`
  in `[Content_Types].xml`.
- **PEP 668** (Ubuntu 23.04+) blocks `pip install` outside venv. Always create
  a venv for the project: `python3 -m venv venv && source venv/bin/activate`.
