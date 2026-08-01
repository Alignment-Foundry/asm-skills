#!/usr/bin/env python3
"""Validate all SKILL.md files in the skills/ directory.

Checks:
- Valid YAML frontmatter (starts with ---, parses correctly)
- name and description fields present
- Description ≤ 1024 chars
- Body non-empty after frontmatter
- Total file size within limits (100KB max)
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

MAX_DESC = 1024
MAX_SIZE = 100_000

errors = []


def check_skill(skill_dir: Path) -> None:
    sk_path = skill_dir / "SKILL.md"

    # SKILL.md must exist
    if not sk_path.exists():
        errors.append(f"{skill_dir.relative_to(REPO_ROOT)}/: Missing SKILL.md")
        return

    content = sk_path.read_text(encoding="utf-8")

    # File size check
    if len(content) > MAX_SIZE:
        errors.append(
            f"{sk_path.relative_to(REPO_ROOT)}: {len(content):,} chars exceeds max {MAX_SIZE:,}"
        )

    # Must start with ---
    if not content.startswith("---"):
        errors.append(
            f"{sk_path.relative_to(REPO_ROOT)}: Must start with '---' (found {repr(content[:20])})"
        )
        return

    # Extract frontmatter
    fm_match = re.search(r"\n---\s*\n", content[3:])
    if not fm_match:
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: No closing '---' found in frontmatter")
        return

    fm_text = content[3:3 + fm_match.start()]
    body = content[3 + fm_match.end():]

    # Parse YAML
    try:
        import yaml
        fm = yaml.safe_load(fm_text)
    except ImportError:
        # Fallback: basic validation without PyYAML
        fm = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    except Exception as e:
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: YAML parse error: {e}")
        return

    if not isinstance(fm, dict):
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: Frontmatter did not parse as a mapping")
        return

    # name field
    name = fm.get("name")
    if not name:
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: Missing or empty 'name' field")

    # description field
    desc = fm.get("description")
    if not desc:
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: Missing or empty 'description' field")
    elif len(desc) > MAX_DESC:
        errors.append(
            f"{sk_path.relative_to(REPO_ROOT)}: Description is {len(desc)} chars (max {MAX_DESC})"
        )

    # Body must be non-empty
    if not body.strip():
        errors.append(f"{sk_path.relative_to(REPO_ROOT)}: Body after frontmatter is empty")


def main():
    skill_dirs = sorted(SKILLS_DIR.rglob("SKILL.md"))

    if not skill_dirs:
        print(f"No SKILL.md files found under {SKILLS_DIR}")
        sys.exit(0)

    for sk_path in skill_dirs:
        check_skill(sk_path.parent)

    # Summary
    total = len(set(s.parent for s in skill_dirs))

    if errors:
        print(f"❌ {len(errors)} validation error(s) in {total} skills:\n")
        for e in errors:
            print(f"  • {e}")
    else:
        print(f"✅ All {total} skills validated — no errors")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
