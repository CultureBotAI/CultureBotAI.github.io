# Account for Pages packaging in the new-site audit

The new directory audit helper fetches every file named by each site's build
manifest. That includes `.nojekyll` and `.site-generated`, while the exact
[pinned Pages uploader](https://github.com/actions/upload-pages-artifact/blob/7b1f4a764d45c48632c6b24a0339c27f5614fb0b/action.yml)
excludes dotfiles when creating its publication archive. The helper would fail
before reaching browser review on a correctly packaged deployment.

Bind the audit to that reviewed uploader revision, record precisely these two
internal marker exclusions, and still require every other manifest asset to be
served with its expected hash. Missing CSS, JavaScript, source YAML or record
pages must remain failures. Do not describe excluded files as publicly verified.

Found in a separate read-only review before the helper's first live audit.
