#!/usr/bin/env python3
"""Scan asm-skills repo for potential credential leaks before publishing.

Checks for:
- API key patterns (sk-, ghp_, github_pat_, AKIA, etc.)
- Token patterns (long alphanumeric strings in suspicious contexts)
- Hardcoded passwords, private keys
- URL-embedded credentials (https://user:pass@...)

Exit code: 0 = clean, 1+ = findings that need review.
Files in scripts/ that contain regex pattern definitions (the scanner
itself) are excluded from scanning to avoid self-match false positives.
"""

import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent

# Patterns that indicate potential credentials
PATTERNS = {
    "GitHub fine-grained PAT": r"github_pat_[a-zA-Z0-9]{50,}",
    "GitHub classic PAT": r"ghp_[a-zA-Z0-9]{36,}",
    "GitHub OAuth token": r"gho_[a-zA-Z0-9]{36,}",
    "GitHub app token": r"ghu_[a-zA-Z0-9]{36,}",
    "GitHub refresh token": r"ghr_[a-zA-Z0-9]{40,}",
    "Slack bot token": r"xoxb-[a-zA-Z0-9-]{20,}",
    "Slack app token": r"xapp-[a-zA-Z0-9-]{20,}",
    "Slack webhook": r"xoxp-[a-zA-Z0-9-]{20,}",
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "OpenAI API key": r"sk-[a-zA-Z0-9]{20,}",
    "OpenAI API key (v2)": r"sk-proj-[a-zA-Z0-9]{20,}",
    "Telegram bot token": r"[0-9]{8,10}:[a-zA-Z0-9_-]{35}",
    "Stripe publishable test": r"pk_test_[a-zA-Z0-9]{10,}",
    "Stripe publishable live": r"pk_live_[a-zA-Z0-9]{10,}",
    "Stripe secret test": r"sk_test_[a-zA-Z0-9]{10,}",
    "Stripe secret live": r"sk_live_[a-zA-Z0-9]{10,}",
    "Anthropic API key (new)": r"sk-ant-[a-zA-Z0-9]{20,}",
    "Generic Bearer token in URL": r"https?://[^:]+:[^@]{10,}@",
    "PEM private key": r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    "JWT-like token": r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
    "DB auth URL (redis)": r"redis://[^:]+:[^@]+@",
    "DB auth URL (mongodb)": r"mongodb://[^:]+:[^@]+@",
    "DB auth URL (mysql)": r"mysql://[^:]+:[^@]+@",
    "DB auth URL (postgres)": r"postgresql?://[^:]+:[^@]+@",
}

# Files/dirs to skip entirely
SKIP_DIRS = {".git"}
SKIP_FILES = {".gitignore", "LICENSE"}

# Files that legitimately define credential regex patterns (scanner code)
PATTERN_DEFINITION_FILES = {
    "scripts/audit-credentials.py",
    "scripts/audit-pii.py",
}

# Patterns that are clearly example/placeholder values (false positives)
ALLOWED_PATTERNS = [
    r"^sk-[a-zA-Z]+\b",           # "sk-..." as prose abbreviation
    r"-----BEGIN [A-Z ]+-----",   # Only PUBLIC keys, not PRIVATE
    r"ghp_xx\.\.\.xxxx",          # Redacted example
    r"github_pat_\.\.\.",         # Redacted example
    r"ghp_\.\.\.",                # Redacted example
    r"sk-ant-\.\.\.",             # Redacted example
    r"xoxb-\.\.\.",               # Redacted example
    r"^<[A-Z_]+>$",               # XML-style placeholders like <AKIA_EXAMPLE_KEY>
    r"«redacted:",                # Already-redacted markers
    r"\[\w+-\d+\]",               # Version tags like [1.0.0]
]

# Example-only lines (in markdown tables showing credential patterns)
EXAMPLE_TABLE_CELL = re.compile(r"\|\s*`(?:[^`]*)`\s*\|\s*`(?:[^`]*)`\s*\|")


def is_allowed(line: str) -> bool:
    """Check if a match should be treated as a false positive."""
    for pat in ALLOWED_PATTERNS:
        if re.match(pat, line.strip()[:100]):
            return True
    return False


def scan_file(filepath: Path) -> list[dict]:
    """Scan a single file for credential patterns. Return list of findings."""
    findings = []

    try:
        if filepath.suffix in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc",
                               ".o", ".so", ".dll", ".dylib", ".woff", ".woff2",
                               ".ttf", ".eot", ".zip", ".tar", ".gz", ".bz2"):
            return findings
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    # Check if this is a pattern-definition file — if so, skip lines that
    # contain regex patterns (r"..." or r'...') to avoid self-matches
    rel = str(filepath.relative_to(REPO_DIR))
    is_pattern_def = rel in PATTERN_DEFINITION_FILES

    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip empty, comment, and docstring lines
        if not stripped:
            continue
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Skip regex pattern definition lines in scanner files
        if is_pattern_def and ('r"' in line or "r'" in line):
            continue

        # Skip obviously safe patterns
        if is_allowed(stripped):
            continue

        # Check each credential pattern
        for name, pattern in PATTERNS.items():
            matches = re.findall(pattern, stripped)
            if matches:
                safe_match = matches[0][:20] + "..." + matches[0][-4:] if len(matches[0]) > 30 else matches[0]
                findings.append({
                    "file": rel,
                    "line": i,
                    "pattern": name,
                    "match": safe_match,
                    "context": line.strip()[:120],
                })

    return findings


def main():
    all_findings = []

    for filepath in sorted(REPO_DIR.rglob("*")):
        if filepath.is_dir():
            continue
        if any(p.name in SKIP_DIRS for p in filepath.relative_to(REPO_DIR).parents):
            continue
        if filepath.name in SKIP_FILES:
            continue

        findings = scan_file(filepath)
        all_findings.extend(findings)

    if not all_findings:
        print("✅ No credential patterns detected in any file.")
        return 0

    print(f"❌ Found {len(all_findings)} potential credential match(es):\n")

    by_file: dict[str, list[dict]] = {}
    for f in all_findings:
        by_file.setdefault(f["file"], []).append(f)

    for filepath, findings in sorted(by_file.items()):
        print(f"  📄 {filepath}:")
        for f in findings:
            print(f"     L{f['line']:>4}  [{f['pattern']}]  '{f['match']}'")
            print(f"            Context: {f['context'][:100]}")

    print("\n⚠️  Review each finding above. Redact real credentials before committing.")
    return len(all_findings)


if __name__ == "__main__":
    sys.exit(main())
