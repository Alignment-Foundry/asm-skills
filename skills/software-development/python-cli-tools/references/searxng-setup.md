# SearXNG Setup for CLI Tool Integration

## Why SearXNG

SearXNG is a self-hosted metasearch engine that aggregates results from Google, DuckDuckGo, Bing, Brave, and others. It returns JSON results via a REST API, making it suitable as a backend for CLI tools that need to execute search queries and get real results.

## Key Constraints

- **JSON format disabled by default** — must be enabled via custom `settings.yml`
- **Rate limiting by upstream engines** — SearXNG's default limiter is fine (it queues requests), but upstream engines (Brave, DDG, Google) may return rate-limit errors
- **Network isolation** — SearXNG runs in its own container; the main tool connects via a shared Docker network

## Required Configuration

### `searxng/settings.yml`

```yaml
use_default_settings: true
server:
  secret_key: "choose-a-random-secret"
  bind_address: "0.0.0.0"
  image_proxy: true
  limiter: false
search:
  formats:
    - html
    - json
```

Without `search.formats` including `json`, the API returns 403.

### Docker Compose

```yaml
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
```

`CAP_NET_RAW` is needed for SearXNG's ping-based engine health checks.

## API Usage

```
GET /search?q=<query>&format=json&language=en-US
Accept: application/json
```

Response:
```json
{
  "query": "site:facebook.com +13365755348",
  "results": [
    {"title": "...", "url": "...", "content": "snippet..."}
  ],
  "unresponsive_engines": [
    ["brave", "too many requests"],
    ["duckduckgo", "CAPTCHA"]
  ]
}
```

The `unresponsive_engines` list is normal — different upstreams rate-limit at different times. Results come from whichever engines respond.

## Testing

```bash
# Start SearXNG independently
docker run -d --name searxng \
  -e SEARXNG_BASE_URL=http://localhost:18080/ \
  -v $(pwd)/searxng/settings.yml:/etc/searxng/settings.yml:ro \
  -p 18080:8080 \
  searxng/searxng:latest

# Test API
curl -s "http://localhost:18080/search?q=test&format=json" \
  -H "Accept: application/json" | python3 -m json.tool

# Connect from another container
docker run --rm --network host \
  -e RECON_SEARCH_BACKEND=searxng \
  -e RECON_SEARXNG_URL=http://localhost:18080 \
  mytool --query "..."
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| HTTP 403 | JSON format not enabled | Add `search.formats: [html, json]` to settings.yml |
| HTTP 000 / connection refused | Container not running or wrong network | Check `docker ps`, verify network assignment |
| Empty results array | No engines responded or query matched nothing | Check `unresponsive_engines` in response |
| "too many requests" per upstream | Rate limited — normal, retry later | Engines rotate — some will work |
