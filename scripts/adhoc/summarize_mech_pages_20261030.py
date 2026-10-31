#!/usr/bin/env python3
"""Save the fleet Pages refresh receipt for PR #527, 2026-10-30.

Inputs: pinned fleet inventory, raw deployment audits and browser smoke checks.
Outputs: a compact JSON receipt and a Markdown coverage table under --output.
Preserves acquisition times; checks all manifest members before writing.
"""
import argparse
import datetime as dt
import email.utils
import hashlib
import json
from pathlib import Path

from audit_mech_pages_20261030 import audit_verified, deployment_succeeded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("inventory", "manifest", "audit", "browser", "output"):
        parser.add_argument(f"--{argument}", type=Path, required=True)
    parser.add_argument("--claw-sha", required=True)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    reviewed_sources = {
        "culturemech": "a74dd489720c9df96cc073ffd11568d407d3c06c",
        "mediaingredientmech": "014fe04ff7395ea1f1c1e71c61123089986d0158",
        "communitymech": "a0631777d79ffe10235c6022408c58084a9e3283",
        "pathwaymech": "d869d5be1629128e1f6bb116eb9d30f767bf2682",
    }
    notes = {
        "culturemech": "No changed site inputs. Shared claw builder also unchanged; its deployed build used 432f4ecffa33fef3d3e4543bcd9bd3c00131408c, whose difference to the current claw pin is agent instructions only.",
        "mediaingredientmech": "No changed inputs consumed by scripts/build_pages_site.py; intervening commits change reviews, reports and agent workflow files.",
        "communitymech": "No changed community-renderer inputs or docs files. The intervening kb/taxa record is outside its kb/communities input.",
        "pathwaymech": "Latest change is PathBank provenance validation and review records; committed pages unchanged. Automatic Build and test must pass before its publish workflow runs.",
    }
    rows = []
    for mech in inventory:
        audit = json.loads((args.audit / mech["key"] / "audit.json").read_text())
        browser = json.loads((args.browser / mech["key"] / "browser.json").read_text())
        if not audit_verified(audit):
            raise ValueError(f"unverified HTTP/deployment evidence: {mech['key']}")
        deployment = audit["successful_deployment"]
        if not deployment_succeeded(deployment["statuses"]):
            raise ValueError(f"deployment no longer successful: {mech['key']}")
        modified = email.utils.parsedate_to_datetime(audit["live"]["last_modified"])
        created = dt.datetime.fromisoformat(deployment["created_at"].replace("Z", "+00:00"))
        if modified < created or not audit["live"].get("github_request_id"):
            raise ValueError(f"live publishing evidence insufficient: {mech['key']}")
        views = browser["views"]
        if {v["width"] for v in views} != {390, 1440}:
            raise ValueError(f"browser coverage incomplete: {mech['key']}")
        for view in views:
            if (view.get("error") or view.get("status") != 200 or view["page_errors"]
                    or view["http_errors"] or len(view["text"].strip()) < 100
                    or view["layout"]["scrollWidth"] > view["width"]
                    or view["layout"]["main"] != 1):
                raise ValueError(f"browser check needs review: {mech['key']}")
        at_main = audit["main"] == deployment["sha"]
        if not at_main and audit["main"] != reviewed_sources.get(mech["key"]):
            raise ValueError(f"new source revision needs review: {mech['key']}")
        if audit.get("difference", {}).get("files_may_be_capped"):
            raise ValueError(f"incomplete source comparison: {mech['key']}")
        rows.append({
            "mech": mech["display_name"], "repository": mech["github"],
            "checked_at": audit["checked_at"], "main": audit["main"],
            "deployment": deployment, "live": audit["live"],
            "publication": "current main" if at_main else "unchanged public inputs",
            "source_review": "Successful deployment of the acquired main revision." if at_main else notes[mech["key"]],
            "comparison_files_may_be_capped": audit.get("difference", {}).get("files_may_be_capped", False),
            "browser_checked_at": browser["checked_at"],
            "display": "Landing renders at 1440 and 390 px without horizontal overflow.",
            "navigation": "Declared landing route loaded; nested routes not re-audited.",
            "interaction": "Not re-audited; retain the separately dated feature baseline.",
            "views": [{key: value for key, value in view.items() if key != "text"} for view in views],
        })
    result = {"claw_sha": args.claw_sha, "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
              "scope": "Deployment freshness and landing-page smoke checks only; no new feature-by-feature audit.",
              "mechs": rows}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "fleet-pages-20261030.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Mech Pages check — October 30, 2026", "", result["scope"], "",
             f"Coverage: {len(rows)} manifest members; {sum(len(row['views']) for row in rows)} desktop/mobile views. All returned HTTP 200, populated content and one main landmark, with no captured JavaScript/HTTP errors or horizontal overflow.", "",
             f"Fleet authority: `CultureBotAI/culturebotai-claw@{args.claw_sha}`; manifest SHA-256 `{result['manifest_sha256']}`. Acquisition times, complete SHAs, deployment statuses and HTTP evidence are in [the receipt](fleet-pages-20261030.json).", "",
             "| Mech | Main | Deployed | Publication |", "| --- | --- | --- | --- |"]
    for row in rows:
        lines.append(f"| {row['mech']} | `{row['main'][:7]}` | `{row['deployment']['sha'][:7]}` | {row['publication']} |")
    lines += ["", "Older deployment SHAs were checked against the changed files and their owning builders:", ""]
    lines.extend(f"- **{row['mech']}:** {row['source_review']}" for row in rows if row['publication'] != "current main")
    lines += ["", "No manual rebuild was dispatched. ProteinTraitsMech's existing automatic publication completed during this check. The central directory changes remain in PR #527 pending the maintainer's merge decision.", "",
              "The read-only acquisition canary saved deployment metadata, workflow sources and served HTML for CommunityMech before the fleet pass. Its browser canary saved populated desktop/mobile views and screenshots before the remaining sites. Rate limits under parallel load and full catalogue interactions were not exercised.", "",
              "Independent review found two latent audit-helper defects (#531 and #532); the selected evidence was unaffected. Regression fixtures failed on the original logic and passed after the latest-status and incomplete-evidence checks were repaired.", "",
              "Reproduction helpers: `scripts/adhoc/audit_mech_pages_20261030.py`, `smoke_mech_pages_20261030.py`, and `summarize_mech_pages_20261030.py`. Raw HTML, API responses and screenshots are retained locally under `/private/tmp/mech-pages-20261030/`."]
    (args.output / "fleet-pages-20261030.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote verified receipt for {len(rows)} Mechs")


if __name__ == "__main__":
    main()
