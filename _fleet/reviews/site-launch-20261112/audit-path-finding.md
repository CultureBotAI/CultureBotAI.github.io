# Confine new-site audit asset requests to the reviewed site

The new audit helper rejects leading slashes and `..` path components, but an
absolute URL such as `https://example.org/record.html` still passes. `urljoin`
then replaces the intended Pages base. Redirect destinations also lack a site
boundary check.

Require relative manifest paths without scheme, authority, query or fragment,
and reject encoded or noncanonical traversal forms. Validate requested and
redirected URLs against the exact Mech site root before following them. This
keeps an asset receipt bound to the site whose deployment was reviewed.

Found in a separate read-only review before the helper's first live audit.
