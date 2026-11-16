---
layout: page
title: "Knowledge gaps across the Mechs"
description: "Browse recorded knowledge gaps, open questions and candidate discussions across the public Mech knowledge bases, with evidence and source coverage."
permalink: /knowledge-gaps/
---

<link rel="stylesheet" href="{{ '/assets/gaps/browser.css' | relative_url }}">

<div id="gap-browser" data-manifest="{{ '/assets/gaps/manifest.json' | relative_url }}" data-worker="{{ '/assets/gaps/search-worker.js' | relative_url }}">
  <header class="gap-intro">
    <p><a href="{{ '/mechs/' | relative_url }}">All Mech projects</a></p>
    <h1>Knowledge gaps</h1>
    <nav class="gap-section-nav" aria-label="Knowledge gap page sections">
      <a href="#gap-form" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="10" cy="10" r="7"></circle><path d="m15 15 6 6"></path></svg><span>Search</span></a>
      <a href="#gap-terms-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 18a5 5 0 0 1-1-10 7 7 0 0 1 13-1 5.5 5.5 0 0 1 0 11zM8 11h8M7 14h4m3 0h3"></path></svg><span>Word cloud</span></a>
      <a href="#gap-pairs-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="5" cy="6" r="3"></circle><circle cx="19" cy="8" r="3"></circle><circle cx="11" cy="19" r="3"></circle><path d="m8 6 8 2M6 9l4 7m7-6-4 6"></path></svg><span>Co-occurrence</span></a>
      <a href="#gap-results-title" data-gap-interactive hidden><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M8 7h9M8 12h9M8 17h9M6 7h.01M6 12h.01M6 17h.01"></path></svg><span>Gap results</span></a>
      <a href="#gap-static-title"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="2"></rect><path d="M3 9h18M3 15h18M9 3v18M15 3v18"></path></svg><span>Coverage</span></a>
      <a href="#bibliography"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 5C9 3 5 3 2 4v15c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1zm0 0v15M5 8h4m6 0h4M5 12h4m6 0h4"></path></svg><span>References</span></a>
    </nav>
    <section id="gap-stats" aria-labelledby="gap-stats-title">
      <h2 id="gap-stats-title" class="gap-sr-only">Knowledge gap statistics</h2>
      <p id="gap-stats-status" class="gap-note" role="status">Gap counts will appear when the search index loads.</p>
      <div id="gap-stats-grid" class="gap-stats-grid" hidden></div>
      <p class="gap-note">Snapshot-wide recorded gaps, across all lifecycle states; candidates and other discussion kinds are excluded. Select a count to browse those gaps with other filters cleared. Unindexed or partial sources are marked separately.</p>
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
          <label for="gap-sort">Sort<select id="gap-sort" name="sort"><option value="relevance">Search relevance</option><option value="record">Record name</option><option value="mech">Mech, then record</option></select></label>
        </div>
        <p class="gap-note">Counts beside discussion kinds, lifecycle and review states describe the full snapshot before filtering.</p>
        <div class="gap-actions"><button id="gap-reset" type="button">Clear all filters</button><button id="gap-export-json" type="button">Export all matches: JSON</button><button id="gap-export-csv" type="button">CSV</button></div>
      </fieldset>
    </form>
    <p id="gap-view-note" class="gap-note"></p>
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
        <h3 id="gap-pairs-title" class="gap-section-target" tabindex="-1">Co-occurrence among the top 20 entities</h3>
        <p class="gap-note">Pairs count distinct discussions mentioning both entities, regardless of repeated mentions. Co-occurrence does not establish a biological relationship. Select a pair to show its discussions.</p>
        <p id="gap-pairs-status" class="gap-note">Co-occurrence will appear when entity occurrences load.</p>
        <p id="gap-pairs-empty" hidden>No pairs occur together among the top 20 entities in this scope.</p>
        <div id="gap-pairs-table" class="gap-term-table" tabindex="0" role="region" aria-label="Entity co-occurrence pairs; scroll to browse" hidden><table><caption>Nonzero pairs among the top 20 entities, ranked by shared discussions</caption><thead><tr><th scope="col">Entity pair</th><th scope="col">Discussions containing both</th></tr></thead><tbody id="gap-term-pairs"></tbody></table></div>
    </section>
    <div id="gap-term-selection" class="gap-term-selection" hidden><p id="gap-term-selection-label"></p><div id="gap-term-sources"></div><button id="gap-terms-clear" type="button">Clear entity selection</button></div>
    <h2 id="gap-results-title" class="gap-section-target" tabindex="-1">Matching discussions</h2>
    <p id="gap-result-status" role="status" aria-live="polite" aria-atomic="true" tabindex="-1">Loading discussions…</p>
    <p id="gap-export-status" role="status" aria-live="polite"></p>
    <ol id="gap-results" class="gap-results" aria-label="Matching discussions"></ol>
    <nav id="gap-pagination" class="gap-pagination" aria-label="Discussion result pages" hidden><button id="gap-prev" type="button">Previous</button><span id="gap-page-label"></span><button id="gap-next" type="button">Next</button></nav>
    <section id="gap-detail" class="gap-detail" aria-labelledby="gap-detail-title" hidden><button id="gap-close-detail" type="button">Close discussion</button><h2 id="gap-detail-title" tabindex="-1">Discussion</h2><div id="gap-detail-body"></div></section>
    <details class="gap-coverage"><summary>Coverage and source snapshots</summary><p>Zero discussions is meaningful only for a complete extraction. Unsupported, unavailable and partially inspected sources remain visible.</p><div id="gap-coverage"></div></details>
  </div>
  <p id="gap-load-status" role="status" aria-live="polite">Loading the search index…</p>
  <button id="gap-retry" type="button" hidden>Retry loading</button>
  <details class="gap-static"><summary id="gap-static-title" class="gap-section-target">Static coverage summary and source links</summary>{% include gaps-summary.html %}</details>
  <noscript><p>Interactive search needs JavaScript. Open the static coverage summary above to browse sources and inspect coverage.</p></noscript>
</div>
<script src="{{ '/assets/gaps/search-core.js' | relative_url }}" defer></script>
<script src="{{ '/assets/gaps/browser.js' | relative_url }}" defer></script>

## Bibliography
{: .gap-section-target tabindex="-1" }

References for individual questions appear in their discussion details. See the [suite bibliography]({{ '/publications/#bibliography' | relative_url }}) for project publications.
