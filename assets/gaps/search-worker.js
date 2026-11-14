/* Complete-corpus search. Scientific details remain in separately verified shards. */
'use strict';
importScripts('search-core.js');
var prepared = null, byId = new Map();
self.onmessage = async function (event) {
  var message = event.data;
  try {
    if (message.type === 'init') {
      prepared = null;
      byId.clear();
      var url = new URL(message.url, self.location.href);
      if (url.origin !== self.location.origin) throw new Error('The search index must be on this site.');
      var response = await fetch(url.href, {cache: 'no-cache'});
      if (!response.ok) throw new Error('Search index request failed (' + response.status + ').');
      var bytes = await response.arrayBuffer();
      var digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(function (b) { return b.toString(16).padStart(2, '0'); }).join('');
      if (digest !== message.sha256) throw new Error('The search index does not match this snapshot. Reload or retry.');
      var doc = JSON.parse(new TextDecoder().decode(bytes));
      if (doc.schema_version !== 1 || doc.build_id !== message.build_id || !Array.isArray(doc.items)) throw new Error('The search index has an incompatible snapshot.');
      doc.items.forEach(function (item) {
        if (!item.id || byId.has(item.id)) throw new Error('The search index contains invalid or duplicate IDs.');
        byId.set(item.id, item);
      });
      prepared = GapSearch.prepare(doc.items);
      var facets = {}, facetCounts = {};
      ['mech', 'kind', 'status', 'review_state'].forEach(function (key) {
        facets[key] = Array.from(new Set(doc.items.map(function (item) { return item[key]; }).filter(Boolean))).sort();
        facetCounts[key] = Object.fromEntries(facets[key].map(function (value) {
          return [value, doc.items.filter(function (item) { return item[key] === value; }).length];
        }));
      });
      self.postMessage({type: 'ready', request: message.request, total: doc.items.length, facets: facets,
        facet_counts: facetCounts,
        candidates: doc.items.filter(function (item) { return item.lane === 'candidate'; }).length});
    } else {
      if (!prepared) throw new Error('The search index has not loaded.');
      if (message.type === 'item') {
        self.postMessage({type: 'item', request: message.request, item: byId.get(message.id) || null});
      } else if (message.type === 'query' || message.type === 'export') {
        var result = GapSearch.search(prepared, message.state);
        if (message.type === 'query') delete result.all;
        self.postMessage({type: message.type, request: message.request, result: result});
      }
    }
  } catch (error) {
    self.postMessage({type: 'error', request: message.request, operation: message.type, message: error.message});
  }
};
