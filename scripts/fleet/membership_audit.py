"""Project retained audit evidence and date membership independently of corpora."""
from copy import deepcopy
from datetime import datetime, timezone

CLAW = "culturebotai-claw"


def timestamp(value):
    """Require an explicit timezone; a naive date cannot establish ordering."""
    if not isinstance(value, str):
        raise ValueError("Audit timestamp must be an ISO datetime with timezone")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Audit timestamp must have a timezone")
    return result


def validate_membership_observation(audit):
    """A membership observation must not predate the CLAW commit it names.

    A complete refresh can use its common check time. A membership-only update
    records its own time without rewriting the earlier corpus observations.
    """
    rows = [row for row in audit["repositories"] if row["repo"] == CLAW]
    if len(rows) != 1:
        raise ValueError("Audit must contain exactly one canonical CLAW row")
    observed = timestamp(audit.get("membership_checked_at_utc", audit["checked_at_utc"]))
    if observed < timestamp(rows[0]["commit_date"]):
        raise ValueError("Membership observation predates its CLAW commit")
    return observed


def refresh_membership_audit(audit, notes, snapshot, commit_date, observed_at):
    """Return public audit/notes copies, preserving retained corpus evidence.

    The snapshot is already CLAW's canonical public projection. Unknown saved
    repository rows and note keys are excluded before either document can be
    staged, including names without a Mech suffix. Inputs remain unchanged.
    """
    allowed = {CLAW}
    for name, member in snapshot["mechs"].items():
        allowed.update(value.lower() for value in
                       (name, member["key"], member["github"], member["github"].rsplit("/", 1)[-1]))
    result = deepcopy(audit)
    public_notes = deepcopy(notes)
    result["repositories"] = [row for row in result["repositories"]
                              if row["repo"].lower() in allowed]
    public_notes["notes"] = {name: text for name, text in public_notes["notes"].items()
                             if name.lower() in allowed}
    revision = snapshot["source"]["revision"]
    observed = timestamp(observed_at).astimezone(timezone.utc).isoformat(timespec="seconds")
    result["membership_checked_at_utc"] = observed
    for row in result["repositories"]:
        if row["repo"] == CLAW:
            row.update(sha=revision, commit_date=commit_date,
                       readme_url=f"https://github.com/CultureBotAI/{CLAW}/blob/{revision}/README.md",
                       notes=public_notes["notes"][CLAW])
    scope = (
        "Retained public corpus figures, source pins, overlap assets and historical "
        "repository statistics keep their original corpus observation at "
        + result["checked_at_utc"] + " and pin-time bound " + result["pinned_at_utc"]
        + ". Public fleet membership was checked separately at " + observed
        + " against CLAW " + revision + ". This membership-only refresh does not "
        "recount corpora, recheck live sites or refresh historical PR totals. Website "
        "feature verdicts retain their separately recorded dates and browser-review "
        "scope. The pinned kg-microbe comparison remains outside Mech statistics."
    )
    result["scope"] = scope
    public_notes["scope"] = scope
    validate_membership_observation(result)
    return result, public_notes
