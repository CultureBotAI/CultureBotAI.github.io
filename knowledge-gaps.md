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
    <p>Find questions recorded across the Mechs, see the evidence behind them, and explore what could resolve them.</p>
    <p class="gap-note">A recorded question is not necessarily reviewed. Scanner proposals awaiting review have a separate candidate view. Coverage describes the inspected records, not everything that remains unknown in biology.</p>
  </header>
  <p id="gap-snapshot" class="gap-note"></p>
  <div id="gap-app" hidden>
    <form id="gap-form" role="search" aria-label="Search Mech discussions">
      <fieldset id="gap-controls" disabled>
        <legend class="gap-sr-only">Search and filter discussions</legend>
        <div class="gap-search-row"><label for="gap-query">Search questions, records, identifiers or references</label><input id="gap-query" name="q" type="search" placeholder="e.g. iron, CHEBI:17234 or a PMID" autocomplete="off"><button type="submit">Search</button></div>
        <div class="gap-filters">
          <label for="gap-view">View<select id="gap-view" name="view"><option value="gaps">Knowledge gaps</option><option value="all">All discussions</option><option value="candidates">Candidates awaiting review</option></select></label>
          <label for="gap-mech">Mech<select id="gap-mech" name="mech"><option value="">All Mechs</option></select></label>
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
    <p id="gap-result-status" role="status" aria-live="polite" aria-atomic="true" tabindex="-1">Loading discussions…</p>
    <p id="gap-export-status" role="status" aria-live="polite"></p>
    <ol id="gap-results" class="gap-results" aria-label="Matching discussions"></ol>
    <nav id="gap-pagination" class="gap-pagination" aria-label="Discussion result pages" hidden><button id="gap-prev" type="button">Previous</button><span id="gap-page-label"></span><button id="gap-next" type="button">Next</button></nav>
    <section id="gap-detail" class="gap-detail" aria-labelledby="gap-detail-title" hidden><button id="gap-close-detail" type="button">Close discussion</button><h2 id="gap-detail-title" tabindex="-1">Discussion</h2><div id="gap-detail-body"></div></section>
    <details class="gap-coverage"><summary>Coverage and source snapshots</summary><p>Zero discussions is meaningful only for a complete extraction. Unsupported, unavailable and partially inspected sources remain visible.</p><div id="gap-coverage"></div></details>
  </div>
  <p id="gap-load-status" role="status" aria-live="polite">Loading the search index…</p>
  <button id="gap-retry" type="button" hidden>Retry loading</button>
  <details class="gap-static"><summary>Static coverage summary and source links</summary>{% include gaps-summary.html %}</details>
  <noscript><p>Interactive search needs JavaScript. Open the static coverage summary above to browse sources and inspect coverage.</p></noscript>
</div>
<script src="{{ '/assets/gaps/search-core.js' | relative_url }}" defer></script>
<script src="{{ '/assets/gaps/browser.js' | relative_url }}" defer></script>

## Bibliography

References for individual questions appear in their discussion details. See the [suite bibliography]({{ '/publications/#bibliography' | relative_url }}) for project publications.
