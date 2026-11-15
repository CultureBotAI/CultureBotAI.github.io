"""Refresh site membership from the reviewed CLAW public API, 2026-11-15.

Serves CLAW #1254 and replaces the membership-only portion of site PR #551.
Inputs: an identity-verified CLAW checkout and its full published commit.
Outputs: manifest, membership audit/notes and page.
Existing corpus pins, cards, browser verdicts and knowledge-gap assets are retained.
Infrastructure scope evidence retains its own source and observation date (#604).
Dry-run first; --apply promotes validated staged bytes under the site lease.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def prepare_refresh(snapshot: dict, commit_date: str, observed_at: str) -> dict[str, str]:
    """Prepare membership bytes without changing separately dated scope evidence."""
    sys.path.insert(0, str(ROOT / "scripts/fleet"))
    from assemble_page import assemble
    from membership_audit import refresh_membership_audit
    from refresh_manifest import validate
    import roots

    def read(path):
        return json.loads((ROOT / path).read_text())

    def encoded(value):
        return json.dumps(value, indent=2, ensure_ascii=False) + "\n"

    revision = snapshot["source"]["revision"]
    infrastructure = read("_fleet/infrastructure.json")
    notes = read("_fleet/audit_notes.json")
    notes["notes"]["culturebotai-claw"] = (
        "Membership-only refresh at " + revision + ". The canonical public projection "
        "declares " + str(len(snapshot["mechs"])) + " members and "
        + str(snapshot["artifact_count"]) + " applicable governed artifacts. "
        "Corpus pins, numeric cards, historical repository statistics and dated "
        "website-feature reviews are retained unchanged, including the admitted "
        "CofactorMech and AssayMech corpora and browser reviews. Capability declarations "
        "report CLAW's contract state; they do not rejudge the published websites."
    )
    audit, notes = refresh_membership_audit(
        read("_fleet/data/site_audit.json"), notes, snapshot, commit_date, observed_at,
    )
    prior = roots.public_names
    roots.public_names = lambda: frozenset(
        token.lower() for name, row in snapshot["mechs"].items()
        for token in (name, row["key"], row["github"], row["github"].rsplit("/", 1)[-1])
    )
    try:
        validate(snapshot)
        page = assemble(
            (ROOT / "_fleet/mechs_template.md").read_text(),
            (ROOT / "_fleet/fleet_fragment.html").read_text(),
            read("_fleet/data/fleet_data.json"), snapshot,
            read("_fleet/data/mech_stats.json"), read("_fleet/data/prefix_census.json"),
            read("_fleet/data/site_features.json"), read("_fleet/data/recent_terms.json"),
            infrastructure=infrastructure,
        )
    finally:
        roots.public_names = prior
    return {
        "_fleet/data/manifest.json": encoded(snapshot),
        "_fleet/audit_notes.json": encoded(notes),
        "_fleet/data/site_audit.json": json.dumps(audit, indent=1, ensure_ascii=False) + "\n",
        "mechs.md": page,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claw-root", type=Path, required=True)
    parser.add_argument("--claw-ref", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    claw = args.claw_root.resolve(strict=True)
    sys.path[:0] = [str(ROOT / "scripts/fleet"), str(claw), str(claw / "src")]
    from kg_microbe_fleet.roots import resolve_culturebotai_site_root
    from kg_microbe_write import ValidatedWriteTransaction
    from plugins.lock_manager import LockManager
    from plugins.repository_settings import RepositorySettings, RepositoryTarget
    from refresh_manifest import read_canonical

    resolved = resolve_culturebotai_site_root(
        claw_root=claw, environ={"CULTUREBOTAI_SITE_ROOT": str(ROOT)}
    )
    if resolved != ROOT:
        raise SystemExit("Site root did not resolve exactly")
    settings = RepositorySettings(
        {"site": RepositoryTarget("site", ROOT, "CultureBotAI/CultureBotAI.github.io")},
        {}, ("site",),
    )
    settings.get_target("site").open()

    with LockManager().lock("culturebotai_site", "refresh-public-membership-1254", timeout=300):
        settings.get_target("site").open()
        snapshot = read_canonical(claw, args.claw_ref)
        revision = snapshot["source"]["revision"]
        commit_date = subprocess.check_output(
            ["git", "-C", str(claw), "show", "-s", "--format=%cI", revision], text=True,
        ).strip()
        changes = prepare_refresh(
            snapshot, commit_date,
            datetime.now(timezone.utc).isoformat(),
        )
        transaction = ValidatedWriteTransaction(ROOT)
        for path, content in changes.items():
            transaction.stage(path, content)
        print(transaction.commit(apply=args.apply))
        if args.apply:
            for path, content in changes.items():
                if (ROOT / path).read_text() != content:
                    raise RuntimeError(f"Staged content differs after promotion: {path}")
            print("Verified all four promoted files against staged bytes.")


if __name__ == "__main__":
    main()
