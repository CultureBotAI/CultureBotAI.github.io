/* Complete-corpus search. Scientific details remain in separately verified shards. */
'use strict';
importScripts('search-core.js');
var prepared = null, byId = new Map(), termData = null, buildID = null, indexGeneration = 0, termsGeneration = 0;
async function verifiedAsset(message, label) {
  var url = new URL(message.url, self.location.href);
  if (url.origin !== self.location.origin) throw new Error(label + ' must be on this site.');
  var response = await fetch(url.href, {cache: 'no-cache'});
  if (!response.ok) throw new Error(label + ' request failed (' + response.status + ').');
  var bytes = await response.arrayBuffer();
  var digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
  if (digest !== message.sha256) throw new Error(label + ' does not match this snapshot. Reload or retry.');
  var doc = JSON.parse(new TextDecoder().decode(bytes));
  if (doc.schema_version !== 1 || doc.build_id !== message.build_id) throw new Error(label + ' has an incompatible snapshot.');
  return doc;
}
self.onmessage = async function (event) {
  var message = event.data;
  try {
    if (message.type === 'init') {
      var generation = ++indexGeneration; termsGeneration++;
      prepared = null;
      termData = null; buildID = null;
      byId.clear();
      var doc = await verifiedAsset(message, 'The search index');
      if (generation !== indexGeneration) throw new Error('This search load was superseded.');
      if (!Array.isArray(doc.items)) throw new Error('Invalid search items.');
      doc.items.forEach(function (item) {
        if (!item.id || byId.has(item.id)) throw new Error('The search index contains invalid or duplicate IDs.');
        byId.set(item.id, item);
      });
      prepared = GapSearch.prepare(doc.items);
      buildID = doc.build_id;
      var facets = {}, facetCounts = {};
      ['mech', 'kind', 'status', 'review_state'].forEach(function (key) {
        facets[key] = Array.from(new Set(doc.items.map(function (item) { return item[key]; }).filter(Boolean))).sort();
        facetCounts[key] = Object.fromEntries(facets[key].map(function (value) {
          return [value, doc.items.filter(function (item) { return item[key] === value; }).length];
        }));
      });
      var layerCounts = {}, stanceCounts = {}, expCounts = {yes: 0, no: 0};
      prepared.forEach(function (entry) {
        if (!entry.layers.length) layerCounts.unattached = (layerCounts.unattached || 0) + 1;
        else entry.layers.forEach(function (ly) { layerCounts[ly] = (layerCounts[ly] || 0) + 1; });
        if (!entry.stances.length) stanceCounts.none = (stanceCounts.none || 0) + 1;
        else entry.stances.forEach(function (st) { stanceCounts[st] = (stanceCounts[st] || 0) + 1; });
        if (entry.hasExperiments) expCounts.yes++; else expCounts.no++;
      });
      facets.layer = Object.keys(layerCounts).filter(function (k) { return k !== 'unattached'; }).sort(function (a, b) {
        return layerCounts[b] - layerCounts[a] || (a < b ? -1 : a > b ? 1 : 0);
      });
      if (layerCounts.unattached) facets.layer.push('unattached');
      facetCounts.layer = layerCounts;
      facets.stance = Object.keys(stanceCounts).filter(function (k) { return k !== 'none'; }).sort();
      if (stanceCounts.none) facets.stance.push('none');
      facetCounts.stance = stanceCounts;
      facetCounts.experiments = expCounts;
      self.postMessage({type: 'ready', request: message.request, total: doc.items.length, facets: facets,
        facet_counts: facetCounts, gap_counts: GapSearch.gapCounts(doc.items),
        map_items: prepared.map(function (entry) {
          var item = entry.item;
          return {id: item.id, prompt: item.prompt, record_label: item.record_label, record_id: item.record_id,
            mech: item.mech, kind: item.kind, status: item.status, review_state: item.review_state,
            evidence_stances: entry.stances, attach_layers: entry.layers, has_experiments: entry.hasExperiments};
        }),
        candidates: doc.items.filter(function (item) { return item.lane === 'candidate'; }).length});
    } else {
      if (!prepared) throw new Error('The search index has not loaded.');
      if (message.type === 'terms-init') {
        var termsToken = ++termsGeneration, searchToken = indexGeneration;
        termData = null;
        if (message.build_id !== buildID) throw new Error('Entity occurrences belong to a different search snapshot.');
        var terms = await verifiedAsset(message, 'Entity occurrences');
        if (termsToken !== termsGeneration || searchToken !== indexGeneration) throw new Error('This entity load was superseded.');
        termData = GapSearch.prepareTerms(terms, prepared);
        self.postMessage({type: 'terms-ready', request: message.request, total: termData.byId.size,
          policy: terms.policy || null, summary: terms.summary || null,
          vocabulary_sources: terms.vocabulary_sources || [], term_build_id: terms.term_build_id || null,
          vocabulary_sha256: terms.vocabulary_sha256 || null});
      } else if (message.type === 'item') {
        self.postMessage({type: 'item', request: message.request, item: byId.get(message.id) || null});
      } else if (message.type === 'query' || message.type === 'export') {
        var result = GapSearch.search(prepared, message.state, termData);
        if (message.type === 'query') {
          result.match_ids = result.all.map(function (item) { return item.id; });
          delete result.all;
        } else {
          delete result.term_summary;
          delete result.analysis;
        }
        self.postMessage({type: message.type, request: message.request, result: result});
      }
    }
  } catch (error) {
    self.postMessage({type: 'error', request: message.request, operation: message.type, message: error.message});
  }
};
