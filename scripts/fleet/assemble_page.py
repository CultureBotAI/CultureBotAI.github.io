"""Assemble mechs.md from _fleet/mechs_template.md, _fleet/fleet_fragment.html and
_fleet/data/fleet_data.json. Run from the site root after build_data.py."""
import os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(REPO, "_fleet")
frag = open(os.path.join(F, "fleet_fragment.html"), encoding="utf-8").read()
data = open(os.path.join(F, "data", "fleet_data.json"), encoding="utf-8").read().strip()
assert "/*FLEET_DATA*/{}/*END*/" in frag
page = open(os.path.join(F, "mechs_template.md"), encoding="utf-8").read().replace("<!--FLEET_FRAGMENT-->", frag.replace("/*FLEET_DATA*/{}/*END*/", data))
assert "{{" not in page and "{%" not in page, "Liquid tags would be interpreted by Jekyll"
open(os.path.join(REPO, "mechs.md"), "w", encoding="utf-8").write(page)
print("wrote mechs.md", len(page), "bytes")
