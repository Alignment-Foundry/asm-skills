#!/usr/bin/env python3
"""Convenience wrapper: scaffold a DOX project for Hermes Agent.

Usage:
    python3 scaffold.py <project-name> [description]

Equivalent to:
    dox-scaffold init <project-name> "description" --agent hermes
"""

import subprocess
import sys

DOC = __doc__ or ""


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(DOC.strip())
        sys.exit(0 if len(sys.argv) < 2 else 1)

    project = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""

    cmd = ["dox-scaffold", "init", project]
    if description:
        cmd.append(description)
    cmd.extend(["--agent", "hermes"])

    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
