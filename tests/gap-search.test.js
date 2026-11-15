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
  const assets = new Map([['index.json', bytes]]), failures = new Set(), holds = new Map();
  const self = {location: {href: 'https://culturebotai.github.io/assets/gaps/search-worker.js',
    origin: 'https://culturebotai.github.io'}, postMessage: message => messages.push(message)};
  const context = vm.createContext({self, GapSearch: core, importScripts() {}, URL, TextDecoder,
    crypto: webcrypto, fetch: async url => {
      const name = new URL(url).pathname.split('/').at(-1), body = assets.get(name);
      if (holds.has(name)) { const held = holds.get(name); holds.delete(name); await held; }
      if (failures.has(name)) { failures.delete(name); return {ok: false, status: 503}; }
      return {ok: Boolean(body), status: body ? 200 : 404, arrayBuffer: async () => body.buffer};
    }});
  vm.runInContext(fs.readFileSync(require.resolve('../assets/gaps/search-worker.js'), 'utf8'), context);
  return {messages, send: async data => self.onmessage({data}),
    add: (name, value) => {
      const body = new TextEncoder().encode(JSON.stringify(value)); assets.set(name, body);
      return {url: name, build_id: value.build_id, sha256: createHash('sha256').update(body).digest('hex')};
    },
    fail: name => failures.add(name),
    hold: name => { let release; holds.set(name, new Promise(resolve => { release = resolve; })); return release; },
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

function entity(id, label, postings) {
  return {id, label, entity_refs: [{mech: 'TraitMech', record_id: id,
    url: 'https://github.com/CultureBotAI/TraitMech/blob/pin/record.yaml'}],
    postings: postings.map(([discussion_id, count]) => ({discussion_id, count}))};
}
function termFixture(rows, terms) {
  const prepared = core.prepare(rows), doc = {schema_version: 1, build_id: 'snapshot-a', terms};
  return {prepared, doc, data: core.prepareTerms(doc, prepared)};
}

test('raw occurrence counts, discussion counts and pair counts have distinct meanings', () => {
  const rows = [item({id: 'one'}), item({id: 'two'}), item({id: 'other-mech', mech: 'CommunityMech'})];
  const fixture = termFixture(rows, [entity('iron', 'Iron', [['one', 4], ['two', 1], ['other-mech', 9]]),
    entity('oxygen', 'Oxygen', [['one', 2], ['two', 5]]), entity('copper', 'Copper', [['two', 1]])]);
  const result = core.search(fixture.prepared, {mech: 'TraitMech'}, fixture.data);
  assert.equal(result.term_summary.occurrences, 13);
  assert.equal(result.term_summary.scope_discussions, 2);
  assert.equal(result.term_summary.terms[0].id, 'oxygen');
  assert.equal(result.term_summary.terms[0].occurrences, 7);
  assert.equal(result.term_summary.terms[0].discussions, 2);
  assert.equal(result.term_summary.pairs.find(p => [p.a, p.b].includes('iron') && [p.a, p.b].includes('oxygen')).discussions, 2);
});

test('entity clicks use exact membership and AND pairs without changing the chart scope', () => {
  const rows = [item({id: 'one', prompt: 'iron is mentioned here'}), item({id: 'two'}), item({id: 'three'})];
  const fixture = termFixture(rows, [entity('iron', 'Same label', [['two', 1], ['three', 1]]),
    entity('oxygen', 'Same label', [['three', 4]])]);
  const base = core.search(fixture.prepared, {}, fixture.data);
  const pair = core.search(fixture.prepared, {term: 'oxygen', term2: 'iron'}, fixture.data);
  assert.deepEqual(pair.all.map(r => r.id), ['three']);
  assert.deepEqual(pair.term_summary, base.term_summary);
  assert.equal(pair.selected_terms.length, 2);
  assert.equal(core.search(fixture.prepared, {term: 'unknown'}, fixture.data).total, 0);
  assert.equal(core.search(fixture.prepared, {term: 'iron'}, fixture.data).total, 2);
  assert.equal(core.search(fixture.prepared, {term: 'iron', q: 'mentioned'}, fixture.data).total, 0);
});

test('term normalization gives pairs one canonical URL state without losing unknown IDs', () => {
  assert.deepEqual([core.normalize({term: 'z', term2: 'a'}).term, core.normalize({term: 'z', term2: 'a'}).term2], ['a', 'z']);
  assert.equal(core.normalize({term2: 'unknown:1'}).term, 'unknown:1');
  assert.equal(core.normalize({term: 'a', term2: 'a'}).term2, '');
});

test('term summaries and selections retain reader-facing canonical identities independently of filter keys', () => {
  const fixture = termFixture([item({id: 'one'})], [
    {...entity('term-opaque-one', 'Iron', [['one', 2]]), canonical_id: 'CHEBI:18248'},
    {...entity('term-opaque-two', 'Iron', [['one', 1]]), canonical_id: 'CHEBI:29033'}]);
  const result = core.search(fixture.prepared, {term: 'term-opaque-one', term2: 'term-opaque-two'}, fixture.data);
  assert.deepEqual(result.term_summary.terms.map(term => term.canonical_id), ['CHEBI:18248', 'CHEBI:29033']);
  assert.deepEqual(result.selected_terms.map(term => term.canonical_id), ['CHEBI:18248', 'CHEBI:29033']);
  assert.deepEqual(result.selected_terms.map(term => term.id), ['term-opaque-one', 'term-opaque-two']);
  const unknown = core.search(fixture.prepared, {term: 'unknown-id'}, fixture.data);
  assert.equal(unknown.total, 0); assert.equal(unknown.selected_terms[0].id, 'unknown-id');
  assert.equal(unknown.selected_terms[0].unavailable, true);
});

test('term scope respects default gaps, source, lifecycle, query and candidate views', () => {
  const rows = [item({id: 'open'}), item({id: 'closed', status: 'RESOLVED'}),
    item({id: 'candidate', lane: 'candidate'}), item({id: 'todo', kind: 'CURATION_TODO'})];
  const fixture = termFixture(rows, [entity('x', 'Entity', rows.map(row => [row.id, 1]))]);
  assert.equal(core.search(fixture.prepared, {}, fixture.data).term_summary.scope_discussions, 1);
  assert.equal(core.search(fixture.prepared, {view: 'all', status: ''}, fixture.data).term_summary.scope_discussions, 4);
  assert.equal(core.search(fixture.prepared, {view: 'candidates', status: ''}, fixture.data).term_summary.scope_discussions, 1);
  assert.equal(core.search(fixture.prepared, {mech: 'unsupported'}, fixture.data).term_summary.terms.length, 0);
  assert.equal(core.search(fixture.prepared, {q: 'not present'}, fixture.data).term_summary.terms.length, 0);
});

test('co-occurrence includes every nonzero pair among the top 20, never lower-ranked terms', () => {
  const rows = [item({id: 'one'})];
  const fixture = termFixture(rows, Array.from({length: 25}, (_, i) => entity('e' + i, 'Entity ' + i, [['one', 30 - i]])));
  const summary = core.search(fixture.prepared, {}, fixture.data).term_summary;
  assert.equal(summary.terms.length, 25); assert.equal(summary.pairs.length, 190);
  assert.ok(summary.pairs.every(pair => Number(pair.a.slice(1)) < 20 && Number(pair.b.slice(1)) < 20 && pair.discussions === 1));
});

test('entity-filtered pagination and export cover all matching discussions', () => {
  const rows = Array.from({length: 115}, (_, n) => item({id: 'row-' + n, record_label: String(n).padStart(3, '0')}));
  const fixture = termFixture(rows, [entity('x', 'Entity', rows.slice(20).map(row => [row.id, 1]))]);
  const result = core.search(fixture.prepared, {term: 'x', page: 2}, fixture.data);
  assert.equal(result.rows.length, 45); assert.equal(result.all.length, 95);
  assert.equal(result.rows[0].id, 'row-70');
});

test('term vocabulary ownership is independent of discussion source and does not duplicate shared entities', () => {
  const shared = {...entity('shared', 'Iron', [['trait-discussion', 3], ['community-discussion', 2]]),
    canonical_id: 'CHEBI:18248', entity_refs: [{mech: 'MediaIngredientMech', record_id: 'CHEBI:18248'},
      {mech: 'CofactorMech', record_id: 'CofactorMech:iron'}]};
  const fixture = termFixture([item({id: 'trait-discussion'}), item({id: 'community-discussion', mech: 'CommunityMech'})],
    [shared, entity('trait', 'Phenotype', [['trait-discussion', 1]])]);
  for (const vocab of ['MediaIngredientMech', 'CofactorMech']) {
    const result = core.search(fixture.prepared, {vocab}, fixture.data);
    assert.equal(result.total, 2);
    assert.equal(result.term_summary.terms.length, 1);
    assert.equal(result.term_summary.occurrences, 5);
    assert.equal(result.term_summary.covered_discussions, 2);
    const source = core.search(fixture.prepared, {vocab, mech: 'TraitMech'}, fixture.data);
    assert.equal(source.total, 1); assert.equal(source.term_summary.occurrences, 3);
  }
  assert.equal(core.search(fixture.prepared, {}, fixture.data).term_summary.occurrences, 6);
});

test('vocabulary filters the ranked term and pair universe before selecting the top20', () => {
  const entries = Array.from({length: 30}, (_, n) => ({...entity('x' + n, 'Entity ' + n, [['one', 40 - n]]),
    entity_refs: [{mech: n < 5 ? 'CofactorMech' : 'TraitMech', record_id: 'Entity:' + n}]}));
  const fixture = termFixture([item({id: 'one'})], entries);
  const summary = core.search(fixture.prepared, {vocab: 'TraitMech'}, fixture.data).term_summary;
  assert.equal(summary.terms.length, 25); assert.equal(summary.terms[0].id, 'x5');
  assert.equal(summary.pairs.length, 190);
  assert.ok(summary.pairs.every(pair => Number(pair.a.slice(1)) >= 5 && Number(pair.a.slice(1)) < 25 &&
    Number(pair.b.slice(1)) >= 5 && Number(pair.b.slice(1)) < 25));
});

test('cold vocabulary/term mismatch returns zero while unknown vocabulary alone keeps ordinary results', () => {
  const fixture = termFixture([item({id: 'one'})], [entity('x', 'Entity', [['one', 2]])]);
  for (const vocab of ['CofactorMech', 'unavailable-vocabulary']) {
    const ordinary = core.search(fixture.prepared, {vocab}, fixture.data);
    assert.equal(ordinary.total, 1); assert.equal(ordinary.term_summary.terms.length, 0);
    assert.equal(ordinary.term_summary.covered_discussions, 0);
    assert.equal(ordinary.term_summary.pairs.length, 0);
    const filtered = core.search(fixture.prepared, {vocab, term: 'x'}, fixture.data);
    assert.equal(filtered.total, 0); assert.equal(filtered.selected_terms[0].in_vocabulary, false);
  }
  assert.equal(core.normalize({vocab: 'unavailable-vocabulary'}).vocab, 'unavailable-vocabulary');
  assert.equal(core.search(fixture.prepared, {vocab: 'TraitMech', term: 'x'}, fixture.data).total, 1);
});

test('invalid entity postings fail instead of silently changing membership or counts', () => {
  const prepared = core.prepare([item({id: 'one'})]);
  for (const terms of [[entity('x', 'X', [['missing', 1]])], [entity('x', 'X', [['one', 0]])],
    [entity('x', 'X', [['one', 1.5]])], [entity('x', 'X', [['one', 1], ['one', 2]])],
    [entity('x', 'X', []), entity('x', 'Duplicate', [])]]) {
    assert.throws(() => core.prepareTerms({terms}, prepared));
  }
  assert.throws(() => core.search(prepared, {term: 'x'}), /must load/);
});

test('failed term sidecar preserves ordinary search, blocks filtered URLs, and supports retry', async () => {
  const rows = [item({id: 'one'}), item({id: 'two'})];
  const worker = await workerFixture({schema_version: 1, build_id: 'snapshot-a', items: rows});
  await worker.send(worker.init);
  const descriptor = worker.add('terms.json', {schema_version: 1, build_id: 'snapshot-a', terms: [entity('x', 'Entity', [['two', 3]])]});
  worker.fail('terms.json');
  await worker.send({type: 'terms-init', request: 2, ...descriptor});
  assert.equal(worker.messages.at(-1).type, 'error');
  await worker.send({type: 'query', request: 3, state: {}});
  assert.equal(worker.messages.at(-1).result.total, 2);
  for (const type of ['query', 'export']) {
    await worker.send({type, request: 4, state: {term: 'x'}});
    assert.equal(worker.messages.at(-1).type, 'error');
  }
  await worker.send({type: 'terms-init', request: 5, ...descriptor});
  assert.equal(worker.messages.at(-1).type, 'terms-ready');
  await worker.send({type: 'query', request: 6, state: {term: 'x'}});
  assert.equal(worker.messages.at(-1).result.total, 1);
  assert.equal(worker.messages.at(-1).result.rows[0].id, 'two');
  for (const change of [{sha256: '0'.repeat(64)}, {build_id: 'old-snapshot'}]) {
    await worker.send({type: 'terms-init', request: 7, ...descriptor, ...change});
    assert.equal(worker.messages.at(-1).type, 'error');
    await worker.send({type: 'query', request: 8, state: {term: 'x'}});
    assert.equal(worker.messages.at(-1).type, 'error');
  }
});

test('a late sidecar response cannot attach itself after a search snapshot reload', async () => {
  const doc = {schema_version: 1, build_id: 'snapshot-a', items: [item({id: 'one'})]};
  const worker = await workerFixture(doc); await worker.send(worker.init);
  const descriptor = worker.add('terms.json', {schema_version: 1, build_id: 'snapshot-a', terms: [entity('x', 'Entity', [['one', 1]])]});
  const release = worker.hold('terms.json');
  const pending = worker.send({type: 'terms-init', request: 2, ...descriptor});
  await worker.send({...worker.init, request: 3});
  release(); await pending;
  assert.equal(worker.messages.at(-1).type, 'error');
  assert.match(worker.messages.at(-1).message, /superseded/);
  await worker.send({type: 'query', request: 4, state: {term: 'x'}});
  assert.equal(worker.messages.at(-1).type, 'error');
  await worker.send({type: 'query', request: 5, state: {}});
  assert.equal(worker.messages.at(-1).result.total, 1);
});

test('verified recognition metadata and readable selected entity provenance survive the export boundary', async () => {
  const worker = await workerFixture({schema_version: 1, build_id: 'snapshot-a', items: [item({id: 'one'})]});
  await worker.send(worker.init);
  const selected = {...entity('term-internal-key', 'Native system', [['one', 2]]), canonical_id: ''};
  selected.entity_refs[0].source = {repository: 'CultureBotAI/TraitMech', revision: 'a'.repeat(40),
    path: 'data/system.yaml', sha256: 'b'.repeat(64), license: 'CC-BY-4.0'};
  const document = {schema_version: 1, build_id: 'snapshot-a', term_build_id: 'c'.repeat(64),
    vocabulary_sha256: 'd'.repeat(64), policy: {version: 2, normalization: 'NFKC', text_fields: ['prompt', 'rationale']},
    terms: [selected]};
  const descriptor = worker.add('terms.json', document);
  await worker.send({type: 'terms-init', request: 2, ...descriptor});
  const ready = worker.messages.at(-1);
  assert.equal(ready.term_build_id, document.term_build_id);
  assert.equal(ready.vocabulary_sha256, document.vocabulary_sha256);
  assert.equal(JSON.stringify(ready.policy), JSON.stringify(document.policy));
  await worker.send({type: 'export', request: 3, state: {term: selected.id}});
  const result = worker.messages.at(-1).result;
  assert.equal(result.all.length, 1);
  assert.equal(result.selected_terms[0].id, selected.id);
  assert.equal(result.selected_terms[0].label, selected.label);
  assert.equal(result.selected_terms[0].canonical_id, '');
  assert.equal(JSON.stringify(result.selected_terms[0].entity_refs), JSON.stringify(selected.entity_refs));
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
