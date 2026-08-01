# Mirror a Live Static Site into Version Control

When the user asks to bring a live site under version control (e.g. for migration or editing):

## Steps

1. **Investigate current hosting** — curl headers (`curl -sI https://site.com`), extract content (`web_extract`), note framework/type
2. **Mirror with wget:**
   ```bash
   wget --mirror --page-requisites --no-parent --convert-links --adjust-extension \
        --no-host-directories --restrict-file-names=unix \
        --directory-prefix=. https://site.com/
   ```
3. **Clean up:**
   - Remove `cdn-cgi/` directory (Cloudflare injection, not part of the site)
   - Clean up `robots.txt` if it got corrupted by the wget conversion
4. **Create a `.gitignore`** (Cloudflare Pages, OS files)
5. **Add `AGENTS.md`** with site structure, editing conventions, and deployment notes — this makes the repo agent-editable in future sessions
6. **Add `README.md`** with one-liner and migration/editing plan
7. **Create private GitHub repo:**
   ```bash
   gh repo create owner/repo-name --private --description "..." --homepage "https://site.com"
   ```
8. **Init, commit, push:**
   ```bash
   git init && git add -A && git commit -m "Initial: mirror site.com from <origin>"
   git branch -M main
   git remote add origin https://github.com/owner/repo-name.git
   git push -u origin main
   ```

## Why AGENTS.md

Without an AGENTS.md, the next agent session has to rediscover the site structure from scratch. With it, any future Hermes, Claude, or Codex session can start editing immediately.

## Pitfalls

- wget's `--convert-links` can corrupt `robots.txt` on Cloudflare-proxied sites — rewrite it from scratch
- Some Squarespace/Wix sites include injected JS that isn't part of the actual site content — don't mirror those dynamically
- Google Fonts preconnect links are fine to keep (they're external references, not embedded content)
