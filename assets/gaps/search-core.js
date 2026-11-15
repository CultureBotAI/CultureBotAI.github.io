/* Deterministic gap search shared by the browser worker and offline tests. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GapSearch = api;
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var PAGE_SIZE = 50;
  var defaults = {q: '', view: 'gaps', mech: '', kind: '', status: 'active', review: '', sort: 'relevance', page: 1, gap: ''};
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
    return state;
  }
  function prepare(items) {
    return items.map(function (item) {
      var ids = [item.id, item.record_id, item.discussion_id].concat(list(item.evidence_refs)).map(fold);
      var label = fold([item.record_label, item.prompt].concat(list(item.aliases)).join(' '));
      var body = fold([label, item.rationale, ids.join(' '), list(item.attaches_to).join(' ')].join(' '));
      return {item: item, ids: ids, label: label, body: body};
    });
  }
  function search(prepared, input) {
    var state = normalize(input), q = fold(state.q), terms = q.split(/\s+/).filter(Boolean);
    var matches = [];
    prepared.forEach(function (entry) {
      var item = entry.item;
      if (state.view === 'gaps' && (item.lane === 'candidate' || !['KNOWLEDGE_GAP', 'HUMAN_MODEL_MISMATCH'].includes(item.kind))) return;
      if (state.view === 'candidates' && item.lane !== 'candidate') return;
      if (state.mech && item.mech !== state.mech) return;
      if (state.kind && item.kind !== state.kind) return;
      if (state.review && item.review_state !== state.review) return;
      if (state.status === 'active' && !['OPEN', 'UNDER_DISCUSSION'].includes(item.status)) return;
      if (state.status && state.status !== 'active' && item.status !== state.status) return;
      if (!terms.every(function (term) { return entry.body.includes(term); })) return;
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
      all: matches.map(function (r) { return r.item; })};
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
    csv: csv, csvCell: csvCell, safeURL: safeURL, referenceURL: referenceURL};
}));
