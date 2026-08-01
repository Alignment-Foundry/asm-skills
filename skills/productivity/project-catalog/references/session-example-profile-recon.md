# Session Example: Profile Recon CLI

Demonstrates the full lifecycle of a project entry in one session: ⚪ Idea → 🟢 Active with working code → report delivered.

## Flow

1. the user says "New project idea, I want a tool..." → Entry created at ⚪ Idea
2. the user says "I want to go with on this search project" → Status moved to 🟢 Active
3. Built the tool (Python, Docker, PhoneInfoga, ignorant, etc.)
4. Tested with a real phone number → iterated on output format
5. Markdown report generated and sent as file

## Key Patterns Applied

- **Parallel writes**: All project files created in one batch when multiple ideas mentioned
- **Status draft then confirm**: the user corrected ⚪ Idea → 🟢 Active (tool had alpha code)
- **No blocker stops build**: gh auth was broken → built anyway, noted as follow-up
- **Project file updated after build**: Notes section swapped "todo" for "done ✓" after completion

## Example Catalog Entry Evolution

**Stage 1 — Idea:**
```
**Status:** ⚪ Idea
**Next Steps:**
- [ ] Research available data sources & APIs
- [ ] Decide on language
```

**Stage 2 — Active + built:**
```
**Status:** 🟢 Active
**Key Files:**
- {projects}/{private-repo-profile-recon}/ — source
- Docker image: {private-repo-profile-recon}:latest

**Notes:**
- ✅ CLI with click + rich
- ✅ 5 data sources: holehe, domain, phone_validate, username_search, web_search
...
```
