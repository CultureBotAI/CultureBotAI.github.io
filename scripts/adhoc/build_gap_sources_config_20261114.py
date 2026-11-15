"""Build reviewed gap-browser source adapters from retained schema/license reads.

Date: 2026-11-14. Inputs: inspect_gap_sources_20261114.py output and reviewed
root/route choices. Output: _gaps/sources.json for the browser implementation PR.
Does not extract records or modify scientific repositories.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / ".temp/knowledge-gaps-20261114/source-inspection"
sys.path.insert(0, str(ROOT / "scripts/fleet"))
from roots import ORDER, RECORD_GLOBS, EXCLUDE_DIRS, is_withheld

# Only fields present in the inspected native root class enter these adapters.
CLASSES = {
    "HabitatMech": "HabitatRecord", "CommunityMech": "MicrobialCommunity",
    "TraitMech": "TraitRecord", "PathwayMech": "PathwayRecord",
    "CellStructureMech": "CellStructureRecord", "ProteinTraitsMech": "ProteinTraitRecord",
    "DUFMech": "FamilyRecord", "NaturalProductMech": "NaturalProductRecord",
    "AntibioticMech": "AntibioticRecord", "CMMMech": "CriticalMineralRecord",
    "MediaIngredientMech": "IngredientRecord", "CultureMech": "MediaRecipe",
    "TaxonMech": "TaxonRecord", "AIMech": "AIConcept",
    "CofactorMech": "CofactorRecord", "AssayMech": "AssayRecord",
}


def root_config(source, schema_path, class_name, globs, name):
    schema = yaml.safe_load(source["schemas"][schema_path])
    attrs = schema["classes"][class_name]["attributes"]
    identifiers = [key for key, value in attrs.items() if value and value.get("identifier")]
    if len(identifiers) != 1:
        raise ValueError(f"Ambiguous native identity: {source['name']} {class_name}")
    alias_fields = [key for key in ("synonyms", "aliases", "short_name") if key in attrs]
    alias_values = []
    if "synonyms" in attrs:
        alias_class = attrs["synonyms"].get("range")
        alias_attrs = schema["classes"].get(alias_class, {}).get("attributes", {})
        alias_values = [key for key in ("synonym_text", "value", "name") if key in alias_attrs]
    supported = "discussions" in attrs or "research_gaps" in attrs
    adapter = "research_gaps" if "research_gaps" in attrs else "discussions"
    result = {
        "name": name, "globs": globs,
        "exclude_globs": [p + "**" for p in EXCLUDE_DIRS.get(source["name"], [])],
        "supported": supported, "adapter": adapter,
        "id_field": identifiers[0],
        "name_fields": [key for key in ("label", "preferred_term", "name") if key in attrs],
        "alias_fields": alias_fields, "alias_value_fields": alias_values,
        "schema_path": schema_path, "schema_class": class_name,
        "schema_sha256": hashlib.sha256(source["schemas"][schema_path].encode()).hexdigest(),
        "unsupported_reason": None if supported else "The native record schema has no structured discussions or research_gaps field; missing fields are not inferred scientific gaps.",
        "page_url_template": None,
    }
    if adapter == "research_gaps":
        key = "corpus" if source["name"] == "CofactorMech" else "scope"
        gap = schema["classes"]["ResearchGap"]["attributes"]
        result.update({
            "gap_key": key,
            "gap_key_values": list(schema["enums"][gap[key]["range"]]["permissible_values"]),
            "gap_kind": "CURATION_TODO", "gap_status": "UNSPECIFIED",
            "gap_id_prefix": "research-gap:",
            "gap_mapping_note": "Project-defined coverage/protocol curation gaps. Use the unique per-record target corpus or scope as the projected local ID; reject duplicate keys. Preserve reason as prompt; do not infer status, review state or evidence from the parent record.",
        })
    if source["name"] == "MediaIngredientMech":
        result["identity_note"] = "The semantic identifier can repeat across documents; retain full source path in document and discussion identity."
    if class_name == "CuratedAIConcept":
        result["publication_allowed"] = False
        result["unsupported_reason"] = "Maintained concepts expose limitations and claims, not structured discussions. The inspected LICENSE-DATA grant covers data/aio only; maintained data publication terms require separate verification."
    return result


def build_source(source):
    name = source["name"]
    if is_withheld(name) or is_withheld(source["repository"]):
        raise ValueError("Source is outside the public projection")
    class_name = CLASSES[name]
    matching = [p for p, text in source["schemas"].items()
                if class_name in (yaml.safe_load(text).get("classes") or {})]
    if len(matching) != 1:
        raise ValueError(f"Ambiguous root schema: {name}")
    schema_path = matching[0]
    globs = ["data/families/*.yaml"] if name == "DUFMech" else RECORD_GLOBS[name]
    if name == "CommunityMech":
        roots = [root_config(source, schema_path, class_name, [g], label)
                 for g, label in zip(globs, ("communities", "isolates"))]
    elif name == "AIMech":
        roots = [root_config(source, schema_path, class_name, [globs[0]], "imported-aio"),
                 root_config(source, "src/aimech/schema/curated_concept.yaml", "CuratedAIConcept", [globs[1]], "maintained-concepts")]
    else:
        roots = [root_config(source, schema_path, class_name, globs, "canonical-records")]
    license_text = source["licenses"]["LICENSE-DATA"]
    if not any(s in license_text for s in ("Attribution 4.0", "CC-BY-4.0", "Creative Commons Attribution 4.0")):
        raise ValueError(f"Unrecognized data license: {name}")
    repo = source["repository"]
    sha = source["revision"]
    result = {key: source[key] for key in ("name", "repository", "default_branch", "revision", "acquired_at")}
    result.update({
        "site_url": "https://culturebotai.github.io/" + repo.split("/")[1] + "/",
        "publication_allowed": True,
        "data_license": "CC-BY-4.0",
        "license_url": f"https://github.com/{repo}/blob/{sha}/LICENSE-DATA",
        "license_sha256": hashlib.sha256(license_text.encode()).hexdigest(),
        "license_scope": "Project-authored data; third-party material retains its source terms. Evidence snippets are excluded from this public projection.",
        "attribution": name + " contributors and cited source contributors",
        "projection_changes": "Selected structured gap fields, normalized browser metadata, source references and coverage; dedicated evidence snippets omitted. Retained prompts and explanations remain subject to source terms.",
        "roots": roots,
    })
    if name == "AIMech":
        result["license_scope"] = "AIO source data and derived data/aio records only. Maintained data/curated publication is not authorized by this inspected data license."
        result["attribution"] = "Artificial Intelligence Ontology authors and AIMech contributors"
        result["additional_attribution_urls"] = [f"https://github.com/{repo}/blob/{sha}/sources/aio/CITATION.cff", f"https://github.com/{repo}/blob/{sha}/sources/aio/LICENSE"]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    args = parser.parse_args()
    sources = []
    for name in ORDER:
        source = json.loads((INPUT / (name + ".json")).read_text())
        if args.inspect:
            print(name, source["revision"])
            for path, body in source["schemas"].items():
                doc = yaml.safe_load(body)
                for key, cls in (doc.get("classes") or {}).items():
                    if cls.get("tree_root") or "discussions" in (cls.get("attributes") or {}):
                        attrs = cls.get("attributes", {})
                        keep = {k: v for k, v in attrs.items() if k in {
                            "identifier", "id", "label", "name", "preferred_term", "short_name",
                            "synonyms", "aliases", "discussions", "research_gaps"}}
                        print(path, key, json.dumps(keep))
                if "ResearchGap" in (doc.get("classes") or {}):
                    print("ResearchGap", json.dumps(doc["classes"]["ResearchGap"]))
                for key, cls in (doc.get("classes") or {}).items():
                    if "Synonym" in key:
                        print("Alias", key, list(cls.get("attributes", {})))
            print("LICENSE-DATA:", source["licenses"].get("LICENSE-DATA", "")[:850])
        else:
            sources.append(build_source(source))
    if not args.inspect:
        config = {"schema_version": 1,
                  "acquired_at": max(s["acquired_at"] for s in sources),
                  "source_scope": "The website's sixteen public corpus Mechs; infrastructure excluded.",
                  "evidence_snippets": False,
                  "sources": sources}
        target = ROOT / "_gaps/sources.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")
        saved = json.loads(target.read_text())
        if len(saved["sources"]) != len(ORDER):
            raise ValueError("Incomplete persisted source config")
        print(f"Wrote {len(sources)} public sources / {sum(len(s['roots']) for s in sources)} roots to {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
