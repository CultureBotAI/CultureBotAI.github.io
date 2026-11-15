"""Emit the reviewed CLAW contract pin for CI checkout (website #577, 2026-11-14)."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    pin = json.loads((ROOT / "_gaps/toolchain.json").read_text())
    if pin["repository"] != "CultureBotAI/culturebotai-claw" or pin["dirty"]:
        raise ValueError("Expected a committed canonical exporter")
    if not re.fullmatch(r"[0-9a-f]{40}", pin["revision"]):
        raise ValueError("Expected an immutable exporter revision")
    for key in ("schema_sha256", "module_sha256"):
        if not re.fullmatch(r"[0-9a-f]{64}", pin[key]):
            raise ValueError("Missing exporter content digest")
    if args.github_output:
        with args.github_output.open("a") as handle:
            handle.write(f"ref={pin['revision']}\n")
    else:
        print(pin["revision"])


if __name__ == "__main__":
    main()
