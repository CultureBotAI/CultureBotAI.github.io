---
layout: page
title: "Knowledge gaps across the Mechs"
description: "Browse recorded knowledge gaps, open questions, cross-Mech analyses and candidate discussions across the public Mech knowledge bases, with evidence and source coverage."
permalink: /knowledge-gaps/
---

<link rel="stylesheet" href="{{ '/assets/gaps/browser.css' | relative_url }}">

<div id="gap-browser" data-manifest="{{ '/assets/gaps/manifest.json' | relative_url }}" data-worker="{{ '/assets/gaps/search-worker.js' | relative_url }}">
  <header class="gap-intro">
    <p><a href="{{ '/mechs/' | relative_url }}">All Mech projects</a></p>
    <h1>Knowledge gaps</h1>
    <nav class="gap-section-nav" aria-label="Knowledge gap page sections">
      <a href="#gap-form" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="7"></circle><path d="m15 15 6 6"></path></svg><span>Search</span></a>
      <a href="#gap-analyses-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M4 20h16M7 20v-8m5 8V6m5 14v-5"></path></svg><span>Analyses</span></a>
      <a href="#gap-terms-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 18a5 5 0 0 1-1-10 7 7 0 0 1 13-1 5.5 5.5 0 0 1 0 11zM8 11h8M7 14h4m3 0h3"></path></svg><span>Word cloud</span></a>
      <a href="#gap-pairs-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="5" cy="6" r="3"></circle><circle cx="19" cy="8" r="3"></circle><circle cx="11" cy="19" r="3"></circle><path d="m8 6 8 2M6 9l4 7m7-6-4 6"></path></svg><span>Co-occurrence</span></a>
      <a href="#gap-map-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 3v18h18"></path><circle cx="7" cy="15" r="1.5"></circle><circle cx="10" cy="9" r="1.5"></circle><circle cx="16" cy="13" r="1.5"></circle><circle cx="19" cy="5" r="1.5"></circle></svg><span>Embedding map</span></a>
      <a href="#gap-results-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M8 7h9M8 12h9M8 17h9M6 7h.01M6 12h.01M6 17h.01"></path></svg><span>Gap results</span></a>
      <a href="#gap-static-title"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M3 9h18M3 15h18M9 3v18M15 3v18"></path></svg><span>Coverage</span></a>
      <a href="#bibliography"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1zm0 0v15M5 8h4m6 0h4M5 12h4m6 0h4"></path></svg><span>References</span></a>
    </nav>
    <section id="gap-stats" aria-labelledby="gap-stats-title">
      <h2 id="gap-stats-title" class="gap-sr-only">Knowledge gap statistics</h2>
      <p id="gap-stats-status" class="gap-note" role="status">Gap counts will appear when the search index loads.</p>
      <div id="gap-stats-grid" class="gap-stats-grid" hidden></div>
      <p class="gap-note">Snapshot-wide recorded gaps across all 16 public corpus Mechs (all lifecycle states; candidates and other discussion kinds excluded), plus non-corpus fleet infrastructure. Select a corpus count to browse those gaps with other filters cleared; unindexed, partial and infrastructure members link to source scope details.</p>
    </section>
    <p>Find questions recorded across the Mechs, see the evidence behind them, and explore what could resolve them.</p>
    <p class="gap-note">A recorded question is not necessarily reviewed. Scanner proposals awaiting review have a separate candidate view. Coverage describes the inspected records, not everything that remains unknown in biology.</p>
  </header>
  <p id="gap-snapshot" class="gap-note"></p>
  <div id="gap-app" hidden>
    <form id="gap-form" class="gap-section-target" tabindex="-1" role="search" aria-label="Search Mech discussions">
      <fieldset id="gap-controls" disabled>
        <legend class="gap-sr-only">Search and filter discussions</legend>
        <div class="gap-search-row"><label for="gap-query">Search questions, records, identifiers or references</label><input id="gap-query" name="q" type="search" placeholder="e.g. iron, CHEBI:17234 or a PMID" autocomplete="off"><button type="submit">Search</button></div>
        <div class="gap-filters">
          <label for="gap-view">View<select id="gap-view" name="view"><option value="gaps">Knowledge gaps</option><option value="all">All discussions</option><option value="candidates">Candidates awaiting review</option></select></label>
          <label for="gap-mech">Source Mech<select id="gap-mech" name="mech"><option value="">All Mechs</option></select></label>
          <label for="gap-kind">Discussion kind<select id="gap-kind" name="kind"><option value="">All kinds in this view</option></select></label>
          <label for="gap-status">Lifecycle<select id="gap-status" name="status"><option value="active">Active (open or under discussion)</option><option value="">All lifecycle states</option></select></label>
          <label for="gap-review">Review state<select id="gap-review" name="review"><option value="">All review states</option></select></label>
          <label for="gap-layer">Schema layer<select id="gap-layer" name="layer"><option value="">All schema layers</option></select></label>
          <label for="gap-stance">Evidence stance<select id="gap-stance" name="stance"><option value="">All evidence stances</option></select></label>
          <label for="gap-experiments">Experiments<select id="gap-experiments" name="experiments"><option value="">All discussions</option></select></label>
          <label for="gap-sort">Sort<select id="gap-sort" name="sort"><option value="relevance">Search relevance</option><option value="record">Record name</option><option value="mech">Mech, then record</option><option value="posed_newest">Posed date (newest)</option><option value="posed_oldest">Posed date (oldest)</option></select></label>
        </div>
        <p class="gap-note">Counts beside discussion kinds, lifecycle, review states, schema layers, stances and experiments describe the full snapshot before filtering.</p>
        <div class="gap-actions"><button id="gap-reset" type="button">Clear all filters</button><button id="gap-export-json" type="button">Export all matches: JSON</button><button id="gap-export-csv" type="button">CSV</button></div>
      </fieldset>
    </form>
    <div id="gap-active-filters" class="gap-active-filters" aria-label="Active drill-down filters" hidden></div>
    <p id="gap-view-note" class="gap-note"></p>
    <section id="gap-analyses" class="gap-analyses" aria-labelledby="gap-analyses-title">
      <h2 id="gap-analyses-title" class="gap-section-target" tabindex="-1">Cross-Mech analyses</h2>
      <p class="gap-note">Visual summaries below reflect the current search and entity filters across all public fleet Mechs. Select any bar segment, matrix cell, month or reference to refine the search.</p>
      <div class="gap-analysis-card">
        <div class="gap-analysis-header">
          <h3>Fleet-wide discussion breakdown across all Mechs</h3>
          <label class="gap-inline-control" for="gap-breakdown-lens">Group segments by<select id="gap-breakdown-lens"><option value="kind">Discussion kind</option><option value="status">Lifecycle state</option><option value="stance">Evidence stance</option><option value="layer">Attached schema layer</option></select></label>
        </div>
        <p id="gap-breakdown-note" class="gap-note">All 16 corpus Mechs and non-corpus fleet infrastructure remain listed even when zero discussions match, distinguishing empty extractions from unsupported or held roots.</p>
        <ul id="gap-breakdown-legend" class="gap-map-legend" aria-label="Breakdown segment legend"></ul>
        <div id="gap-breakdown-rows" class="gap-breakdown-rows" role="region" aria-label="Per-Mech discussion breakdown"></div>
      </div>
      <div class="gap-analysis-card">
        <div class="gap-analysis-header">
          <h3>Source Mech × Term vocabulary cross-pollination</h3>
          <label class="gap-inline-control" for="gap-matrix-mode">Cell metric<select id="gap-matrix-mode"><option value="discussions">Distinct discussions</option><option value="occurrences">Total occurrences</option><option value="cross">Cross-Mech mentions only (off-diagonal)</option></select></label>
        </div>
        <p id="gap-matrix-note" class="gap-note">Rows are discussion source Mechs; columns are Mech entity vocabularies matched in discussion prose. Diagonal cells (dashed outline) are within-Mech vocabulary mentions; off-diagonal cells reveal cross-Mech concept reuse. Select a cell to filter Source Mech and Term vocabulary together.</p>
        <p id="gap-matrix-status" class="gap-note" role="status">Cross-Mech vocabulary matrix will appear when entity occurrences load.</p>
        <div id="gap-matrix-wrap" class="gap-matrix-wrap" tabindex="0" role="region" aria-label="16 by 16 Source Mech by Term vocabulary matrix; scroll horizontally if needed" hidden></div>
      </div>
      <div class="gap-analysis-grid">
        <div class="gap-analysis-card">
          <h3>Posed vs. resolved timeline</h3>
          <p id="gap-timeline-note" class="gap-note">Monthly discussion activity for matching entries carrying ISO dates. Select a month bar to filter by posed or resolved month.</p>
          <div id="gap-timeline-chart" class="gap-timeline-chart" role="region" aria-label="Monthly posed and resolved discussions"></div>
        </div>
        <div class="gap-analysis-card">
          <div class="gap-analysis-header">
            <h3>Reference concentration &amp; citation silos</h3>
            <label class="gap-inline-control" for="gap-refs-mode">Show<select id="gap-refs-mode"><option value="top">Most-cited references</option><option value="cross">Cross-Mech shared citations (2+ Mechs)</option></select></label>
          </div>
          <p id="gap-refs-note" class="gap-note">Case-normalized DOIs, PMIDs, ontology terms and URLs cited in matching discussions. Select Filter to show all discussions citing a reference.</p>
          <div id="gap-refs-list" class="gap-compact-list"></div>
        </div>
      </div>
      <details id="gap-synthesis-details" class="gap-synthesis-details" open>
        <summary>Synthesis opportunities: semantic bridges, proposed experiments &amp; vocabulary blind-spots</summary>
        <p id="gap-analytics-status" class="gap-note" role="status" aria-live="polite">Loading snapshot synthesis sidecar…</p>
        <button id="gap-analytics-retry" type="button" hidden>Retry synthesis sidecar</button>
        <div id="gap-analytics-content" class="gap-analysis-grid" hidden>
          <div class="gap-analysis-subcard">
            <h4>Cross-Mech semantic bridges (embedding space)</h4>
            <p id="gap-bridges-summary" class="gap-note"></p>
            <div id="gap-bridges-list" class="gap-compact-list"></div>
          </div>
          <div class="gap-analysis-subcard">
            <h4>Proposed-experiments backlog</h4>
            <p id="gap-experiments-summary" class="gap-note"></p>
            <div id="gap-experiments-list" class="gap-compact-list"></div>
          </div>
          <div class="gap-analysis-subcard">
            <div class="gap-analysis-header">
              <h4>Unmatched-discussion vocabulary blind-spots</h4>
              <label class="gap-inline-control" for="gap-blindspot-scope">Scope<select id="gap-blindspot-scope"><option value="gaps">Recorded knowledge gaps</option><option value="all">All discussions</option></select></label>
            </div>
            <p id="gap-blindspot-summary" class="gap-note"></p>
            <div id="gap-blindspot-phrases" class="gap-chip-cloud" role="group" aria-label="Frequent phrases in discussions with zero dictionary entity matches"></div>
          </div>
          <div class="gap-analysis-subcard">
            <h4>Entity semantic cohesion &amp; duplicate prompts</h4>
            <p id="gap-cohesion-summary" class="gap-note"></p>
            <div id="gap-cohesion-list" class="gap-compact-list"></div>
          </div>
        </div>
      </details>
    </section>
    <section class="gap-term-explorer" aria-labelledby="gap-terms-title">
      <h2 id="gap-terms-title" class="gap-section-target" tabindex="-1">Mech entities in these discussions</h2>
      <p class="gap-note">Explore entity mentions in the discussions selected by the filters above. Selecting a term filters the results below; the cloud keeps the same scope.</p>
      <label class="gap-vocab-control" for="gap-vocab">Term vocabulary<select id="gap-vocab" name="vocab"><option value="">All Mech vocabularies</option></select></label>
      <p class="gap-note">Choose which Mech's entities to explore. Source Mech above chooses where discussions come from. A vocabulary choice alone does not filter discussions; changing it clears the entity selection.</p>
      <details class="gap-term-method"><summary>Matching method and vocabulary coverage</summary><p>Dictionary matching uses pinned Mech names, identifiers, declared aliases and exact typed synonyms. It counts occurrences in question text, rationale, evidence explanations, proposed experiment prose and resolution text, excluding the owning record's label and other metadata. Ambiguous aliases and short or common strings are intentionally unlinked; valid entities may be missed. Counts include negated and contextual mentions; they do not assert truth or research priority.</p><p>The initial scope is active recorded knowledge gaps from all source Mechs. Choose All discussions to include other kinds and candidates. Entity vocabulary sources are separate from the source Mech of a discussion. A shared canonical entity can belong to several Mech vocabularies; each occurrence is still counted once. The chosen vocabulary limits the cloud, ranked entities and pair universe. Entity filters must also belong to that vocabulary.</p><p>JSON exports preserve filters and selected entity identities, plus matching policy and source hashes when the entity index is loaded. CSV exports contain discussion rows only.</p><div id="gap-term-coverage">Vocabulary coverage will appear when entity occurrences load.</div></details>
      <p id="gap-terms-status" role="status" aria-live="polite">Loading entity occurrences…</p>
      <button id="gap-terms-retry" type="button" hidden>Retry entity occurrences</button>
      <div id="gap-terms-content" hidden>
        <p id="gap-terms-count" class="gap-note"></p>
        <p class="gap-note">Up to 50 entities by raw occurrences. Word size follows the square root of occurrences, with a minimum readable size. Buttons show exact counts, including repeated mentions in one discussion.</p>
        <div id="gap-term-cloud" class="gap-term-cloud" role="group" aria-label="Most mentioned entities; select one to filter discussions"></div>
        <details class="gap-term-ranking"><summary>All entities and exact counts</summary><div class="gap-term-table" tabindex="0" role="region" aria-label="Ranked entity counts; scroll to browse"><table><caption>Entities ranked by raw occurrences in the current scope</caption><thead><tr><th scope="col">Entity</th><th scope="col">Occurrences</th><th scope="col">Discussions</th></tr></thead><tbody id="gap-term-ranking"></tbody></table></div></details>
      </div>
      <div class="gap-analysis-header">
        <h3 id="gap-pairs-title" class="gap-section-target" tabindex="-1">Co-occurrence among the top 20 entities</h3>
        <label class="gap-inline-control" for="gap-pairs-metric">Rank &amp; weight by<select id="gap-pairs-metric"><option value="discussions">Shared discussions</option><option value="npmi">NPMI specificity (−1 to +1)</option><option value="jaccard">Jaccard overlap (0 to 1)</option></select></label>
      </div>
      <p class="gap-note">Pairs count distinct discussions mentioning both entities, alongside Jaccard overlap and normalized pointwise mutual information (NPMI, which highlights specific pairings over ubiquitous hubs). Co-occurrence does not establish a biological relationship. Select a node, edge or table row to filter discussions.</p>
      <p id="gap-pairs-status" class="gap-note">Co-occurrence will appear when entity occurrences load.</p>
      <p id="gap-pairs-empty" hidden>No pairs occur together among the top 20 entities in this scope.</p>
      <div id="gap-pairs-network" class="gap-pairs-network" role="region" aria-label="Co-occurrence network graph of top 20 entities" hidden></div>
      <div id="gap-pairs-table" class="gap-term-table" tabindex="0" role="region" aria-label="Entity co-occurrence pairs; scroll to browse" hidden><table><caption>Nonzero pairs among the top 20 entities in the current scope</caption><thead><tr><th scope="col">Entity pair</th><th scope="col">Jaccard</th><th scope="col">NPMI</th><th scope="col">Discussions</th></tr></thead><tbody id="gap-term-pairs"></tbody></table></div>
    </section>
    <div id="gap-term-selection" class="gap-term-selection" hidden><p id="gap-term-selection-label"></p><div id="gap-term-sources"></div><button id="gap-terms-clear" type="button">Clear entity selection</button></div>
    <section id="gap-embedding" class="gap-embedding" aria-labelledby="gap-map-title">
      <h2 id="gap-map-title" class="gap-section-target" tabindex="-1">Discussion embedding map</h2>
      <p>Explore discussions by the combined text of each question, its context, and the matched Mech entries with their native definitions or descriptions. Each point is one discussion; the map uses the same discussion filters as the results below.</p>
      <p class="gap-note">The 2D projection is approximate. Nearby points do not establish a biological relationship or the importance of a knowledge gap. Inspect the original discussion and matched source records.</p>
      <p id="gap-map-status" role="status" aria-live="polite">The embedding map will become available after the search index loads.</p>
      <button id="gap-map-load" type="button" disabled>Load embedding map</button><button id="gap-map-retry" type="button" hidden>Retry embedding map</button>
      <div id="gap-map-content" hidden>
        <fieldset id="gap-map-controls" disabled>
          <legend class="gap-sr-only">Embedding map controls</legend>
          <div class="gap-map-controls">
            <label for="gap-map-color">Color points by<select id="gap-map-color"><option value="mech">Source Mech</option><option value="kind">Discussion kind</option><option value="status">Lifecycle</option><option value="stance">Evidence stance</option><option value="layer">Schema layer</option><option value="experiments">Proposed experiments</option><option value="bridge">Cross-Mech neighbor bridge</option></select></label>
            <label for="gap-map-point">Choose a matching discussion<select id="gap-map-point"><option value="">Choose a matching discussion</option></select></label>
          </div>
          <div class="gap-actions"><button id="gap-map-zoom-in" type="button">Zoom in</button><button id="gap-map-zoom-out" type="button">Zoom out</button><button id="gap-map-reset" type="button">Reset view</button><button id="gap-map-left" type="button" aria-label="Pan map left">←</button><button id="gap-map-right" type="button" aria-label="Pan map right">→</button><button id="gap-map-up" type="button" aria-label="Pan map up">↑</button><button id="gap-map-down" type="button" aria-label="Pan map down">↓</button><label class="gap-map-toggle" for="gap-map-bridges"><input id="gap-map-bridges" type="checkbox"><span>Show cross-Mech neighbor arcs (cosine ≥ 0.78)</span></label></div>
        </fieldset>
        <p id="gap-map-count" class="gap-note" role="status"></p>
        <p id="gap-map-help" class="gap-note">Select a point or choose a discussion above to inspect it. Drag empty map space to pan. With the map focused, use arrow keys to pan, +/− to zoom, and 0 to reset. Focus a point and use arrows to browse points, then Enter to open it. <a href="#gap-results-title">Browse the matching discussion list</a>.</p>
        <ul id="gap-map-legend" class="gap-map-legend" aria-label="Map color legend"></ul>
        <p id="gap-map-unshown" class="gap-note" hidden></p>
        <p id="gap-map-empty" hidden>No embedded discussions match these filters.</p>
        <div id="gap-map-plot" class="gap-map-plot"></div>
        <div class="gap-actions"><button id="gap-map-export-json" type="button" disabled>Export all filtered map points: JSON</button><button id="gap-map-export-csv" type="button" disabled>CSV</button></div>
        <p id="gap-map-export-status" role="status" aria-live="polite"></p>
        <details class="gap-map-method"><summary>Embedding method, coverage and projection</summary><p id="gap-map-method"></p><pre id="gap-map-provenance"></pre></details>
      </div>
      <section id="gap-map-selection" class="gap-map-selection" aria-label="Selected discussion embedding context" hidden></section>
    </section>
    <h2 id="gap-results-title" class="gap-section-target" tabindex="-1">Matching discussions</h2>
    <p id="gap-result-status" role="status" aria-live="polite" aria-atomic="true" tabindex="-1">Loading discussions…</p>
    <p id="gap-export-status" role="status" aria-live="polite"></p>
    <ol id="gap-results" class="gap-results" aria-label="Matching discussions"></ol>
    <nav id="gap-pagination" class="gap-pagination" aria-label="Discussion result pages" hidden><button id="gap-prev" type="button">Previous</button><span id="gap-page-label"></span><button id="gap-next" type="button">Next</button></nav>
    <section id="gap-detail" class="gap-detail" aria-labelledby="gap-detail-title" hidden><button id="gap-close-detail" type="button">Close discussion</button><h2 id="gap-detail-title" tabindex="-1">Discussion</h2><div id="gap-detail-body"></div></section>
    <details class="gap-coverage"><summary>Coverage and source snapshots</summary><p>Zero discussions is meaningful only for a complete extraction. Unsupported, unavailable, partially inspected and non-corpus infrastructure projects remain visible.</p><div id="gap-coverage"></div></details>
  </div>
  <p id="gap-load-status" role="status" aria-live="polite">Loading the search index…</p>
  <button id="gap-retry" type="button" hidden>Retry loading</button>
  <details class="gap-static"><summary id="gap-static-title" class="gap-section-target">Static coverage summary and source links</summary>{% include gaps-summary.html %}</details>
  <noscript><p>Interactive search needs JavaScript. Open the static coverage summary above to browse sources and inspect coverage.</p></noscript>
</div>
<script src="{{ '/assets/gaps/search-core.js' | relative_url }}" defer></script>
<script src="{{ '/assets/gaps/embedding-map.js' | relative_url }}" defer></script>
<script src="{{ '/assets/gaps/browser.js' | relative_url }}" defer></script>

## Bibliography
{: .gap-section-target tabindex="-1" }

References for individual questions appear in their discussion details. See the [suite bibliography]({{ '/publications/#bibliography' | relative_url }}) for project publications.
