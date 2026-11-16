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
  var termsReady = false, termsLoading = false, termsVersion = 0, termInfo = new Map(), termRecognition = null;
  var analyticsReady = false, analyticsLoading = false, analyticsVersion = 0, analyticsDoc = null;
  var lastAnalysis = null, lastTermSummary = null, lastSelectedTerms = [];
  var CHART_PALETTE = ['#a51b78', '#2b6cb0', '#228833', '#d97706', '#6b46c1', '#0d9488', '#be123c', '#64748b'];
  var SHORT_MECH = {
    HabitatMech: 'Habitat', CommunityMech: 'Community', TraitMech: 'Trait', PathwayMech: 'Pathway',
    CellStructureMech: 'CellStruct', ProteinTraitsMech: 'ProtTraits', DUFMech: 'DUF',
    NaturalProductMech: 'NatProd', AntibioticMech: 'Antibiotic', CMMMech: 'CMM',
    MediaIngredientMech: 'MediaIngr', CultureMech: 'Culture', TaxonMech: 'Taxon',
    AIMech: 'AI', CofactorMech: 'Cofactor', AssayMech: 'Assay'
  };
  var embedding = window.GapEmbedding && window.GapEmbedding.create({root: $('embedding'),
    loadDocument: function () { return verifiedJSON(manifest.embedding); }, safeURL: core.safeURL, csvCell: core.csvCell, referenceURL: core.referenceURL,
    openDiscussion: function (id, origin) { lastDetailButton = origin; openDetail(id, true, true); },
    onLayout: function () {
      var context = $('detail-body').querySelector('.gap-map-detail-context');
      if (context) embedding.appendContext(context.dataset.gapId, context);
      navigatePendingSection();
    }});
  var sectionIDs = ['gap-form', 'gap-analyses-title', 'gap-terms-title', 'gap-pairs-title', 'gap-map-title', 'gap-results-title', 'gap-static-title', 'bibliography'];
  var pendingSection = location.hash, pendingSectionTarget = null;
  function node(tag, content, className) {
    var el = document.createElement(tag);
    if (content != null) el.textContent = String(content);
    if (className) el.className = className;
    return el;
  }
  function svgNode(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
  function human(value) { return value == null || value === '' ? 'Unspecified' : String(value).replace(/_/g, ' ').toLowerCase(); }
  function number(value) { return value == null ? 'unknown' : Number(value).toLocaleString('en'); }
  function shortMech(name) { return SHORT_MECH[name] || String(name || '').replace(/Mech$/, ''); }
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
    return url;
  }
  function historyState(replace) { history[replace ? 'replaceState' : 'pushState'](null, '', stateURL(state)); }
  function applyStatePatch(patch, hashTarget) {
    if (!ready) return;
    var next = core.normalize(Object.assign({}, state, {page: 1, gap: ''}, patch));
    if (Object.keys(core.defaults).every(function (key) { return next[key] === state[key]; })) {
      if (hashTarget) jumpToSection(hashTarget);
      return;
    }
    closeDetail(false, false);
    state = next;
    syncControls();
    if (hashTarget) {
      var url = stateURL(state); url.hash = hashTarget;
      history.pushState(null, '', url);
      pendingSection = url.hash; pendingSectionTarget = null;
    } else {
      historyState(false);
    }
    query(false);
  }
  function sectionOffset() {
    var header = document.querySelector('.site-header');
    document.documentElement.style.setProperty('--gap-section-offset', ((header ? header.getBoundingClientRect().height : 0) + 24) + 'px');
  }
  function navigatePendingSection() {
    var id = pendingSection.slice(1);
    if (!sectionIDs.includes(id)) { pendingSection = ''; return; }
    var target = document.getElementById(id);
    if (!target || target.closest('[hidden]')) return;
    // Do not restore an async anchor after the reader has moved focus elsewhere.
    if (pendingSectionTarget && document.activeElement !== pendingSectionTarget) { pendingSection = ''; pendingSectionTarget = null; return; }
    if (id === 'gap-static-title') target.parentElement.open = true;
    if (id === 'gap-map-title' && embedding) embedding.ensureLoaded();
    sectionOffset();
    target.focus({preventScroll: true}); target.scrollIntoView({block: 'start'});
    // Show the loading heading now, then keep it in view when async panels arrive.
    if (((termsLoading || analyticsLoading) && ['gap-terms-title', 'gap-pairs-title', 'gap-map-title', 'gap-results-title'].includes(id)) ||
        (embedding && embedding.isLoading() && ['gap-results-title', 'gap-static-title', 'bibliography'].includes(id))) pendingSectionTarget = target;
    else { pendingSection = ''; pendingSectionTarget = null; }
  }
  function jumpToSection(id) {
    var url = new URL(location.href); url.hash = id;
    if (url.href !== location.href) history.pushState(null, '', url);
    pendingSection = url.hash; pendingSectionTarget = null; navigatePendingSection();
  }
  function resetStats(message) {
    $('stats-grid').hidden = true; $('stats-grid').replaceChildren();
    $('stats-status').hidden = false; $('stats-status').textContent = message;
  }
  function splitCamelName(target, name) {
    name.split(/(?=[A-Z][a-z])/).forEach(function (part, index) {
      if (index) target.append(node('wbr'));
      target.append(document.createTextNode(part));
    });
  }
  function renderStats(counts) {
    if (!counts || !Number.isSafeInteger(counts.total) || !counts.by_mech) throw new Error('Snapshot gap counts are unavailable.');
    var fragment = document.createDocumentFragment();
    function tile(name, count, coverage) {
      var complete = coverage === 'complete', filterable = complete || count > 0;
      var button = node('button', null, 'gap-stat' + (name ? '' : ' gap-stat-total'));
      button.type = 'button'; button.dataset.mech = name; button.dataset.count = count;
      button.dataset.coverage = coverage; button.dataset.action = filterable ? 'filter' : 'coverage';
      var label = node('span', name ? null : 'Total indexed gaps', 'gap-stat-name');
      if (name) splitCamelName(label, name);
      button.append(label,
        node('span', complete ? number(count) : count ? number(count) + '+' : '—', 'gap-stat-count'),
        node('span', !name ? 'All lifecycle states' : complete ? 'Recorded gaps' : count ? 'Partial coverage' : human(coverage) + ' coverage', 'gap-stat-coverage'));
      button.setAttribute('aria-label', !filterable ? name + ': ' + human(coverage) + ' coverage; inspect sources' :
        (name || 'All Mechs') + ': browse ' + number(count) + ' indexed gaps across all lifecycle states' + (!complete ? '; partial coverage' : ''));
      button.addEventListener('click', function () {
        if (!ready) return;
        if (!filterable) { jumpToSection('gap-static-title'); return; }
        closeDetail(false, false);
        state = core.normalize({mech: name, status: ''}); syncControls();
        var url = stateURL(state); url.hash = 'gap-results-title';
        history.pushState(null, '', url); pendingSection = url.hash; pendingSectionTarget = null; query(false);
      });
      fragment.append(button);
    }
    tile('', counts.total, 'complete');
    manifest.sources.forEach(function (source) { tile(source.name, counts.by_mech[source.name] || 0, source.coverage_status); });
    (manifest.infrastructure || []).forEach(function (member) {
      var infra = node('a', null, 'gap-stat gap-stat-infrastructure');
      infra.href = '#gap-static-title';
      infra.dataset.infrastructure = member.name;
      var label = node('span', null, 'gap-stat-name');
      splitCamelName(label, member.name);
      infra.append(label, node('span', '—', 'gap-stat-count'), node('span', 'Infrastructure · no corpus', 'gap-stat-coverage'));
      infra.setAttribute('aria-label', member.name + ': shared curation infrastructure without a scientific corpus; inspect scope details');
      infra.addEventListener('click', function (event) {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault(); jumpToSection('gap-static-title');
      });
      fragment.append(infra);
    });
    $('stats-grid').replaceChildren(fragment); $('stats-grid').hidden = false;
    $('stats-status').hidden = true;
  }
  function syncControls() {
    $('query').value = state.q;
    ['view', 'mech', 'kind', 'status', 'review', 'layer', 'stance', 'experiments', 'sort', 'vocab'].forEach(function (key) {
      var select = $(key);
      if (!select) return;
      // An obsolete filter is never silently replaced with a broader search.
      Array.from(select.options).filter(function (o) { return o.dataset.unavailable; }).forEach(function (o) { o.remove(); });
      if (!Array.from(select.options).some(function (o) { return o.value === state[key]; })) {
        var option = node('option', state[key] + ' (not in this snapshot)');
        option.value = state[key]; option.dataset.unavailable = 'true'; select.append(option);
      }
      select.value = state[key];
    });
    renderActiveFilters();
  }
  function renderActiveFilters() {
    var bar = $('active-filters');
    if (!bar || !state) return;
    var chips = [];
    function addChip(label, patch) {
      var btn = node('button', label + ' ×', 'gap-filter-chip');
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Remove filter ' + label);
      btn.addEventListener('click', function () { applyStatePatch(patch); });
      chips.push(btn);
    }
    if (state.q) addChip('Query: "' + state.q + '"', {q: ''});
    if (state.mech) addChip('Source: ' + state.mech, {mech: ''});
    if (state.kind) addChip('Kind: ' + human(state.kind), {kind: ''});
    if (state.status !== core.defaults.status) addChip('Lifecycle: ' + (state.status ? human(state.status) : 'all states'), {status: core.defaults.status});
    if (state.review) addChip('Review: ' + human(state.review), {review: ''});
    if (state.layer) addChip('Layer: ' + (state.layer === 'unattached' ? 'unattached' : human(state.layer)), {layer: ''});
    if (state.stance) addChip('Stance: ' + (state.stance === 'none' ? 'no cited evidence' : human(state.stance)), {stance: ''});
    if (state.experiments) addChip('Experiments: ' + (state.experiments === 'yes' ? 'has proposed' : state.experiments === 'no' ? 'none' : state.experiments), {experiments: ''});
    if (state.ref) addChip('Reference: ' + (state.ref.length > 42 ? state.ref.slice(0, 40) + '…' : state.ref), {ref: ''});
    if (state.month) addChip('Month: ' + state.month, {month: ''});
    if (state.vocab) addChip('Vocabulary: ' + state.vocab, {vocab: '', term: '', term2: ''});
    bar.replaceChildren.apply(bar, chips);
    bar.hidden = !chips.length;
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
    resetStats('Gap counts are unavailable until the search index loads. Retry loading below, or inspect the static coverage summary.');
    $('results').replaceChildren(); $('pagination').hidden = true;
    $('load-status').textContent = 'Search could not load: ' + message + ' The static source summary remains available below.';
    $('load-status').className = 'gap-error'; $('load-status').hidden = false; $('retry').hidden = false;
    if (embedding) embedding.invalidateScope('The search index is unavailable. Retry loading before exploring the map.');
    exportButtons();
  }

  /* ---------- Cross-Mech Analyses Renderers ---------- */
  function lensLabel(lens, key) {
    if (lens === 'stance' && key === 'none') return 'No cited evidence';
    if (lens === 'layer' && key === 'unattached') return 'Unattached';
    if (lens === 'layer' && key === '__other__') return 'Other attached slot';
    return human(key);
  }
  function breakdownSegments(analysis, lens) {
    var totals = analysis.totals || {};
    if (lens === 'kind') {
      return Object.keys(totals.kinds || {}).sort(function (a, b) { return totals.kinds[b] - totals.kinds[a] || (a < b ? -1 : 1); });
    }
    if (lens === 'status') {
      return Object.keys(totals.statuses || {}).sort(function (a, b) { return totals.statuses[b] - totals.statuses[a] || (a < b ? -1 : 1); });
    }
    if (lens === 'stance') {
      var keys = Object.keys(totals.stances || {}).sort(function (a, b) { return totals.stances[b] - totals.stances[a] || (a < b ? -1 : 1); });
      if (totals.no_evidence) keys.push('none');
      return keys;
    }
    var layerKeys = Object.keys(totals.layers || {}).sort(function (a, b) { return totals.layers[b] - totals.layers[a] || (a < b ? -1 : 1); });
    var topLayers = layerKeys.slice(0, 6);
    if (layerKeys.length > 6) topLayers.push('__other__');
    if (totals.unattached) topLayers.push('unattached');
    return topLayers;
  }
  function bucketValue(bucket, lens, key, topSet) {
    if (!bucket) return 0;
    if (lens === 'kind') return bucket.kinds[key] || 0;
    if (lens === 'status') return bucket.statuses[key] || 0;
    if (lens === 'stance') return key === 'none' ? bucket.no_evidence : (bucket.stances[key] || 0);
    if (key === 'unattached') return bucket.unattached || 0;
    if (key === '__other__') {
      return Object.keys(bucket.layers || {}).reduce(function (sum, k) { return topSet.has(k) ? sum : sum + bucket.layers[k]; }, 0);
    }
    return bucket.layers[key] || 0;
  }
  function applyLensFilter(lens, key, mechName) {
    var patch = {};
    if (mechName !== undefined) patch.mech = state.mech === mechName && !key ? '' : mechName;
    if (key && key !== '__other__') {
      var stateKey = lens;
      if (lens === 'kind' && state.view === 'gaps' && !['KNOWLEDGE_GAP', 'HUMAN_MODEL_MISMATCH'].includes(key)) patch.view = 'all';
      if (lens === 'status' && state.status === 'active' && !['OPEN', 'UNDER_DISCUSSION'].includes(key)) patch.status = key;
      else patch[stateKey] = state[stateKey] === key && (!mechName || state.mech === mechName) ? '' : key;
    }
    applyStatePatch(patch);
  }
  function renderBreakdown(analysis) {
    if (!manifest || !analysis) return;
    var lens = $('breakdown-lens').value || 'kind';
    var keys = breakdownSegments(analysis, lens);
    var topSet = new Set(keys.filter(function (k) { return k !== '__other__' && k !== 'unattached'; }));
    var colorMap = new Map(keys.map(function (k, i) { return [k, CHART_PALETTE[i % CHART_PALETTE.length]]; }));

    var legend = document.createDocumentFragment();
    keys.forEach(function (k) {
      var li = node('li');
      var swatch = node('span', null, 'gap-map-swatch');
      swatch.style.backgroundColor = colorMap.get(k);
      swatch.setAttribute('aria-hidden', 'true');
      if (k === '__other__') {
        li.append(swatch, document.createTextNode(lensLabel(lens, k)));
      } else {
        var btn = node('button', lensLabel(lens, k), 'gap-legend-btn');
        btn.type = 'button';
        btn.setAttribute('aria-pressed', String(state[lens] === k));
        btn.addEventListener('click', function () { applyLensFilter(lens, k, undefined); });
        li.append(swatch, btn);
      }
      legend.append(li);
    });
    $('breakdown-legend').replaceChildren(legend);

    var sources = manifest.sources.slice().sort(function (a, b) {
      var ca = (analysis.by_mech[a.name] && analysis.by_mech[a.name].total) || 0;
      var cb = (analysis.by_mech[b.name] && analysis.by_mech[b.name].total) || 0;
      return cb - ca || b.items - a.items || (a.name < b.name ? -1 : 1);
    });
    var maxTotal = Math.max.apply(null, [1].concat(sources.map(function (s) {
      return (analysis.by_mech[s.name] && analysis.by_mech[s.name].total) || 0;
    })));

    var rowsFrag = document.createDocumentFragment();
    sources.forEach(function (source) {
      var bucket = analysis.by_mech[source.name];
      var count = bucket ? bucket.total : 0;
      var row = node('div', null, 'gap-breakdown-row' + (state.mech === source.name ? ' is-active' : ''));
      var mechCell = node('div', null, 'gap-breakdown-mech');
      var complete = source.coverage_status === 'complete' || source.items > 0;
      if (complete) {
        var mechBtn = node('button', source.name, 'gap-breakdown-mech-btn');
        mechBtn.type = 'button';
        mechBtn.setAttribute('aria-pressed', String(state.mech === source.name));
        mechBtn.addEventListener('click', function () { applyStatePatch({mech: state.mech === source.name ? '' : source.name}); });
        mechCell.append(mechBtn);
      } else {
        var mechLink = node('a', source.name, 'gap-breakdown-mech-link');
        mechLink.href = '#gap-static-title';
        mechLink.addEventListener('click', function (e) { e.preventDefault(); jumpToSection('gap-static-title'); });
        mechCell.append(mechLink);
      }
      var barArea = node('div', null, 'gap-breakdown-track');
      if (count > 0) {
        var segs = keys.map(function (k) { return {key: k, val: bucketValue(bucket, lens, k, topSet)}; }).filter(function (s) { return s.val > 0; });
        var segSum = segs.reduce(function (acc, s) { return acc + s.val; }, 0) || count;
        var barWrap = node('div', null, 'gap-breakdown-bar');
        barWrap.style.width = Math.max(4, (count / maxTotal) * 100).toFixed(2) + '%';
        segs.forEach(function (seg) {
          var el = node(seg.key === '__other__' ? 'span' : 'button', null, 'gap-breakdown-seg');
          if (seg.key !== '__other__') {
            el.type = 'button';
            el.addEventListener('click', function () { applyLensFilter(lens, seg.key, source.name); });
          }
          el.style.width = ((seg.val / segSum) * 100).toFixed(2) + '%';
          el.style.backgroundColor = colorMap.get(seg.key);
          var desc = source.name + ' · ' + lensLabel(lens, seg.key) + ': ' + number(seg.val) +
            (lens === 'stance' || lens === 'layer' ? ' layer/stance assignments across ' + number(count) + ' discussions' : ' of ' + number(count) + ' discussions');
          el.title = desc;
          el.setAttribute('aria-label', desc + (seg.key === '__other__' ? '' : '. Filter discussions'));
          barWrap.append(el);
        });
        barArea.append(barWrap);
      } else {
        var reason = source.coverage_status === 'complete'
          ? (source.items > 0 ? '0 matching filters (' + number(source.items) + ' in snapshot)' : '0 items in corpus (complete extraction)')
          : source.coverage_status === 'unsupported'
            ? 'Unsupported schema (no native discussion field)'
            : 'Partial coverage · maintained root held';
        barArea.append(node('span', reason, 'gap-breakdown-empty'));
      }
      row.append(mechCell, barArea, node('span', count ? number(count) : '0', 'gap-breakdown-count'));
      rowsFrag.append(row);
    });
    (manifest.infrastructure || []).forEach(function (member) {
      var row = node('div', null, 'gap-breakdown-row is-infrastructure');
      var mechCell = node('div', null, 'gap-breakdown-mech');
      var a = node('a', member.name, 'gap-breakdown-mech-link');
      a.href = '#gap-static-title';
      a.addEventListener('click', function (e) { e.preventDefault(); jumpToSection('gap-static-title'); });
      mechCell.append(a);
      var track = node('div', null, 'gap-breakdown-track');
      track.append(node('span', 'Shared curation infrastructure — no scientific corpus', 'gap-breakdown-empty'));
      row.append(mechCell, track, node('span', '—', 'gap-breakdown-count'));
      rowsFrag.append(row);
    });
    $('breakdown-rows').replaceChildren(rowsFrag);
    var noteExtra = (lens === 'stance' || lens === 'layer') ? ' Note: one discussion may attach to multiple schema layers or evidence stances; bar length reflects discussion count while segments reflect assignment shares.' : '';
    $('breakdown-note').textContent = 'Showing ' + number(analysis.total) + ' matching discussions across ' + number(manifest.sources.length) + ' corpus Mechs' +
      (manifest.infrastructure && manifest.infrastructure.length ? ' and ' + number(manifest.infrastructure.length) + ' infrastructure project' : '') + '.' + noteExtra;
  }

  function renderVocabMatrix(analysis) {
    var statusEl = $('matrix-status'), wrap = $('matrix-wrap');
    if (!manifest || !analysis || !termsReady || !analysis.vocab_matrix) {
      wrap.hidden = true;
      statusEl.hidden = false;
      statusEl.textContent = termsLoading ? 'Loading entity occurrences to build the 16 × 16 cross-pollination matrix…' :
        !termsReady ? 'Cross-Mech vocabulary matrix requires the entity index. Retry entity occurrences below.' :
        'Cross-Mech vocabulary matrix is updating…';
      return;
    }
    statusEl.hidden = true;
    wrap.hidden = false;
    var mode = $('matrix-mode').value || 'discussions';
    var rawMatrix = mode === 'occurrences' ? analysis.vocab_matrix.occurrences : analysis.vocab_matrix.discussions;
    var names = manifest.sources.map(function (s) { return s.name; });
    var sourceStatus = new Map(manifest.sources.map(function (s) { return [s.name, s]; }));

    var maxCell = 1, crossTotal = 0, diagTotal = 0;
    names.forEach(function (src) {
      names.forEach(function (voc) {
        var val = (rawMatrix[src] && rawMatrix[src][voc]) || 0;
        if (src === voc) diagTotal += val; else crossTotal += val;
        if (mode === 'cross' && src === voc) return;
        if (val > maxCell) maxCell = val;
      });
    });

    var table = node('table', null, 'gap-matrix-table');
    table.append(node('caption', 'Source Mech rows by Term vocabulary columns (' +
      (mode === 'occurrences' ? 'raw entity occurrences' : mode === 'cross' ? 'off-diagonal cross-Mech distinct discussions' : 'distinct discussions') +
      '; cross-Mech total ' + number(crossTotal) + ', within-Mech diagonal ' + number(diagTotal) + ')'));
    var thead = node('thead'), headRow = node('tr');
    var corner = node('th', 'Source \\ Vocab'); corner.scope = 'col'; headRow.append(corner);
    names.forEach(function (voc) {
      var th = node('th', shortMech(voc));
      th.scope = 'col'; th.title = voc + ' entity vocabulary';
      if (state.vocab === voc) th.className = 'is-selected';
      headRow.append(th);
    });
    thead.append(headRow); table.append(thead);

    var tbody = node('tbody');
    names.forEach(function (src) {
      var tr = node('tr');
      var srcInfo = sourceStatus.get(src);
      var rowHead = node('th', shortMech(src));
      rowHead.scope = 'row';
      rowHead.title = src + ' (' + human(srcInfo.coverage_status) + ', ' + number(srcInfo.items) + ' snapshot items)';
      if (state.mech === src) rowHead.className = 'is-selected';
      tr.append(rowHead);
      names.forEach(function (voc) {
        var isDiag = src === voc;
        var val = (rawMatrix[src] && rawMatrix[src][voc]) || 0;
        var td = node('td', null, (isDiag ? 'is-diagonal' : '') + (state.mech === src && state.vocab === voc ? ' is-selected' : ''));
        if (mode === 'cross' && isDiag) {
          td.textContent = '·';
          td.title = src + ' within-Mech mentions hidden in off-diagonal view (' + number(val) + ' discussions)';
        } else if (val > 0) {
          var intensity = Math.min(0.92, 0.14 + 0.78 * Math.sqrt(val / maxCell));
          td.style.setProperty('--cell-alpha', intensity.toFixed(3));
          td.classList.add('has-value');
          var btn = node('button', number(val), 'gap-matrix-btn');
          btn.type = 'button';
          var activeCell = state.mech === src && state.vocab === voc;
          btn.setAttribute('aria-pressed', String(activeCell));
          var cellLabel = src + ' discussions mentioning ' + voc + ' entities: ' + number(val) +
            (mode === 'occurrences' ? ' occurrences' : ' discussions') + (isDiag ? ' (within-Mech)' : ' (cross-Mech)');
          btn.title = cellLabel;
          btn.setAttribute('aria-label', cellLabel + '. Filter to this Source Mech and Term vocabulary');
          btn.addEventListener('click', function () {
            if (activeCell) applyStatePatch({mech: '', vocab: '', term: '', term2: ''});
            else applyStatePatch({mech: src, vocab: voc, term: '', term2: ''}, 'gap-terms-title');
          });
          td.append(btn);
        } else {
          td.textContent = srcInfo.coverage_status !== 'complete' && !srcInfo.items ? '—' : '0';
          td.classList.add('is-zero');
          td.title = srcInfo.coverage_status !== 'complete' && !srcInfo.items
            ? src + ' (' + human(srcInfo.coverage_status) + ') × ' + voc + ': source not indexed'
            : src + ' × ' + voc + ': 0 matched mentions in current filters';
        }
        tr.append(td);
      });
      tbody.append(tr);
    });
    table.append(tbody);
    wrap.replaceChildren(table);
  }

  function renderTimeline(analysis) {
    var container = $('timeline-chart');
    if (!analysis) return;
    var series = analysis.timeline || [];
    var totalPosed = series.reduce(function (s, r) { return s + r.posed; }, 0);
    var totalResolved = series.reduce(function (s, r) { return s + r.resolved; }, 0);
    var undated = Math.max(0, analysis.total - totalPosed);
    $('timeline-note').textContent = number(totalPosed) + ' matching discussions carry a posed date (' + number(undated) + ' undated); ' +
      number(totalResolved) + ' carry a resolved date. Select a bar to filter by month.';
    if (!series.length) {
      container.replaceChildren(node('p', 'No dated discussions match the current filters.', 'gap-note'));
      return;
    }
    var W = 560, H = 215, padL = 44, padR = 14, padT = 18, padB = 46;
    var plotW = W - padL - padR, plotH = H - padT - padB;
    var maxVal = Math.max.apply(null, [1].concat(series.map(function (r) { return Math.max(r.posed, r.resolved); })));
    var svg = svgNode('svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('role', 'group');
    svg.setAttribute('aria-label', 'Monthly posed and resolved discussion counts');

    [0, 0.5, 1].forEach(function (frac) {
      var y = padT + plotH * (1 - frac);
      var line = svgNode('line');
      line.setAttribute('x1', padL); line.setAttribute('x2', W - padR);
      line.setAttribute('y1', y); line.setAttribute('y2', y);
      line.setAttribute('class', 'gap-chart-grid');
      var txt = svgNode('text');
      txt.setAttribute('x', padL - 6); txt.setAttribute('y', y + 4);
      txt.setAttribute('text-anchor', 'end'); txt.setAttribute('class', 'gap-chart-axis');
      txt.textContent = number(Math.round(maxVal * frac));
      svg.append(line, txt);
    });

    var slotW = plotW / series.length, barW = Math.max(4, Math.min(26, (slotW - 6) / 2));
    var labelStep = Math.max(1, Math.ceil(series.length / 8));
    series.forEach(function (row, idx) {
      var centerX = padL + idx * slotW + slotW / 2;
      [
        {kind: 'posed', count: row.posed, x: centerX - barW - 1, cls: 'gap-bar-posed', label: 'Posed'},
        {kind: 'resolved', count: row.resolved, x: centerX + 1, cls: 'gap-bar-resolved', label: 'Resolved'}
      ].forEach(function (bar) {
        if (!bar.count) return;
        var h = Math.max(3, (bar.count / maxVal) * plotH), y = padT + plotH - h;
        var filterToken = bar.kind + ':' + row.month;
        var active = state.month === filterToken || state.month === row.month;
        var rect = svgNode('rect');
        rect.setAttribute('x', bar.x.toFixed(1)); rect.setAttribute('y', y.toFixed(1));
        rect.setAttribute('width', barW.toFixed(1)); rect.setAttribute('height', h.toFixed(1));
        rect.setAttribute('rx', '2');
        rect.setAttribute('class', bar.cls + (active ? ' is-selected' : ''));
        rect.setAttribute('role', 'button');
        rect.setAttribute('tabindex', '0');
        var desc = bar.label + ' in ' + row.month + ': ' + number(bar.count) + ' discussions';
        rect.setAttribute('aria-label', desc + '. Filter by this month');
        var title = svgNode('title'); title.textContent = desc; rect.append(title);
        function activate() {
          var patch = {month: state.month === filterToken ? '' : filterToken};
          if (bar.kind === 'resolved' && state.status === 'active') patch.status = '';
          applyStatePatch(patch);
        }
        rect.addEventListener('click', activate);
        rect.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); }
        });
        svg.append(rect);
      });
      if (idx % labelStep === 0 || idx === series.length - 1) {
        var lbl = svgNode('text');
        lbl.setAttribute('x', centerX.toFixed(1)); lbl.setAttribute('y', padT + plotH + 18);
        lbl.setAttribute('text-anchor', 'middle'); lbl.setAttribute('class', 'gap-chart-axis');
        lbl.textContent = row.month;
        svg.append(lbl);
      }
    });
    var legendRow = node('div', null, 'gap-chart-inline-legend');
    [['gap-swatch-posed', 'Posed (' + number(totalPosed) + ')'], ['gap-swatch-resolved', 'Resolved (' + number(totalResolved) + ')']].forEach(function (pair) {
      var item = node('span', null, 'gap-chart-key');
      var sw = node('span', null, 'gap-map-swatch ' + pair[0]); sw.setAttribute('aria-hidden', 'true');
      item.append(sw, document.createTextNode(pair[1]));
      legendRow.append(item);
    });
    container.replaceChildren(legendRow, svg);
  }

  function renderRefs(analysis) {
    var container = $('refs-list');
    if (!analysis) return;
    var mode = $('refs-mode').value || 'top';
    var rows = mode === 'cross' ? (analysis.cross_mech_refs || []) : (analysis.top_refs || []);
    $('refs-note').textContent = number(analysis.distinct_refs || 0) + ' distinct normalized references across matching discussions; ' +
      number((analysis.cross_mech_refs || []).length) + ' cited in 2+ Mechs. Select Filter to isolate discussions citing a reference.';
    if (!rows.length) {
      container.replaceChildren(node('p', mode === 'cross'
        ? 'Zero normalized references are shared across two or more Mechs in the current filter scope — literature citations remain siloed within individual Mechs even when questions overlap semantically.'
        : 'No cited references appear in the matching discussions.', 'gap-note'));
      return;
    }
    var frag = document.createDocumentFragment();
    rows.slice(0, 10).forEach(function (entry) {
      var item = node('div', null, 'gap-compact-row');
      var main = node('div', null, 'gap-compact-main');
      var display = entry.ref.length > 68 ? entry.ref.slice(0, 65) + '…' : entry.ref;
      var href = core.referenceURL(entry.raw_ref || entry.ref);
      if (href) {
        var a = node('a', display); a.href = href; a.rel = 'noopener noreferrer'; a.title = entry.ref;
        main.append(a);
      } else {
        var sp = node('span', display); sp.title = entry.ref; main.append(sp);
      }
      var meta = node('span', ' · ' + number(entry.discussions) + ' discussions · ' + entry.mechs.join(', '), 'gap-note');
      main.append(meta);
      var btn = node('button', state.ref === entry.ref ? 'Filtered ✓' : 'Filter', 'gap-mini-btn');
      btn.type = 'button';
      btn.setAttribute('aria-pressed', String(state.ref === entry.ref));
      btn.addEventListener('click', function () { applyStatePatch({ref: state.ref === entry.ref ? '' : entry.ref}); });
      item.append(main, btn);
      frag.append(item);
    });
    container.replaceChildren(frag);
  }

  function renderAnalyses(analysis) {
    lastAnalysis = analysis;
    renderBreakdown(analysis);
    renderVocabMatrix(analysis);
    renderTimeline(analysis);
    renderRefs(analysis);
  }

  /* ---------- Synthesis Sidecar (analytics.*.json) ---------- */
  function renderAnalyticsSidecar() {
    if (!analyticsReady || !analyticsDoc) return;
    $('analytics-status').hidden = true;
    $('analytics-retry').hidden = true;
    $('analytics-content').hidden = false;

    // 1. Cross-Mech semantic bridges
    var bridges = analyticsDoc.embedding_bridges;
    if (bridges) {
      $('bridges-summary').textContent = number(bridges.total_cross_mech_unordered_pairs) +
        ' unordered original-vector nearest-neighbor pairs link discussions in different Mechs (' +
        number(bridges.discussions_with_cross_mech_top1) + ' discussions have their #1 nearest neighbor in another Mech).';
      var bFrag = document.createDocumentFragment();
      if (bridges.cross_mech_matrix && bridges.cross_mech_matrix.length) {
        var pairChips = node('div', null, 'gap-chip-cloud');
        bridges.cross_mech_matrix.slice(0, 6).forEach(function (m) {
          var badge = node('span', shortMech(m.mech_a) + ' ↔ ' + shortMech(m.mech_b) + ': ' + number(m.directed_neighbor_edges) + ' edges (max ' + m.max_cosine.toFixed(2) + ')', 'gap-badge');
          pairChips.append(badge);
        });
        bFrag.append(pairChips);
      }
      (bridges.cross_mech_pairs || []).slice(0, 6).forEach(function (pair) {
        var row = node('div', null, 'gap-compact-row gap-bridge-pair');
        var header = node('div', pair.mech_a + ' ↔ ' + pair.mech_b + ' · cosine ' + pair.cosine_similarity.toFixed(3), 'gap-bridge-meta');
        var btns = node('div', null, 'gap-bridge-links');
        var btnA = node('button', pair.mech_a + ': ' + (pair.prompt_a || pair.record_a).slice(0, 72) + ((pair.prompt_a || '').length > 72 ? '…' : ''), 'gap-mini-btn');
        btnA.type = 'button';
        btnA.addEventListener('click', function () { lastDetailButton = btnA; openDetail(pair.id_a, true, true); });
        var btnB = node('button', pair.mech_b + ': ' + (pair.prompt_b || pair.record_b).slice(0, 72) + ((pair.prompt_b || '').length > 72 ? '…' : ''), 'gap-mini-btn');
        btnB.type = 'button';
        btnB.addEventListener('click', function () { lastDetailButton = btnB; openDetail(pair.id_b, true, true); });
        btns.append(btnA, btnB);
        row.append(header, btns);
        bFrag.append(row);
      });
      $('bridges-list').replaceChildren(bFrag);
    } else {
      $('bridges-summary').textContent = 'Embedding bridge summaries are not included in this bundle.';
      $('bridges-list').replaceChildren();
    }

    // 2. Proposed-experiments backlog
    var exps = analyticsDoc.proposed_experiments || {discussions_with_experiments: 0, total_experiments: 0, by_mech: {}, items: []};
    var mechSummary = Object.keys(exps.by_mech || {}).map(function (m) { return m + ' (' + number(exps.by_mech[m]) + ')'; }).join(', ');
    $('experiments-summary').textContent = number(exps.discussions_with_experiments) + ' snapshot discussions carry ' +
      number(exps.total_experiments) + ' structured proposed experiments' + (mechSummary ? ' across ' + mechSummary : '') + '.';
    var eFrag = document.createDocumentFragment();
    if (exps.discussions_with_experiments > 0) {
      var filterExpBtn = node('button', state.experiments === 'yes' ? 'Showing proposed-experiment discussions ✓' : 'Browse all ' + number(exps.discussions_with_experiments) + ' discussions with experiments', 'gap-mini-btn');
      filterExpBtn.type = 'button';
      filterExpBtn.addEventListener('click', function () {
        if (state.experiments === 'yes') applyStatePatch({experiments: ''});
        else applyStatePatch({view: 'all', status: '', experiments: 'yes'}, 'gap-results-title');
      });
      eFrag.append(filterExpBtn);
      (exps.items || []).slice(0, 6).forEach(function (entry) {
        var row = node('div', null, 'gap-compact-row');
        var main = node('div', null, 'gap-compact-main');
        var openBtn = node('button', (entry.prompt || entry.record_label || entry.id).slice(0, 90) + ((entry.prompt || '').length > 90 ? '…' : ''), 'gap-open');
        openBtn.type = 'button';
        openBtn.addEventListener('click', function () { lastDetailButton = openBtn; openDetail(entry.id, true, true); });
        main.append(openBtn, node('span', ' · ' + entry.mech + ' · ' + (entry.experiment_names || []).join('; '), 'gap-note'));
        row.append(main);
        eFrag.append(row);
      });
    }
    $('experiments-list').replaceChildren(eFrag);

    // 3. Unmatched-discussion vocabulary blind-spots
    renderBlindspots();

    // 4. Entity cohesion & duplicate prompts
    var cFrag = document.createDocumentFragment();
    if (bridges && Array.isArray(bridges.entity_cohesion)) {
      $('cohesion-summary').textContent = 'Within-entity neighbor share measures whether discussions mentioning an entity cluster together in embedding space or span distinct topics. Also flags ' +
        number(bridges.duplicate_cluster_count) + ' duplicate-input clusters (' + number(bridges.duplicate_discussion_count) + ' discussions).';
      bridges.entity_cohesion.slice(0, 5).forEach(function (ent) {
        var row = node('div', null, 'gap-compact-row');
        var main = node('div', null, 'gap-compact-main');
        var btn = node('button', ent.label, 'gap-mini-btn');
        btn.type = 'button';
        btn.addEventListener('click', function () { selectTerms(ent.id, ''); jumpToSection('gap-results-title'); });
        main.append(btn, node('span', ' · ' + (ent.within_entity_neighbor_share * 100).toFixed(1) + '% same-entity neighbors · ' +
          number(ent.discussions) + ' discussions across ' + number(ent.discussion_mech_count) + ' Mechs', 'gap-note'));
        row.append(main);
        cFrag.append(row);
      });
      (bridges.duplicate_clusters || []).slice(0, 3).forEach(function (dup) {
        var row = node('div', null, 'gap-compact-row');
        var main = node('div', null, 'gap-compact-main');
        var btn = node('button', 'Duplicate prompt (' + number(dup.count) + '×): ' + (dup.sample_prompt || '').slice(0, 68) + '…', 'gap-mini-btn');
        btn.type = 'button';
        btn.addEventListener('click', function () {
          if (dup.discussion_ids && dup.discussion_ids[0]) { lastDetailButton = btn; openDetail(dup.discussion_ids[0], true, true); }
        });
        main.append(btn, node('span', ' · ' + Object.keys(dup.mechs || {}).join(', '), 'gap-note'));
        row.append(main);
        cFrag.append(row);
      });
    } else {
      $('cohesion-summary').textContent = 'Cohesion diagnostics require embedding vectors.';
    }
    $('cohesion-list').replaceChildren(cFrag);
  }

  function renderBlindspots() {
    if (!analyticsReady || !analyticsDoc || !analyticsDoc.unmatched_coverage) return;
    var cov = analyticsDoc.unmatched_coverage;
    var scopeMode = $('blindspot-scope').value || 'gaps';
    var block = scopeMode === 'gaps' && cov.gaps_only ? cov.gaps_only : cov;
    var topUnmatchedMechs = Object.keys(block.by_mech || {}).filter(function (m) {
      return block.by_mech[m].unmatched > 0;
    }).sort(function (a, b) { return block.by_mech[b].unmatched - block.by_mech[a].unmatched; }).slice(0, 4).map(function (m) {
      return m + ' (' + number(block.by_mech[m].unmatched) + '/' + number(block.by_mech[m].total) + ')';
    }).join(', ');
    $('blindspot-summary').textContent = number(block.unmatched_discussions) + ' of ' + number(block.total_discussions) +
      (scopeMode === 'gaps' ? ' recorded knowledge gaps' : ' snapshot discussions') +
      ' had zero accepted dictionary entity matches' + (topUnmatchedMechs ? ' — most in ' + topUnmatchedMechs : '') +
      '. Select a candidate phrase to search those discussions:';
    var frag = document.createDocumentFragment();
    (block.candidate_phrases || []).slice(0, 18).forEach(function (p) {
      var btn = node('button', p.phrase + ' (' + number(p.discussions) + ')', 'gap-phrase-chip');
      btn.type = 'button';
      var mechList = Object.keys(p.mechs || {}).join(', ');
      btn.title = '"' + p.phrase + '" in ' + number(p.discussions) + ' unmatched discussions (' + mechList + ')';
      btn.addEventListener('click', function () {
        var patch = {q: p.phrase, term: '', term2: ''};
        if (scopeMode === 'all') { patch.view = 'all'; patch.status = ''; }
        else { patch.view = 'gaps'; patch.status = ''; }
        applyStatePatch(patch, 'gap-results-title');
      });
      frag.append(btn);
    });
    $('blindspot-phrases').replaceChildren(frag);
  }

  async function loadAnalytics() {
    if (!ready || analyticsLoading) return;
    if (!manifest.analytics) {
      $('analytics-status').textContent = 'Snapshot synthesis sidecar is not present in this bundle.';
      return;
    }
    var version = ++analyticsVersion, snapshotVersion = loadVersion;
    analyticsLoading = true; analyticsReady = false; analyticsDoc = null;
    $('analytics-content').hidden = true; $('analytics-retry').hidden = true;
    $('analytics-status').hidden = false; $('analytics-status').className = 'gap-note';
    $('analytics-status').textContent = 'Loading snapshot synthesis sidecar…';
    try {
      var doc = await verifiedJSON(manifest.analytics);
      if (version !== analyticsVersion || snapshotVersion !== loadVersion) return;
      if (manifest.terms && doc.terms_sha256 && doc.terms_sha256 !== manifest.terms.sha256) {
        throw new Error('Synthesis sidecar does not match the active entity index.');
      }
      analyticsDoc = doc; analyticsReady = true; analyticsLoading = false;
      renderAnalyticsSidecar();
      navigatePendingSection();
    } catch (error) {
      if (version !== analyticsVersion || snapshotVersion !== loadVersion) return;
      analyticsLoading = false;
      $('analytics-status').className = 'gap-error';
      $('analytics-status').textContent = 'Synthesis sidecar could not load: ' + error.message + ' Search and charts above remain available.';
      $('analytics-retry').hidden = false;
      navigatePendingSection();
    }
  }

  /* ---------- Term Explorer & Co-occurrence Network ---------- */
  function termIdentity(term) {
    if (term.canonical_id) return term.canonical_id;
    return Array.from(new Set((term.entity_refs || []).map(function (ref) {
      return ref.mech + ' / ' + ref.record_id;
    }))).join(' · ');
  }
  function termLabel(term) { return term.label + (term.duplicateLabel && termIdentity(term) ? ' (' + termIdentity(term) + ')' : ''); }
  function showTermSelection(selected) {
    (selected || []).forEach(function (term) { termInfo.set(term.id, Object.assign({}, termInfo.get(term.id), term)); });
    var ids = [state.term, state.term2].filter(Boolean);
    $('term-selection').hidden = !ids.length;
    $('term-selection-label').textContent = ids.length ? 'Showing discussions containing ' + ids.map(function (id) {
      var term = termInfo.get(id);
      if (!term) return 'selected entity (details require the entity index)';
      if (term.unavailable) return id + ' (not in this entity index)';
      return term.label + (term.canonical_id ? ' (' + term.canonical_id + ')' : '') +
        (term.in_vocabulary === false ? ' (outside the selected vocabulary)' : '');
    }).join(' AND ') + '. Other search filters still apply.' : '';
    var sources = document.createDocumentFragment();
    ids.forEach(function (id) {
      var term = termInfo.get(id);
      if (!term || !term.entity_refs || !term.entity_refs.length) return;
      var p = node('p'); p.append(document.createTextNode(term.label + ' — entity vocabulary: '));
      term.entity_refs.forEach(function (ref, i) {
        if (i) p.append(document.createTextNode(' · '));
        p.append(link(ref.mech + ' / ' + ref.record_id, ref.url));
      }); sources.append(p);
    });
    $('term-sources').replaceChildren(sources);
  }
  function selectTerms(first, second) {
    var next = core.normalize(Object.assign({}, state, {term: first || '', term2: second || '', page: 1, gap: ''}));
    if (next.term === state.term && next.term2 === state.term2) { $('result-status').focus(); return; }
    closeDetail(false, false); state = next; historyState(false); showTermSelection(); query(true);
  }
  function termButton(term, cloud) {
    var button = node('button', termLabel(term), cloud ? 'gap-term-word' : '');
    button.type = 'button'; button.dataset.term = term.id;
    button.setAttribute('aria-pressed', String(state.term === term.id || state.term2 === term.id));
    button.title = term.label + (termIdentity(term) ? ' (' + termIdentity(term) + ')' : '') + ': ' + number(term.occurrences) + ' occurrences in ' + number(term.discussions) + ' discussions';
    button.setAttribute('aria-label', button.title + '. Show matching discussions');
    if (cloud) button.append(node('span', number(term.occurrences), 'gap-term-count'));
    button.addEventListener('click', function () { selectTerms(term.id, ''); });
    return button;
  }
  function sortedPairs(pairs, metric) {
    var copy = (pairs || []).slice();
    if (!metric || metric === 'discussions') return copy;
    return copy.sort(function (a, b) {
      if (metric === 'npmi' && b.npmi !== a.npmi) return b.npmi - a.npmi;
      if (metric === 'jaccard' && b.jaccard !== a.jaccard) return b.jaccard - a.jaccard;
      return b.discussions - a.discussions;
    });
  }
  function renderPairsNetwork(summary, orderedPairs, metric) {
    var container = $('pairs-network');
    if (!container) return;
    if (!orderedPairs.length) {
      container.hidden = true;
      container.replaceChildren();
      return;
    }
    var topTerms = summary.terms.slice(0, 20);
    var activeIds = new Set();
    orderedPairs.slice(0, 35).forEach(function (p) { activeIds.add(p.a); activeIds.add(p.b); });
    var nodes = topTerms.filter(function (t) { return activeIds.has(t.id); });
    if (nodes.length < 2) {
      container.hidden = true;
      container.replaceChildren();
      return;
    }
    container.hidden = false;
    var W = 680, H = 400, cx = W / 2, cy = H / 2, rx = 180, ry = 138;
    var maxDisc = Math.max.apply(null, [1].concat(nodes.map(function (t) { return t.discussions; })));
    var pos = new Map();
    nodes.forEach(function (term, idx) {
      var angle = -Math.PI / 2 + (2 * Math.PI * idx) / nodes.length;
      pos.set(term.id, {
        x: cx + rx * Math.cos(angle),
        y: cy + ry * Math.sin(angle),
        cos: Math.cos(angle),
        sin: Math.sin(angle),
        r: 6 + 9 * Math.sqrt(term.discussions / maxDisc)
      });
    });
    var edges = orderedPairs.slice(0, 35);
    var maxWeight = Math.max.apply(null, [0.0001].concat(edges.map(function (p) {
      return metric === 'npmi' ? Math.max(0.05, (p.npmi + 1) / 2) : metric === 'jaccard' ? Math.max(0.02, p.jaccard) : p.discussions;
    })));

    var svg = svgNode('svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('role', 'group');
    svg.setAttribute('aria-label', 'Network of co-occurring top entities; select an edge or node to filter');

    var edgeGroup = svgNode('g');
    edges.forEach(function (pair) {
      var pa = pos.get(pair.a), pb = pos.get(pair.b);
      if (!pa || !pb) return;
      var rawW = metric === 'npmi' ? Math.max(0.05, (pair.npmi + 1) / 2) : metric === 'jaccard' ? Math.max(0.02, pair.jaccard) : pair.discussions;
      var norm = Math.min(1, rawW / maxWeight);
      var selectedEdge = [state.term, state.term2].includes(pair.a) && [state.term, state.term2].includes(pair.b);
      var line = svgNode('line');
      line.setAttribute('x1', pa.x.toFixed(1)); line.setAttribute('y1', pa.y.toFixed(1));
      line.setAttribute('x2', pb.x.toFixed(1)); line.setAttribute('y2', pb.y.toFixed(1));
      line.setAttribute('stroke-width', (selectedEdge ? 3.5 : 1 + 3.2 * norm).toFixed(2));
      line.setAttribute('stroke-opacity', (selectedEdge ? 0.95 : 0.22 + 0.58 * norm).toFixed(2));
      line.setAttribute('class', 'gap-net-edge' + (selectedEdge ? ' is-selected' : ''));
      line.setAttribute('role', 'button');
      line.setAttribute('tabindex', '0');
      var la = termLabel(termInfo.get(pair.a)), lb = termLabel(termInfo.get(pair.b));
      var desc = la + ' + ' + lb + ': ' + number(pair.discussions) + ' discussions, Jaccard ' + (pair.jaccard || 0).toFixed(3) + ', NPMI ' + (pair.npmi || 0).toFixed(3);
      line.setAttribute('aria-label', desc + '. Show discussions with both');
      var title = svgNode('title'); title.textContent = desc; line.append(title);
      line.addEventListener('click', function () { selectTerms(pair.a, pair.b); });
      line.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectTerms(pair.a, pair.b); }
      });
      edgeGroup.append(line);
    });
    svg.append(edgeGroup);

    var nodeGroup = svgNode('g');
    nodes.forEach(function (term) {
      var p = pos.get(term.id);
      var isSel = state.term === term.id || state.term2 === term.id;
      var g = svgNode('g');
      g.setAttribute('class', 'gap-net-node' + (isSel ? ' is-selected' : ''));
      g.setAttribute('role', 'button');
      g.setAttribute('tabindex', '0');
      var desc = termLabel(term) + ': ' + number(term.discussions) + ' discussions (' + number(term.occurrences) + ' occurrences)';
      g.setAttribute('aria-label', desc + '. Filter discussions');
      var title = svgNode('title'); title.textContent = desc; g.append(title);

      var circle = svgNode('circle');
      circle.setAttribute('cx', p.x.toFixed(1)); circle.setAttribute('cy', p.y.toFixed(1));
      circle.setAttribute('r', p.r.toFixed(1));
      g.append(circle);

      var labelStr = termLabel(term);
      if (labelStr.length > 22) labelStr = labelStr.slice(0, 20) + '…';
      var txt = svgNode('text');
      var offset = p.r + 7;
      var polar = Math.abs(p.cos) < 0.08;
      var tx = p.x + (polar ? 0 : (p.cos > 0 ? offset : -offset));
      var ty = p.y + (polar ? (p.sin > 0 ? offset + 11 : -offset - 3) : (p.sin * 5 + 4));
      txt.setAttribute('x', tx.toFixed(1));
      txt.setAttribute('y', ty.toFixed(1));
      txt.setAttribute('text-anchor', polar ? 'middle' : (p.cos > 0 ? 'start' : 'end'));
      txt.textContent = labelStr;
      g.append(txt);

      g.addEventListener('click', function () { selectTerms(term.id, ''); });
      g.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectTerms(term.id, ''); }
      });
      nodeGroup.append(g);
    });
    svg.append(nodeGroup);
    container.replaceChildren(svg);
  }
  function renderPairsView(summary) {
    if (!termsReady || !summary) return;
    var metric = $('pairs-metric').value || 'discussions';
    var ordered = sortedPairs(summary.pairs, metric);
    renderPairsNetwork(summary, ordered, metric);
    var pairs = document.createDocumentFragment();
    ordered.forEach(function (pair) {
      var row = node('tr'), names = node('td');
      var button = node('button', termLabel(termInfo.get(pair.a)) + ' + ' + termLabel(termInfo.get(pair.b)));
      button.type = 'button'; button.dataset.term = pair.a; button.dataset.term2 = pair.b;
      button.setAttribute('aria-pressed', String([state.term, state.term2].includes(pair.a) && [state.term, state.term2].includes(pair.b)));
      button.setAttribute('aria-label', termLabel(termInfo.get(pair.a)) + ' and ' + termLabel(termInfo.get(pair.b)) + ': ' +
        number(pair.discussions) + ' discussions, Jaccard ' + (pair.jaccard || 0).toFixed(3) + ', NPMI ' + (pair.npmi || 0).toFixed(3));
      button.addEventListener('click', function () { selectTerms(pair.a, pair.b); });
      names.append(button);
      row.append(
        names,
        node('td', (pair.jaccard || 0).toFixed(3)),
        node('td', (pair.npmi || 0).toFixed(3)),
        node('td', number(pair.discussions))
      );
      pairs.append(row);
    });
    $('term-pairs').replaceChildren(pairs);
    $('pairs-status').hidden = true;
    $('pairs-table').hidden = !ordered.length; $('pairs-empty').hidden = Boolean(ordered.length);
  }
  function renderTerms(summary, selected) {
    lastTermSummary = summary;
    lastSelectedTerms = selected || [];
    showTermSelection(selected);
    if (!termsReady || !summary) return;
    var labels = new Map();
    summary.terms.forEach(function (term) { labels.set(term.label, (labels.get(term.label) || 0) + 1); });
    summary.terms.forEach(function (term) { term.duplicateLabel = labels.get(term.label) > 1; termInfo.set(term.id, term); });
    $('terms-status').className = '';
    $('terms-status').textContent = summary.terms.length ? 'Entity occurrences loaded.' : 'No indexed entity mentions occur in this scope. This does not mean the discussions contain no entities.';
    $('terms-count').textContent = number(summary.occurrences) + ' occurrences of ' + number(summary.terms.length) + ' entities from ' + (state.vocab || 'all Mech vocabularies') + ' in ' + number(summary.covered_discussions) + ' of ' + number(summary.scope_discussions) + ' discussions before entity selection.';
    $('terms-content').hidden = !summary.terms.length;
    var cloud = document.createDocumentFragment(), table = document.createDocumentFragment();
    var max = summary.terms.length ? summary.terms[0].occurrences : 1;
    summary.terms.forEach(function (term, index) {
      if (index < 50) {
        var word = termButton(term, true);
        word.style.fontSize = Math.max(1, 2.8 * Math.sqrt(term.occurrences / max)).toFixed(3) + 'rem';
        cloud.append(word);
      }
      var row = node('tr'), name = node('td'); name.append(termButton(term, false));
      row.append(name, node('td', number(term.occurrences)), node('td', number(term.discussions))); table.append(row);
    });
    $('term-cloud').replaceChildren(cloud); $('term-ranking').replaceChildren(table);
    renderPairsView(summary);
  }
  function termCoverage(reply) {
    var sources = Array.isArray(reply.vocabulary_sources) ? reply.vocabulary_sources : [];
    var fragment = document.createDocumentFragment();
    fragment.append(node('p', number(sources.length) + ' entity vocabulary sources. Vocabulary coverage describes names available for matching; discussion extraction has its own coverage below.'));
    var list = node('ul');
    sources.forEach(function (source) {
      var li = node('li'); li.append(node('strong', source.name + ' — ' + human(source.coverage_status)));
      if (source.repository && source.revision) li.append(document.createTextNode(' · '), link('Pinned vocabulary source', 'https://github.com/' + source.repository + '/tree/' + source.revision));
      var roots = node('ul');
      (source.roots || []).forEach(function (root) {
        var text = root.name + ': ' + human(root.status) + '; ' + number(root.inspected_records) + ' of ' + number(root.eligible_records) + ' eligible records inspected';
        if (root.publication_allowed === false) text += '; publication held';
        if (root.reason) text += '. ' + root.reason;
        roots.append(node('li', text));
      });
      li.append(roots); list.append(li);
    });
    fragment.append(list);
    if (reply.term_build_id) fragment.append(node('p', 'Entity index ' + reply.term_build_id, 'gap-note'));
    $('term-coverage').replaceChildren(fragment);
  }
  async function loadTerms() {
    if (!ready || termsLoading) return;
    var version = ++termsVersion, snapshotVersion = loadVersion;
    termsLoading = true; termsReady = false; termRecognition = null;
    $('terms-content').hidden = true; $('terms-retry').hidden = true;
    if ($('pairs-network')) $('pairs-network').hidden = true;
    $('pairs-table').hidden = true; $('pairs-empty').hidden = true; $('pairs-status').hidden = false;
    $('pairs-status').textContent = 'Co-occurrence will appear when entity occurrences load.';
    $('terms-status').className = ''; $('terms-status').textContent = 'Loading entity occurrences…';
    $('term-coverage').textContent = 'Loading vocabulary coverage…';
    if ($('matrix-wrap')) $('matrix-wrap').hidden = true;
    if ($('matrix-status')) { $('matrix-status').hidden = false; $('matrix-status').textContent = 'Loading entity occurrences to build the 16 × 16 cross-pollination matrix…'; }
    if (state.term || state.term2) query(false);
    try {
      if (!manifest.terms || typeof manifest.terms.url !== 'string' || !/^[a-f0-9]{64}$/.test(manifest.terms.sha256)) throw new Error('This snapshot does not provide a valid entity occurrence index.');
      var reply = await request('terms-init', {url: new URL(manifest.terms.url, manifestURL).href, sha256: manifest.terms.sha256, build_id: manifest.build_id});
      if (version !== termsVersion || snapshotVersion !== loadVersion) return;
      termsReady = true; termsLoading = false;
      termRecognition = {asset: {url: manifest.terms.url, sha256: manifest.terms.sha256},
        term_build_id: reply.term_build_id, vocabulary_sha256: reply.vocabulary_sha256, policy: reply.policy};
      termCoverage(reply);
      query(false);
    } catch (error) {
      if (version !== termsVersion || snapshotVersion !== loadVersion) return;
      termsLoading = false;
      $('terms-status').className = 'gap-error';
      $('terms-status').textContent = 'Entity occurrences could not load: ' + error.message + ' Ordinary search remains available. Selected entity filters require this index.';
      $('term-coverage').textContent = 'Vocabulary coverage is unavailable until the entity index loads successfully.';
      $('terms-retry').hidden = false;
      $('pairs-status').textContent = 'Co-occurrence is unavailable. Retry entity occurrences above.';
      if ($('matrix-status')) $('matrix-status').textContent = 'Cross-Mech vocabulary matrix is unavailable until entity occurrences load. Retry below.';
      if (state.term || state.term2) query(false);
      navigatePendingSection();
    }
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
    if (item.has_experiments || (item.proposed_experiments && item.proposed_experiments.length)) {
      row.append(node('span', 'Has proposed experiments', 'gap-badge gap-badge-accent'));
    }
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
      if (item.posed_date) meta.append(document.createTextNode(' · posed ' + item.posed_date));
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
    var version = ++queryVersion; lastTotal = 0; exportButtons(); renderActiveFilters();
    if (embedding) embedding.invalidateScope('Updating the map to match the current filters…');
    $('results').replaceChildren(); $('pagination').hidden = true; $('result-status').textContent = 'Searching all indexed discussions…';
    $('view-note').textContent = state.view === 'gaps' ? 'Knowledge gaps shows KNOWLEDGE_GAP and HUMAN_MODEL_MISMATCH entries, excluding identified proposals awaiting review. Lifecycle and other filters also apply.' : state.view === 'candidates' ? 'Candidates are identified proposals requiring review, including those stored in native records. Their citations do not establish the proposed claim.' : 'All discussion kinds and both recorded and candidate entries are available. Lifecycle and other filters still apply.';
    showTermSelection();
    if ((state.term || state.term2) && !termsReady) {
      if (embedding) embedding.invalidateScope('Selected entity filters require the entity index. Retry entity occurrences or clear the selection; no broader map points are shown.');
      $('result-status').textContent = termsLoading ? 'Loading entity occurrences before applying the selected entity filters…' : 'Selected entity filters could not be applied. Retry entity occurrences or clear the entity selection. No broader results are shown.';
      if (focus) $('result-status').focus();
      navigatePendingSection();
      return;
    }
    try {
      var reply = await request('query', {state: state});
      if (version !== queryVersion) return;
      var result = reply.result; state.page = result.page; historyState(true);
      lastTotal = result.total;
      renderRows(result);
      renderAnalyses(result.analysis);
      renderTerms(result.term_summary, result.selected_terms);
      if (analyticsReady) renderAnalyticsSidecar();
      exportButtons();
      if (embedding) {
        if (Array.isArray(result.match_ids)) embedding.setScope(result.match_ids, state);
        else embedding.invalidateScope('The map filter scope is unavailable. Reload to update the search worker.');
      }
      if (focus) $('result-status').focus();
      navigatePendingSection();
    } catch (error) { if (version === queryVersion) fail(error.message); }
  }
  function closeDetail(restore, update) {
    detailVersion++; $('detail').hidden = true; $('detail-body').replaceChildren();
    state.gap = ''; if (update) historyState(false);
    if (embedding) embedding.setSelection('');
    if (restore) { if (lastDetailButton && lastDetailButton.isConnected) lastDetailButton.focus(); else $('result-status').focus(); }
  }
  function renderDetail(item) {
    $('detail-title').textContent = item.prompt || 'Discussion';
    var body = $('detail-body'); body.replaceChildren(badges(item));
    body.append(node('p', (item.record_label || item.record_id) + ' · ' + item.record_id));
    if (embedding) {
      var context = node('div', null, 'gap-map-detail-context'); context.dataset.gapId = item.id;
      embedding.appendContext(item.id, context); body.append(context);
    }
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
    var permalinkURL = stateURL(Object.assign({}, state, {gap: item.id}));
    permalinkURL.hash = '';
    var permalink = node('a', 'Link to this discussion'); permalink.href = permalinkURL;
    sourceLinks.append(document.createTextNode(' · '), permalink); body.append(sourceLinks);
    var provenance = node('dl'); field(provenance, 'Repository', source.repository); field(provenance, 'Revision', source.revision);
    field(provenance, 'Source file', source.path); field(provenance, 'Source SHA-256', source.sha256); field(provenance, 'Licence', values(source.license));
    body.append(provenance);
  }
  async function openDetail(id, update, focus) {
    var version = ++detailVersion;
    state.gap = id; if (update) historyState(false);
    if (embedding) embedding.setSelection(id);
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
    });
    (manifest.infrastructure || []).forEach(function (member) {
      var infraBox = node('div', null, 'gap-coverage-infra');
      infraBox.append(node('h3', member.name + ' — shared curation infrastructure (no scientific corpus)'));
      infraBox.append(link('Repository ' + member.repository, member.repository_url));
      infraBox.append(node('p', member.description));
      infraBox.append(node('p', member.scope_note, 'gap-note'));
      var meta = node('p', null, 'gap-note');
      meta.append(document.createTextNode('Scope checked ' + member.checked_on + ' · '), link('Pinned fleet declaration', member.evidence_url));
      infraBox.append(meta);
      frag.append(infraBox);
    });
    $('coverage').replaceChildren(frag);
  }
  async function exportMatches(format) {
    if (!ready || exporting) return;
    exporting = true; exportButtons(); var snapshot = manifest, captured = Object.assign({}, state);
    var recognition = termRecognition, recognitionVersion = termsVersion;
    $('export-status').textContent = 'Preparing all filtered results with full details…';
    try {
      var reply = await request('export', {state: captured});
      var keys = Array.from(new Set(reply.result.all.map(shardKey)));
      var details = new Map(await Promise.all(keys.map(async function (key) { return [key, await detailShard(key)]; })));
      if (snapshot !== manifest) throw new Error('The snapshot changed during export. Please retry.');
      if (recognition !== termRecognition || recognitionVersion !== termsVersion) throw new Error('The entity index changed during export. Please retry.');
      var items = reply.result.all.map(function (row) { return getDetail(details.get(shardKey(row)), row.id); });
      var content = format === 'csv' ? core.csv(items) : JSON.stringify({schema_version: 1, build_id: snapshot.build_id,
        filters: captured, sources: snapshot.sources, infrastructure: snapshot.infrastructure || [],
        term_recognition: recognition, selected_entities: reply.result.selected_terms, items: items}, null, 2);
      var blob = new Blob([content], {type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json'});
      var url = URL.createObjectURL(blob), a = node('a'); a.href = url; a.download = 'mech-discussions.' + format; document.body.append(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      $('export-status').textContent = 'Exported all ' + number(items.length) + ' matching discussions. Filters and pagination did not truncate the export.';
    } catch (error) { $('export-status').textContent = 'Export failed; no partial file was downloaded. ' + error.message; }
    finally { exporting = false; exportButtons(); }
  }
  async function load() {
    var version = ++loadVersion; ready = false; queryVersion++; detailVersion++; stopWorker(); shards.clear();
    if (embedding) embedding.reset(null, []);
    resetStats('Gap counts will appear when the search index loads.');
    app.querySelectorAll('[data-gap-interactive]').forEach(function (a) { a.hidden = true; });
    termsVersion++; termsReady = false; termsLoading = false; termRecognition = null; termInfo.clear();
    analyticsVersion++; analyticsReady = false; analyticsLoading = false; analyticsDoc = null;
    lastAnalysis = null; lastTermSummary = null; lastSelectedTerms = [];
    $('terms-content').hidden = true; $('terms-retry').hidden = true;
    if ($('analytics-content')) $('analytics-content').hidden = true;
    if ($('analytics-retry')) $('analytics-retry').hidden = true;
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
      if (embedding) embedding.reset(manifest, reply.map_items);
      renderStats(reply.gap_counts);
      var names = manifest.sources.map(function (source) { return source.name; }).sort();
      [
        ['mech', names, 1],
        ['vocab', names, 1],
        ['kind', reply.facets.kind || [], 1],
        ['status', reply.facets.status || [], 2],
        ['review', reply.facets.review_state || [], 1],
        ['layer', reply.facets.layer || [], 1],
        ['stance', reply.facets.stance || [], 1]
      ].forEach(function (entry) {
        var select = $(entry[0]);
        if (!select) return;
        while (select.options.length > entry[2]) select.remove(entry[2]);
        entry[1].forEach(function (value) {
          var key = entry[0] === 'review' ? 'review_state' : entry[0];
          var countVal = reply.facet_counts[key] ? reply.facet_counts[key][value] : 0;
          var labelText = ['mech', 'vocab'].includes(entry[0]) ? value :
            (entry[0] === 'stance' && value === 'none' ? 'no cited evidence' :
             entry[0] === 'layer' && value === 'unattached' ? 'unattached' : human(value)) + ' (' + number(countVal) + ')';
          var option = node('option', labelText); option.value = value; select.append(option);
        });
      });
      var expSelect = $('experiments');
      if (expSelect && reply.facet_counts.experiments) {
        while (expSelect.options.length > 1) expSelect.remove(1);
        [['yes', 'Has proposed experiments'], ['no', 'No proposed experiments']].forEach(function (pair) {
          var opt = node('option', pair[1] + ' (' + number(reply.facet_counts.experiments[pair[0]] || 0) + ')');
          opt.value = pair[0]; expSelect.append(opt);
        });
      }
      state = readState(); syncControls(); coverage();
      var infraNames = (manifest.infrastructure || []).map(function (m) { return m.name; });
      var infraText = infraNames.length ? ' + ' + number(infraNames.length) + ' infrastructure project (' + infraNames.join(', ') + ')' : '';
      $('snapshot').textContent = number(reply.total) + ' indexed discussions · ' + number(reply.candidates) + ' candidates awaiting review · ' + number(manifest.sources.length) + ' corpus Mechs' + infraText + ' accounted for. Snapshot ' + manifest.build_id.slice(0, 12) + '. Inspect coverage for source dates and limitations.';
      ready = true; $('controls').disabled = false; $('app').hidden = false; $('load-status').hidden = true;
      app.querySelectorAll('[data-gap-interactive]').forEach(function (a) { a.hidden = false; });
      query(false); loadTerms(); loadAnalytics(); if (state.gap) openDetail(state.gap, false, false);
    } catch (error) { if (version === loadVersion) fail(error.message); }
  }
  function changeFilters() {
    if (!ready) return;
    var next = Object.assign({}, state, {q: $('query').value, page: 1, gap: ''});
    ['view', 'mech', 'kind', 'status', 'review', 'layer', 'stance', 'experiments', 'sort'].forEach(function (key) {
      if ($(key)) next[key] = $(key).value;
    });
    next = core.normalize(next);
    // Enter in a search input can dispatch both submit and search (#580).
    // Apply that state once; the native clear control still updates the query.
    if (Object.keys(core.defaults).every(function (key) { return next[key] === state[key]; })) return;
    closeDetail(false, false);
    state = next; renderActiveFilters(); historyState(false); query(false);
  }
  $('form').addEventListener('submit', function (event) { event.preventDefault(); changeFilters(); });
  ['view', 'mech', 'kind', 'status', 'review', 'layer', 'stance', 'experiments', 'sort'].forEach(function (key) {
    if (!$(key)) return;
    $(key).addEventListener('change', function () {
      if (key === 'view') { $('kind').value = ''; $('status').value = $('view').value === 'gaps' ? 'active' : ''; }
      changeFilters();
    });
  });
  $('query').addEventListener('search', changeFilters);
  $('vocab').addEventListener('change', function () {
    if (!ready) return;
    var next = core.normalize(Object.assign({}, state, {vocab: $('vocab').value, term: '', term2: '', page: 1, gap: ''}));
    if (Object.keys(core.defaults).every(function (key) { return next[key] === state[key]; })) return;
    closeDetail(false, false); state = next; renderActiveFilters(); historyState(false); query(false);
  });
  $('breakdown-lens').addEventListener('change', function () { if (lastAnalysis) renderBreakdown(lastAnalysis); });
  $('matrix-mode').addEventListener('change', function () { if (lastAnalysis) renderVocabMatrix(lastAnalysis); });
  $('refs-mode').addEventListener('change', function () { if (lastAnalysis) renderRefs(lastAnalysis); });
  $('blindspot-scope').addEventListener('change', renderBlindspots);
  $('pairs-metric').addEventListener('change', function () { if (lastTermSummary) renderPairsView(lastTermSummary); });
  $('analytics-retry').addEventListener('click', loadAnalytics);
  $('reset').addEventListener('click', function () { closeDetail(false, false); state = core.normalize({}); syncControls(); historyState(false); query(false); $('query').focus(); });
  $('prev').addEventListener('click', function () { state.page--; historyState(false); query(true); });
  $('next').addEventListener('click', function () { state.page++; historyState(false); query(true); });
  $('close-detail').addEventListener('click', function () { closeDetail(true, true); });
  $('retry').addEventListener('click', load);
  $('terms-retry').addEventListener('click', loadTerms);
  $('terms-clear').addEventListener('click', function () { selectTerms('', ''); });
  $('export-json').addEventListener('click', function () { exportMatches('json'); });
  $('export-csv').addEventListener('click', function () { exportMatches('csv'); });
  window.addEventListener('popstate', function () {
    if (!ready) return;
    var next = readState();
    // A section-only history entry does not need to rebuild the search view.
    if (Object.keys(core.defaults).every(function (key) { return next[key] === state[key]; })) return;
    state = next; pendingSection = location.hash; pendingSectionTarget = null; syncControls(); query(false);
    if (state.gap) openDetail(state.gap, false, false); else closeDetail(false, false);
  });
  app.querySelectorAll('.gap-section-nav a').forEach(function (anchor) {
    anchor.addEventListener('click', function (event) {
      if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); jumpToSection(anchor.hash.slice(1));
    });
  });
  window.addEventListener('hashchange', function () { pendingSection = location.hash; pendingSectionTarget = null; navigatePendingSection(); });
  function cancelSectionRestore() { pendingSection = ''; pendingSectionTarget = null; }
  window.addEventListener('wheel', cancelSectionRestore, {passive: true});
  window.addEventListener('touchmove', cancelSectionRestore, {passive: true});
  window.addEventListener('keydown', function (event) {
    if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp', 'Home', 'End', ' '].includes(event.key)) cancelSectionRestore();
  });
  window.addEventListener('resize', sectionOffset);
  var siteHeader = document.querySelector('.site-header');
  if (siteHeader && window.ResizeObserver) new ResizeObserver(sectionOffset).observe(siteHeader);
  sectionOffset();
  load();
}());
