"""Protocol stub for immutable-source tests; not a production fleet loader."""
from types import SimpleNamespace


class Fleet:
    def __init__(self, raw):
        self.mechs = {}
        for key, row in raw['mechs'].items():
            caps = {}
            for name, cap in row['capabilities'].items():
                claims = cap.get('reason_claims')
                caps[name] = SimpleNamespace(status=cap['status'], reason=cap.get('reason'),
                    settings=cap.get('settings', {}), reason_claims=(
                        SimpleNamespace(present=claims.get('present', []), absent=claims.get('absent', [])) if claims else None))
            self.mechs[key] = SimpleNamespace(display_name=row['display_name'], github=row['github'], capabilities=caps)
        self.capability_catalogue = {name: SimpleNamespace(settings={
            key: SimpleNamespace(value_type=setting['type'], required_when_enabled=setting.get('required_when_enabled', False), minimum=setting.get('minimum'))
            for key, setting in value.get('settings', {}).items()})
            for name, value in raw['capability_catalogue'].items()}
    @property
    def keys(self):
        return tuple(self.mechs)
    def public(self):
        return self


def parse_fleet_manifest(raw, source):
    return Fleet(raw)
