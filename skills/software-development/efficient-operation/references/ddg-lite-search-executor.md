# DuckDuckGo Lite Search Execution

Free, no-auth approach to executing search queries programmatically and getting parseable results. Used as the default backend for the `dork_executor` source in {private-repo-profile-recon}.

## Why DDG Lite

- **No API key needed** — unlike Google Custom Search
- **No rate limit signup** — unlike most commercial APIs
- **Parseable HTML** — structured table format, not JavaScript-rendered
- **POST-based** — accepts form data at `https://lite.duckduckgo.com/lite/`
- **Works for dork queries** — `site:facebook.com "phone"` syntax works

## API Endpoint

```
POST https://lite.duckduckgo.com/lite/
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36

q=site:facebook.com "+13365755348"
```

## HTML Structure to Parse

```html
<tr>
  <td valign="top">1.&nbsp;</td>
  <td>
    <a rel="nofollow" href="//duckduckgo.com/l/?uddg=https%3A%2F%2F...&rut=..."
       class='result-link'>Result Title</a>
  </td>
</tr>
<tr>
  <td>&nbsp;&nbsp;&nbsp;</td>
  <td class='result-snippet'>Snippet text here</td>
</tr>
<tr>
  <td>&nbsp;&nbsp;&nbsp;</td>
  <td><span class='link-text'>example.com</span></td>
</tr>
```

## Python Parser (reusable)

```python
import re
from urllib.parse import unquote

def parse_ddg_lite_results(html: str) -> list[dict]:
    results = []
    links = re.findall(
        r'<a\s+rel="nofollow"\s+href="([^"]+)"[^>]*class=\'result-link\'[^>]*>(.*?)</a>',
        html, re.DOTALL,
    )
    snippets = re.findall(
        r"<td\s+class='result-snippet'[^>]*>(.*?)</td>",
        html, re.DOTALL,
    )
    for i, (href, title) in enumerate(links):
        actual_url = href
        uddg = re.search(r"uddg=([^&]+)", href)
        if uddg:
            actual_url = unquote(uddg.group(1))
        title_clean = re.sub(r"<[^>]+>", "", title).strip()
        snippet = snippets[i].strip() if i < len(snippets) else ""
        snippet_clean = re.sub(r"<[^>]+>", "", snippet).strip()
        if title_clean:
            results.append({
                "title": title_clean[:200],
                "url": actual_url,
                "snippet": snippet_clean[:300],
            })
    return results
```

## Rate Limiting

- DDG Lite tolerates ~1 request per 500ms
- At 15 queries, expect ~7-12 seconds total execution time
- No IP blocks observed at this rate for legitimate queries
- Consider using exponential backoff on 429 responses

## Limitations

- Returns fewer results than Google (typically 5-10 per query)
- Some dork operators work differently than Google (`site:` works, `intext:` may not)
- Results are HTML only — no JSON API
- DDG may return zero-click info pages instead of web results for some queries
