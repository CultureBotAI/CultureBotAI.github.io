/* Deterministic gap search and analytical summaries shared by worker and offline tests. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GapSearch = api;
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var PAGE_SIZE = 50;
  var defaults = {
    q: '', view: 'gaps', mech: '', kind: '', status: 'active', review: '',
    layer: '', stance: '', experiments: '', ref: '', month: '',
    sort: 'relevance', page: 1, gap: '', term: '', term2: '', vocab: ''
  };
  function text(value) { return value == null ? '' : String(value); }
  function fold(value) { return text(value).normalize('NFKC').toLocaleLowerCase('en'); }
  function list(value) { return Array.isArray(value) ? value : []; }
  var MONTH_RE = /^\d{4}-(?:0[1-9]|1[0-2])$/;
  function extractMonth(dateStr) {
    if (typeof dateStr !== 'string') return '';
    var m = dateStr.match(/^(\d{4}-(?:0[1-9]|1[0-2]))(?:$|[-T\s])/);
    return m ? m[1] : '';
  }
  function normalizeAttachLayer(target) {
    var raw = text(target).trim();
    if (!raw) return '';
    var base = raw.split('#', 1)[0].trim();
    if (!base) return '';
    if (/^https?:\/\/\S+$/i.test(base)) return 'external_uri';
    if (/^[A-Za-z][A-Za-z0-9_.-]*:\S+$/.test(base)) return 'entity_curie';
    return base.split(/[.\[/]/)[0].trim();
  }
  function normalizeRefKey(ref) {
    var raw = text(ref).trim();
    if (!raw) return '';
    var doiUrl = raw.match(/^https?:\/\/(?:dx\.)?doi\.org\/(10\.\d{4,9}\/\S+)$/i);
    if (doiUrl) return 'DOI:' + doiUrl[1].toLowerCase();
    var pubmedUrl = raw.match(/^https?:\/\/pubmed\.ncbi\.nlm\.nih\.gov\/(\d+)\/?$/i);
    if (pubmedUrl) return 'PMID:' + pubmedUrl[1];
    var lower = raw.toLowerCase();
    if (lower.startsWith('doi:')) {
      var doiBody = raw.slice(4).trim().toLowerCase();
      return doiBody ? 'DOI:' + doiBody : '';
    }
    if (/^10\.\d{4,9}\/\S+$/.test(raw)) return 'DOI:' + lower;
    if (lower.startsWith('pmid:')) {
      var pmidBody = raw.slice(5).trim();
      return pmidBody ? 'PMID:' + pmidBody : '';
    }
    return raw;
  }
  function normalize(input) {
    input = input || {};
    var state = {};
    Object.keys(defaults).forEach(function (key) { state[key] = text(input[key] == null ? defaults[key] : input[key]); });
    if (!['gaps', 'all', 'candidates'].includes(state.view)) state.view = defaults.view;
    if (!['relevance', 'record', 'mech', 'posed_newest', 'posed_oldest'].includes(state.sort)) state.sort = defaults.sort;
    state.page = /^\d+$/.test(state.page) ? Math.max(1, Math.min(1000000, Number(state.page))) : 1;
    ['q', 'layer', 'stance', 'experiments', 'ref', 'month', 'vocab'].forEach(function (key) {
      state[key] = state[key].trim();
    });
    if (state.ref) state.ref = normalizeRefKey(state.ref);
    var selected = Array.from(new Set([state.term.trim(), state.term2.trim()].filter(Boolean))).sort();
    state.term = selected[0] || ''; state.term2 = selected[1] || '';
    return state;
  }
  function prepareTerms(doc, prepared) {
    if (!doc || !Array.isArray(doc.terms)) throw new Error('Invalid entity occurrence index.');
    var ids = new Set(prepared.map(function (entry) { return entry.item.id; }));
    var byId = new Map(), byDiscussion = new Map();
    doc.terms.forEach(function (term) {
      if (!term || typeof term.id !== 'string' || !term.id.trim() || byId.has(term.id) ||
          typeof term.label !== 'string' || !term.label.trim() || !Array.isArray(term.postings) || !Array.isArray(term.entity_refs)) {
        throw new Error('Invalid or duplicate entity identity.');
      }
      var seen = new Set();
      term.postings.forEach(function (posting) {
        if (!posting || !ids.has(posting.discussion_id) || seen.has(posting.discussion_id) ||
            !Number.isSafeInteger(posting.count) || posting.count < 1) throw new Error('Invalid entity occurrence or discussion reference.');
        seen.add(posting.discussion_id);
        if (!byDiscussion.has(posting.discussion_id)) byDiscussion.set(posting.discussion_id, new Map());
        byDiscussion.get(posting.discussion_id).set(term.id, posting.count);
      });
      byId.set(term.id, term);
    });
    return {byId: byId, byDiscussion: byDiscussion};
  }
  function inVocabulary(term, vocabulary) {
    return !vocabulary || Boolean(term && list(term.entity_refs).some(function (ref) { return ref.mech === vocabulary; }));
  }
  function round4(value) {
    return Number.isFinite(value) ? Math.round(value * 10000) / 10000 : 0;
  }
  function summarizeTerms(items, data, vocabulary) {
    var counts = new Map(), occurrences = 0, covered = 0, totalDocs = items.length;
    items.forEach(function (item) {
      var mentions = data.byDiscussion.get(item.id);
      if (!mentions || !mentions.size) return;
      var hasTerm = false;
      mentions.forEach(function (count, id) {
        if (!inVocabulary(data.byId.get(id), vocabulary)) return;
        hasTerm = true;
        if (!counts.has(id)) {
          var term = data.byId.get(id);
          counts.set(id, {id: id, label: term.label, canonical_id: term.canonical_id == null ? null : term.canonical_id,
            entity_refs: term.entity_refs, occurrences: 0, discussions: 0});
        }
        var row = counts.get(id); row.occurrences += count; row.discussions++; occurrences += count;
      });
      if (hasTerm) covered++;
    });
    var ranked = Array.from(counts.values()).sort(function (a, b) {
      return b.occurrences - a.occurrences || (fold(a.label) < fold(b.label) ? -1 : fold(a.label) > fold(b.label) ? 1 : a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    });
    var top = ranked.slice(0, 20), rank = new Map(top.map(function (term, i) { return [term.id, i]; })), pairs = new Map();
    items.forEach(function (item) {
      var mentions = data.byDiscussion.get(item.id);
      if (!mentions) return;
      var selected = Array.from(mentions.keys()).filter(function (id) { return rank.has(id); }).sort(function (a, b) { return rank.get(a) - rank.get(b); });
      selected.forEach(function (a, i) { selected.slice(i + 1).forEach(function (b) {
        var key = JSON.stringify([a, b]);
        if (!pairs.has(key)) pairs.set(key, {a: a, b: b, discussions: 0});
        pairs.get(key).discussions++;
      }); });
    });
    var enrichedPairs = Array.from(pairs.values()).map(function (pair) {
      var na = counts.get(pair.a).discussions, nb = counts.get(pair.b).discussions, nab = pair.discussions;
      var denom = na + nb - nab;
      var jaccard = denom > 0 ? round4(nab / denom) : 0;
      var npmi = 0;
      if (totalDocs > 1 && nab > 0 && nab < totalDocs) {
        var raw = (Math.log(nab * totalDocs) - Math.log(na * nb)) / (Math.log(totalDocs) - Math.log(nab));
        npmi = round4(Math.max(-1, Math.min(1, raw)));
      }
      return {a: pair.a, b: pair.b, discussions: nab, jaccard: jaccard, npmi: npmi};
    }).sort(function (a, b) {
      return b.discussions - a.discussions || rank.get(a.a) - rank.get(b.a) || rank.get(a.b) - rank.get(b.b);
    });
    return {scope_discussions: totalDocs, covered_discussions: covered, occurrences: occurrences,
      terms: ranked, pairs: enrichedPairs};
  }
  function summarizeAnalytics(entries, termData) {
    var byMech = {}, totals = {kinds: {}, statuses: {}, stances: {}, layers: {}, unattached: 0, no_evidence: 0, with_experiments: 0};
    var posedByMonth = new Map(), resolvedByMonth = new Map();
    var refDocs = new Map(), refMechs = new Map(), refRaw = new Map();
    function bump(obj, key, delta) { obj[key] = (obj[key] || 0) + (delta == null ? 1 : delta); }
    entries.forEach(function (entry) {
      var item = entry.item, mech = item.mech || 'Unspecified';
      if (!byMech[mech]) {
        byMech[mech] = {total: 0, kinds: {}, statuses: {}, stances: {}, layers: {}, unattached: 0, no_evidence: 0, with_experiments: 0};
      }
      var bucket = byMech[mech];
      bucket.total++;
      var kind = item.kind || 'UNSPECIFIED', status = item.status || 'UNSPECIFIED';
      bump(bucket.kinds, kind); bump(totals.kinds, kind);
      bump(bucket.statuses, status); bump(totals.statuses, status);
      if (!entry.stances.length) { bucket.no_evidence++; totals.no_evidence++; }
      else entry.stances.forEach(function (st) { bump(bucket.stances, st); bump(totals.stances, st); });
      if (!entry.layers.length) { bucket.unattached++; totals.unattached++; }
      else entry.layers.forEach(function (ly) { bump(bucket.layers, ly); bump(totals.layers, ly); });
      if (entry.hasExperiments) { bucket.with_experiments++; totals.with_experiments++; }
      if (entry.posedMonth) posedByMonth.set(entry.posedMonth, (posedByMonth.get(entry.posedMonth) || 0) + 1);
      if (entry.resolvedMonth) resolvedByMonth.set(entry.resolvedMonth, (resolvedByMonth.get(entry.resolvedMonth) || 0) + 1);
      var seenRefs = new Set();
      list(item.evidence_refs).forEach(function (raw) {
        var key = normalizeRefKey(raw);
        if (!key || seenRefs.has(key)) return;
        seenRefs.add(key);
        if (!refRaw.has(key)) refRaw.set(key, text(raw).trim());
        refDocs.set(key, (refDocs.get(key) || 0) + 1);
        if (!refMechs.has(key)) refMechs.set(key, new Set());
        refMechs.get(key).add(mech);
      });
    });
    var months = Array.from(new Set(Array.from(posedByMonth.keys()).concat(Array.from(resolvedByMonth.keys())))).filter(function (m) {
      return MONTH_RE.test(m);
    }).sort();
    var timeline = [];
    if (months.length) {
      var first = months[0], last = months[months.length - 1];
      var startIdx = Number(first.slice(0, 4)) * 12 + (Number(first.slice(5, 7)) - 1);
      var endIdx = Number(last.slice(0, 4)) * 12 + (Number(last.slice(5, 7)) - 1);
      var spanMonths = endIdx - startIdx;
      if (spanMonths >= 0 && spanMonths <= 60) {
        for (var idx = startIdx; idx <= endIdx; idx++) {
          var yr = Math.floor(idx / 12), mo = (idx % 12) + 1;
          var cur = String(yr).padStart(4, '0') + '-' + String(mo).padStart(2, '0');
          timeline.push({month: cur, posed: posedByMonth.get(cur) || 0, resolved: resolvedByMonth.get(cur) || 0});
        }
      } else {
        timeline = months.map(function (m) { return {month: m, posed: posedByMonth.get(m) || 0, resolved: resolvedByMonth.get(m) || 0}; });
      }
    }
    var allRefs = Array.from(refDocs.entries()).map(function (pair) {
      var key = pair[0], count = pair[1], mechs = Array.from(refMechs.get(key)).sort();
      return {ref: key, raw_ref: refRaw.get(key) || key, discussions: count, mech_count: mechs.length, mechs: mechs};
    });
    var topRefs = allRefs.slice().sort(function (a, b) {
      return b.discussions - a.discussions || b.mech_count - a.mech_count || (a.ref < b.ref ? -1 : a.ref > b.ref ? 1 : 0);
    }).slice(0, 25);
    var crossRefs = allRefs.filter(function (r) { return r.mech_count > 1; }).sort(function (a, b) {
      return b.mech_count - a.mech_count || b.discussions - a.discussions || (a.ref < b.ref ? -1 : a.ref > b.ref ? 1 : 0);
    }).slice(0, 25);

    var vocabMatrix = null;
    if (termData) {
      var discMatrix = {}, occMatrix = {}, matchedBySource = {};
      entries.forEach(function (entry) {
        var item = entry.item, src = item.mech || 'Unspecified';
        var mentions = termData.byDiscussion.get(item.id);
        if (!mentions || !mentions.size) return;
        matchedBySource[src] = (matchedBySource[src] || 0) + 1;
        if (!discMatrix[src]) discMatrix[src] = {};
        if (!occMatrix[src]) occMatrix[src] = {};
        var seenVocabs = new Set();
        mentions.forEach(function (count, id) {
          var term = termData.byId.get(id);
          if (!term) return;
          var vocabs = new Set(list(term.entity_refs).map(function (r) { return r && r.mech; }).filter(Boolean));
          vocabs.forEach(function (vm) {
            occMatrix[src][vm] = (occMatrix[src][vm] || 0) + count;
            seenVocabs.add(vm);
          });
        });
        seenVocabs.forEach(function (vm) { discMatrix[src][vm] = (discMatrix[src][vm] || 0) + 1; });
      });
      vocabMatrix = {discussions: discMatrix, occurrences: occMatrix, matched_by_source: matchedBySource};
    }

    return {
      total: entries.length,
      by_mech: byMech,
      totals: totals,
      timeline: timeline,
      top_refs: topRefs,
      cross_mech_refs: crossRefs,
      distinct_refs: allRefs.length,
      vocab_matrix: vocabMatrix
    };
  }
  function prepare(items) {
    return items.map(function (item) {
      var ids = [item.id, item.record_id, item.discussion_id].concat(list(item.evidence_refs)).map(fold);
      var label = fold([item.record_label, item.prompt].concat(list(item.aliases)).join(' '));
      var body = fold([label, item.rationale, ids.join(' '), list(item.attaches_to).join(' ')].join(' '));
      var layers = Array.isArray(item.attach_layers) ? item.attach_layers.slice() :
        Array.from(new Set(list(item.attaches_to).map(normalizeAttachLayer).filter(Boolean))).sort();
      var stances = Array.isArray(item.evidence_stances) ? item.evidence_stances.slice() :
        Array.from(new Set(list(item.evidence).map(function (e) { return e && e.supports ? text(e.supports).trim() : ''; }).filter(Boolean))).sort();
      var hasExperiments = Boolean(item.has_experiments || list(item.proposed_experiments).length);
      var refKeys = new Set(list(item.evidence_refs).map(normalizeRefKey).filter(Boolean));
      var posedMonth = extractMonth(item.posed_date);
      var resolvedMonth = extractMonth(item.resolved_date);
      return {item: item, ids: ids, label: label, body: body, layers: layers, stances: stances,
        hasExperiments: hasExperiments, refKeys: refKeys, posedMonth: posedMonth, resolvedMonth: resolvedMonth};
    });
  }
  function isKnowledgeGap(item) {
    return item.lane !== 'candidate' && ['KNOWLEDGE_GAP', 'HUMAN_MODEL_MISMATCH'].includes(item.kind);
  }
  function gapCounts(items) {
    var total = 0, byMech = new Map();
    items.forEach(function (item) {
      if (!byMech.has(item.mech)) byMech.set(item.mech, 0);
      if (isKnowledgeGap(item)) {
        total++; byMech.set(item.mech, byMech.get(item.mech) + 1);
      }
    });
    return {total: total, by_mech: Object.fromEntries(Array.from(byMech.entries()).sort(function (a, b) {
      return a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0;
    }))};
  }
  function matchesMonth(entry, filter) {
    if (!filter) return true;
    if (filter.startsWith('posed:')) {
      var pm = filter.slice(6);
      return MONTH_RE.test(pm) && entry.posedMonth === pm;
    }
    if (filter.startsWith('resolved:')) {
      var rm = filter.slice(9);
      return MONTH_RE.test(rm) && entry.resolvedMonth === rm;
    }
    return MONTH_RE.test(filter) && (entry.posedMonth === filter || entry.resolvedMonth === filter);
  }
  function search(prepared, input, termData) {
    var state = normalize(input), q = fold(state.q), terms = q.split(/\s+/).filter(Boolean);
    if ((state.term || state.term2) && !termData) throw new Error('Entity occurrences must load before applying the selected term filter. Retry the term explorer or clear its selection.');
    var matches = [], scope = [];
    var targetRef = state.ref ? normalizeRefKey(state.ref) : '';
    prepared.forEach(function (entry) {
      var item = entry.item;
      if (state.view === 'gaps' && !isKnowledgeGap(item)) return;
      if (state.view === 'candidates' && item.lane !== 'candidate') return;
      if (state.mech && item.mech !== state.mech) return;
      if (state.kind && item.kind !== state.kind) return;
      if (state.review && item.review_state !== state.review) return;
      if (state.status === 'active' && !['OPEN', 'UNDER_DISCUSSION'].includes(item.status)) return;
      if (state.status && state.status !== 'active' && item.status !== state.status) return;
      if (state.layer) {
        if (state.layer === 'unattached') { if (entry.layers.length) return; }
        else if (!entry.layers.includes(state.layer)) return;
      }
      if (state.stance) {
        if (state.stance === 'none') { if (entry.stances.length) return; }
        else if (!entry.stances.includes(state.stance)) return;
      }
      if (state.experiments) {
        if (state.experiments === 'yes') { if (!entry.hasExperiments) return; }
        else if (state.experiments === 'no') { if (entry.hasExperiments) return; }
        else return;
      }
      if (targetRef && !entry.refKeys.has(targetRef)) return;
      if (state.month && !matchesMonth(entry, state.month)) return;
      if (!terms.every(function (term) { return entry.body.includes(term); })) return;
      scope.push(item);
      var mentions = termData && termData.byDiscussion.get(item.id);
      if (state.term && (!mentions || !mentions.has(state.term) || !inVocabulary(termData.byId.get(state.term), state.vocab))) return;
      if (state.term2 && (!mentions || !mentions.has(state.term2) || !inVocabulary(termData.byId.get(state.term2), state.vocab))) return;
      var score = q && entry.ids.includes(q) ? 1000 : q && entry.label.includes(q) ? 100 : 0;
      terms.forEach(function (term) { if (entry.label.includes(term)) score += 10; });
      matches.push({item: item, entry: entry, score: score});
    });
    function compare(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
    matches.sort(function (a, b) {
      if (state.sort === 'relevance' && a.score !== b.score) return b.score - a.score;
      if (state.sort === 'mech') { var m = compare(a.item.mech, b.item.mech); if (m) return m; }
      if (state.sort === 'posed_newest' || state.sort === 'posed_oldest') {
        var da = text(a.item.posed_date), db = text(b.item.posed_date);
        if (Boolean(da) !== Boolean(db)) return da ? -1 : 1;
        if (da && db && da !== db) return state.sort === 'posed_newest' ? compare(db, da) : compare(da, db);
      }
      return compare(fold(a.item.record_label), fold(b.item.record_label)) || compare(a.item.id, b.item.id);
    });
    var total = matches.length, pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    var page = Math.min(state.page, pages), start = (page - 1) * PAGE_SIZE;
    return {total: total, pages: pages, page: page,
      records: new Set(matches.map(function (r) { return r.item.mech + '\u0000' + (r.item.source_url || r.item.id); })).size,
      rows: matches.slice(start, start + PAGE_SIZE).map(function (r) { return r.item; }),
      all: matches.map(function (r) { return r.item; }),
      selected_terms: [state.term, state.term2].filter(Boolean).map(function (id) {
        var term = termData && termData.byId.get(id);
        return term ? {id: id, label: term.label, canonical_id: term.canonical_id == null ? null : term.canonical_id,
          entity_refs: term.entity_refs, in_vocabulary: inVocabulary(term, state.vocab)} : {id: id, label: id, entity_refs: [], unavailable: true};
      }),
      term_summary: termData ? summarizeTerms(scope, termData, state.vocab) : null,
      analysis: summarizeAnalytics(matches.map(function (r) { return r.entry; }), termData)};
  }
  function csvCell(value) {
    var s = typeof value === 'object' && value !== null ? JSON.stringify(value) : text(value);
    // Quote every cell and neutralize formulas even after leading whitespace.
    if (/^[\s\uFEFF]*[=+@-]/.test(s) || /^[\t\r\n]/.test(s)) s = "'" + s;
    return '"' + s.replace(/"/g, '""') + '"';
  }
  function csv(items) {
    var fields = ['id', 'mech', 'record_id', 'record_label', 'aliases', 'discussion_id', 'prompt', 'rationale', 'kind', 'status',
      'storage_mode', 'origin', 'origin_basis', 'current_attribution', 'review_state', 'lane', 'classification_reason', 'attaches_to', 'evidence', 'evidence_refs', 'proposed_experiments',
      'posed_date', 'resolved_date', 'resolution_note', 'source'];
    return [fields.map(csvCell).join(',')].concat(items.map(function (item) {
      return fields.map(function (f) { return csvCell(item[f]); }).join(',');
    })).join('\r\n') + '\r\n';
  }
  function safeURL(value) {
    try {
      var u = new URL(value);
      if (u.protocol !== 'https:' || u.username || u.password || (u.port && u.port !== '443')) return null;
      if (!['github.com', 'culturebotai.github.io', 'doi.org', 'pubmed.ncbi.nlm.nih.gov',
        'pmc.ncbi.nlm.nih.gov', 'europepmc.org'].includes(u.hostname)) return null;
      return u.href;
    } catch (_) { return null; }
  }
  function referenceURL(ref) {
    ref = text(ref);
    if (/^PMID:\d+$/i.test(ref)) return 'https://pubmed.ncbi.nlm.nih.gov/' + ref.split(':')[1] + '/';
    if (/^(?:DOI:)?10\.\d{4,9}\/\S+$/i.test(ref)) return 'https://doi.org/' + encodeURI(ref.replace(/^DOI:/i, '')).replace(/#/g, '%23').replace(/\?/g, '%3F');
    return safeURL(ref);
  }
  return {PAGE_SIZE: PAGE_SIZE, defaults: defaults, normalize: normalize, prepare: prepare, search: search,
    prepareTerms: prepareTerms, summarizeTerms: summarizeTerms, summarizeAnalytics: summarizeAnalytics,
    normalizeAttachLayer: normalizeAttachLayer, normalizeRefKey: normalizeRefKey,
    gapCounts: gapCounts, csv: csv, csvCell: csvCell, safeURL: safeURL, referenceURL: referenceURL};
}));
