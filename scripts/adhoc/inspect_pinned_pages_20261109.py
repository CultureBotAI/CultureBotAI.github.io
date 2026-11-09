#!/usr/bin/env python3
"""Inspect committed HTML/JSON pages at the 2026-11-09 pins in $SNAP/mechs/* for exact counts and digests.

Inputs: $SNAP/revisions.json, $SNAP/mechs/*.
Outputs: _fleet/reviews/refresh-20261109/pinned-pages-inspection.json.
Date: 2026-11-09; serves X-Mech Suite November 9 refresh PR.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL="/dev/null",
    GIT_CONFIG_NOSYSTEM="1",
    XDG_CONFIG_HOME="/tmp",
)


def show_blob(clone: Path, sha: str, relpath: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(clone), "show", f"{sha}:{relpath}"],
        text=True,
        env=ENV,
    )


def strip_tags(html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", type=Path, required=True)
    args = ap.parse_args()

    pins = json.loads((args.snapshot / "revisions.json").read_text())["mechs"]
    out = {}

    pages_to_check = {
        "AntibioticMech": ["pages/index.html", "pages/browse.html", "pages/chemical-map.html", "pages/sequence-map.html"],
        "CellStructureMech": ["pages/index.html", "pages/browse.html"],
        "CommunityMech": ["docs/index.html", "docs/browser.html", "docs/communities.json"],
        "DUFMech": ["pages/index.html", "pages/sources.html"],
        "HabitatMech": ["pages/index.html", "pages/browse.html"],
        "NaturalProductMech": ["pages/index.html", "pages/browse.html"],
        "PathwayMech": ["pages/index.html", "pages/browse.html", "pages/downloads/manifest.json"],
        "TaxonMech": ["pages/index.html", "pages/sources.html"],
        "TraitMech": ["pages/index.html", "pages/browse.html", "pages/umap.html", "pages/sequence-map.html"],
        "CMMMech": ["pages/index.html", "pages/browse.html", "pages/graph.html", "pages/map.html", "pages/materials/cobalt.html"],
        "AIMech": ["pages/index.html", "pages/browse.html", "pages/graph.html", "pages/map.html", "pages/aio/TrainingStrategy.html"],
    }

    for mech, relpaths in pages_to_check.items():
        clone = args.snapshot / "mechs" / mech
        sha = pins[mech]["sha"]
        mech_out = {"sha": sha, "files": {}}
        for rel in relpaths:
            try:
                raw = show_blob(clone, sha, rel)
                if rel.endswith(".json"):
                    data = json.loads(raw)
                    mech_out["files"][rel] = {
                        "type": type(data).__name__,
                        "len": len(data),
                        "preview": str(data)[:800] if isinstance(data, dict) else f"list[{len(data)}]",
                    }
                else:
                    footer_match = re.findall(r"<footer\b[^>]*>(.*?)</footer>", raw, flags=re.S | re.I)
                    mech_out["files"][rel] = {
                        "text_excerpt": strip_tags(raw)[:1500],
                        "footer": [strip_tags(f) for f in footer_match],
                    }
            except Exception as e:
                mech_out["files"][rel] = {"error": str(e)}
        out[mech] = mech_out

    dest = ROOT / "_fleet/reviews/refresh-20261109/pinned-pages-inspection.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    for mech, m in out.items():
        print(f"=== {mech} ({m['sha'][:7]}) ===")
        for rel, info in m["files"].items():
            if "footer" in info and info["footer"]:
                print(f"  {rel} footer: {info['footer'][0][:200]}")
            elif "text_excerpt" in info:
                print(f"  {rel} text: {info['text_excerpt'][:250]}")
            else:
                print(f"  {rel}: {info}")


if __name__ == "__main__":
    main()
