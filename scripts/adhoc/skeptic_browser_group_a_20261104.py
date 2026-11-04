#!/usr/bin/env python3
"""Record independent 24-criterion review of six group-A Mech websites.
Inputs: this reviewer's live browser captures and the other auditor's proposals.
Outputs: compact skeptic ledgers; never edits catalogue or website sources.
Serves the Nov 4 fleet refresh PR. 2026-11-04.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUT = Path('_fleet/reviews/refresh-20261104')
ARCHIVE = Path('/private/tmp/xmech-refresh-20261104-browser-evidence/group-b')
SITES = ['CellStructureMech', 'AntibioticMech', 'NaturalProductMech', 'HabitatMech', 'TaxonMech', 'PathwayMech']
# Judgments independently derived from the captured behavior, before comparison.
PARTIAL = {
 'CellStructureMech': {'schema_docs'},
 'AntibioticMech': {'search','term_links','downloads','schema_docs','build_provenance','load_failure'},
 'NaturalProductMech': {'term_links','evidence','downloads','schema_docs','build_provenance','responsive','load_failure'},
 'HabitatMech': {'search','term_links','evidence','cross_mech_links','downloads','schema_docs','license','build_provenance','theme_toggle','responsive','load_failure'},
 'TaxonMech': {'shareable_state','cross_mech_links','downloads','schema_docs','build_provenance'},
 'PathwayMech': {'term_links','category_browse','schema_docs','license','build_provenance'},
}
MISSING = {'NaturalProductMech': {'curation_history'}, 'PathwayMech': {'review_status','cross_mech_links'}}
NA = {'PathwayMech': {'load_failure'}}
REASONS = {
 'CellStructureMech': {
  'term_links':'Attachment organelle membrane now has named Subject/Object GO:0033111, GO:0033099 and GO:0005886 resolver anchors, including the mechanism table; the old unlinked-section reason is no longer true.',
  'build_provenance':'The footer explicitly dates its own corpus 2026-11-03 05:55:11 UTC and identifies digest d7c5fef867d9 and 1022 records.',
  'downloads':'The linked corpus.json is distinct from index.json and contains complete structure records with components, taxonomic_distribution, evidence, causal_graphs and curation_history.',
  'domain_view':'The valid embedding-map.html and sequence-map.html routes render; the obsolete map.html URL is not the current linked text map.'},
 'AntibioticMech': {
  'search':'Identifier and label queries work, but query a matches 3064 and renders only the first 500 without a continuation control.',
  'term_links':'The avibactam record retains a broader ChEBI grounding with Label unavailable, so the main grounding section is not fully labeled.',
  'downloads':'The linked index and individual record files do not constitute a linked bulk scientific record export.',
  'build_provenance':'The date refers to ChEBI/CARD upstream retrieval; the corpus digest is not a dated own-record release.',
  'load_failure':'Blocking sequence_map.json first shows Failed to fetch; entering protein then replaces it with Showing 0 of 0 proteins. Independent reproduction confirms partial.'},
 'NaturalProductMech': {
  'term_links':'Main biosynthetic/producer terms remain CURIE text without resolver anchors on the sampled records.',
  'evidence':'PMID/DOI references in sampled record text remain unlinked; source-database links do not remedy the citation section.',
  'curation_history':'The sampled record headings and bodies do not display an event-by-event curation history.',
  'downloads':'Index and plotted coordinate exports cover entries but omit their substantive record evidence.',
  'build_provenance':'The footer identifies an undated corpus digest plus upstream retrieval date, not a dated own-record build.',
  'responsive':'Fresh and resized 390px views independently reproduce anisomycin 409px, rebeccamycin 407px, staurosporine 415px and the long diketopiperazine record 464px.',
  'load_failure':'Blocking sequence_map.json gives a real error initially; typing protein then replaces it with Showing 0 of 0 proteins.'},
 'HabitatMech': {
  'search':'water finds 310 and shows 200; broad query a finds 3178 and shows 200, with no result continuation.',
  'term_links':'Associated taxa are named but NCBITaxon identifiers remain plain text in a main record section.',
  'evidence':'Sampled PMID and DOI citation strings are not resolver anchors.',
  'cross_mech_links':'Associated taxa have specific names/identifiers, but the Taxon search target /TaxonMech/browse.html?q=Sulfurimonas returns 404. This is partial under the broken-related-record criterion.',
  'downloads':'Category indexes contain listing metadata and do not export complete environmental/taxon evidence records.',
  'license':'The standalone text-map-source page does not state both licenses although ordinary pages do.',
  'build_provenance':'Generated from kg-microbe on 2026-08-16 dates the upstream source, not the current own-record corpus.',
  'theme_toggle':'After explicitly selecting Dark, the standalone text-map-source route has no data-theme value or toggle and ignores that saved choice.',
  'responsive':'The aquatic-macrophyte-associated record independently reaches 404px at a 390px viewport.',
  'load_failure':'Abort the eight lazy category JSON requests and search water: the browser reports zero matches rather than a load failure.'},
 'TaxonMech': {
  'shareable_state':'Combined BACTERIA/SPECIES/NCBITAXON with query NCBITaxon:562 gives 239; reload preserves only query/sort, clears all three facets and returns 259.',
  'cross_mech_links':'Strain/source identifiers referring to kg-microbe are plain text; suite navigation does not count as a record cross-link.',
  'downloads':'The bulk search-index gzip contains listing metadata, while complete details are fetched separately per record.',
  'build_provenance':'The site exposes the corpus digest and upstream releases without a dated site or own-record version.'},
 'PathwayMech': {
  'term_links':'The components/edges sections contain unlinked CURIEs, despite working protein source links.',
  'review_status':'Record views show pathway metadata and curation events but no overall review/workflow state.',
  'cross_mech_links':'Sampled records link external ontology/protein sources but no specific sibling Mech record.',
  'category_browse':'Types are Browse filters rather than linked category pages; several option labels are edge-count fragments.',
  'downloads':'Substantive KGX nodes and edges export the full 280-pathway corpus, including source_records, description, evidence, reference_metadata and endpoint_qualifiers. Root arbitration accepts this scientific export; lossless YAML/history serialization is not required.',
  'license':'Landing names CC BY data; Browse and sampled record pages do not state both project data and code licenses.',
  'build_provenance':'A corpus hash is available but does not date the build or records.',
  'load_failure':'Reviewed pages and maps use embedded data; no catalogue fetch/XHR to block was observed.'},
}
COMMON = {
 'search':'Independent identifier, label and unmatched queries were executed; their live counts and result rows are retained.',
 'facets':'Property-filter selection, combination with search and reset were independently exercised.',
 'result_counts':'Observed counts respond to queries and facets and are distinct from the total.',
 'sorting':'Each available sort option was selected, with URL/control state and first result rows retained.',
 'shareable_state':'A combined query/filter/sort view was reloaded and its controls and matching count compared.',
 'full_catalogue':'The total is backed by linked listings/category pagination or complete indexed corpus; search-result caps are assessed separately.',
 'record_pages':'Multiple stable individual record URLs opened successfully from a fresh browser navigation.',
 'term_links':'The sampled own-grounding and main-section terms have readable labels beside resolver anchors.',
 'evidence':'Sampled record references include working-format PMID/DOI/source URL anchors rather than only database navigation.',
 'review_status':'Sampled record headers explicitly state their workflow state.',
 'curation_history':'Sampled records show dated curation-event sections with attribution and action text.',
 'source_link':'Sampled record pages link their own YAML source file rather than just the repository root.',
 'domain_view':'Domain figures or maps rendered in the independently opened routes, with data-bearing visuals.',
 'cross_mech_links':'Sampled record content includes a direct link to a specific sibling record; navigation links were excluded.',
 'corpus_stats':'The generated landing figures were read from the browser and compared with the audited corpus counts.',
 'category_browse':'Landing links lead into distinct category subsets with continuation where needed.',
 'suite_nav':'Visible suite-directory links occur in the reviewed navigation or footer.',
 'downloads':'Linked export fields and coverage were inspected separately from navigation/search indexes.',
 'schema_docs':'Visible schema links reach raw LinkML YAML; consistent fleet arbitration requires partial when rendered schema documentation is not provided.',
 'license':'Reviewed landing, browser, records and maps distinguish CC BY data from BSD code.',
 'build_provenance':'Dated own-record or build provenance was distinguished from upstream retrieval timestamps.',
 'theme_toggle':'Dark was selected and independently carried across the valid reviewed routes.',
 'responsive':'Every valid reviewed route was checked at fresh and resized 390px; none exceeded the viewport.',
 'load_failure':'Relevant data requests were aborted and the resulting reader-facing error was inspected.'}

def read_capture(name):
    p=OUT/name
    if not p.exists():p=ARCHIVE/name
    return p,json.loads(p.read_text())

def lines_near(text, pattern, radius=1, limit=14):
    lines=text.splitlines();indices=set()
    for i,line in enumerate(lines):
        if re.search(pattern,line,re.I):indices.update(range(max(0,i-radius),min(len(lines),i+radius+1)))
    return [lines[i][:600] for i in sorted(indices)][:limit]

def page_evidence(p):
    links=[x for x in p.get('links',[]) if isinstance(x.get('url'),str)]
    seen=set();selected=[]
    for x in links:
        if re.search(r'github.com/.+\.ya?ml|doi.org|pubmed|obolibrary|identifiers.org|/mechs/|\.json|\.tsv|Mech/.+(?:html|ya?ml)',x['url']):
            pair=(x.get('text'),x['url'])
            if pair not in seen:selected.append(x);seen.add(pair)
    return {k:p.get(k) for k in ['url','http_status','checked_at','title','headings','footer','counts','theme','saved_theme','fresh_390','resized_390','record_links_count','unique_record_links','record_links_sha256','canvas','svg']} | {
      'body_excerpt':p.get('body','')[:1400],
      'field_excerpts':lines_near(p.get('body',''),r'curation|history|proposed|reviewed|seeded|subject|object|references|citation|TaxonMech|GO:0033111|GO:0033099|GO:0005886|kg.microbe|Label unavailable|PMID:28373542',2,35),
      'selected_links':selected[:65],
      'sorts_and_facets':p.get('selects',[])}

def main():
    baseline=json.loads(Path('_fleet/data/site_features.json').read_text());criteria=baseline['catalogue']
    cpath,challenges=read_capture('group-a-skeptic-challenges.json')
    assert challenges.get('finished_at'), 'Targeted challenges incomplete'
    results={};mismatches=[]
    for mech in SITES:
        path,raw=read_capture(mech.lower()+'-skeptic-b-observations.json')
        assert raw.get('finished_at')
        auditor_path=OUT/(mech.lower()+'-auditor-a.json');auditor=json.loads(auditor_path.read_text())
        actions={k:{f:v.get(f) for f in ['url','counts','controls','checked','rows','first_results','error']} for k,v in raw['actions'].items()}
        receipts={'pages':{url:page_evidence(p) for url,p in raw['pages'].items()},'actions':actions,
          'failure_cases':{url:{'aborted':v.get('aborted'),'excerpt':lines_near(v.get('state',{}).get('body',''),r'error|fail|unavailable|could not|0 of 0',1)} for url,v in raw.get('failure_cases',{}).items()}}
        features={}
        for key in criteria:
            status='not_applicable' if key in NA.get(mech,set()) else 'missing' if key in MISSING.get(mech,set()) else 'partial' if key in PARTIAL[mech] else 'present'
            proposed=auditor['features'][key]
            if status!=proposed['status']:mismatches.append((mech,key,status,proposed['status']))
            features[key]={'status':status,'auditor_status':proposed['status'],'agreement':status==proposed['status'],
             'rationale':REASONS.get(mech,{}).get(key,COMMON[key]),
             'claim_locator':f'_fleet/data/site_features.json#/mechs/{mech}/features/{key}',
             'auditor_evidence':f'{auditor_path}#/features/{key}',
             'independent_evidence': 'receipts.actions' if key in ['search','facets','result_counts','sorting','shareable_state'] else 'receipts.pages',
             'url':proposed['url']}
            if key in ['search','load_failure','downloads','theme_toggle','cross_mech_links']:
                features[key]['targeted_challenges']=str(cpath)
        report={'mech':mech,'reviewer':'central_directory independent skeptic of deployment_review','pin':raw['pin'],
          'started_at':raw['started_at'],'finished_at':datetime.now(timezone.utc).isoformat(),
          'browser_finished_at':raw['finished_at'],'deployment_before':raw['deployment_before'],'deployment_after':raw['deployment_after'],
          'raw_capture':str(path),'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'auditor_report':str(auditor_path),'features':features,'receipts':receipts,
          'limits':['Independent representative-route review, not a crawl of every record. Shared rubric and root schema/download arbitrations applied.','Absence judgments are scoped to the independently captured routes and controls.']}
        dest=OUT/(mech.lower()+'-skeptic-b.json');dest.write_text(json.dumps(report,indent=2)+'\n')
        results[mech]={'verdict_count':len(features),'agreements':sum(v['agreement'] for v in features.values()),'report':str(dest),'statuses':{k:v['status'] for k,v in features.items()}}
        dest.with_suffix('.md').write_text('# '+mech+' independent review — 2026-11-04\n\n'+ '\n'.join(f'- {k}: **{v["status"]}**. {v["rationale"]}' for k,v in features.items())+'\n')
    summary={'reviewer':'central_directory','finished_at':datetime.now(timezone.utc).isoformat(),'sites':results,'verdict_count':sum(r['verdict_count'] for r in results.values()),'disagreements':mismatches,
      'arbitrations':['Raw LinkML source alone is partial schema documentation.','Full-corpus scientific KGX exports with evidence qualify as downloads; listing metadata and coordinate-only projections do not.']}
    (OUT/'group-a-skeptic-b.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'verdict_count':summary['verdict_count'],'disagreements':mismatches}))
    assert not mismatches, mismatches

if __name__=='__main__':main()
