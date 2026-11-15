/* Gap browser contract regressions: search scope, candidate routing and exports.
 * Inputs: synthetic scientific records. Outputs: node:test results; 2026-11-14.
 */
'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('../assets/gaps/search-core.js');
const fs = require('node:fs');
const vm = require('node:vm');
const {webcrypto, createHash} = require('node:crypto');

function item(overrides) {
  return Object.assign({id: 'TraitMech:test:one', mech: 'TraitMech', record_id: 'traitmech:1',
    record_label: 'Iron acquisition', aliases: ['Ferric uptake'], discussion_id: 'question-one',
    prompt: 'Which receptor mediates iron uptake?', rationale: 'The mechanism remains uncertain.',
    kind: 'KNOWLEDGE_GAP', status: 'OPEN', origin: 'unspecified', review_state: 'unspecified',
    lane: 'recorded', evidence_refs: ['DOI:10.1000/Ab:C.1', 'PMID:1234'], attaches_to: []}, overrides);
}
function search(items, filters) { return core.search(core.prepare(items), filters); }

test('default gaps exclude native scanner candidates, other kinds and inactive states', () => {
  const rows = [item(), item({id: 'candidate', lane: 'candidate', origin: 'scanner', review_state: 'review_required'}),
    item({id: 'todo', kind: 'CURATION_TODO'}), item({id: 'closed', status: 'RESOLVED'})];
  assert.deepEqual(search(rows).all.map(r => r.id), ['TraitMech:test:one']);
  assert.deepEqual(search(rows, {view: 'candidates', status: ''}).all.map(r => r.id), ['candidate']);
  assert.equal(search(rows, {view: 'all', status: ''}).total, 4);
});

test('corrected scanner-origin question is not excluded on origin or ID prefix alone', () => {
  const corrected = item({id: 'kgscan-old-id', origin: 'scanner', lane: 'recorded'});
  assert.equal(search([corrected]).total, 1);
});

test('aliases and exact CURIE/DOI punctuation remain searchable', () => {
  for (const q of ['Ferric', 'traitmech:1', 'DOI:10.1000/Ab:C.1', '10.1000/Ab:C.1', 'PMID:1234']) {
    assert.equal(search([item()], {q}).total, 1, q);
  }
  assert.equal(search([item()], {q: 'DOI:10.1000/Ab:C.2'}).total, 0);
});

test('exact identifiers rank ahead of prose mentions and sort precedes pagination', () => {
  const exact = item({id: 'exact', record_id: 'CHEBI:17234', record_label: 'Z glucose'});
  const prose = item({id: 'prose', record_label: 'A CHEBI:17234 example', evidence_refs: []});
  assert.equal(search([prose, exact], {q: 'CHEBI:17234'}).rows[0].id, 'exact');
  assert.equal(search([prose, exact], {q: 'CHEBI:17234', sort: 'record'}).rows[0].id, 'prose');
});

test('whole index is searched beyond the first page and export selection is complete', () => {
  const rows = Array.from({length: 115}, (_, n) => item({id: 'id-' + n, record_id: 'record-' + n,
    record_label: String(n).padStart(3, '0'), prompt: n === 114 ? 'Uncommon secretion channel' : 'Iron question'}));
  const second = search(rows, {page: 2});
  assert.equal(second.rows.length, 50); assert.equal(second.rows[0].record_label, '050');
  assert.equal(second.total, 115); assert.equal(second.all.length, 115); assert.equal(second.records, 115);
  assert.equal(search(rows, {q: 'uncommon'}).rows[0].id, 'id-114');
  assert.equal(search(rows, {page: 100}).page, 3);
});

test('filters combine and identical record IDs in distinct Mechs stay distinct', () => {
  const rows = [item({source_url: 'https://github.com/test/one'}), item({id: 'second', mech: 'CommunityMech'}),
    item({id: 'third', source_url: 'https://github.com/test/one', status: 'UNDER_DISCUSSION', review_state: 'documented_review'})];
  assert.equal(search(rows).records, 2);
  assert.equal(search(rows, {mech: 'TraitMech', status: 'UNDER_DISCUSSION', review: 'documented_review'}).total, 1);
  assert.equal(search(rows, {mech: 'no longer available'}).total, 0);
});

test('distinct source documents sharing a chemical ID count separately, discussions in one document do not', () => {
  const first = item({id: 'one', mech: 'MediaIngredientMech', record_id: 'CHEBI:1', source_url: 'https://github.com/test/blob/pin/form-a.yaml'});
  const second = item({id: 'two', mech: 'MediaIngredientMech', record_id: 'CHEBI:1', source_url: 'https://github.com/test/blob/pin/form-b.yaml'});
  const third = {...first, id: 'three', discussion_id: 'second-discussion'};
  assert.equal(search([first, second, third]).records, 2);
});

test('literal markup is search text and unknown state falls back conservatively', () => {
  const rows = [item({prompt: 'Is <img src=x onerror=alert(1)> literally described? '})];
  assert.equal(search(rows, {q: '<img'}).total, 1);
  assert.equal(core.normalize({view: 'unexpected', page: '-3', sort: 'missing'}).view, 'gaps');
  assert.equal(core.normalize({page: 'NaN'}).page, 1);
});

test('CSV preserves full details and prevents formula execution including leading whitespace', () => {
  for (const value of ['=1+1', '  +1', '\t=1', '\r@SUM(A1)', '-cmd', '\uFEFF=1']) {
    assert.ok(core.csvCell(value).startsWith('"\''), JSON.stringify(value));
  }
  assert.equal(core.csvCell('A "quoted"\nquestion'), '"A ""quoted""\nquestion"');
  const csv = core.csv([item({proposed_experiments: [{name: 'Isogenic comparison'}], source: {revision: 'abc'}})]);
  assert.ok(csv.includes('Isogenic comparison')); assert.ok(csv.includes('revision')); assert.ok(csv.includes('abc'));
});

test('only declared HTTPS destinations become clickable links', () => {
  for (const value of ['javascript:alert(1)', 'http://github.com/a', 'https://github.com.evil.test/a',
    'https://github.com@evil.test/a', 'https://user:pass@github.com/a', 'https://github.com:444/a']) {
    assert.equal(core.safeURL(value), null, value);
  }
  assert.equal(core.safeURL('https://github.com/CultureBotAI/TraitMech'), 'https://github.com/CultureBotAI/TraitMech');
  assert.equal(core.referenceURL('PMID:1234'), 'https://pubmed.ncbi.nlm.nih.gov/1234/');
  assert.equal(core.referenceURL('DOI:10.1000/ab#c'), 'https://doi.org/10.1000/ab%23c');
});

async function workerFixture(doc) {
  const bytes = new TextEncoder().encode(JSON.stringify(doc));
  const messages = [];
  const self = {location: {href: 'https://culturebotai.github.io/assets/gaps/search-worker.js',
    origin: 'https://culturebotai.github.io'}, postMessage: message => messages.push(message)};
  const context = vm.createContext({self, GapSearch: core, importScripts() {}, URL, TextDecoder,
    crypto: webcrypto, fetch: async () => ({ok: true, arrayBuffer: async () => bytes.buffer})});
  vm.runInContext(fs.readFileSync(require.resolve('../assets/gaps/search-worker.js'), 'utf8'), context);
  return {messages, send: async data => self.onmessage({data}),
    init: {type: 'init', request: 1, url: 'index.json', build_id: doc.build_id,
      sha256: createHash('sha256').update(bytes).digest('hex')}};
}

test('worker verifies snapshot, searches later records and returns complete export selection', async () => {
  const rows = Array.from({length: 60}, (_, n) => item({id: 'row-' + n, record_id: 'record-' + n}));
  const worker = await workerFixture({schema_version: 1, build_id: 'snapshot-a', items: rows});
  await worker.send(worker.init);
  assert.equal(worker.messages.at(-1).type, 'ready');
  assert.equal(worker.messages.at(-1).facet_counts.kind.KNOWLEDGE_GAP, 60);
  await worker.send({type: 'query', request: 2, state: {page: 2}});
  assert.equal(worker.messages.at(-1).result.rows.length, 10);
  assert.equal(worker.messages.at(-1).result.all, undefined);
  await worker.send({type: 'export', request: 3, state: {page: 2}});
  assert.equal(worker.messages.at(-1).result.all.length, 60);
});

test('worker refuses hash/build mismatches and duplicate identities instead of showing an empty corpus', async () => {
  for (const change of [{sha256: '0'.repeat(64)}, {build_id: 'different-build'}]) {
    const worker = await workerFixture({schema_version: 1, build_id: 'snapshot-a', items: [item()]});
    await worker.send({...worker.init, ...change});
    assert.equal(worker.messages.at(-1).type, 'error');
    await worker.send({type: 'query', request: 2, state: {}});
    assert.equal(worker.messages.at(-1).type, 'error');
  }
  const duplicate = await workerFixture({schema_version: 1, build_id: 'snapshot-a', items: [item(), item()]});
  await duplicate.send(duplicate.init);
  assert.equal(duplicate.messages.at(-1).type, 'error');
});
