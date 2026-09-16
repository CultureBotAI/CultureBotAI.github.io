"""Assemble mechs.md from _fleet/mechs_template.md, _fleet/fleet_fragment.html and
the derived data under _fleet/data. Run from the site root after build_data.py."""
import datetime
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F = os.path.join(REPO, "_fleet")
frag = open(os.path.join(F, "fleet_fragment.html"), encoding="utf-8").read()
data = open(os.path.join(F, "data", "fleet_data.json"), encoding="utf-8").read().strip()
assert "/*FLEET_DATA*/{}/*END*/" in frag
page = open(os.path.join(F, "mechs_template.md"), encoding="utf-8").read().replace(
    "<!--FLEET_FRAGMENT-->", frag.replace("/*FLEET_DATA*/{}/*END*/", data))

# Every count the page states is written in here rather than typed into the
# markup. They were typed once, and by the time anyone noticed, the cards were
# claiming 57 CellStructureMech records against a corpus that had grown to 338
# (CultureBotAI.github.io#64). A placeholder left unfilled now fails the build
# instead of shipping.
census = json.load(open(os.path.join(F, "data", "prefix_census.json"), encoding="utf-8"))
as_of = census.pop("_as_of")  # written by prefix_census.py; the rest are Mechs
# When the corpora were counted, which is not when the page was assembled and
# is emphatically not the file's mtime: git does not preserve those, so a fresh
# clone would date the page to the day it was cloned (#74).
page = page.replace("<!--AS_OF-->", datetime.date.fromisoformat(as_of).strftime("%-d %B %Y"))
stats = json.load(open(os.path.join(F, "data", "mech_stats.json"), encoding="utf-8"))

records = {m: c["files"] for m, c in census.items()}
page = page.replace("<!--MECH_COUNT-->", f"{len(records):,}")
page = page.replace("<!--RECORDS_TOTAL-->", f"{sum(records.values()):,}")
# The strip's "ontologies & databases cited" is how many distinct prefixes the
# census found anywhere in the fleet, not the 22 the heatmap has room for.
page = page.replace("<!--VOCAB_COUNT-->", f"{len({p for c in census.values() for p in c['prefixes']}):,}")
for mech, n in records.items():
    page = page.replace(f"<!--RECORDS:{mech}-->", f"{n:,}")      # cards and strip
    page = page.replace(f"/*RECORDS:{mech}*/", str(n))           # graph node subtitles

page = page.replace("<!--PRS_TOTAL-->", f"{stats['merged_prs_total']:,}")
for m in stats["mechs"]:
    prs = f"{m['merged_prs']:,} merged PRs"
    # null reviewed means the Mech's schema has no status that can say REVIEWED,
    # which is not the same as nothing having been reviewed. See mech_stats.py.
    line = prs if m["reviewed"] is None else f"{m['reviewed']:,} reviewed · {prs}"
    page = page.replace(f"<!--STATS:{m['mech']}-->", line)
    if m["highlight"]:
        page = page.replace(f"<!--HIGHLIGHT:{m['mech']}-->", m["highlight"])

left = [t for t in ("<!--PRS_TOTAL-->", "<!--STATS:", "<!--RECORDS", "/*RECORDS:",
                    "<!--HIGHLIGHT:", "<!--MECH_COUNT-->", "<!--VOCAB_COUNT-->",
                    "<!--AS_OF-->") if t in page]
assert not left, f"unsubstituted placeholder in mechs.md: {left}"
assert "{{" not in page and "{%" not in page, "Liquid tags would be interpreted by Jekyll"
open(os.path.join(REPO, "mechs.md"), "w", encoding="utf-8").write(page)
print("wrote mechs.md", len(page), "bytes")
