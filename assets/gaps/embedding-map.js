/* Pinned, precomputed discussion embeddings. No visitor-time model calls. */
(function (root, factory) {
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.GapEmbedding = api;
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var HASH = /^[a-f0-9]{64}$/;
  var PALETTE = ['#4477aa', '#cc6677', '#228833', '#aa3377', '#66ccee', '#ee7733', '#999933', '#332288', '#44aa99', '#882255', '#661100', '#6699cc', '#aa4499', '#117733', '#ddaa33', '#777777'];
  var STANCE_ORDER = ['REFUTE', 'SUPPORT', 'PARTIAL', 'NO_EVIDENCE', 'UNSPECIFIED'];
  var TOP_LAYERS = ['components', 'ecological_interactions', 'causal_graphs', 'record', 'identifier', 'taxonomy'];

  function prepare(doc, manifest, items) {
    if (!doc || doc.schema_version !== 1 || doc.build_id !== manifest.build_id ||
        !manifest.terms || doc.terms_sha256 !== manifest.terms.sha256 || !HASH.test(doc.inputs_sha256 || '')) {
      throw new Error('The embedding map does not match this discussion and entity snapshot.');
    }
    if (!Array.isArray(doc.points) || !Array.isArray(doc.records) || !Array.isArray(doc.contexts) ||
        !doc.model || !doc.projection || !doc.coverage) throw new Error('Invalid embedding map metadata.');
    var index = new Map(), points = new Map(), records = new Map(), contexts = new Map(), hashCounts = new Map();
    items.forEach(function (item) {
      if (!item || !item.id || index.has(item.id)) throw new Error('Invalid map discussion index.');
      index.set(item.id, item);
    });
    doc.points.forEach(function (point) {
      if (!point || !index.has(point.id) || points.has(point.id) || !Number.isFinite(point.x) || !Number.isFinite(point.y) ||
          !HASH.test(point.input_sha256 || '') || !Number.isSafeInteger(point.token_count) || point.token_count < 1 ||
          !Number.isSafeInteger(point.chunk_count) || point.chunk_count < 1 || point.chunk_count > point.token_count ||
          !Array.isArray(point.neighbors) || point.neighbors.length > 15) throw new Error('Invalid, duplicate or unknown embedding point.');
      points.set(point.id, point);
      hashCounts.set(point.input_sha256, (hashCounts.get(point.input_sha256) || 0) + 1);
    });
    if (points.size !== index.size) throw new Error('The embedding map does not cover the complete discussion index.');
    doc.points.forEach(function (point) {
      var seen = new Set();
      point.neighbors.forEach(function (neighbor) {
        if (!neighbor || !points.has(neighbor.id) || neighbor.id === point.id || seen.has(neighbor.id) ||
            !Number.isFinite(neighbor.cosine_similarity) || Math.abs(neighbor.cosine_similarity) > 1.000001) {
          throw new Error('Invalid original-vector neighbor reference.');
        }
        seen.add(neighbor.id);
      });
    });
    doc.records.forEach(function (record) {
      if (!record || typeof record.id !== 'string' || !record.id || records.has(record.id) ||
          typeof record.label !== 'string' || typeof record.description !== 'string' ||
          !Array.isArray(record.definition_sources) || record.definition_sources.some(function (citation) { return typeof citation !== 'string' || !citation.trim(); }) ||
          !['present', 'missing_native_field', 'unsupported_field'].includes(record.description_status) ||
          !record.source || typeof record.source.url !== 'string') throw new Error('Invalid embedding source record.');
      records.set(record.id, record);
    });
    doc.contexts.forEach(function (context) {
      if (!context || !points.has(context.id) || contexts.has(context.id) || !Array.isArray(context.record_ids) ||
          !Array.isArray(context.matched_terms) || new Set(context.record_ids).size !== context.record_ids.length ||
          context.record_ids.some(function (id) { return !records.has(id); })) throw new Error('Invalid embedding context.');
      var seen = new Set();
      context.matched_terms.forEach(function (term) {
        if (!term || typeof term.term_id !== 'string' || !term.term_id || seen.has(term.term_id) ||
            !Number.isSafeInteger(term.occurrence_count) || term.occurrence_count < 1 || !Array.isArray(term.record_ids) ||
            new Set(term.record_ids).size !== term.record_ids.length ||
            term.record_ids.some(function (id) { return !context.record_ids.includes(id); })) throw new Error('Invalid matched entity context.');
        seen.add(term.term_id);
      });
      contexts.set(context.id, context);
    });
    if (contexts.size !== points.size) throw new Error('Embedding contexts are incomplete.');
    var duplicateHashes = new Set();
    hashCounts.forEach(function (cnt, sha) { if (cnt > 1) duplicateHashes.add(sha); });
    var xs = doc.points.map(function (p) { return p.x; }), ys = doc.points.map(function (p) { return p.y; });
    var minX = xs.length ? Math.min.apply(null, xs) : -1, maxX = xs.length ? Math.max.apply(null, xs) : 1;
    var minY = ys.length ? Math.min.apply(null, ys) : -1, maxY = ys.length ? Math.max.apply(null, ys) : 1;
    return {document: doc, index: index, points: points, records: records, contexts: contexts,
      duplicateHashes: duplicateHashes,
      bounds: {minX: minX, maxX: maxX, minY: minY, maxY: maxY}};
  }
  function pointCategory(data, point, colorField) {
    var item = data.index.get(point.id) || {};
    if (colorField === 'stance') {
      var stances = Array.isArray(item.evidence_stances) ? item.evidence_stances : [];
      if (!stances.length) return 'No cited evidence';
      for (var i = 0; i < STANCE_ORDER.length; i++) {
        if (stances.includes(STANCE_ORDER[i])) return STANCE_ORDER[i];
      }
      return stances[0];
    }
    if (colorField === 'layer') {
      var layers = Array.isArray(item.attach_layers) ? item.attach_layers : [];
      if (!layers.length) return 'Unattached';
      for (var j = 0; j < TOP_LAYERS.length; j++) {
        if (layers.includes(TOP_LAYERS[j])) return TOP_LAYERS[j];
      }
      return 'Other attached slot';
    }
    if (colorField === 'experiments') {
      return item.has_experiments ? 'Has proposed experiments' : 'No proposed experiments';
    }
    if (colorField === 'bridge') {
      if (data.duplicateHashes && data.duplicateHashes.has(point.input_sha256)) return 'Duplicate input text';
      var neighbors = point.neighbors || [];
      if (neighbors.length) {
        var first = data.index.get(neighbors[0].id);
        if (first && first.mech !== item.mech && neighbors[0].cosine_similarity >= 0.75) {
          return 'Top-1 neighbor in another Mech (≥0.75)';
        }
        var top5Cross = neighbors.slice(0, 5).some(function (n) {
          var target = data.index.get(n.id);
          return target && target.mech !== item.mech && n.cosine_similarity >= 0.70;
        });
        if (top5Cross) return 'Top-5 neighbor in another Mech (≥0.70)';
      }
      return 'Same-Mech neighborhood';
    }
    return item[colorField] || '';
  }
  function crossMechArcs(data, ids, minCosine) {
    var threshold = Number.isFinite(minCosine) ? minCosine : 0.78;
    var active = new Set(ids), seen = new Map();
    ids.forEach(function (id) {
      var point = data.points.get(id), item = data.index.get(id);
      if (!point || !item) return;
      (point.neighbors || []).slice(0, 5).forEach(function (neighbor) {
        if (!active.has(neighbor.id) || neighbor.cosine_similarity < threshold) return;
        var other = data.index.get(neighbor.id);
        if (!other || other.mech === item.mech) return;
        var a = id < neighbor.id ? id : neighbor.id, b = id < neighbor.id ? neighbor.id : id;
        var key = a + '\u0000' + b;
        if (!seen.has(key) || neighbor.cosine_similarity > seen.get(key).cosine_similarity) {
          seen.set(key, {a: a, b: b, mech_a: data.index.get(a).mech, mech_b: data.index.get(b).mech,
            cosine_similarity: neighbor.cosine_similarity});
        }
      });
    });
    return Array.from(seen.values()).sort(function (x, y) {
      return y.cosine_similarity - x.cosine_similarity || (x.a < y.a ? -1 : x.a > y.a ? 1 : 0);
    }).slice(0, 120);
  }
  function missingSourcesNote(manifest, presentMechs) {
    if (!manifest || !Array.isArray(manifest.sources)) return '';
    var parts = [];
    manifest.sources.forEach(function (source) {
      if (presentMechs.has(source.name)) return;
      var status = source.coverage_status === 'complete' ? (source.items ? '0 matching filters' : '0 items in corpus') :
        source.coverage_status;
      parts.push(source.name + ' (' + status + ')');
    });
    if (Array.isArray(manifest.infrastructure)) {
      manifest.infrastructure.forEach(function (member) {
        parts.push(member.name + ' (infrastructure, no corpus)');
      });
    }
    return parts.length ? 'Public fleet members without plotted points in this view: ' + parts.join(' · ') + '.' : '';
  }
  function matchingPoints(data, ids) {
    var seen = new Set();
    return ids.map(function (id) {
      if (!data.points.has(id) || seen.has(id)) throw new Error('The map scope contains unknown or duplicate discussions.');
      seen.add(id); return data.points.get(id);
    });
  }
  function exportDocument(data, ids, filters) {
    var points = matchingPoints(data, ids), contexts = ids.map(function (id) { return data.contexts.get(id); });
    var recordIds = new Set(contexts.flatMap(function (context) { return context.record_ids; }));
    return {schema_version: 1, build_id: data.document.build_id, terms_sha256: data.document.terms_sha256,
      inputs_sha256: data.document.inputs_sha256, model: data.document.model, projection: data.document.projection,
      filters: Object.assign({}, filters), point_scope: 'All filtered discussions, independent of result pagination',
      neighbor_scope: 'Global original-vector cosine neighbors; neighbors may be outside the current filters',
      points: points.map(function (point) { return Object.assign({}, data.index.get(point.id), point); }), contexts: contexts,
      records: data.document.records.filter(function (record) { return recordIds.has(record.id); })};
  }
  function csv(document, csvCell) {
    // Validated numeric coordinates remain numeric; untrusted text keeps formula protection (#612).
    function cell(value) { return Number.isFinite(value) ? String(value) : csvCell(value); }
    var fields = ['id', 'mech', 'record_id', 'record_label', 'prompt', 'x', 'y', 'input_sha256', 'token_count', 'chunk_count'];
    var contexts = new Map(document.contexts.map(function (context) { return [context.id, context]; }));
    var header = fields.concat(['matched_record_ids', 'build_id', 'terms_sha256', 'inputs_sha256', 'filters', 'model', 'projection']);
    return [header.map(csvCell).join(',')].concat(document.points.map(function (point) {
      return fields.map(function (field) { return point[field]; }).concat([contexts.get(point.id).record_ids,
        document.build_id, document.terms_sha256, document.inputs_sha256, document.filters, document.model, document.projection]).map(cell).join(',');
    })).join('\r\n') + '\r\n';
  }
  function create(options) {
    var root = options.root, $ = function (name) { return root.querySelector('#gap-map-' + name); };
    var generation = 0, manifest = null, items = [], data = null, loading = false, attempted = false, ids = [], scopeReady = false, scopeMessage = '', filters = {}, selected = '';
    var view = {x: 0, y: 0, width: 900, height: 520}, svg = null, circles = new Map(), drag = null;
    function node(tag, text, className) {
      var el = document.createElement(tag); if (text != null) el.textContent = String(text); if (className) el.className = className; return el;
    }
    function svgNode(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
    function label(item) { return (item.prompt || 'Untitled discussion') + ' — ' + item.mech + ' / ' + item.record_id; }
    function count(value) { return Number(value).toLocaleString('en'); }
    function readable(value, field) {
      if (field === 'mech' || field === 'experiments' || field === 'bridge') return value || 'Unspecified';
      if (value === 'No cited evidence' || value === 'Unattached' || value === 'Other attached slot') return value;
      return value ? String(value).replace(/_/g, ' ').toLowerCase() : 'Unspecified';
    }
    function sourceLink(text, url) { var href = options.safeURL(url), a = node(href ? 'a' : 'span', text); if (href) { a.href = href; a.rel = 'noopener noreferrer'; } return a; }
    function controls() {
      var usable = Boolean(data && scopeReady);
      $('controls').disabled = !usable; $('export-json').disabled = !usable || !ids.length; $('export-csv').disabled = !usable || !ids.length;
    }
    function failed(error) {
      loading = false; data = null;
      $('content').hidden = true; $('selection').hidden = true; $('status').className = 'gap-error';
      $('status').textContent = 'Embedding map could not load: ' + error.message + ' Search and discussion details remain available.';
      $('retry').hidden = false; controls(); if (options.onLayout) options.onLayout();
    }
    function safeDraw() { try { draw(); } catch (error) { failed(error); } }
    function appendRecords(container, id) {
      var context = data.contexts.get(id);
      container.append(node('h4', 'Matched Mech entries used in the embedding'));
      if (!context.record_ids.length) container.append(node('p', 'No Mech entities were linked in this discussion. Its embedding uses the discussion text.'));
      context.record_ids.forEach(function (id) {
        var record = data.records.get(id), disclosure = node('details'), summary = node('summary', record.label + ' · ' + record.mech + ' / ' + record.record_id);
        disclosure.append(summary, node('p', record.description_status === 'present' ? record.description : 'No definition or description was available in the permitted native fields.', 'gap-map-description'));
        if (record.definition_sources.length) {
          var citations = node('ul');
          record.definition_sources.forEach(function (citation) {
            var row = node('li'); row.append(sourceLink(citation, options.referenceURL ? options.referenceURL(citation) : '')); citations.append(row);
          });
          disclosure.append(node('p', 'Definition sources'), citations);
        }
        disclosure.append(sourceLink('Pinned source record', record.source.url));
        var provenance = node('p', 'Definition field: ' + (record.description_field || 'unavailable') + ' · Source revision: ' + (record.source.revision || 'unspecified'), 'gap-note');
        disclosure.append(provenance); container.append(disclosure);
      });
    }
    function appendNeighbors(container, id) {
      var point = data.points.get(id), owner = data.index.get(id);
      container.append(node('h4', 'Nearest discussions by original-vector cosine similarity'),
        node('p', 'These neighbors use the complete embedding vectors across all discussions. They may be outside the current filters; proximity on the 2D map can differ.', 'gap-note'));
      var neighbors = node('ol');
      point.neighbors.forEach(function (neighbor) {
        var target = data.index.get(neighbor.id), row = node('li'), button = node('button', label(target)); button.type = 'button';
        button.addEventListener('click', function () { options.openDiscussion(neighbor.id, $('point')); });
        var cross = owner && target && owner.mech !== target.mech ? ' · cross-Mech (' + target.mech + ')' : '';
        row.append(button, document.createTextNode(' · ' + neighbor.cosine_similarity.toFixed(3) + cross + (ids.includes(neighbor.id) ? '' : ' · outside filters')));
        neighbors.append(row);
      });
      container.append(neighbors);
    }
    function appendContext(id, container) {
      container.replaceChildren(); container.hidden = !data || !data.points.has(id);
      if (container.hidden) return;
      var disclosure = node('details'), summary = node('summary', 'Matched Mech entries and embedding neighbors');
      disclosure.append(summary); appendRecords(disclosure, id); appendNeighbors(disclosure, id); container.append(disclosure);
    }
    function selection() {
      $('selection').replaceChildren();
      if (!data || !selected || !data.points.has(selected)) { $('selection').hidden = true; return; }
      var item = data.index.get(selected);
      $('selection').hidden = false;
      $('selection').append(node('h3', item.prompt || 'Selected discussion'), node('p', item.mech + ' · ' + item.record_id, 'gap-note'));
      if (!ids.includes(selected)) $('selection').append(node('p', 'This selected discussion is outside the current map filters.', 'gap-note'));
      var open = node('button', 'Open discussion and evidence'); open.type = 'button';
      open.addEventListener('click', function () { options.openDiscussion(selected, $('point')); }); $('selection').append(open);
      appendRecords($('selection'), selected); appendNeighbors($('selection'), selected);
    }
    function updateView() {
      if (!svg) return;
      svg.setAttribute('viewBox', [view.x, view.y, view.width, view.height].join(' '));
      // The SVG may be narrower than its viewBox or letterboxed on mobile (#616).
      // Its screen transform includes both responsive layout and the current zoom.
      var transform = svg.getScreenCTM(), scale = transform && Math.hypot(transform.a, transform.b);
      if (!Number.isFinite(scale) || scale <= 0) return;
      circles.forEach(function (circle, id) { circle.setAttribute('r', (id === selected ? 7 : 4) / scale); });
    }
    function pan(dx, dy) { view.x += dx * view.width; view.y += dy * view.height; updateView(); }
    function zoom(factor) {
      var width = Math.max(90, Math.min(1800, view.width * factor)), ratio = width / view.width;
      view.x += view.width * (1 - ratio) / 2; view.y += view.height * (1 - ratio) / 2;
      view.width = width; view.height *= ratio; updateView();
    }
    function resetView() { view = {x: 0, y: 0, width: 900, height: 520}; updateView(); }
    function draw() {
      controls(); $('plot').replaceChildren(); $('legend').replaceChildren(); circles.clear(); svg = null;
      var unshown = $('unshown');
      if (unshown) { unshown.hidden = true; unshown.textContent = ''; }
      if (!data || !scopeReady) { $('content').hidden = true; return; }
      var points = matchingPoints(data, ids), colorField = $('color').value;
      var showBridges = Boolean($('bridges') && $('bridges').checked);
      $('content').hidden = false;
      var arcs = showBridges ? crossMechArcs(data, ids, 0.78) : [];
      $('count').textContent = count(points.length) + ' of ' + count(data.points.size) + ' embedded discussions match the current filters' +
        (showBridges ? ' (' + count(arcs.length) + ' cross-Mech cosine arcs ≥ 0.78 shown)' : '') +
        '. Coordinates stay fixed when filters change.';
      $('empty').hidden = Boolean(points.length);
      var choices = [node('option', 'Choose a matching discussion')]; choices[0].value = '';
      ids.forEach(function (id) { var option = node('option', label(data.index.get(id))); option.value = id; choices.push(option); });
      $('point').replaceChildren.apply($('point'), choices); $('point').value = ids.includes(selected) ? selected : '';
      var allCats = new Set(), counts = new Map();
      data.points.forEach(function (pt) { allCats.add(pointCategory(data, pt, colorField)); });
      var categories = Array.from(allCats).sort();
      points.forEach(function (point) {
        var key = pointCategory(data, point, colorField);
        counts.set(key, (counts.get(key) || 0) + 1);
      });
      categories.forEach(function (category, index) {
        if (!counts.has(category)) return;
        var row = node('li'), swatch = node('span', null, 'gap-map-swatch'); swatch.style.backgroundColor = PALETTE[index % PALETTE.length]; swatch.setAttribute('aria-hidden', 'true');
        row.append(swatch, document.createTextNode(readable(category, colorField) + ' (' + count(counts.get(category)) + ')')); $('legend').append(row);
      });
      if (unshown && colorField === 'mech') {
        var presentMechs = new Set(Array.from(counts.keys()));
        var missingText = missingSourcesNote(manifest, presentMechs);
        if (missingText) { unshown.textContent = missingText; unshown.hidden = false; }
      }
      svg = svgNode('svg'); svg.setAttribute('aria-label', 'Embedding map of matching discussions'); svg.setAttribute('role', 'group');
      svg.setAttribute('tabindex', '0'); svg.setAttribute('aria-describedby', 'gap-map-help');
      var bounds = data.bounds, width = bounds.maxX - bounds.minX, height = bounds.maxY - bounds.minY;
      var scale = Math.min(820 / (width || 1), 440 / (height || 1));
      function px(x) { return 450 + (x - (bounds.minX + bounds.maxX) / 2) * scale; }
      function py(y) { return 260 - (y - (bounds.minY + bounds.maxY) / 2) * scale; }
      if (arcs.length) {
        var arcGroup = svgNode('g'); arcGroup.setAttribute('class', 'gap-map-arcs'); arcGroup.setAttribute('aria-hidden', 'true');
        arcs.forEach(function (arc) {
          var pa = data.points.get(arc.a), pb = data.points.get(arc.b), line = svgNode('line');
          line.setAttribute('x1', px(pa.x)); line.setAttribute('y1', py(pa.y));
          line.setAttribute('x2', px(pb.x)); line.setAttribute('y2', py(pb.y));
          line.setAttribute('class', 'gap-map-arc');
          arcGroup.append(line);
        });
        svg.append(arcGroup);
      }
      points.forEach(function (point, index) {
        var item = data.index.get(point.id), circle = svgNode('circle'), cat = pointCategory(data, point, colorField);
        circle.dataset.gapId = point.id; circle.setAttribute('cx', px(point.x));
        circle.setAttribute('cy', py(point.y));
        circle.setAttribute('fill', PALETTE[categories.indexOf(cat) % PALETTE.length]);
        circle.setAttribute('class', 'gap-map-point' + (point.id === selected ? ' is-selected' : ''));
        circle.setAttribute('role', 'button'); circle.setAttribute('aria-label', label(item));
        circle.setAttribute('tabindex', point.id === selected || (!ids.includes(selected) && index === 0) ? '0' : '-1');
        var title = svgNode('title'); title.textContent = label(item) + ' [' + readable(cat, colorField) + ']'; circle.append(title);
        circle.addEventListener('click', function () { options.openDiscussion(point.id, $('point')); });
        circle.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); options.openDiscussion(point.id, $('point')); }
          else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key)) {
            event.preventDefault(); event.stopPropagation();
            var next = event.key === 'Home' ? 0 : event.key === 'End' ? points.length - 1 :
              (index + (['ArrowRight', 'ArrowDown'].includes(event.key) ? 1 : -1) + points.length) % points.length;
            circles.forEach(function (target) { target.setAttribute('tabindex', '-1'); });
            var target = circles.get(points[next].id); target.setAttribute('tabindex', '0'); target.focus();
          }
        });
        circles.set(point.id, circle); svg.append(circle);
      });
      svg.addEventListener('keydown', function (event) {
        if (event.target !== svg) return;
        var actions = {ArrowLeft: function () { pan(-.1, 0); }, ArrowRight: function () { pan(.1, 0); },
          ArrowUp: function () { pan(0, -.1); }, ArrowDown: function () { pan(0, .1); }, '+': function () { zoom(.8); },
          '=': function () { zoom(.8); }, '-': function () { zoom(1.25); }, '0': resetView};
        if (actions[event.key]) { event.preventDefault(); actions[event.key](); }
      });
      svg.addEventListener('pointerdown', function (event) {
        if (event.target !== svg || event.button !== 0) return;
        drag = {id: event.pointerId, x: event.clientX, y: event.clientY}; svg.setPointerCapture(event.pointerId);
      });
      svg.addEventListener('pointermove', function (event) {
        if (!drag || drag.id !== event.pointerId) return;
        var scale = view.width / svg.getBoundingClientRect().width;
        view.x -= (event.clientX - drag.x) * scale; view.y -= (event.clientY - drag.y) * scale;
        drag.x = event.clientX; drag.y = event.clientY; updateView();
      });
      ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(function (name) { svg.addEventListener(name, function () { drag = null; }); });
      $('plot').append(svg); updateView(); selection();
    }
    function reset(nextManifest, nextItems) {
      generation++; manifest = nextManifest; items = nextItems || []; data = null; loading = false; attempted = false; ids = []; scopeReady = false; selected = ''; drag = null; svg = null; circles.clear();
      $('content').hidden = true; $('selection').hidden = true; $('plot').replaceChildren(); $('retry').hidden = true;
      if ($('unshown')) { $('unshown').hidden = true; $('unshown').textContent = ''; }
      $('load').hidden = false; $('load').disabled = !manifest || !manifest.embedding;
      var compressedBytes = manifest && manifest.sizes && manifest.sizes.embedding_gzip_bytes;
      $('load').textContent = 'Load embedding map' + (Number.isSafeInteger(compressedBytes) && compressedBytes > 0 ?
        ' (about ' + (compressedBytes / 1048576).toFixed(1) + ' MiB compressed)' : '');
      $('status').className = ''; $('status').textContent = manifest && manifest.embedding ? 'Load the embedding map to explore these discussions by their combined text.' : 'This snapshot does not provide an embedding map.';
      $('export-status').textContent = ''; resetView(); controls();
    }
    async function load() {
      if (loading || data || !manifest || !manifest.embedding) return;
      var version = ++generation; loading = true; attempted = true; $('load').hidden = true; $('retry').hidden = true;
      $('status').className = ''; $('status').textContent = 'Loading embedding map…';
      try {
        var doc = await options.loadDocument(); if (version !== generation) return;
        data = prepare(doc, manifest, items); loading = false;
        $('status').textContent = scopeReady ? 'Embedding map loaded.' : scopeMessage;
        var coverage = doc.input_coverage || doc.coverage;
        var coverageText = Number.isSafeInteger(coverage.discussions_with_descriptions) ?
          ' Native descriptions are available in ' + count(coverage.discussions_with_descriptions) + ' discussion inputs; ' +
          count(coverage.label_only_matched_discussions) + ' use matched labels without native descriptions, and ' +
          count(coverage.gap_text_only_discussions) + ' use discussion text alone.' : '';
        var overlap = doc.diagnostics && doc.diagnostics.neighbor_overlap_k15 && doc.diagnostics.neighbor_overlap_k15.mean;
        var overlapText = Number.isFinite(overlap) && overlap >= 0 && overlap <= 1 ?
          ' The 2D map retains an average of ' + (overlap * 100).toFixed(1) +
          '% of the original top-15 neighbors; inspect the original-vector neighbor list for each selected discussion.' : '';
        $('method').textContent = 'Model: ' + (doc.model.name || doc.model.model_id || doc.model.id || 'See export metadata') +
          '. Projection: ' + (doc.projection.method || doc.projection.name || 'See export metadata') +
          '. Combined discussion text and matched native record definitions are embedded once; filters do not change the projection.' + coverageText + overlapText;
        $('provenance').textContent = JSON.stringify({model: doc.model, projection: doc.projection, diagnostics: doc.diagnostics, coverage: doc.coverage, input_coverage: doc.input_coverage}, null, 2);
        draw(); if (options.onLayout) options.onLayout();
      } catch (error) {
        if (version !== generation) return; failed(error);
      }
    }
    function setScope(nextIds, nextFilters) {
      ids = nextIds.slice(); filters = Object.assign({}, nextFilters); scopeReady = true; selected = filters.gap || '';
      if (data) { $('status').className = ''; $('status').textContent = 'Embedding map loaded.'; safeDraw(); }
    }
    function invalidateScope(message) {
      scopeReady = false; ids = []; scopeMessage = message; $('content').hidden = true; $('selection').hidden = true;
      $('export-status').textContent = ''; if (data) $('status').textContent = message; controls();
    }
    function setSelection(id) { selected = id || ''; filters.gap = selected; if (data && scopeReady) safeDraw(); }
    function download(format) {
      if (!data || !scopeReady || !ids.length) return;
      try {
        var payload = exportDocument(data, ids, filters), content = format === 'csv' ? csv(payload, options.csvCell) : JSON.stringify(payload, null, 2);
        var url = URL.createObjectURL(new Blob([content], {type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json'}));
        var a = node('a'); a.href = url; a.download = 'mech-discussion-map.' + format; document.body.append(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
        $('export-status').textContent = 'Exported all ' + count(ids.length) + ' filtered map points with embedding provenance.';
      } catch (error) { $('export-status').textContent = 'Map export failed: ' + error.message; }
    }
    $('load').addEventListener('click', load); $('retry').addEventListener('click', load);
    $('color').addEventListener('change', safeDraw);
    if ($('bridges')) $('bridges').addEventListener('change', safeDraw);
    $('point').addEventListener('change', function () { if ($('point').value) options.openDiscussion($('point').value, $('point')); });
    $('zoom-in').addEventListener('click', function () { zoom(.8); }); $('zoom-out').addEventListener('click', function () { zoom(1.25); });
    $('reset').addEventListener('click', resetView);
    [['left', -.1, 0], ['right', .1, 0], ['up', 0, -.1], ['down', 0, .1]].forEach(function (entry) { $(entry[0]).addEventListener('click', function () { pan(entry[1], entry[2]); }); });
    $('export-json').addEventListener('click', function () { download('json'); }); $('export-csv').addEventListener('click', function () { download('csv'); });
    if (window.ResizeObserver) {
      var resizeObserver = new window.ResizeObserver(updateView); resizeObserver.observe($('plot'));
    } else window.addEventListener('resize', updateView);
    return {reset: reset, load: load, setScope: setScope, invalidateScope: invalidateScope, setSelection: setSelection, appendContext: appendContext,
      ensureLoaded: function () { if (!attempted) load(); }, isLoading: function () { return loading; }};
  }
  return {prepare: prepare, pointCategory: pointCategory, crossMechArcs: crossMechArcs, missingSourcesNote: missingSourcesNote,
    matchingPoints: matchingPoints, exportDocument: exportDocument, csv: csv, create: create};
}));
