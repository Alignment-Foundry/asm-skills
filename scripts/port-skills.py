#!/usr/bin/env python3
"""Port user-created skills from a Hermes local store to the published skills repo.

Holdlist gate (.publish-holdlist.md at repo root — PRIVATE, gitignored):
  - Skills whose holdlist status is not `approved` are SKIPPED and reported as
    "on hold — pending Alex review". Nothing new publishes without approval.
  - Skills missing from the holdlist (new) are auto-added as `pending-review`
    and skipped, so the first run after a new skill appears just flags it.
  - An `approved` skill whose content changed since the last port is flipped
    back to `pending-review` and skipped until re-approved.

Path configuration (this repo is public — no local paths are hardcoded):
  HERMES_PROFILE_DIR   — local profile root, e.g. /home/you/.hermes/profiles/alpha
  HERMES_PROJECTS_DIR  — local projects root, e.g. /home/you/projects
  PORT_SKILLS          — optional comma-separated subset of SKILLS_TO_PORT
The {profile}/{projects} placeholders below are documentation defaults; set the
env vars to run.
"""

import hashlib
import os
import shutil
import sys
from datetime import date
from pathlib import Path

PROFILE_DIR = os.environ.get("HERMES_PROFILE_DIR", "{profile}")
PROJECTS_DIR = os.environ.get("HERMES_PROJECTS_DIR", "{projects}")

USER_SKILLS_DIR = Path(PROFILE_DIR) / "skills"
REPO_DIR = Path(PROJECTS_DIR) / "asm-skills"
REPO_SKILLS_DIR = REPO_DIR / "skills"
HOLDLIST_FILE = REPO_DIR / ".publish-holdlist.md"

# User-created skills (not in bundled Hermes manifest)
SKILLS_TO_PORT = [
    "autonomous-ai-agents/paperclip-company",
    "github/github-org-ops",
    "mlops/langfuse",
    "monitoring/nous-credits-check",
    "productivity/digital-chief-of-staff",
    "productivity/local-tts",
    "productivity/network-connectivity-diagnostics",
    "productivity/project-catalog",
    "productivity/special-projects-manager",
    "productivity/structured-reference-delivery",
    "security/password-store-vault",
    "software-development/cross-agent-skill-repo",
    "software-development/dox-scaffold",
    "software-development/efficient-operation",
    "software-development/markdown-publishing",
    "software-development/mcp-server-builder",
    "software-development/python-cli-tools",
    "software-development/test-fixture-authoring",
]

# Hermes-internal files to skip
SKIP_FILES = {".curator_backups", ".curator_state", ".hub", ".usage.json", ".usage.json.lock"}

HOLDLIST_HEADER = """# Publish Holdlist — PRIVATE review state (gitignored, never committed)

Status: `pending-review` (default for any new/updated skill), `approved`, `blocked`.
Skills other than `approved` are skipped by `scripts/port-skills.py`.

| skill | status | reason | date | notes |
|-------|--------|--------|------|-------|
"""


def read_holdlist() -> dict[str, dict]:
    """Parse holdlist table into {skill: {status, reason, date, notes}}."""
    entries: dict[str, dict] = {}
    if not HOLDLIST_FILE.exists():
        return entries
    for line in HOLDLIST_FILE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| skill") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0]:
            continue
        entries[cells[0]] = {
            "status": cells[1],
            "reason": cells[2],
            "date": cells[3],
            "notes": cells[4] if len(cells) > 4 else "",
        }
    return entries


def write_holdlist(entries: dict[str, dict]) -> None:
    """Rewrite holdlist table, sorted by skill path."""
    HOLDLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines = [HOLDLIST_HEADER.rstrip("\n")]
    for skill in sorted(entries):
        e = entries[skill]
        notes = e.get("notes", "").replace("|", "/")
        lines.append(f"| {skill} | {e['status']} | {e['reason']} | {e['date']} | {notes} |")
    HOLDLIST_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def dir_hash(skill_dir: Path) -> str:
    """SHA-256 over sorted (relative path, content) pairs of a skill dir."""
    h = hashlib.sha256()
    for p in sorted(skill_dir.rglob("*")):
        if p.is_dir():
            continue
        rel_parts = p.relative_to(skill_dir).parts
        if any(part in SKIP_FILES for part in rel_parts):
            continue
        if p.name in SKIP_FILES:
            continue
        h.update(str(p.relative_to(skill_dir)).encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def port_skill(source_dir: Path, target_dir: Path) -> list[str]:
    """Port a single skill, return list of created files."""
    created = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for src_path in source_dir.rglob("*"):
        rel_parts = src_path.relative_to(source_dir).parts
        if any(p.name in SKIP_FILES for p in src_path.relative_to(source_dir).parents):
            continue
        if src_path.name in SKIP_FILES:
            continue
        rel = src_path.relative_to(source_dir)
        dst_path = target_dir / rel
        if src_path.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)
            created.append(str(rel))
    return created


def main() -> int:
    if "{profile}" in str(USER_SKILLS_DIR) or "{projects}" in str(REPO_DIR):
        print(
            "❌ Path placeholders not resolved.\n"
            "   Set the env vars before running:\n"
            "     HERMES_PROFILE_DIR=/home/you/.hermes/profiles/alpha \\\n"
            "     HERMES_PROJECTS_DIR=/home/you/projects \\\n"
            "     python3 scripts/port-skills.py\n"
            "   (This repo is public, so no local paths are hardcoded.)"
        )
        return 1

    skills = SKILLS_TO_PORT
    override = os.environ.get("PORT_SKILLS", "").strip()
    if override:
        skills = [s.strip() for s in override.split(",") if s.strip()]

    entries = read_holdlist()
    changed = False
    stats = {"ported": 0, "held": 0, "new": 0, "updated": 0, "files": 0, "errors": []}

    for skill_path in skills:
        src = USER_SKILLS_DIR / skill_path
        dst = REPO_SKILLS_DIR / skill_path

        if not src.exists():
            stats["errors"].append(f"NOT FOUND in profile: {skill_path}")
            continue

        entry = entries.get(skill_path)

        # New skill — auto-add to holdlist as pending-review, don't port
        if entry is None:
            entries[skill_path] = {
                "status": "pending-review",
                "reason": "new skill — auto-added by port",
                "date": date.today().isoformat(),
                "notes": "awaiting Alex approval — nothing new publishes without it",
            }
            changed = True
            stats["new"] += 1
            print(f"🆕 {skill_path} — NEW: added to holdlist as pending-review; on hold — pending Alex review")
            continue

        status = entry["status"]

        # Approved skill whose content changed — flip back to pending-review
        if status == "approved" and dst.exists() and dir_hash(src) != dir_hash(dst):
            entries[skill_path] = {
                "status": "pending-review",
                "reason": "content updated — flipped by port",
                "date": date.today().isoformat(),
                "notes": "re-approve in the holdlist to publish this update",
            }
            changed = True
            stats["updated"] += 1
            print(f"🔄 {skill_path} — UPDATED: flipped to pending-review; on hold — pending Alex review")
            continue

        if status != "approved":
            stats["held"] += 1
            print(f"⏸️  {skill_path} — on hold — pending Alex review (status: {status})")
            continue

        # Approved + unchanged (or approved but not yet present) — port
        files = port_skill(src, dst)
        stats["ported"] += 1
        stats["files"] += len(files)
        print(f"✅ {skill_path} — ported ({len(files)} files)")

    if changed:
        write_holdlist(entries)
        print(f"\n📋 Holdlist updated: {HOLDLIST_FILE}")

    print(f"\n{'='*50}")
    print(f"Port complete: {stats['ported']} ported, {stats['held']} held, "
          f"{stats['new']} new (auto-flagged), {stats['updated']} updated (re-flagged)")
    if stats["errors"]:
        print(f"\n⚠️  {len(stats['errors'])} errors:")
        for e in stats["errors"]:
            print(f"  • {e}")
        return 1

    print("\n⚠️  Before pushing, run all three audits (all must exit 0):")
    print("  python3 scripts/audit-credentials.py")
    print("  python3 scripts/audit-pii.py")
    print("  python3 scripts/audit-generic.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
