"""Build deterministic cross-Mech analytical summaries for the gap browser.

Inputs: validated snapshot document, optional term-recognition document, and
optional retained embedding bundle document.
Outputs: a canonical JSON-serializable analytics sidecar bound by SHA-256 to the
exact snapshot, term index, and embedding inputs. No network or model calls.
2026-11-16.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math
import re

from snapshot import contains_unlisted_mech, digest, json_bytes

STOPWORDS = frozenset({
    "about", "above", "across", "after", "again", "against", "all", "also", "although",
    "among", "an", "and", "any", "are", "around", "as", "assign", "assigned", "at", "be",
    "because", "been", "before", "being", "below", "between", "both", "broad", "broader",
    "but", "by", "can", "cannot", "check", "checked", "child", "children", "clarify",
    "confirm", "confirmed", "confirms", "could", "curated", "curation", "current",
    "currently", "data", "defined", "definition", "describe", "described", "describes",
    "determine", "determined", "different", "direct", "directly", "discussion", "discussions",
    "distinct", "do", "documented", "does", "during", "each", "either", "ensure", "entry",
    "establish", "established", "establishes", "evidence", "exact", "example", "existing",
    "experimental", "experimentally", "explicit", "explicitly", "field", "fields", "for",
    "from", "further", "gap", "gaps", "general", "given", "has", "have", "having", "here",
    "how", "however", "identified", "identify", "if", "in", "include", "included", "includes",
    "including", "incomplete", "independent", "independently", "indicated", "individual",
    "information", "into", "investigated", "is", "it", "its", "itself", "known", "lack",
    "lacking", "lacks", "level", "levels", "linked", "literature", "local", "made", "main",
    "many", "mapping", "mappings", "may", "mechanism", "mechanisms", "mechanistic", "mint",
    "minted", "minting", "missing", "model", "models", "more", "most", "multiple", "must",
    "narrow", "narrower", "native", "need", "needed", "needs", "neither", "new", "no", "none",
    "nor", "not", "note", "noted", "observed", "occur", "occurs", "of", "often", "on", "once",
    "one", "only", "open", "or", "other", "others", "our", "out", "over", "overall", "own",
    "parent", "parents", "part", "partial", "partially", "particular", "per", "possible",
    "potential", "potentially", "precise", "present", "primary", "prior", "process",
    "processes", "proposed", "provide", "provided", "provides", "published", "question",
    "questions", "rather", "record", "recorded", "records", "reference", "references",
    "related", "relationship", "relationships", "relative", "remain", "remaining", "remains",
    "reported", "reports", "require", "required", "requires", "research", "resolve",
    "resolved", "resolves", "respective", "result", "results", "review", "reviewed", "role",
    "roles", "same", "schema", "scientific", "see", "several", "should", "shown", "shows",
    "similar", "single", "slot", "slots", "so", "some", "source", "sources", "specific",
    "specifically", "state", "states", "status", "still", "structured", "studies", "study",
    "such", "sufficient", "suggest", "suggested", "suggests", "support", "supported",
    "supporting", "system", "systems", "table", "tables", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "through", "throughout",
    "thus", "to", "todo", "two", "type", "types", "uncertain", "uncertainty", "unclear",
    "under", "unknown", "unresolved", "unspecified", "until", "up", "update", "updated",
    "upon", "use", "used", "using", "validate", "validated", "value", "values", "various",
    "verify", "verified", "very", "via", "was", "way", "well", "were", "what", "when",
    "where", "whether", "which", "while", "who", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet",
})

TOKEN_RE = re.compile(r"[a-z][a-z0-9-]{2,}")
CURIE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*:\S+$")
ATTACH_SPLIT_RE = re.compile(r"[#.\[/]")


def normalize_attach_layer(target: str) -> str:
    """Project an attaches_to path onto its top-level schema slot."""
    raw = str(target or "").strip()
    if not raw:
        return ""
    head = ATTACH_SPLIT_RE.split(raw, maxsplit=1)[0].strip()
    if not head:
        return ""
    if CURIE_RE.match(head):
        return "entity_curie"
    return head


def normalize_reference_key(ref: str) -> str:
    """Case-fold DOI and PMID prefixes so cross-Mech citation checks are canonical."""
    text = str(ref or "").strip()
    if not text:
        return ""
    lower = text.lower()
    if lower.startswith("doi:"):
        return "DOI:" + text[4:].strip().lower()
    if re.match(r"^10\.\d{4,9}/\S+$", text):
        return "DOI:" + lower
    if lower.startswith("pmid:"):
        return "PMID:" + text[5:].strip()
    return text


def extract_tokens(text: str) -> list[str]:
    tokens = []
    for match in TOKEN_RE.finditer((text or "").lower()):
        word = match.group(0).strip("-")
        if len(word) < 3 or word in STOPWORDS or word.isdigit():
            continue
        tokens.append(word)
    return tokens


def _unmatched_phrases(items: list[dict], matched_ids: set[str]) -> tuple[dict, list[dict]]:
    by_mech: dict[str, dict[str, int]] = {}
    unmatched_items = []
    for item in items:
        mech = item["mech"]
        entry = by_mech.setdefault(mech, {"total": 0, "matched": 0, "unmatched": 0})
        entry["total"] += 1
        if item["id"] in matched_ids:
            entry["matched"] += 1
        else:
            entry["unmatched"] += 1
            unmatched_items.append(item)

    phrase_docs: dict[tuple[str, str], set[str]] = defaultdict(set)
    phrase_mechs: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for item in unmatched_items:
        prose = f'{item.get("prompt") or ""} {item.get("rationale") or ""}'
        words = extract_tokens(prose)
        seen_unigrams = {w for w in words if len(w) >= 4}
        seen_bigrams = {f"{a} {b}" for a, b in zip(words, words[1:])}
        for unigram in seen_unigrams:
            key = ("unigram", unigram)
            phrase_docs[key].add(item["id"])
            phrase_mechs[key][item["mech"]] += 1
        for bigram in seen_bigrams:
            key = ("bigram", bigram)
            phrase_docs[key].add(item["id"])
            phrase_mechs[key][item["mech"]] += 1

    min_docs = 3 if len(unmatched_items) >= 10 else 2 if len(unmatched_items) >= 2 else 1
    bigrams = []
    bigram_counts: dict[str, int] = {}
    for (kind, phrase), doc_ids in phrase_docs.items():
        if kind != "bigram" or len(doc_ids) < min_docs:
            continue
        bigram_counts[phrase] = len(doc_ids)
        mechs = phrase_mechs[(kind, phrase)]
        bigrams.append({
            "phrase": phrase,
            "kind": "bigram",
            "discussions": len(doc_ids),
            "mech_count": len(mechs),
            "mechs": {m: mechs[m] for m in sorted(mechs)},
            "sample_ids": sorted(doc_ids)[:3],
        })
    bigrams.sort(key=lambda r: (-r["discussions"], -r["mech_count"], r["phrase"]))
    kept_bigrams = bigrams[:30]

    # Suppress unigrams whose occurrences are nearly subsumed by a kept bigram.
    subsumed: dict[str, int] = defaultdict(int)
    for row in kept_bigrams:
        for part in row["phrase"].split(" "):
            if row["discussions"] > subsumed[part]:
                subsumed[part] = row["discussions"]

    unigrams = []
    for (kind, phrase), doc_ids in phrase_docs.items():
        if kind != "unigram" or len(doc_ids) < min_docs:
            continue
        if subsumed.get(phrase, 0) >= len(doc_ids) * 0.85:
            continue
        mechs = phrase_mechs[(kind, phrase)]
        unigrams.append({
            "phrase": phrase,
            "kind": "unigram",
            "discussions": len(doc_ids),
            "mech_count": len(mechs),
            "mechs": {m: mechs[m] for m in sorted(mechs)},
            "sample_ids": sorted(doc_ids)[:3],
        })
    unigrams.sort(key=lambda r: (-r["discussions"], -r["mech_count"], r["phrase"]))

    combined = sorted(
        kept_bigrams[:25] + unigrams[:25],
        key=lambda r: (-r["discussions"], 0 if r["kind"] == "bigram" else 1, -r["mech_count"], r["phrase"]),
    )[:40]
    ordered_by_mech = {m: by_mech[m] for m in sorted(by_mech)}
    return ordered_by_mech, combined


def _proposed_experiments(items: list[dict]) -> dict:
    by_mech: Counter = Counter()
    rows = []
    total_experiments = 0
    for item in sorted(items, key=lambda i: i["id"]):
        exps = item.get("proposed_experiments") or []
        if not exps:
            continue
        by_mech[item["mech"]] += 1
        total_experiments += len(exps)
        names = []
        approaches = []
        for exp in exps[:5]:
            if isinstance(exp, dict):
                title = str(exp.get("name") or exp.get("experiment_id") or "Proposed experiment").strip()
                names.append(title[:120])
                approach = str(exp.get("approach") or "").strip()
                if approach:
                    approaches.append(approach[:160])
            else:
                names.append(str(exp).strip()[:120])
        rows.append({
            "id": item["id"],
            "mech": item["mech"],
            "record_id": item.get("record_id") or "",
            "record_label": item.get("record_label") or "",
            "prompt": item.get("prompt") or "",
            "kind": item.get("kind") or "UNSPECIFIED",
            "status": item.get("status") or "UNSPECIFIED",
            "experiment_count": len(exps),
            "experiment_names": names,
            "approaches": approaches[:3],
        })
    return {
        "discussions_with_experiments": len(rows),
        "total_experiments": total_experiments,
        "by_mech": {m: by_mech[m] for m in sorted(by_mech)},
        "items": rows[:50],
    }


def _citation_silos(items: list[dict]) -> dict:
    ref_docs: dict[str, set[str]] = defaultdict(set)
    ref_mechs: dict[str, set[str]] = defaultdict(set)
    ref_raw: dict[str, str] = {}
    items_with_refs = 0
    for item in items:
        refs = item.get("evidence_refs") or []
        if refs:
            items_with_refs += 1
        for raw in refs:
            canonical = normalize_reference_key(raw)
            if not canonical:
                continue
            ref_raw.setdefault(canonical, str(raw).strip())
            ref_docs[canonical].add(item["id"])
            ref_mechs[canonical].add(item["mech"])

    cross_mech = []
    for canonical, mechs in ref_mechs.items():
        if len(mechs) > 1:
            docs = ref_docs[canonical]
            cross_mech.append({
                "ref": canonical,
                "raw_ref": ref_raw[canonical],
                "discussions": len(docs),
                "mech_count": len(mechs),
                "mechs": sorted(mechs),
                "sample_ids": sorted(docs)[:5],
            })
    cross_mech.sort(key=lambda r: (-r["mech_count"], -r["discussions"], r["ref"]))
    return {
        "distinct_normalized_refs": len(ref_docs),
        "discussions_with_refs": items_with_refs,
        "cross_mech_ref_count": len(cross_mech),
        "cross_mech_refs": cross_mech[:30],
    }


def _embedding_analytics(items_by_id: dict[str, dict], term_document: dict | None, embedding_document: dict) -> dict:
    points = embedding_document.get("points") or []
    point_by_id = {p["id"]: p for p in points if isinstance(p, dict) and p.get("id") in items_by_id}

    # 1. Cross-Mech nearest-neighbor pairs and Mech-pair summary matrix.
    unordered_pairs: dict[tuple[str, str], float] = {}
    mech_pair_edges: dict[tuple[str, str], list[float]] = defaultdict(list)
    top1_cross_count = 0
    any_cross_count = 0

    for pid in sorted(point_by_id):
        point = point_by_id[pid]
        mech_a = items_by_id[pid]["mech"]
        neighbors = point.get("neighbors") or []
        has_cross = False
        for idx, neighbor in enumerate(neighbors):
            nid = neighbor.get("id")
            sim = neighbor.get("cosine_similarity")
            if nid not in items_by_id or type(sim) not in (int, float) or not math.isfinite(sim):
                continue
            mech_b = items_by_id[nid]["mech"]
            if mech_a == mech_b:
                continue
            has_cross = True
            if idx == 0:
                top1_cross_count += 1
            m_pair = (mech_a, mech_b) if mech_a < mech_b else (mech_b, mech_a)
            mech_pair_edges[m_pair].append(float(sim))
            id_pair = (pid, nid) if pid < nid else (nid, pid)
            prev = unordered_pairs.get(id_pair)
            if prev is None or float(sim) > prev:
                unordered_pairs[id_pair] = float(sim)
        if has_cross:
            any_cross_count += 1

    ranked_pairs = sorted(
        unordered_pairs.items(),
        key=lambda kv: (-round(kv[1], 6), kv[0][0], kv[0][1]),
    )
    featured_pairs = []
    per_id_cap: Counter = Counter()
    for (id_a, id_b), sim in ranked_pairs:
        if per_id_cap[id_a] >= 2 or per_id_cap[id_b] >= 2:
            continue
        per_id_cap[id_a] += 1
        per_id_cap[id_b] += 1
        item_a, item_b = items_by_id[id_a], items_by_id[id_b]
        featured_pairs.append({
            "id_a": id_a,
            "mech_a": item_a["mech"],
            "record_a": item_a.get("record_label") or item_a.get("record_id") or id_a,
            "prompt_a": (item_a.get("prompt") or "")[:180],
            "kind_a": item_a.get("kind") or "UNSPECIFIED",
            "id_b": id_b,
            "mech_b": item_b["mech"],
            "record_b": item_b.get("record_label") or item_b.get("record_id") or id_b,
            "prompt_b": (item_b.get("prompt") or "")[:180],
            "kind_b": item_b.get("kind") or "UNSPECIFIED",
            "cosine_similarity": round(sim, 6),
        })
        if len(featured_pairs) >= 40:
            break

    mech_matrix = []
    for (mech_a, mech_b), sims in sorted(mech_pair_edges.items()):
        mech_matrix.append({
            "mech_a": mech_a,
            "mech_b": mech_b,
            "directed_neighbor_edges": len(sims),
            "max_cosine": round(max(sims), 6),
            "mean_cosine": round(sum(sims) / len(sims), 4),
        })
    mech_matrix.sort(key=lambda r: (-r["directed_neighbor_edges"], -r["max_cosine"], r["mech_a"], r["mech_b"]))

    # 2. Duplicate input-text clusters (identical input_sha256).
    by_hash: dict[str, list[str]] = defaultdict(list)
    for pid in sorted(point_by_id):
        sha = point_by_id[pid].get("input_sha256")
        if sha:
            by_hash[sha].append(pid)
    duplicate_clusters = []
    duplicate_discussions = 0
    for sha, ids in by_hash.items():
        if len(ids) < 2:
            continue
        duplicate_discussions += len(ids)
        mechs = Counter(items_by_id[i]["mech"] for i in ids)
        first = items_by_id[ids[0]]
        duplicate_clusters.append({
            "input_sha256": sha,
            "count": len(ids),
            "cross_mech": len(mechs) > 1,
            "mechs": {m: mechs[m] for m in sorted(mechs)},
            "sample_prompt": (first.get("prompt") or "")[:180],
            "discussion_ids": ids[:8],
        })
    duplicate_clusters.sort(key=lambda r: (-r["count"], not r["cross_mech"], r["input_sha256"]))

    # 3. Entity semantic cohesion in original-vector neighbor space.
    entity_cohesion = []
    if term_document and isinstance(term_document.get("terms"), list):
        candidates = []
        for term in term_document["terms"]:
            postings = term.get("postings") or []
            doc_ids = {p["discussion_id"] for p in postings if isinstance(p, dict) and p.get("discussion_id") in point_by_id}
            if len(doc_ids) < 5:
                continue
            occ = sum(int(p.get("count", 0)) for p in postings if isinstance(p, dict) and p.get("discussion_id") in doc_ids)
            candidates.append((occ, term["id"], term, doc_ids))
        candidates.sort(key=lambda t: (-t[0], t[1]))
        for occ, term_id, term, doc_ids in candidates[:50]:
            with_same_neighbor = 0
            shared_edges = 0
            possible_edges = 0
            same_sims = []
            mechs = Counter(items_by_id[d]["mech"] for d in doc_ids)
            for did in sorted(doc_ids):
                neighbors = point_by_id[did].get("neighbors") or []
                possible_edges += min(len(neighbors), max(0, len(doc_ids) - 1))
                hits = [
                    float(n["cosine_similarity"])
                    for n in neighbors
                    if n.get("id") in doc_ids and type(n.get("cosine_similarity")) in (int, float)
                    and math.isfinite(n["cosine_similarity"])
                ]
                if hits:
                    with_same_neighbor += 1
                    shared_edges += len(hits)
                    same_sims.extend(hits)
            hit_rate = round(with_same_neighbor / len(doc_ids), 4)
            edge_share = round(shared_edges / possible_edges, 4) if possible_edges else 0.0
            mean_sim = round(sum(same_sims) / len(same_sims), 4) if same_sims else None
            vocab_mechs = sorted({
                ref["mech"] for ref in (term.get("entity_refs") or [])
                if isinstance(ref, dict) and ref.get("mech")
            })
            entity_cohesion.append({
                "id": term_id,
                "label": term.get("label") or term_id,
                "canonical_id": term.get("canonical_id"),
                "discussions": len(doc_ids),
                "occurrences": occ,
                "discussion_mech_count": len(mechs),
                "vocab_mechs": vocab_mechs,
                "neighbor_hit_rate": hit_rate,
                "within_entity_neighbor_share": edge_share,
                "mean_same_entity_cosine": mean_sim,
            })
        entity_cohesion.sort(key=lambda r: (-r["within_entity_neighbor_share"], -r["neighbor_hit_rate"], -r["discussions"], r["id"]))

    return {
        "total_cross_mech_unordered_pairs": len(unordered_pairs),
        "discussions_with_cross_mech_top1": top1_cross_count,
        "discussions_with_any_cross_mech_top15": any_cross_count,
        "cross_mech_pairs": featured_pairs,
        "cross_mech_matrix": mech_matrix,
        "duplicate_discussion_count": duplicate_discussions,
        "duplicate_cluster_count": len(duplicate_clusters),
        "duplicate_clusters": duplicate_clusters[:30],
        "entity_cohesion": entity_cohesion,
    }


def build_analytics_document(snapshot: dict, term_document: dict | None = None,
                             embedding_document: dict | None = None) -> dict:
    """Construct a deterministic, canonical analytics sidecar for the snapshot."""
    raw_snapshot = json_bytes(snapshot)
    if contains_unlisted_mech(raw_snapshot.decode("utf-8")):
        raise ValueError("Unlisted or withheld Mech in gap analytics input")
    build_id = digest(raw_snapshot)
    items = snapshot.get("items") or []
    items_by_id = {item["id"]: item for item in items}
    sources = [source["name"] for source in (snapshot.get("sources") or [])]

    matched_ids: set[str] = set()
    terms_sha = None
    if term_document is not None:
        terms_sha = digest(json_bytes(term_document))
        for term in term_document.get("terms") or []:
            for posting in term.get("postings") or []:
                did = posting.get("discussion_id")
                if did in items_by_id:
                    matched_ids.add(did)

    unmatched_by_mech, unmatched_phrases = _unmatched_phrases(items, matched_ids)
    for source_name in sources:
        unmatched_by_mech.setdefault(source_name, {"total": 0, "matched": 0, "unmatched": 0})
    unmatched_by_mech = {m: unmatched_by_mech[m] for m in sorted(unmatched_by_mech)}

    gap_items = [
        item for item in items
        if item.get("lane") != "candidate" and item.get("kind") in ("KNOWLEDGE_GAP", "HUMAN_MODEL_MISMATCH")
    ]
    gap_by_mech, gap_phrases = _unmatched_phrases(gap_items, matched_ids)
    for source_name in sources:
        gap_by_mech.setdefault(source_name, {"total": 0, "matched": 0, "unmatched": 0})
    gap_by_mech = {m: gap_by_mech[m] for m in sorted(gap_by_mech)}
    matched_gap_count = sum(1 for item in gap_items if item["id"] in matched_ids)

    document = {
        "schema_version": 1,
        "build_id": build_id,
        "terms_sha256": terms_sha,
        "embedding_inputs_sha256": embedding_document.get("inputs_sha256") if embedding_document else None,
        "unmatched_coverage": {
            "has_term_index": term_document is not None,
            "total_discussions": len(items),
            "matched_discussions": len(matched_ids),
            "unmatched_discussions": len(items) - len(matched_ids),
            "by_mech": unmatched_by_mech,
            "candidate_phrases": unmatched_phrases if term_document is not None else [],
            "gaps_only": {
                "total_discussions": len(gap_items),
                "matched_discussions": matched_gap_count,
                "unmatched_discussions": len(gap_items) - matched_gap_count,
                "by_mech": gap_by_mech,
                "candidate_phrases": gap_phrases if term_document is not None else [],
            },
        },
        "proposed_experiments": _proposed_experiments(items),
        "citations": _citation_silos(items),
        "embedding_bridges": (
            _embedding_analytics(items_by_id, term_document, embedding_document)
            if embedding_document is not None else None
        ),
    }
    serialized = json_bytes(document)
    if contains_unlisted_mech(serialized.decode("utf-8")):
        raise ValueError("Withheld identity in public gap analytics")
    return document
