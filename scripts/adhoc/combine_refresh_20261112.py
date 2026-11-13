#!/usr/bin/env python3
"""Combine PRs 564 and 570 without losing refreshed counts or new browser links.

Inputs: the three source-file merge conflicts between those PRs.
Outputs: resolved sources (mechs.md is regenerated separately).
Serves: the November 12 X-Mech refresh PR. Date: 2026-11-12.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
for name in ("CLAUDE.md", "index.md", "_fleet/fleet_fragment.html"):
    path = ROOT / name
    text = path.read_text()
    pattern = r"<<<<<<< HEAD\n(.*?)=======\n.*?>>>>>>> origin/feat/cofactor-assay-website-links-20261111\n"
    text, count = re.subn(pattern, lambda match: match[1], text, flags=re.S)
    assert count == 1, (name, count)
    if name == "CLAUDE.md":
        text = text.replace("**AssayMech** (https://github.com/CultureBotAI/AssayMech)",
                            "**AssayMech** (https://culturebotai.github.io/AssayMech/)")
    elif name == "index.md":
        for mech in ("CofactorMech", "AssayMech"):
            text = text.replace(f"[{mech}](https://github.com/CultureBotAI/{mech})",
                                f"[{mech}](https://culturebotai.github.io/{mech}/)")
    else:
        lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.startswith("    AssayMech: {"):
                lines[i] = line.replace('site: ""', 'site: "https://culturebotai.github.io/AssayMech/"').replace(
                    "BSD-3-Clause code", "CC0 1.0 code and schemas")
        text = "".join(lines)
    assert "<<<<<<<" not in text
    path.write_text(text)
