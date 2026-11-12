# Preserve earlier screenshots when repeating a site audit

The new audit helper refuses an existing JSON receipt but gives screenshots
fixed names. A later run with a new JSON output and the same screenshot folder
would overwrite those earlier images.

Refuse existing screenshot targets before the audit starts, or reserve a unique
run directory. Preserve receipts from failed as well as successful attempts.

Found in a separate read-only review before the helper's first live audit.
