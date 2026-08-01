#!/usr/bin/env python3
"""Scan for PII: real emails, phone numbers, and IPs in repo files.

Filters out well-known safe domains, private IP ranges, localhost, and
placeholder patterns. Exit code: 0 = clean, 1+ = findings.
"""

import re
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent

# Patterns for PII scanning
PATTERNS = {
    "Email address": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "Phone number": r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    "IP address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

# Known safe email domains (documentation examples, non-routable)
SAFE_DOMAINS = {
    "example.com", "example.org", "example.net",
    "test.com", "domain.com", "yourdomain.com",
    "email.com", "your-email.com", "acme.com",
    "company.com", "mycompany.com", "domain.tld",
    "gmail.com",                    # user@gmail.com is a placeholder
    "github.com",                   # git@github.com is SSH syntax
}

# Files that legitimately contain example/test data
EXAMPLE_FILE_MARKERS = {
    "test-fixture-authoring",
    "structured-reference-delivery",
    "local-tts",
}

# IPs that are always safe (loopback, private ranges, multicast)
SAFE_IPS = re.compile(
    r"^(127\.\d{1,3}\.\d{1,3}\.\d{1,3}"      # loopback
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}"          # 10.x.x.x
    r"|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"  # 172.16-31.x.x
    r"|192\.168\.\d{1,3}\.\d{1,3}"              # 192.168.x.x
    r"|224\.\d{1,3}\.\d{1,3}\.\d{1,3}"          # multicast
    r"|0\.0\.0\.0"                               # bind-all
    r")$"
)

# Scanner files to skip (self-referential false positives)
SKIP_PATTERN_FILES = {"scripts/audit-pii.py", "scripts/audit-credentials.py"}
SKIP_DIRS = {".git"}
SKIP_FILES = {"LICENSE"}

# Known non-email matches
SAFE_EMAIL_MATCHES = {
    "git@github.com",        # SSH URL syntax
    "git@github.com:",       # SSH clone URL
}


def is_safe_ip(ip: str) -> bool:
    return bool(SAFE_IPS.match(ip))


def scan_file(filepath: Path) -> list[dict]:
    findings = []

    try:
        if filepath.suffix in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".pyc",
                               ".o", ".so", ".dll", ".dylib", ".woff", ".woff2",
                               ".ttf", ".eot", ".zip", ".tar", ".gz", ".bz2"):
            return findings
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings

    rel = str(filepath.relative_to(REPO_DIR))

    # Skip scanner files entirely
    if rel in SKIP_PATTERN_FILES:
        return findings

    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        for name, pattern in PATTERNS.items():
            matches = re.findall(pattern, stripped)
            for m in matches:
                # Phone number must be at least 7 chars to be meaningful
                if name == "Phone number" and len(m.strip()) < 7:
                    continue
                if name == "Email address":
                    domain = m.split("@")[-1] if "@" in m else ""
                    if domain.lower() in SAFE_DOMAINS:
                        continue
                    if m.strip() in SAFE_EMAIL_MATCHES:
                        continue
                    if any(p in str(filepath) for p in EXAMPLE_FILE_MARKERS):
                        continue

                if name == "IP address":
                    # Strip any trailing ports/paths for IP check
                    ip_part = m.split(":")[0].split("/")[0]
                    if is_safe_ip(ip_part):
                        continue

                findings.append({
                    "file": rel,
                    "line": i,
                    "type": name,
                    "match": m[:60],
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

        all_findings.extend(scan_file(filepath))

    if not all_findings:
        print("✅ No PII (emails, phones, IPs) detected in repo files.")
        return 0

    print(f"❌ Found {len(all_findings)} PII match(es) needing review:\n")
    by_file: dict[str, list[dict]] = {}
    for f in all_findings:
        by_file.setdefault(f["file"], []).append(f)

    for filepath, findings in sorted(by_file.items()):
        print(f"  📄 {filepath}:")
        for f in findings:
            print(f"     L{f['line']:>4}  [{f['type']}]  '{f['match']}'")
            print(f"            Context: {f['context'][:100]}")

    print("\n⚠️  Review each finding. Redact real PII before committing.")
    return len(all_findings)


if __name__ == "__main__":
    sys.exit(main())
