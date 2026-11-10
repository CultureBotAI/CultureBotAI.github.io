"""Emit the exact canonical revision for CI's pinned public-snapshot check."""
import json
import re
from pathlib import Path


def pin(document):
    source = document.get("source", {})
    revision = source.get("revision")
    if source.get("repository") != "CultureBotAI/culturebotai-claw" or not (
        isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision)
    ):
        raise ValueError("Public snapshot requires an immutable canonical CLAW revision")
    return revision


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[2] / "_fleet/data/manifest.json"
    print("revision=" + pin(json.loads(path.read_text())))
