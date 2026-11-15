/* Accessible, static cross-Mech discussion browser. No visitor-time GitHub API. */
(function () {
  'use strict';
  var app = document.getElementById('gap-browser');
  if (!app) return;
  var core = window.GapSearch;
  var $ = function (id) { return document.getElementById('gap-' + id); };
  var manifestURL = new URL(app.dataset.manifest, location.href);
  var worker, manifest, state, ready = false, requestID = 0, loadVersion = 0, queryVersion = 0, detailVersion = 0;
  var pending = new Map(), shards = new Map(), lastTotal = 0, exporting = false, lastDetailButton = null;
  function node(tag, content, className) {
    var el = document.createElement(tag);
    if (content != null) el.textContent = String(content);
    if (className) el.className = className;
    return el;
  }
  function human(value) { return value == null || value === '' ? 'Unspecified' : String(value).replace(/_/g, ' ').toLowerCase(); }
  function number(value) { return value == null ? 'unknown' : Number(value).toLocaleString('en'); }
  function link(label, value) {
    var href = core.safeURL(value);
    if (!href) return node('span', label);
    var a = node('a', label); a.href = href; a.rel = 'noopener noreferrer'; return a;
  }
  function field(dl, label, value) {
    dl.append(node('dt', label), node('dd', value == null || value === '' ? 'Unspecified' : value));
  }
  function values(value) {
    if (value == null) return '';
    if (Array.isArray(value)) return value.map(values).join('; ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }
  function readState() {
    var params = new URL(location.href).searchParams, input = {};
    Object.keys(core.defaults).forEach(function (key) { if (params.has(key)) input[key] = params.get(key); });
    return core.normalize(input);
  }
  function stateURL(current) {
    var url = new URL(location.href);
    Object.keys(core.defaults).forEach(function (key) {
      if (String(current[key]) === String(core.defaults[key])) url.searchParams.delete(key);
      else url.searchParams.set(key, current[key]);
    });
    url.hash = '';
    return url;
  }
  function historyState(replace) { history[replace ? 'replaceState' : 'pushState'](null, '', stateURL(state)); }
  function syncControls() {
    $('query').value = state.q;
    ['view', 'mech', 'kind', 'status', 'review', 'sort'].forEach(function (key) {
      var select = $(key);
      // An obsolete filter is never silently replaced with a broader search.
      Array.from(select.options).filter(function (o) { return o.dataset.unavailable; }).forEach(function (o) { o.remove(); });
      if (!Array.from(select.options).some(function (o) { return o.value === state[key]; })) {
        var option = node('option', state[key] + ' (not in this snapshot)');
        option.value = state[key]; option.dataset.unavailable = 'true'; select.append(option);
      }
      select.value = state[key];
    });
  }
  function exportButtons() {
    ['export-json', 'export-csv'].forEach(function (id) { $(id).disabled = !ready || exporting || lastTotal === 0; });
  }
  function request(type, data) {
    return new Promise(function (resolve, reject) {
      var id = ++requestID;
      var timer = setTimeout(function () { pending.delete(id); reject(new Error('Search took too long. Retry loading the snapshot.')); }, 60000);
      pending.set(id, {resolve: resolve, reject: reject, timer: timer});
      worker.postMessage(Object.assign({type: type, request: id}, data));
    });
  }
  function stopWorker() {
    if (worker) worker.terminate();
    pending.forEach(function (p) { clearTimeout(p.timer); p.reject(new Error('Search was restarted.')); });
    pending.clear();
  }
  function fail(message) {
    ready = false; lastTotal = 0; $('controls').disabled = true;
    $('results').replaceChildren(); $('pagination').hidden = true;
    $('load-status').textContent = 'Search could not load: ' + message + ' The static source summary remains available below.';
    $('load-status').className = 'gap-error'; $('load-status').hidden = false; $('retry').hidden = false;
    exportButtons();
  }
  async function verifiedJSON(descriptor) {
    if (!descriptor || typeof descriptor.url !== 'string' || !/^[a-f0-9]{64}$/.test(descriptor.sha256)) throw new Error('Invalid snapshot asset descriptor.');
    var url = new URL(descriptor.url, manifestURL);
    if (url.origin !== location.origin) throw new Error('Snapshot assets must be on this site.');
    var response = await fetch(url.href, {cache: 'no-cache'});
    if (!response.ok) throw new Error('Could not load ' + url.pathname + ' (' + response.status + ').');
    var bytes = await response.arrayBuffer();
    var hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
    if (hash !== descriptor.sha256) throw new Error('This asset does not match the selected snapshot. Reload or retry.');
    var data = JSON.parse(new TextDecoder().decode(bytes));
    if (data.schema_version !== 1 || data.build_id !== manifest.build_id) throw new Error('Snapshot versions do not match.');
    return data;
  }
  function shardKey(item) { return item.detail_shard || item.mech; }
  function detailShard(key) {
    if (!shards.has(key)) {
      var promise = verifiedJSON(manifest.details[key]).then(function (data) {
        if (!data.items || Array.isArray(data.items) || typeof data.items !== 'object') throw new Error('Invalid discussion details.');
        return data.items;
      }).catch(function (error) { shards.delete(key); throw error; });
      shards.set(key, promise);
    }
    return shards.get(key);
  }
  function getDetail(items, id) {
    if (!Object.prototype.hasOwnProperty.call(items, id) || items[id].id !== id) throw new Error('This discussion is missing from its detail snapshot.');
    return items[id];
  }
  function badges(item) {
    var row = node('div', null, 'gap-badges');
    [item.mech, human(item.kind), human(item.status), 'Review: ' + human(item.review_state)].forEach(function (s) { row.append(node('span', s, 'gap-badge')); });
    if (item.lane === 'candidate') row.append(node('span', 'Candidate awaiting review', 'gap-badge gap-badge-candidate'));
    return row;
  }
  function renderRows(result) {
    var fragment = document.createDocumentFragment();
    result.rows.forEach(function (item) {
      var li = node('li', null, 'gap-result'); li.append(badges(item));
      var h = node('h2'), button = node('button', item.prompt || 'Untitled discussion', 'gap-open');
      button.type = 'button'; button.dataset.gapId = item.id;
      button.addEventListener('click', function () { lastDetailButton = button; openDetail(item.id, true, true); });
      h.append(button); li.append(h);
      li.append(node('p', (item.record_label || item.record_id) + ' · ' + item.record_id, 'gap-record'));
      if (item.rationale) li.append(node('p', item.rationale.length > 300 ? item.rationale.slice(0, 300) + '…' : item.rationale));
      var meta = node('p', null, 'gap-note');
      meta.append(link('Pinned source', item.source_url), document.createTextNode(' · ' + number((item.evidence_refs || []).length) + ' cited references'));
      li.append(meta); fragment.append(li);
    });
    $('results').replaceChildren(fragment);
    $('result-status').textContent = result.total ? number(result.total) + ' matching discussions in ' + number(result.records) + ' records. Showing ' + ((result.page - 1) * core.PAGE_SIZE + 1) + '–' + Math.min(result.page * core.PAGE_SIZE, result.total) + '.' : 'No discussions match these filters. Change the view or clear filters to broaden the search.';
    $('pagination').hidden = result.pages <= 1;
    $('page-label').textContent = 'Page ' + result.page + ' of ' + result.pages;
    $('prev').disabled = result.page <= 1; $('next').disabled = result.page >= result.pages;
  }
  async function query(focus) {
    if (!ready) return;
    var version = ++queryVersion; lastTotal = 0; exportButtons();
    $('results').replaceChildren(); $('pagination').hidden = true; $('result-status').textContent = 'Searching all indexed discussions…';
    $('view-note').textContent = state.view === 'gaps' ? 'Knowledge gaps shows KNOWLEDGE_GAP and HUMAN_MODEL_MISMATCH entries, excluding identified proposals awaiting review. Lifecycle and other filters also apply.' : state.view === 'candidates' ? 'Candidates are identified proposals requiring review, including those stored in native records. Their citations do not establish the proposed claim.' : 'All discussion kinds and both recorded and candidate entries are available. Lifecycle and other filters still apply.';
    try {
      var reply = await request('query', {state: state});
      if (version !== queryVersion) return;
      var result = reply.result; state.page = result.page; historyState(true);
      lastTotal = result.total; renderRows(result); exportButtons();
      if (focus) $('result-status').focus();
    } catch (error) { if (version === queryVersion) fail(error.message); }
  }
  function closeDetail(restore, update) {
    detailVersion++; $('detail').hidden = true; $('detail-body').replaceChildren();
    state.gap = ''; if (update) historyState(false);
    if (restore) { if (lastDetailButton && lastDetailButton.isConnected) lastDetailButton.focus(); else $('result-status').focus(); }
  }
  function renderDetail(item) {
    $('detail-title').textContent = item.prompt || 'Discussion';
    var body = $('detail-body'); body.replaceChildren(badges(item));
    body.append(node('p', (item.record_label || item.record_id) + ' · ' + item.record_id));
    if (item.rationale) { body.append(node('h3', 'Why this matters'), node('p', item.rationale)); }
    var dl = node('dl');
    field(dl, 'Storage mode', human(item.storage_mode));
    field(dl, 'Origin', human(item.origin)); field(dl, 'Review state', human(item.review_state));
    if (item.origin_basis) field(dl, 'Origin basis', values(item.origin_basis));
    if (item.current_attribution) field(dl, 'Current attribution', values(item.current_attribution));
    field(dl, 'Classification', values(item.classification_reason)); field(dl, 'Discussion ID', item.discussion_id);
    field(dl, 'Posed', item.posed_date); field(dl, 'Resolved', item.resolved_date);
    if (item.attaches_to && item.attaches_to.length) field(dl, 'Attached to', item.attaches_to.join('; '));
    body.append(dl);
    if (item.resolution_note) body.append(node('h3', 'Resolution'), node('p', item.resolution_note));
    body.append(node('h3', 'Evidence and context'));
    if (!(item.evidence || []).length) body.append(node('p', 'No evidence references recorded for this discussion. This is not evidence that relevant literature does not exist.'));
    else {
      var evidence = node('ul');
      item.evidence.forEach(function (entry) {
        var li = node('li'); li.append(link(entry.reference || 'Unspecified reference', core.referenceURL(entry.reference)));
        li.append(document.createTextNode(' — ' + human(entry.supports)));
        if (entry.explanation) li.append(node('p', entry.explanation));
        evidence.append(li);
      }); body.append(evidence);
    }
    body.append(node('h3', 'Proposed experiments'));
    if (!(item.proposed_experiments || []).length) body.append(node('p', 'No proposed experiments recorded.'));
    else {
      var experiments = node('ol');
      item.proposed_experiments.forEach(function (experiment) {
        var li = node('li');
        if (typeof experiment === 'string') li.append(node('p', experiment));
        else {
          li.append(node('h4', experiment.name || experiment.experiment_id || 'Proposed experiment'));
          var details = node('dl'); Object.keys(experiment).filter(function (key) { return key !== 'name'; }).forEach(function (key) { field(details, human(key), values(experiment[key])); }); li.append(details);
        }
        experiments.append(li);
      }); body.append(experiments);
    }
    var source = item.source || {};
    body.append(node('h3', 'Source and provenance'));
    var sourceLinks = node('p'); sourceLinks.append(link('Pinned source record', source.url || item.source_url));
    if (source.record_url) sourceLinks.append(document.createTextNode(' · '), link('Current record page', source.record_url));
    var permalink = node('a', 'Link to this discussion'); permalink.href = stateURL(Object.assign({}, state, {gap: item.id}));
    sourceLinks.append(document.createTextNode(' · '), permalink); body.append(sourceLinks);
    var provenance = node('dl'); field(provenance, 'Repository', source.repository); field(provenance, 'Revision', source.revision);
    field(provenance, 'Source file', source.path); field(provenance, 'Source SHA-256', source.sha256); field(provenance, 'Licence', values(source.license));
    body.append(provenance);
  }
  async function openDetail(id, update, focus) {
    var version = ++detailVersion;
    state.gap = id; if (update) historyState(false);
    $('detail').hidden = false; $('detail-title').textContent = 'Loading discussion…'; $('detail-body').replaceChildren();
    if (focus) $('detail-title').focus();
    try {
      var reply = await request('item', {id: id});
      if (version !== detailVersion) return;
      if (!reply.item) throw new Error('This discussion ID is not present in the selected snapshot.');
      var items = await detailShard(shardKey(reply.item));
      if (version !== detailVersion) return;
      renderDetail(getDetail(items, id));
      if (focus) $('detail-title').focus();
    } catch (error) {
      if (version !== detailVersion) return;
      $('detail-title').textContent = 'Discussion could not load';
      var retry = node('button', 'Retry this discussion'); retry.type = 'button';
      retry.addEventListener('click', function () { openDetail(id, false, true); });
      $('detail-body').replaceChildren(node('p', error.message, 'gap-error'), retry);
    }
  }
  function coverage() {
    var frag = document.createDocumentFragment();
    manifest.sources.forEach(function (source) {
      var article = node('article'); article.append(node('h3', source.name + ' — ' + human(source.coverage_status)));
      if (source.revision) article.append(link('Source snapshot ' + source.revision.slice(0, 12), 'https://github.com/' + source.repository + '/tree/' + source.revision));
      var sourceMeta = node('p', null, 'gap-note');
      sourceMeta.append(document.createTextNode('Snapshot acquired: ' + (source.acquired_at || 'unspecified') + '. '));
      if (source.data_license) sourceMeta.append(link(source.data_license, source.license_url));
      article.append(sourceMeta);
      (source.roots || []).forEach(function (root) {
        var dl = node('dl'); field(dl, 'Source root', root.name); field(dl, 'Support / coverage', human(root.support) + ' / ' + human(root.status));
        field(dl, 'Records inspected', number(root.inspected_records) + ' of ' + number(root.eligible_records) + ' eligible');
        field(dl, 'Discussions', number(root.discussion_count)); if (root.reason) field(dl, 'Scope', root.reason);
        article.append(dl);
      }); frag.append(article);
    }); $('coverage').replaceChildren(frag);
  }
  async function exportMatches(format) {
    if (!ready || exporting) return;
    exporting = true; exportButtons(); var snapshot = manifest, captured = Object.assign({}, state);
    $('export-status').textContent = 'Preparing all filtered results with full details…';
    try {
      var reply = await request('export', {state: captured});
      var keys = Array.from(new Set(reply.result.all.map(shardKey)));
      var details = new Map(await Promise.all(keys.map(async function (key) { return [key, await detailShard(key)]; })));
      if (snapshot !== manifest) throw new Error('The snapshot changed during export. Please retry.');
      var items = reply.result.all.map(function (row) { return getDetail(details.get(shardKey(row)), row.id); });
      var content = format === 'csv' ? core.csv(items) : JSON.stringify({schema_version: 1, build_id: snapshot.build_id, filters: captured, sources: snapshot.sources, items: items}, null, 2);
      var blob = new Blob([content], {type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json'});
      var url = URL.createObjectURL(blob), a = node('a'); a.href = url; a.download = 'mech-discussions.' + format; document.body.append(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      $('export-status').textContent = 'Exported all ' + number(items.length) + ' matching discussions. Filters and pagination did not truncate the export.';
    } catch (error) { $('export-status').textContent = 'Export failed; no partial file was downloaded. ' + error.message; }
    finally { exporting = false; exportButtons(); }
  }
  async function load() {
    var version = ++loadVersion; ready = false; queryVersion++; detailVersion++; stopWorker(); shards.clear();
    $('app').hidden = true; $('retry').hidden = true; $('load-status').hidden = false;
    $('load-status').className = ''; $('load-status').textContent = 'Loading the search index…';
    $('detail').hidden = true; $('detail-body').replaceChildren();
    try {
      if (!core || !window.Worker || !window.crypto || !crypto.subtle) throw new Error('This browser does not support the search features.');
      var response = await fetch(manifestURL.href, {cache: 'no-cache'});
      if (!response.ok) throw new Error('Snapshot manifest request failed (' + response.status + ').');
      var nextManifest = await response.json();
      if (version !== loadVersion) return;
      if (nextManifest.schema_version !== 1 || !nextManifest.build_id || !Array.isArray(nextManifest.sources) || !nextManifest.details || !nextManifest.index) throw new Error('Invalid snapshot manifest.');
      manifest = nextManifest;
      worker = new Worker(new URL(app.dataset.worker, location.href));
      worker.onmessage = function (event) {
        var p = pending.get(event.data.request); if (!p) return;
        pending.delete(event.data.request); clearTimeout(p.timer);
        if (event.data.type === 'error') p.reject(new Error(event.data.message)); else p.resolve(event.data);
      };
      worker.onerror = function () { if (version === loadVersion) { stopWorker(); fail('The search worker stopped.'); } };
      var reply = await request('init', {url: new URL(manifest.index.url, manifestURL).href, sha256: manifest.index.sha256, build_id: manifest.build_id});
      if (version !== loadVersion) return;
      if (reply.total !== manifest.counts.items) throw new Error('The index count does not match the snapshot manifest.');
      var names = manifest.sources.map(function (source) { return source.name; }).sort();
      [['mech', names, 1], ['kind', reply.facets.kind, 1], ['status', reply.facets.status, 2], ['review', reply.facets.review_state, 1]].forEach(function (entry) {
        var select = $(entry[0]); while (select.options.length > entry[2]) select.remove(entry[2]);
        entry[1].forEach(function (value) {
          var key = entry[0] === 'review' ? 'review_state' : entry[0];
          var label = entry[0] === 'mech' ? value : human(value) + ' (' + number(reply.facet_counts[key][value]) + ')';
          var option = node('option', label); option.value = value; select.append(option);
        });
      });
      state = readState(); syncControls(); coverage();
      $('snapshot').textContent = number(reply.total) + ' indexed discussions · ' + number(reply.candidates) + ' candidates awaiting review · ' + number(manifest.sources.length) + ' Mechs accounted for. Snapshot ' + manifest.build_id.slice(0, 12) + '. Inspect coverage for source dates and limitations.';
      ready = true; $('controls').disabled = false; $('app').hidden = false; $('load-status').hidden = true;
      query(false); if (state.gap) openDetail(state.gap, false, false);
    } catch (error) { if (version === loadVersion) fail(error.message); }
  }
  function changeFilters() {
    if (!ready) return;
    var next = Object.assign({}, state, {q: $('query').value, page: 1, gap: ''});
    ['view', 'mech', 'kind', 'status', 'review', 'sort'].forEach(function (key) { next[key] = $(key).value; });
    next = core.normalize(next);
    // Enter in a search input can dispatch both submit and search (#580).
    // Apply that state once; the native clear control still updates the query.
    if (Object.keys(core.defaults).every(function (key) { return next[key] === state[key]; })) return;
    closeDetail(false, false);
    state = next; historyState(false); query(false);
  }
  $('form').addEventListener('submit', function (event) { event.preventDefault(); changeFilters(); });
  ['view', 'mech', 'kind', 'status', 'review', 'sort'].forEach(function (key) {
    $(key).addEventListener('change', function () {
      if (key === 'view') { $('kind').value = ''; $('status').value = $('view').value === 'gaps' ? 'active' : ''; }
      changeFilters();
    });
  });
  $('query').addEventListener('search', changeFilters);
  $('reset').addEventListener('click', function () { closeDetail(false, false); state = core.normalize({}); syncControls(); historyState(false); query(false); $('query').focus(); });
  $('prev').addEventListener('click', function () { state.page--; historyState(false); query(true); });
  $('next').addEventListener('click', function () { state.page++; historyState(false); query(true); });
  $('close-detail').addEventListener('click', function () { closeDetail(true, true); });
  $('retry').addEventListener('click', load);
  $('export-json').addEventListener('click', function () { exportMatches('json'); });
  $('export-csv').addEventListener('click', function () { exportMatches('csv'); });
  window.addEventListener('popstate', function () {
    if (!ready) return;
    state = readState(); syncControls(); query(false);
    if (state.gap) openDetail(state.gap, false, false); else closeDetail(false, false);
  });
  load();
}());
