"""Hold the site integration lease during edits; input: CLAW path; output: lease.

Serves the canonical public-fleet integration PR, 2026-11-10. No send path.
"""
import sys
from pathlib import Path

claw = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(claw), str(claw / 'src')]
from kg_microbe_fleet.roots import resolve_culturebotai_site_root
from plugins.repository_settings import RepositorySettings, RepositoryTarget
from plugins.lock_manager import LockManager

root = Path(__file__).resolve().parents[2]
resolved = resolve_culturebotai_site_root(claw_root=claw, environ={'CULTUREBOTAI_SITE_ROOT': str(root)})
assert resolved == root
settings = RepositorySettings({'site': RepositoryTarget('site', root, 'CultureBotAI/CultureBotAI.github.io')}, {}, ('site',))
settings.get_target('site').open()
with LockManager().lock('culturebotai-site', 'canonical-public-membership'):
    print('Site identity verified; integration lease held until stdin closes.', flush=True)
    sys.stdin.read()
