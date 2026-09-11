"""Assemble mechs.md from _fleet/mechs_template.md, _fleet/fleet_fragment.html and
the derived data under _fleet/data. Run from the site root after build_data.py."""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(REPO, "_fleet")
frag = open(os.path.join(F, "fleet_fragment.html"), encoding="utf-8").read()
data = open(os.path.join(F, "data", "fleet_data.json"), encoding="utf-8").read().strip()
assert "/*FLEET_DATA*/{}/*END*/" in frag
page = open(os.path.join(F, "mechs_template.md"), encoding="utf-8").read().replace(
    "<!--FLEET_FRAGMENT-->", frag.replace("/*FLEET_DATA*/{}/*END*/", data))

# Counts that mech_stats.py derived, written in here rather than typed into the
# markup, so a recount moves the page instead of quietly disagreeing with it.
stats = json.load(open(os.path.join(F, "data", "mech_stats.json"), encoding="utf-8"))
page = page.replace("<!--PRS_TOTAL-->", f"{stats['merged_prs_total']:,}")
for m in stats["mechs"]:
    prs = f"{m['merged_prs']:,} merged PRs"
    # null reviewed means the Mech's schema has no status that can say REVIEWED,
    # which is not the same as nothing having been reviewed. See mech_stats.py.
    line = prs if m["reviewed"] is None else f"{m['reviewed']:,} reviewed &middot; {prs}"
    page = page.replace(f"<!--STATS:{m['mech']}-->", line)

left = [t for t in ("<!--PRS_TOTAL-->", "<!--STATS:") if t in page]
assert not left, f"unsubstituted placeholder in mechs.md: {left}"
assert "{{" not in page and "{%" not in page, "Liquid tags would be interpreted by Jekyll"
open(os.path.join(REPO, "mechs.md"), "w", encoding="utf-8").write(page)
print("wrote mechs.md", len(page), "bytes")
