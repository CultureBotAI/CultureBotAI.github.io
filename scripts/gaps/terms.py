"""Dictionary term linking for the knowledge-gap explorer; 2026-11-15.

Inputs: retained public discussion snapshot and a pinned public term vocabulary.
Outputs: deterministic term occurrence postings; no model calls or source writes.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from copy import deepcopy


TEXT_FIELDS = ("prompt", "rationale", "resolution_note")
EXPERIMENT_TEXT_FIELDS = ("name", "description", "approach", "decision_criterion",
                          "would_support", "would_refute")
EXPERIMENT_LIST_FIELDS = ("model_systems", "perturbations", "readouts")
SEMANTIC_NAMESPACES = {prefix.casefold(): prefix for prefix in (
    "CHEBI", "NCBITaxon", "METPO", "ENVO", "FOODON", "UBERON", "BTO", "PO",
    "ARO", "GO", "PR", "PFAM", "InterPro", "AIO",
)}
STOP_FORMS = frozenset("""a an and any are as at be but by can for from had has have he
if in into is it its may more most no not now of on one or other our out per than
that the this to unknown unclassified unspecified none use used via was were will
with without lead reduces imports produces accumulates""".split())
PLACEHOLDER_LABELS = frozenset(("unknown", "unclassified", "unspecified", "none",
                              "n/a", "unnamed", "not available", "not applicable"))
# Source-scoped precision decisions from the retained full-corpus audit (#592).
# These do not modify native names or claim that a synonym is never valid.
SURFACE_DENIALS = [
    {"mech": "HabitatMech", "record_id": "ENVO:00000084", "surfaces": ["pass"],
     "reason": "Ordinary curation passes do not identify a mountain pass"},
    {"mech": "HabitatMech", "record_id": "ENVO:00000020", "surfaces": ["broad", "mere"],
     "reason": "Broad mappings and mere possession do not identify a lake (#592, #597)"},
    {"mech": "HabitatMech", "record_id": "ENVO:01000910", "surfaces": ["biological"],
     "reason": "The generic adjective does not identify soil biocrust"},
    {"mech": "HabitatMech", "record_id": "UBERON:0006726", "surfaces": ["outer"],
     "reason": "Generic spatial language does not identify an outer canthus"},
    {"mech": "HabitatMech", "record_id": "UBERON:0005611", "surfaces": ["inner"],
     "reason": "Generic spatial language does not identify an inner canthus"},
    {"mech": "HabitatMech", "record_id": "ENVO:00000029",
     "surfaces": ["course", "kill", "narrows", "passage", "reach", "run"],
     "reason": "These ordinary words do not establish a watercourse"},
    {"mech": "HabitatMech", "record_id": "habitatmech:GOLD.cd0b0940e5", "surfaces": ["human"],
     "reason": "Human cell and gene descriptions do not identify an associated environment"},
    {"mech": "ProteinTraitsMech", "record_id": "MI:1110", "surfaces": ["predicted"],
     "reason": "Predicted peptides and annotations do not establish a predicted interaction"},
    {"mech": "ProteinTraitsMech", "record_id": "MI:0796", "surfaces": ["suppression"],
     "reason": "Disease suppression does not identify combined genetic perturbation effects (#596)"},
    {"mech": "HabitatMech", "record_id": "ENVO:01001069", "surfaces": ["metal"],
     "reason": "Dissolved metal ions do not identify material primarily composed of pure metals (#596)"},
    {"mech": "ProteinTraitsMech", "record_id": "EC:3.5.1.88", "surfaces": ["pdf"],
     "reason": "Document and diffraction references do not identify peptide deformylase (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "UniProtKB-KW:KW-0732", "surfaces": ["signal"],
     "reason": "Assay signals do not identify a protein targeting signal sequence (#597)"},
    {"mech": "HabitatMech", "record_id": "ENVO:00000040", "surfaces": ["cascade", "fall", "falls", "force"],
     "reason": "Reaction cascades and mechanical force do not identify a waterfall (#597)"},
    {"mech": "HabitatMech", "record_id": "ENVO:00002144", "surfaces": ["wall"],
     "reason": "Cell-wall descriptions do not identify a cave wall (#597)"},
    {"mech": "HabitatMech", "record_id": "UBERON:0002183", "surfaces": ["secondary"],
     "reason": "Secondary plastids and metabolites do not identify a lobar bronchus (#597)"},
    {"mech": "HabitatMech", "record_id": "ENVO:00000064", "surfaces": ["drive", "drove"],
     "reason": "Driving a biological outcome does not identify a road (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "Pfam:PF12361", "surfaces": ["dbp"],
     "reason": "Dibromophenol abbreviations do not identify Plasmodium Duffy-antigen binding protein (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "NCBIfam:NF045600", "surfaces": ["bsta"],
     "reason": "The phage-defense BstA system does not identify the sterol transporter (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "EC:1.14.13.8", "surfaces": ["fmo"],
     "reason": "Unresolved Lamassu FMO profile labels do not establish this exact EC chemistry (#597)"},
]
ID_ONLY_ENTITIES = [
    {"mech": "ProteinTraitsMech", "record_id": "OrthoDB:110285at2759",
     "reason": "Generic protein text does not identify this specific eukaryotic ortholog group (#593)"},
    {"mech": "ProteinTraitsMech", "record_id": "Reactome:R-HSA-168298",
     "reason": "Generic release does not identify this viral release pathway (#593)"},
    {"mech": "ProteinTraitsMech", "record_id": "Reactome:R-HSA-168302",
     "reason": "Budding yeast does not identify this viral budding pathway (#593)"},
    {"mech": "ProteinTraitsMech", "record_id": "PATO:0000141",
     "reason": "Graph-model structure does not identify organism morphology (#594)"},
    {"mech": "ProteinTraitsMech", "record_id": "Pfam:CL0165",
     "reason": "Literature and software caches do not identify this protein-family clan (#596)"},
    {"mech": "MediaIngredientMech", "record_id": "NCIT:C71971",
     "reason": "Fig figure references do not identify the fig fruit concept (#596)"},
    {"mech": "ProteinTraitsMech", "record_id": "PROSITE:PDOC00955",
     "reason": "Graph and reference links do not identify this protein family (#597)"},
    {"mech": "HabitatMech", "record_id": "habitatmech:GOLD.5df162af13",
     "reason": "Graph-modeling prose does not identify the Engineered > Modeled source branch (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "IDPO:0000006",
     "reason": "Analysis order does not identify a protein intrinsic-disorder structural state (#597)"},
    {"mech": "TaxonMech", "record_id": "NCBITaxon:32644",
     "reason": "Collection provenance and unidentified proteins do not identify this taxonomy placeholder (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "SCOP:46726",
     "reason": "Taxon-paired protein accessions do not identify this specific SCOPe node (#597)"},
    {"mech": "ProteinTraitsMech", "record_id": "MI:0914",
     "reason": "Organism-level associations do not identify physical molecular complexes (#597)"},
]
# Apply to the canonical identity so shared vocabulary owners cannot bypass it.
# The symbol keeps native case; the descriptive suffix keeps normal case folding.
CANONICAL_CASE_RULES = [
    {"canonical_id": "PFAM:PF02597", "surface": "this family", "pattern": "ThiS (?i:family)",
     "reason": "Ordinary this family prose does not identify the ThiS protein family (#605)"},
]
POLICY = {
    "version": 3, "method": "dictionary-linked entity recognition; no contextual inference",
    "normalization": "Unicode NFKC, casefold, collapse whitespace; punctuation retained",
    "text_fields": list(TEXT_FIELDS) + ["evidence[].explanation"] +
        ["proposed_experiments[]." + field for field in EXPERIMENT_TEXT_FIELDS] +
        ["proposed_experiments[]." + field + "[]" for field in EXPERIMENT_LIST_FIELDS],
    "excluded_metadata": ["record_label", "aliases", "record_id", "discussion_id", "attaches_to",
                          "evidence_refs", "source", "experiment_id"],
    "counting": "Each accepted occurrence in each actual text field; copied fields count independently",
    "interpretation": "Includes negated and contextual mentions; lexical counts do not assert scientific claims or interactions",
    "overlap": "Leftmost longest whole-word surface; letters, numbers and combining marks belong to words; ambiguous longest spans block nested fallback",
    "ambiguity": "A surface with multiple eligible canonical concepts remains unlinked",
    "short_forms": "Forms without letters, or with fewer than 3 alphanumeric characters, are excluded except explicit CURIEs; 3 characters require exact case",
    "acronyms": "Compact uppercase acronyms and mixed-case symbols with internal capitals of up to 6 letters require exact case",
    "canonical_case_rules": CANONICAL_CASE_RULES,
    "source_surface_denials": SURFACE_DENIALS,
    "identifier_only_entities": ID_ONLY_ENTITIES,
    "denial_behavior": "A denied eligible surface blocks reassignment to competing concepts; full descriptive forms and identifiers remain available",
    "stop_forms": sorted(STOP_FORMS),
    "canonical_namespaces": SEMANTIC_NAMESPACES,
    "identity": "Exact declared canonical CURIE with normalized recognized prefix; otherwise source-unique ID",
    "display_label": "Lexicographically first informative native label, or explicit identifier if all labels are placeholders; all source labels retained",
    "pair_unit": "One unordered distinct-term pair per discussion, after reader filters",
    "span_encoding": "Unicode codepoint offsets into original field text",
}


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def _digest(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def normalize_surface(text):
    """Normalize matching text, preserving chemical punctuation and word forms."""
    if not isinstance(text, str):
        raise ValueError("Term matching text must be a string")
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def iter_item_texts(item):
    """Yield (field locator, original text), never owning-record metadata."""
    def checked(field, value):
        if not isinstance(value, str):
            raise ValueError(f"Discussion text at {field} must be a string")
        return field, value

    for field in TEXT_FIELDS:
        yield checked(field, item.get(field, ""))
    for index, evidence in enumerate(item.get("evidence", [])):
        yield checked(f"evidence[{index}].explanation", evidence.get("explanation", ""))
    for index, experiment in enumerate(item.get("proposed_experiments", [])):
        for field in EXPERIMENT_TEXT_FIELDS:
            yield checked(f"proposed_experiments[{index}].{field}", experiment.get(field, ""))
        for field in EXPERIMENT_LIST_FIELDS:
            values = experiment.get(field, [])
            if not isinstance(values, list):
                raise ValueError(f"Experiment {field} must be a list")
            for position, value in enumerate(values):
                yield checked(f"proposed_experiments[{index}].{field}[{position}]", value)


def corpus_texts(snapshot):
    """The complete matching corpus, including noninitial detail shard fields."""
    return [text for item in snapshot["items"] for _field, text in iter_item_texts(item) if text]


def make_surface_prefilter(snapshot):
    """Safe lexical superset for streaming a large pinned vocabulary.

    Every source record sharing a possible surface must be retained. This only
    removes surfaces absent from all fields; boundaries, ambiguity and case
    policy belong to the final matcher, not vocabulary acquisition.
    """
    corpus = "\0".join(normalize_surface(text) for text in corpus_texts(snapshot))
    tokens = set(re.findall(r"\w+", corpus))

    def possible(surface):
        normalized = normalize_surface(surface)
        return bool(normalized and
                    all(token in tokens for token in re.findall(r"\w+", normalized)) and
                    normalized in corpus)

    return possible


def _normalized_with_offsets(text):
    """Map normalized word-boundary matches back to original codepoint offsets.

    Normalize whole Unicode words (including combining marks), so ligatures,
    decomposed accents and Hangul compose identically to the vocabulary. Every
    accepted boundary is outside a word, so word-level offset ranges are exact.
    """
    chunks = []
    position = 0
    while position < len(text):
        end = position + 1
        word = text[position].isalnum() or text[position] == "_" or unicodedata.category(text[position]).startswith("M")
        if word:
            while end < len(text) and (text[end].isalnum() or text[end] == "_" or
                                       unicodedata.category(text[end]).startswith("M")):
                end += 1
        value = unicodedata.normalize("NFKC", text[position:end]).casefold()
        chunks.extend((char, position, end) for char in value)
        position = end
    characters, starts, ends = [], [], []
    for char, start, end in chunks:
        if char.isspace():
            if characters and characters[-1] != " ":
                characters.append(" ")
                starts.append(start)
                ends.append(end)
            elif characters:
                ends[-1] = end
        else:
            characters.append(char)
            starts.append(start)
            ends.append(end)
    if characters and characters[-1] == " ":
        characters.pop()
        starts.pop()
        ends.pop()
    normalized = "".join(characters)
    if normalized != normalize_surface(text):
        raise ValueError("Cannot map Unicode normalization to exact source spans")
    return normalized, starts, ends


def _case_form(text):
    return " ".join(unicodedata.normalize("NFKC", text).split())


def _word_character(char):
    return char.isalnum() or char == "_" or unicodedata.category(char).startswith("M")


def _display_label(labels, canonical_id, references):
    informative = [label for label in labels if any(char.isalnum() for char in label)
                   and normalize_surface(label) not in PLACEHOLDER_LABELS]
    if informative:
        return informative[0]
    return canonical_id or min(ref["record_id"] for ref in references)


def _concept_key(term):
    value = term.get("canonical_id", term["record_id"])
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Vocabulary canonical_id must be nonempty text")
    prefix, separator, local = value.partition(":")
    if separator and local and not re.search(r"\s", value) and prefix.casefold() in SEMANTIC_NAMESPACES:
        canonical = SEMANTIC_NAMESPACES[prefix.casefold()] + ":" + local
        return "canonical:" + canonical, canonical
    return "source:" + term["id"], ""


def _surface_rule(form):
    normalized = normalize_surface(form)
    explicit_id = bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*:[^\s]+", form))
    if not normalized or normalized in STOP_FORMS:
        return None
    letters = [char for char in _case_form(form) if char.isalpha()]
    alphanumeric = sum(char.isalnum() for char in normalized)
    if not explicit_id and (alphanumeric < 3 or not any(char.isalpha() for char in normalized)):
        return None
    acronym = (0 < len(letters) <= 6 and not re.search(r"\s", form)
               and all(char.isupper() for char in letters))
    mixed_symbol = (0 < len(letters) <= 6 and not re.search(r"\s", form)
                    and any(char.islower() for char in letters)
                    and any(char.isupper() for char in letters[1:]))
    return normalized, not explicit_id and (alphanumeric <= 3 or acronym or mixed_symbol)


def _surface_denial(term, form):
    # A source's explicit native/canonical identifier always remains available.
    if form in {term["record_id"], term.get("canonical_id", term["record_id"])}:
        return ""
    identity = (term["mech"], term["record_id"])
    for row in ID_ONLY_ENTITIES:
        if identity == (row["mech"], row["record_id"]):
            return row["reason"]
    for row in SURFACE_DENIALS:
        if identity == (row["mech"], row["record_id"]) and normalize_surface(form) in row["surfaces"]:
            return row["reason"]
    return ""


def build_term_document(snapshot, vocabulary):
    """Validate inputs and create deterministic complete occurrence postings.

    Vocabulary acquisition owns public-source/schema/license validation. This
    function additionally binds its snapshot/config hashes and rejects malformed
    identities, aliases, provenance or duplicate IDs rather than dropping them.
    """
    if snapshot.get("schema_version") != 1 or vocabulary.get("schema_version") != 1:
        raise ValueError("Unsupported term input version")
    build_id = _digest(snapshot)
    if vocabulary.get("snapshot_sha256") != build_id:
        raise ValueError("Vocabulary belongs to a different discussion snapshot")
    if vocabulary.get("source_config_sha256") != snapshot.get("source_config_sha256"):
        raise ValueError("Vocabulary source configuration mismatch")
    if not isinstance(vocabulary.get("sources"), list) or not isinstance(vocabulary.get("terms"), list):
        raise ValueError("Vocabulary sources and terms must be lists")
    item_ids = [item.get("id") for item in snapshot["items"]]
    if any(not isinstance(value, str) or not value for value in item_ids) or len(set(item_ids)) != len(item_ids):
        raise ValueError("Discussion IDs must be unique nonempty strings")
    groups, surfaces = {}, defaultdict(dict)
    possible_surface = make_surface_prefilter(snapshot)
    seen_ids, excluded, denied = set(), set(), set()
    for term in vocabulary["terms"]:
        if not isinstance(term, dict):
            raise ValueError("Vocabulary entries must be objects")
        for field in ("id", "mech", "record_id", "label"):
            if not isinstance(term.get(field), str) or not term[field].strip():
                raise ValueError(f"Vocabulary {field} must be nonempty text")
        if term["id"] in seen_ids:
            raise ValueError("Duplicate vocabulary source identity")
        seen_ids.add(term["id"])
        aliases = term.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
            raise ValueError("Vocabulary aliases must be strings")
        source = term.get("source")
        if not isinstance(source, dict) or any(not isinstance(source.get(field), str) or not source[field]
                                              for field in ("repository", "revision", "path", "sha256", "url", "license")):
            raise ValueError("Vocabulary source provenance is incomplete")
        concept, canonical = _concept_key(term)
        entity_id = "term-" + hashlib.sha256(concept.encode()).hexdigest()
        group = groups.setdefault(entity_id, {"id": entity_id, "canonical_id": canonical,
                                              "labels": set(), "entity_refs": []})
        group["labels"].add(term["label"])
        group["entity_refs"].append({"mech": term["mech"], "record_id": term["record_id"],
                                     "label": term["label"], "url": source["url"], "source": deepcopy(source)})
        for form in set([term["label"], term["record_id"], term.get("canonical_id", term["record_id"])] + aliases):
            rule = _surface_rule(form)
            if rule is None:
                excluded.add(form)
                continue
            # #587: retained source records may have many absent alternate forms.
            # Group every record first to preserve collisions and source credit;
            # only the regex vocabulary is bounded to corpus-possible surfaces.
            if not possible_surface(form):
                continue
            normalized, sensitive = rule
            case_pattern = next((re.compile(row["pattern"]) for row in CANONICAL_CASE_RULES
                                 if canonical == row["canonical_id"] and normalized == row["surface"]), None)
            reason = _surface_denial(term, form)
            if reason:
                denied.add((term["mech"], term["record_id"], form, reason))
            surfaces[normalized].setdefault(entity_id, set()).add((_case_form(form), sensitive, case_pattern, reason))
    # Alternation order establishes longest matching at each leftmost position.
    pattern = (re.compile(r"(?<!\w)(?:" + "|".join(re.escape(surface) for surface in
               sorted(surfaces, key=lambda value: (-len(value), value))) + r")(?!\w)") if surfaces else None)
    postings = defaultdict(lambda: defaultdict(list))
    ambiguous = Counter()
    rejected_case = 0
    rejected_boundary = 0
    rejected_policy = 0
    for item in sorted(snapshot["items"], key=lambda row: row["id"]):
        for field, text in iter_item_texts(item):
            if not text or pattern is None:
                continue
            normalized, starts, ends = _normalized_with_offsets(text)
            for match in pattern.finditer(normalized):
                # Python re's \w omits combining marks. Treat them as part of the
                # neighboring word, and never emit a partial normalized source
                # cluster with a span covering more text than the match (#585).
                if ((match.start() and _word_character(normalized[match.start() - 1])) or
                        (match.end() < len(normalized) and _word_character(normalized[match.end()]))):
                    rejected_boundary += 1
                    continue
                start, end = starts[match.start()], ends[match.end() - 1]
                original = text[start:end]
                if normalize_surface(original) != match.group():
                    rejected_boundary += 1
                    continue
                original_case = _case_form(original)
                eligible_forms = {key: [reason for form, sensitive, case_pattern, reason in forms
                                        if (not sensitive or original_case == form)
                                        and (case_pattern is None or case_pattern.fullmatch(original_case))]
                                  for key, forms in surfaces[match.group()].items()}
                eligible = {key for key, reasons in eligible_forms.items() if reasons}
                if not eligible:
                    rejected_case += 1
                    continue
                if any(reason for reasons in eligible_forms.values() for reason in reasons):
                    rejected_policy += 1
                    continue
                if len(eligible) != 1:
                    ambiguous[(match.group(), tuple(sorted(eligible)))] += 1
                    continue
                entity_id = next(iter(eligible))
                postings[entity_id][item["id"]].append({"field": field, "start": start, "end": end,
                                                        "text": original, "matched_as": match.group()})
    terms = []
    for entity_id in sorted(postings):
        group = groups[entity_id]
        labels = sorted(group["labels"], key=lambda label: (label.casefold(), label))
        terms.append({"id": entity_id, "canonical_id": group["canonical_id"],
                      "label": _display_label(labels, group["canonical_id"], group["entity_refs"]),
                      "labels": labels,
                      "entity_refs": sorted(group["entity_refs"], key=lambda ref: (ref["mech"], ref["source"]["path"], ref["record_id"])),
                      "postings": [{"discussion_id": discussion_id, "count": len(mentions), "mentions": mentions}
                                   for discussion_id, mentions in sorted(postings[entity_id].items())]})
    vocabulary_hash = _digest(vocabulary)
    binding = {"build_id": build_id, "vocabulary_sha256": vocabulary_hash, "policy": POLICY}
    return {"schema_version": 1, "build_id": build_id, "term_build_id": _digest(binding),
            "vocabulary_sha256": vocabulary_hash, "policy": deepcopy(POLICY),
            "vocabulary_sources": deepcopy(vocabulary["sources"]), "terms": terms,
            "ambiguities": [{"surface": surface, "candidate_ids": list(ids), "occurrences": count}
                            for (surface, ids), count in sorted(ambiguous.items())],
            "summary": {"recognized_terms": len(terms),
                        "accepted_occurrences": sum(p["count"] for term in terms for p in term["postings"]),
                        "discussions_with_terms": len({p["discussion_id"] for term in terms for p in term["postings"]}),
                        "ambiguous_occurrences": sum(ambiguous.values()),
                        "case_rejected_occurrences": rejected_case,
                        "unicode_boundary_rejected_occurrences": rejected_boundary,
                        "policy_rejected_occurrences": rejected_policy,
                        "denied_surfaces": [{"mech": mech, "record_id": record_id, "surface": form,
                                             "reason": reason} for mech, record_id, form, reason in sorted(denied)],
                        "excluded_forms": sorted(excluded)}}
