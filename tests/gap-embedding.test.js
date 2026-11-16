/* Embedding-map integrity and complete filtered exports; issue #609, 2026-11-15.
 * Inputs: synthetic snapshot/map assets. Outputs: node:test assertions only. */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {webcrypto, createHash} = require('node:crypto');
const map = require('../assets/gaps/embedding-map.js');
const core = require('../assets/gaps/search-core.js');

function fixture(count = 65) {
  const items = Array.from({length: count}, (_, n) => ({id: 'gap-' + n, prompt: n ? 'Question ' + n : '=formula',
    record_id: 'record-' + n, record_label: 'Record ' + n, mech: n % 2 ? 'TraitMech' : 'DUFMech',
    kind: 'KNOWLEDGE_GAP', status: 'OPEN', review_state: 'unspecified', lane: 'recorded'}));
  const manifest = {build_id: 'snapshot', terms: {sha256: 'a'.repeat(64)}};
  const doc = {schema_version: 1, build_id: 'snapshot', terms_sha256: manifest.terms.sha256,
    inputs_sha256: 'b'.repeat(64), model: {name: 'fixture'}, projection: {method: 'fixture'}, coverage: {},
    points: items.map((item, n) => ({id: item.id, x: n, y: -n, input_sha256: 'c'.repeat(64), token_count: 10, chunk_count: 1,
      neighbors: count > 1 ? [{id: items[(n + 1) % count].id, cosine_similarity: .5}] : []})),
    records: [{id: 'entity', label: 'A native definition', description: 'Source definition.', description_status: 'present', definition_sources: [],
      source: {url: 'https://github.com/CultureBotAI/DUFMech/blob/pin/example.yaml'}}],
    contexts: items.map(item => ({id: item.id, record_ids: ['entity'],
      matched_terms: [{term_id: 'term', record_ids: ['entity'], occurrence_count: 1}]}))};
  return {items, manifest, doc};
}

test('map binds exact entity index separately from the discussion snapshot', () => {
  const {items, manifest, doc} = fixture();
  assert.equal(map.prepare(doc, manifest, items).points.size, 65);
  assert.throws(() => map.prepare({...doc, terms_sha256: 'd'.repeat(64)}, manifest, items), /does not match/);
  assert.throws(() => map.prepare({...doc, build_id: 'stale'}, manifest, items), /does not match/);
  assert.throws(() => map.prepare({...doc, inputs_sha256: ''}, manifest, items), /does not match/);
});

test('malformed coordinates, unknown identities, context gaps and bad neighbors fail visibly', () => {
  const changes = [d => d.points[0].x = Infinity, d => d.points[0].id = 'unknown',
    d => d.points[1].id = d.points[0].id, d => d.points.pop(), d => d.contexts.pop(),
    d => d.contexts[0].record_ids.push('unknown'), d => d.points[0].token_count = 0,
    d => d.points[0].neighbors[0].id = d.points[0].id,
    d => d.points[0].neighbors[0].cosine_similarity = 2,
    d => d.records[0].definition_sources = [''],
    d => d.contexts[0].matched_terms[0].record_ids.push('entity')];
  for (const change of changes) {
    const {items, manifest, doc} = fixture(); change(doc);
    assert.throws(() => map.prepare(doc, manifest, items), /Invalid|complete/);
  }
});

test('filtered points retain fixed coordinates and complete exports exceed the result page', () => {
  const {items, manifest, doc} = fixture(), data = map.prepare(doc, manifest, items);
  const all = core.search(core.prepare(items), {view: 'all', status: '', page: 2});
  const ids = all.all.map(item => item.id), before = JSON.stringify(doc.points);
  assert.equal(all.rows.length, 15);
  const exported = map.exportDocument(data, ids, {view: 'all', page: 2});
  assert.equal(exported.points.length, 65);
  const subset = items.filter(item => item.mech === 'DUFMech').map(item => item.id);
  assert.deepEqual(map.matchingPoints(data, subset).map(point => [point.x, point.y]),
    doc.points.filter(point => subset.includes(point.id)).map(point => [point.x, point.y]));
  assert.equal(JSON.stringify(doc.points), before);
  assert.equal(exported.records.length, 1);
  assert.match(map.csv(exported, core.csvCell), /"'=formula"/);
  assert.equal(map.csv(exported, core.csvCell).trim().split('\r\n').length, 66);
  assert.throws(() => map.matchingPoints(data, ['gap-0', 'gap-0']), /duplicate/);
  assert.throws(() => map.matchingPoints(data, ['missing']), /unknown/);
});

test('empty filters export no points or unrelated native records', () => {
  const {items, manifest, doc} = fixture(), data = map.prepare(doc, manifest, items);
  const exported = map.exportDocument(data, [], {mech: 'missing'});
  assert.deepEqual(exported.points, []); assert.deepEqual(exported.contexts, []); assert.deepEqual(exported.records, []);
});

test('map CSV preserves negative numeric coordinates while neutralizing formula-like text (#612)', () => {
  const {items, manifest, doc} = fixture(1);
  items[0].record_id = '-12.5'; items[0].record_label = '-1+2'; items[0].prompt = '=1+1';
  doc.points[0].x = -12.5; doc.points[0].y = -.03125;
  const exported = map.exportDocument(map.prepare(doc, manifest, items), ['gap-0'], {});
  const row = map.csv(exported, core.csvCell).split('\r\n')[1];
  assert.match(row, /^"gap-0","DUFMech","'-12\.5","'-1\+2","'=1\+1",-12\.5,-0\.03125,/);
});

test('worker supplies compact map metadata and the entire filtered ID set', async () => {
  const {items} = fixture(), doc = {schema_version: 1, build_id: 'snapshot', items};
  const bytes = new TextEncoder().encode(JSON.stringify(doc)), messages = [];
  const self = {location: {href: 'https://culturebotai.github.io/assets/gaps/search-worker.js', origin: 'https://culturebotai.github.io'}, postMessage: message => messages.push(message)};
  const context = vm.createContext({self, GapSearch: core, importScripts() {}, URL, TextDecoder, crypto: webcrypto,
    fetch: async () => ({ok: true, arrayBuffer: async () => bytes.buffer})});
  vm.runInContext(fs.readFileSync(require.resolve('../assets/gaps/search-worker.js'), 'utf8'), context);
  await self.onmessage({data: {type: 'init', request: 1, url: 'index.json', build_id: 'snapshot', sha256: createHash('sha256').update(bytes).digest('hex')}});
  assert.equal(messages.at(-1).map_items.length, 65);
  assert.ok(!Object.hasOwn(messages.at(-1).map_items[0], 'rationale'));
  await self.onmessage({data: {type: 'query', request: 2, state: {view: 'all', status: '', page: 2}}});
  assert.equal(messages.at(-1).result.rows.length, 15);
  assert.equal(messages.at(-1).result.match_ids.length, 65);
  assert.ok(!Object.hasOwn(messages.at(-1).result, 'all'));
  await self.onmessage({data: {type: 'query', request: 3, state: {mech: 'DUFMech'}}});
  assert.deepEqual(Array.from(messages.at(-1).result.match_ids).sort(), items.filter(item => item.mech === 'DUFMech').map(item => item.id).sort());
});

test('pointCategory, crossMechArcs and missingSourcesNote expose semantic bridges and full fleet coverage', () => {
  const {items, manifest, doc} = fixture(4);
  items[0].mech = 'TraitMech'; items[0].evidence_stances = ['PARTIAL', 'REFUTE']; items[0].attach_layers = ['causal_graphs']; items[0].has_experiments = true;
  items[1].mech = 'CellStructureMech'; items[1].evidence_stances = []; items[1].attach_layers = []; items[1].has_experiments = false;
  items[2].mech = 'CommunityMech'; items[2].evidence_stances = ['SUPPORT']; items[2].attach_layers = ['custom_slot'];
  items[3].mech = 'CommunityMech';
  doc.points[0].input_sha256 = '0'.repeat(64);
  doc.points[1].input_sha256 = '1'.repeat(64);
  doc.points[0].neighbors = [{id: 'gap-1', cosine_similarity: 0.86}];
  doc.points[1].neighbors = [{id: 'gap-0', cosine_similarity: 0.86}];
  doc.points[2].input_sha256 = 'e'.repeat(64);
  doc.points[3].input_sha256 = 'e'.repeat(64);
  const fullManifest = {
    ...manifest,
    sources: [
      {name: 'TraitMech', coverage_status: 'complete', items: 10},
      {name: 'CellStructureMech', coverage_status: 'complete', items: 5},
      {name: 'CommunityMech', coverage_status: 'complete', items: 5},
      {name: 'CultureMech', coverage_status: 'complete', items: 0},
      {name: 'PathwayMech', coverage_status: 'unsupported', items: 0}
    ],
    infrastructure: [{name: 'EdgeMech'}]
  };
  const data = map.prepare(doc, fullManifest, items);
  assert.equal(map.pointCategory(data, doc.points[0], 'stance'), 'REFUTE');
  assert.equal(map.pointCategory(data, doc.points[1], 'stance'), 'No cited evidence');
  assert.equal(map.pointCategory(data, doc.points[0], 'layer'), 'causal_graphs');
  assert.equal(map.pointCategory(data, doc.points[1], 'layer'), 'Unattached');
  assert.equal(map.pointCategory(data, doc.points[2], 'layer'), 'Other attached slot');
  assert.equal(map.pointCategory(data, doc.points[0], 'experiments'), 'Has proposed experiments');
  assert.equal(map.pointCategory(data, doc.points[0], 'bridge'), 'Top-1 neighbor in another Mech (≥0.75)');
  assert.equal(map.pointCategory(data, doc.points[2], 'bridge'), 'Duplicate input text');

  const arcs = map.crossMechArcs(data, ['gap-0', 'gap-1', 'gap-2'], 0.78);
  assert.equal(arcs.length, 1);
  assert.deepEqual({a: arcs[0].a, b: arcs[0].b, cos: arcs[0].cosine_similarity}, {a: 'gap-0', b: 'gap-1', cos: 0.86});

  const note = map.missingSourcesNote(fullManifest, new Set(['TraitMech', 'CellStructureMech', 'CommunityMech']));
  assert.match(note, /CultureMech \(0 items in corpus\)/);
  assert.match(note, /PathwayMech \(unsupported\)/);
  assert.match(note, /EdgeMech \(infrastructure, no corpus\)/);
});
