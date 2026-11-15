/* Deterministic gap search shared by the browser worker and offline tests. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GapSearch = api;
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var PAGE_SIZE = 50;
  var defaults = {q: '', view: 'gaps', mech: '', kind: '', status: 'active', review: '', sort: 'relevance', page: 1, gap: '', term: '', term2: '', vocab: ''};
  function text(value) { return value == null ? '' : String(value); }
  function fold(value) { return text(value).normalize('NFKC').toLocaleLowerCase('en'); }
  function list(value) { return Array.isArray(value) ? value : []; }
  function normalize(input) {
    input = input || {};
    var state = {};
    Object.keys(defaults).forEach(function (key) { state[key] = text(input[key] == null ? defaults[key] : input[key]); });
    if (!['gaps', 'all', 'candidates'].includes(state.view)) state.view = defaults.view;
    if (!['relevance', 'record', 'mech'].includes(state.sort)) state.sort = defaults.sort;
    state.page = /^\d+$/.test(state.page) ? Math.max(1, Math.min(1000000, Number(state.page))) : 1;
    state.q = state.q.trim();
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
  function summarizeTerms(items, data, vocabulary) {
    var counts = new Map(), occurrences = 0, covered = 0;
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
    return {scope_discussions: items.length, covered_discussions: covered, occurrences: occurrences,
      terms: ranked, pairs: Array.from(pairs.values()).sort(function (a, b) {
        return b.discussions - a.discussions || rank.get(a.a) - rank.get(b.a) || rank.get(a.b) - rank.get(b.b);
      })};
  }
  function prepare(items) {
    return items.map(function (item) {
      var ids = [item.id, item.record_id, item.discussion_id].concat(list(item.evidence_refs)).map(fold);
      var label = fold([item.record_label, item.prompt].concat(list(item.aliases)).join(' '));
      var body = fold([label, item.rationale, ids.join(' '), list(item.attaches_to).join(' ')].join(' '));
      return {item: item, ids: ids, label: label, body: body};
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
  function search(prepared, input, termData) {
    var state = normalize(input), q = fold(state.q), terms = q.split(/\s+/).filter(Boolean);
    if ((state.term || state.term2) && !termData) throw new Error('Entity occurrences must load before applying the selected term filter. Retry the term explorer or clear its selection.');
    var matches = [], scope = [];
    prepared.forEach(function (entry) {
      var item = entry.item;
      if (state.view === 'gaps' && !isKnowledgeGap(item)) return;
      if (state.view === 'candidates' && item.lane !== 'candidate') return;
      if (state.mech && item.mech !== state.mech) return;
      if (state.kind && item.kind !== state.kind) return;
      if (state.review && item.review_state !== state.review) return;
      if (state.status === 'active' && !['OPEN', 'UNDER_DISCUSSION'].includes(item.status)) return;
      if (state.status && state.status !== 'active' && item.status !== state.status) return;
      if (!terms.every(function (term) { return entry.body.includes(term); })) return;
      scope.push(item);
      var mentions = termData && termData.byDiscussion.get(item.id);
      if (state.term && (!mentions || !mentions.has(state.term) || !inVocabulary(termData.byId.get(state.term), state.vocab))) return;
      if (state.term2 && (!mentions || !mentions.has(state.term2) || !inVocabulary(termData.byId.get(state.term2), state.vocab))) return;
      var score = q && entry.ids.includes(q) ? 1000 : q && entry.label.includes(q) ? 100 : 0;
      terms.forEach(function (term) { if (entry.label.includes(term)) score += 10; });
      matches.push({item: item, score: score});
    });
    function compare(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
    matches.sort(function (a, b) {
      if (state.sort === 'relevance' && a.score !== b.score) return b.score - a.score;
      if (state.sort === 'mech') { var m = compare(a.item.mech, b.item.mech); if (m) return m; }
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
      term_summary: termData ? summarizeTerms(scope, termData, state.vocab) : null};
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
    prepareTerms: prepareTerms, summarizeTerms: summarizeTerms, gapCounts: gapCounts,
    csv: csv, csvCell: csvCell, safeURL: safeURL, referenceURL: referenceURL};
}));
