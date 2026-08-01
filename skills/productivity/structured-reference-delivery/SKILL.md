---
name: structured-reference-delivery
category: productivity
version: 1.1
description: "Research multi-source topics, compile structured data, and deliver formatted Excel/CSV reference files with color-coded sheets, data validation, and proper Excel formatting. Covers the full pipeline from web research to a polished .xlsx workbook."
triggers:
  - user asks for a reference document, study guide, or structured data file
  - user asks to compile research into Excel/CSV/structured format
  - multi-source research needs to become a formatted deliverable
---

# Structured Reference Delivery

Research multi-source topics → compile structured data → deliver as formatted file (Excel, CSV, markdown tables, etc.). Covers the full pipeline from gathering cross-referenced data to producing a polished, color-coded, multi-sheet workbook the user can open immediately.

## Workflow

### 1. Multi-source research
Gather from 3+ authoritative sources. Cross-reference dates, spellings, and facts. For calendar / schedule / reference content, prefer:
- **The domain's authoritative calendar source** — the canonical schedule for the subject (league schedules, term dates, cycle calendars, release calendars)
- **A secondary verification source** — confirm individual dates/entries against a second independent site to catch discrepancies
- **Wikipedia** — canonical lists, official ranges, and summary tables
- **Domain-specific commentary or reference sites** — seasonal context, explanations, and nuance from recognized authorities in the subject

**Cross-reference pattern:** Pull a full-period grid from the primary calendar source, then verify individual entries against a secondary source to catch discrepancies.

### 2. Compile structured data
Write data as JSON or Python list-of-dicts. This is the **source of truth** — the build script reads it, not inline constants.

```python
# /tmp/reference_data.json — one file for all rows
[
  {
    "week": 1,
    "period": "2026-10-05",
    "event": "Season opener",
    "subtype": "regular",
    "details": "Home venue, 7:00 PM",
    "notes": "Marquee matchup"
  },
  {
    "week": 2,
    "period": "2026-10-12",
    "event": "Week 2",
    "subtype": "regular",
    "details": "Away",
    "notes": ""
  },
  ...
]
```

### 3. Build the deliverable
Write a standalone Python script that reads the JSON and generates the file. Use **openpyxl** for .xlsx output.

#### openpyxl boilerplate

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

wb = openpyxl.Workbook()

# Reusable styles
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
cat_fill_a  = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")  # yellow
cat_fill_b  = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")  # green
cat_fill_c  = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")  # peach
thin_border = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
wrap        = Alignment(wrap_text=True, vertical='top')
```

**Multi-sheet structure** (example from a periodic schedule guide):
| Sheet | Purpose |
|---|---|
| Schedule / Main Grid | Full data grid with color-coded rows, auto-filter, freeze pane |
| Reference | Standalone reference table (special dates, definitions) |
| Tracker | Replica period list + editable columns + dropdowns |
| Legend | Color key, notes, caveats |

**Row colouring strategy:**
```python
for row_data in entries:
    fill = cat_fill_b if row_data['event'] in combined_set else \
           cat_fill_a if row_data.get('subtype') == 'special' else \
           cat_fill_c if row_data.get('notes') else None
    if fill:
        for ci in range(1, n_cols+1):
            ws.cell(row=r, column=ci).fill = fill
```

**Data validation (dropdowns for tracking)**
```python
dv_method = DataValidation(type="list", formula1='\"A,B,C,Text,Audio\"', allow_blank=True)
ws.add_data_validation(dv_method)
dv_method.add(f'D2:D{max_row}')
```

**Freeze + filter**
```python
ws.freeze_panes = 'A2'
ws.auto_filter.ref = f"A1:{get_column_letter(n_cols)}{n_rows+1}"
```

### 4. Handle tool limits
When the script + data together exceed `execute_code` content limits (script + data > ~50KB or the 5-min timeout):

1. **Write JSON data** via `write_file(path='/tmp/data.json', content=json_data)` 
2. **Write the Python build script** via `write_file(path='/tmp/build.py', content=script)`
3. **Run via terminal**: `cd /tmp && pip install openpyxl 2>&1 | tail -3 && python3 build.py`
4. **Verify** with `ls -lh {user_home}/output.xlsx`

This avoids the execute_code timeout/block that occurs when large inline code is submitted.

### 5. Deliver
- Save to `{user_home}/<descriptive-name>.xlsx`
- Check file size with `ls -lh`
- Deliver as `MEDIA:{user_home}/filename.xlsx` in the response (Telegram auto-sends native files)
- Include a summary table in the response text showing what's in each sheet

## Reference files in this skill

| File | Content |
|---|---|
| (deliverable-specific seed data stays local) | Keep period-specific reference data (e.g. a cycle-calendar reference) out of the published copy — publish only the generic workflow. |

## Pitfalls

- **execute_code timeout on large payloads** — always split data + script for complex workbooks. execute_code is fine for lightweight analysis (3-5 rows), but 50+ rows + formatting + multi-sheet logic belongs in separate files.
- **Missing openpyxl** — check and install first: `pip install openpyxl 2>&1 | tail -3`
- **Non-Latin scripts in Excel** — openpyxl handles UTF-8 natively. If non-Latin characters render as boxes, the viewer needs the relevant font installed (not a file issue).
- **Period gaps** — some periods have no regular entry (overlapping special dates). Account for these gaps when numbering — the canonical entry count is the total across the cycle, not the number of actual periods in a given year.
- **Year-type variations** — some calendars shift by year type (leap years, aligned vs. offset years); combined entries differ by year type. Always verify the specific year's schedule.
