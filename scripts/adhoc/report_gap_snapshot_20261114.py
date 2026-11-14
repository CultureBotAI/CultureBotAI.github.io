"""Persist measured gap-export receipts for website #577 (2026-11-14).

Inputs: immutable snapshot, current config and built manifest/assets. Output:
JSON receipt with verified hashes/counts and measured classification cohorts.
Use after the builder's --check; this supplements its contract validation.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/gaps"))
from snapshot import digest, json_bytes, write_atomic


def report(snapshot_path, assets):
    snapshot = json.loads(snapshot_path.read_text())
    manifest = json.loads((assets / "manifest.json").read_text())
    config = json.loads((ROOT / "_gaps/sources.json").read_text())
    assert manifest["build_id"] == digest(json_bytes(snapshot))
    assert manifest["source_config_sha256"] == digest(json_bytes(config))
    assert manifest["exporter"] == snapshot["exporter"]
    assert not snapshot["exporter"]["dirty"]
    descriptors = [manifest["index"], *manifest["details"].values()]
    for descriptor in descriptors:
        payload = (assets / descriptor["url"]).read_bytes()
        assert payload and digest(payload) == descriptor["sha256"]
        assert json.loads(payload)["build_id"] == manifest["build_id"]
    items = snapshot["items"]
    assert len(items) == manifest["counts"]["items"]
    assert len({item["id"] for item in items}) == len(items)
    assert sum(s["items"] for s in snapshot["sources"]) == len(items)
    assert manifest["sources"] == snapshot["sources"]
    for item in items:
        source = item["source"]
        assert source["revision"] in source["url"]
        assert source["path"] and len(source["sha256"]) == 64
    cohorts = Counter((i["origin"], i["current_attribution"], i["origin_basis"],
                       i["review_state"], i["lane"]) for i in items)
    corrected = [i for i in items if i["origin_basis"] == "documented_scan_provenance"]
    current_scanner = [i for i in items if i["current_attribution"] == "scanner"]
    assert all(i["origin"] == "scanner" for i in corrected)
    assert all(i["lane"] == "candidate" for i in current_scanner)
    return {
        "schema_version": 1, "purpose": "Persisted acquisition and bundle verification",
        "snapshot_path": snapshot_path.relative_to(ROOT).as_posix(),
        "build_id": manifest["build_id"], "exporter": snapshot["exporter"],
        "source_config_sha256": manifest["source_config_sha256"],
        "counts": manifest["counts"], "sizes": manifest["sizes"],
        "verified_asset_count": len(descriptors),
        "supported_records_inspected": sum(r["inspected_records"] for s in snapshot["sources"] for r in s["roots"]),
        "sources": [{k: s[k] for k in ("name", "revision", "coverage_status", "items", "roots")} for s in snapshot["sources"]],
        "classification_cohorts": [dict(zip(("origin", "current_attribution", "origin_basis", "review_state", "lane"), key), items=count)
                                   for key, count in sorted(cohorts.items())],
        "documented_scanner_origin_items": len(corrected),
        "current_scanner_candidates": len(current_scanner),
        "checks": ["persisted assets nonempty", "all asset SHA-256 values", "snapshot build ID",
                   "source configuration digest", "clean pinned exporter", "unique item identities",
                   "source/item counts", "pinned source URLs", "scanner origin and current attribution separated"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = report(args.snapshot.resolve(), args.assets.resolve())
    write_atomic(args.output, json_bytes(receipt))
    assert json.loads(args.output.read_text()) == receipt
    print(json.dumps({"receipt": str(args.output), "build_id": receipt["build_id"],
                      "counts": receipt["counts"], "supported_records_inspected": receipt["supported_records_inspected"]}, indent=2))


if __name__ == "__main__":
    main()
