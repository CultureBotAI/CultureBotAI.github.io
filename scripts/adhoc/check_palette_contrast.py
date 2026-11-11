#!/usr/bin/env python3
"""
Purpose: Verify contrast (>= 4.5:1 for -ink variants against all light/dark
         surfaces in assets/custom.css) and OKLab separation from existing
         Mech identity colors for CofactorMech and AssayMech.
Inputs:  assets/custom.css and _fleet/fleet_fragment.html
Outputs: Console verification of contrast ratios and pairwise OKLab distances.
Date:    2026-11-10
"""

from __future__ import annotations

import math
import re
from pathlib import Path

ROOT = Path("/Users/marcin/Documents/newera/CultureBotAI/CultureBotAI.github.io")


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def luminance(h: str) -> float:
    r, g, b = (srgb_to_linear(c) for c in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(c1: str, c2: str) -> float:
    l1, l2 = sorted((luminance(c1), luminance(c2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def hex_to_oklab(h: str) -> tuple[float, float, float]:
    r, g, b = (srgb_to_linear(c) for c in hex_to_rgb(h))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return (L * 100.0, A * 100.0, B * 100.0)


def oklab_dist(c1: str, c2: str) -> float:
    p1, p2 = hex_to_oklab(c1), hex_to_oklab(c2)
    return math.dist(p1, p2)


def main() -> None:
    theme = (ROOT / "assets/custom.css").read_text()
    blocks = re.findall(r":root[^{}]*\{([^{}]+)\}", theme)[:3]
    frag = (ROOT / "_fleet/fleet_fragment.html").read_text()
    frag_blocks = re.findall(r":root[^{}]*\{([^{}]+)\}", frag)[:3]

    candidates = {
        "light": {
            "cofactormech": "#c85a00",
            "cofactormech-ink": "#994500",
            "assaymech": "#09697a",
            "assaymech-ink": "#086373",
        },
        "dark": {
            "cofactormech": "#ff9233",
            "cofactormech-ink": "#ff9233",
            "assaymech": "#4dd4e8",
            "assaymech-ink": "#4dd4e8",
        },
    }

    for idx, (mode, tblock, fblock) in enumerate(
        zip(("light", "dark", "dark"), blocks, frag_blocks)
    ):
        surf = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6});", tblock))
        mechs = dict(
            re.findall(r"--mech-([a-z]+mech):\s*(#[0-9A-Fa-f]{6});", fblock)
        )
        cand = candidates[mode]
        print(f"=== Block {idx} ({mode}) ===")
        for k in ("cofactormech-ink", "assaymech-ink"):
            col = cand[k]
            min_cr = min(
                contrast(col, surf[s])
                for s in ("card", "bg", "wash-a", "wash-b", "pastel-a", "pastel-b")
            )
            print(f"  {k} ({col}) min contrast across surfaces: {min_cr:.2f}")
        for k in ("cofactormech", "assaymech"):
            col = cand[k]
            dists = {m: oklab_dist(col, mcol) for m, mcol in mechs.items()}
            nearest = min(dists.items(), key=lambda kv: kv[1])
            print(
                f"  {k} ({col}) nearest existing Mech: {nearest[0]} "
                f"(OKLab dist={nearest[1]:.2f})"
            )
        print(
            "  cofactormech vs assaymech OKLab dist:",
            f"{oklab_dist(cand['cofactormech'], cand['assaymech']):.2f}",
        )


if __name__ == "__main__":
    main()
