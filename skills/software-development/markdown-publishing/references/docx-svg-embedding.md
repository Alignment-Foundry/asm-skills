# SVG Embedding in DOCX for Word-Editable Shapes

The technique for adding vector SVG images to Word DOCX files so they render
natively and can be converted to editable shapes via right-click → "Convert to Shapes".

## How It Works

Word 2016+ (Office 2019+) supports SVG images via a DrawingML extension.
The SVG is stored as a regular image part (`word/media/*.svg`) and referenced
from the document XML through an `<asvg:svgBlip>` extension element.

## OpenXML Structure

### 1. SVG image part in `word/media/`

Place the SVG file alongside the PNG fallback:
```
word/media/
├── rId9.png    # PNG fallback (pandoc embeds this)
├── rId9.svg    # SVG vector (added by post-processor)
├── rId13.png
└── rId13.svg
```

### 2. Relationship in `word/_rels/document.xml.rels`

```xml
<Relationship
  Id="rIdSvg1"
  Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
  Target="media/rId9.svg" />
```

### 3. SVG blip extension in `word/document.xml`

Inside the existing `<a:blip>` element (added by pandoc for the PNG), add an
`<a:extLst>` containing an SVG extension:

```xml
<a:blip r:embed="rId9">
  <a:extLst>
    <a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}">
      <asvg:svgBlip r:embed="rIdSvg1" />
    </a:ext>
  </a:extLst>
</a:blip>
```

The URI `{96DAC541-7B7A-43D3-8B79-37D633B846F1}` is the magic identifier
Word uses to recognise SVG extensions.

### 4. Content type in `[Content_Types].xml`

```xml
<Default Extension="svg" ContentType="image/svg+xml" />
```

Without this, pandoc exits with code 63 and Word may not render the SVG.

## Python Implementation

### Finding mermaid images by alt-text fingerprint

Pandoc preserves markdown alt text (`![alt](src)`) in the `docPr/@descr` attribute:

```python
NS = {
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "asvg": "http://schemas.microsoft.com/office/drawing/2016/SVG/main",
}

for inline in root.iter(f"{{{NS['wp']}}}inline"):
    docPr = inline.find(f"{{{NS['wp']}}}docPr")
    descr = docPr.get("descr", "")
    fp_match = re.search(r"\[fp:([a-f0-9]+)\]", descr)
    if not fp_match:
        continue
    # Found a mermaid image — navigate to its blip
    blip = inline.find(f".//{{{NS['a']}}}blip")
    embed = blip.get(f"{{{NS['r']}}}embed")
```

### Adding the SVG extension

```python
# Add relationship
new_rel = ET.SubElement(rels_root, f"{{{NS['rel']}}}Relationship")
new_rel.set("Id", rid)
new_rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image")
new_rel.set("Target", f"media/{svg_filename}")

# Add SVG blip extension
ext_list = blip.find(f"{{{NS['a']}}}extLst")
if ext_list is None:
    ext_list = ET.Element(f"{{{NS['a']}}}extLst")
    blip.append(ext_list)

svg_ext = ET.SubElement(ext_list, f"{{{NS['a']}}}ext")
svg_ext.set("uri", "{96DAC541-7B7A-43D3-8B79-37D633B846F1}")
svg_blip = ET.SubElement(svg_ext, f"{{{NS['asvg']}}}svgBlip")
svg_blip.set(f"{{{NS['r']}}}embed", rid)
```

### Rebuilding the DOCX zip

Always write the `[Content_Types].xml` first (if modified), then re-zip:

```python
import zipfile, os
with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(tmpdir):
        for fname in files:
            fpath = Path(root) / fname
            arcname = str(fpath.relative_to(tmpdir))
            zout.write(fpath, arcname)
```

## Limitations

| Issue | Detail |
|-------|--------|
| **Word version** | SVG rendering requires Word 2016+. Older versions show the PNG fallback. |
**Pandoc round-trip** | Pandoc 3.9 cannot parse SVG-extended DOCX (exit code 63). Ingest works on non-SVG versions. |
**ElementTree `find("..")`** | Python's C implementation of `xml.etree.ElementTree` returns `None` for `find("..")`. Never walk up — always iterate over the parent elements (e.g. `wp:inline`) and navigate down to both `docPr` and `blip`. |
**SVG complexity**
| **Namespace registration** | `ET.register_namespace("asvg", ...)` must be called BEFORE parsing/creating elements or the namespace prefix renders as `ns0` instead of `asvg`. |

## Verification

```bash
# Check SVG files are embedded
python3 -c "
import zipfile
z = zipfile.ZipFile('output.docx', 'r')
for n in z.namelist():
    if 'svg' in n.lower():
        print(f'{n}: {len(z.read(n))} bytes')
z.close()
"

# Check SVG blip extensions exist
python3 -c "
import zipfile, xml.etree.ElementTree as ET
z = zipfile.ZipFile('output.docx', 'r')
root = ET.fromstring(z.read('word/document.xml'))
ns = {'asvg': 'http://schemas.microsoft.com/office/drawing/2016/SVG/main'}
count = sum(1 for _ in root.iter(f'{{{ns[\"asvg\"]}}}svgBlip'))
print(f'SVG blips: {count}')
z.close()
"

# Check content type
python3 -c "
import zipfile
z = zipfile.ZipFile('output.docx', 'r')
ct = z.read('[Content_Types].xml').decode()
print('SVG type:', 'svg' in ct and 'image/svg+xml' in ct)
z.close()
"
```

## References

- [Microsoft docs: SVGBlip class](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.office2019.drawing.svg.svgblip)
- [Eidias blog: Insert SVG into Word via OpenXML](https://www.eidias.com/blog/2022/9/14/openxml-insert-svg-image-into-word-document)
- [python-docx GitHub issue #651 (SVG support)](https://github.com/python-openxml/python-docx/issues/651)
