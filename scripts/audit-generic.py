#!/usr/bin/env python3
"""Scan the skills repo for identifying topical markers before publishing.

Reads the marker list from `.audit-generic-markers.json` (repo root, PRIVATE —
gitignored, never committed). If that file is missing, falls back to the
committed `.audit-generic-markers.example.json` (CI / unconfigured mode:
placeholder markers only, always clean). If neither exists, exits with an error.

Exit codes:
  0 = clean (no marker hits)
  1 = marker hits found (review/redact before push)
  2 = configuration error (no markers file found)

Marker schema (.audit-generic-markers.json):
  {
    "markers": {"proper_nouns": [], "projects": [], "orgs": [], "jargon": [], "paths": []},
    "exclude_files": []
  }

Rules:
- All markers match case-insensitively as substrings of a line.
- Files listed in `exclude_files` (repo-root-relative paths) are skipped —
  used for root identity docs (README/SKILL/AGENTS/CLAUDE) and meta-docs that
  legitimately name the repo, org, or a tool they document.
- A marker that matches a skill's own directory name (case-insensitive
  substring) is allowed inside that skill's own directory: a skill
  legitimately names itself; the marker exists to catch that name leaking
  into OTHER skills' content.
- Gitignored files are skipped (only publishable content is scanned).
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent

PRIVATE_CONFIG = REPO_DIR / ".audit-generic-markers.json"
EXAMPLE_CONFIG = REPO_DIR / ".audit-generic-markers.example.json"

# Binary / non-text suffixes never scanned
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc",
    ".o", ".so", ".dll", ".dylib", ".woff", ".woff2",
    ".ttf", ".eot", ".zip", ".tar", ".gz", ".bz2",
}

# Scanner files that define the matching logic itself (self-skip, like the
# credential/PII scanners skip their own pattern definitions). The example
# markers config is also skipped — its placeholder markers are the config
# itself, not publishable content.
SELF_SKIP = {"scripts/audit-generic.py", ".audit-generic-markers.example.json"}

MARKER_CATEGORIES = ["proper_nouns", "projects", "orgs", "jargon", "paths"]


def is_gitignored(rel_path: Path) -> bool:
    """True if the file is ignored by git (never committed -> never published)."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-q", str(rel_path)],
            cwd=REPO_DIR, capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def skill_name_for(rel_path: Path) -> str:
    """Skill dir name for paths like skills/<category>/<name>/...; '' otherwise."""
    parts = rel_path.parts
    if len(parts) >= 3 and parts[0] == "skills":
        return parts[2]
    return ""


def load_markers() -> tuple[dict, str]:
    """Return (config, mode) where mode is 'local' or 'example'."""
    if PRIVATE_CONFIG.exists():
        return json.loads(PRIVATE_CONFIG.read_text(encoding="utf-8")), "local"
    if EXAMPLE_CONFIG.exists():
        return json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8")), "example"
    print(
        "❌ No marker config found.\n"
        f"   Expected {PRIVATE_CONFIG.name} or {EXAMPLE_CONFIG.name} at repo root.\n"
        "   Copy the example and fill in your private markers:\n"
        f"     cp {EXAMPLE_CONFIG.name} {PRIVATE_CONFIG.name}\n"
        "   Keep it private — never commit it. (If even the example is missing,\n"
        "   re-clone the repo or restore .audit-generic-markers.example.json.)"
    )
    sys.exit(2)


def main() -> int:
    config, mode = load_markers()

    markers: list[tuple[str, str]] = []
    for category in MARKER_CATEGORIES:
        for marker in config.get("markers", {}).get(category, []):
            marker = str(marker).strip()
            if marker:
                markers.append((category, marker))

    exclude_files = {str(f) for f in config.get("exclude_files", [])}

    if mode == "example":
        print(
            f"ℹ️  Using committed example markers ({EXAMPLE_CONFIG.name}) — "
            "no private marker config found. "
            "In CI this is expected; locally, copy the example to "
            f"{PRIVATE_CONFIG.name} and fill in your real markers for enforcement.\n"
        )

    if not markers:
        print("✅ No markers configured — nothing to scan for.")
        return 0

    findings: list[dict] = []

    for filepath in sorted(REPO_DIR.rglob("*")):
        if filepath.is_dir():
            continue
        if ".git" in filepath.relative_to(REPO_DIR).parts:
            continue
        if filepath.suffix.lower() in BINARY_SUFFIXES:
            continue

        rel = filepath.relative_to(REPO_DIR)
        rel_str = str(rel)

        if rel_str in SELF_SKIP:
            continue
        if rel_str in exclude_files:
            continue
        if is_gitignored(rel):
            continue

        try:
            lines = filepath.read_text(encoding="utf-8", errors="replace").split("\n")
        except Exception:
            continue

        skill_name = skill_name_for(rel)
        for i, line in enumerate(lines, 1):
            lowered = line.lower()
            for category, marker in markers:
                ml = marker.lower()
                if ml not in lowered:
                    continue
                # A skill may name itself inside its own directory
                if skill_name and ml in skill_name.lower():
                    continue
                findings.append({
                    "file": rel_str,
                    "line": i,
                    "category": category,
                    "marker": marker,
                    "context": line.strip()[:120],
                })

    if not findings:
        print(f"✅ No genericness markers detected (mode: {mode}, {len(markers)} markers).")
        return 0

    print(f"❌ Found {len(findings)} marker hit(s) needing review:\n")
    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    for filepath, hits in sorted(by_file.items()):
        print(f"  📄 {filepath}:")
        for h in hits:
            print(f"     L{h['line']:>4} → [{h['category']}] {h['marker']}")
            print(f"            Context: {h['context'][:100]}")

    print("\n⚠️  Review each hit. Redact or genericize identifying content, or add")
    print("   legitimately self-referential files to 'exclude_files' in the marker")
    print("   config. Re-run until clean before pushing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
