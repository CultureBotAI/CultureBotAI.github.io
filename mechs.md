---
layout: default
title: "X-Mech Suite"
description: "Eight ontology-grounded microbial knowledge bases, from habitat to culture medium, orchestrated by culturebotai-claw and connected through shared ontology terms and direct cross-references"
permalink: /mechs/
---

# X-Mech Suite: eight knowledge bases, one standard

The X-Mech suite is a fleet of eight curated, ontology-grounded knowledge bases that together describe a microbe at every scale: the habitat it lives in, the community it belongs to, the traits it expresses, the structures and proteins that implement them, the antibiotics that act on it, and the ingredients and media it is grown in. Each Mech follows the same curation model, one validated YAML record per entity with evidence and provenance, and the fleet is coordinated by a single orchestrator, [culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw).

<!-- ===== Mech fleet: interactive component (self-contained: styles, markup, script) ===== -->
<style>
  /* Mech identity colors: each node wears the accent of its own site. */
  :root {
    --mech-habitatmech: #2b6a4d; --mech-communitymech: #3D7DD6; --mech-traitmech: #C5474B;
    --mech-cellstructuremech: #5257C9; --mech-proteintraitsmech: #2E8B84; --mech-antibioticmech: #85551C;
    --mech-mediaingredientmech: #7E5BC4; --mech-culturemech: #4B9E5F;
    --fleet-edge: rgba(90, 99, 94, .34);
    --fleet-heat-hue: 150 22%;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --mech-habitatmech: #4fbf85; --mech-communitymech: #5c9cf0; --mech-traitmech: #f0696e;
      --mech-cellstructuremech: #8a8ef5; --mech-proteintraitsmech: #3dbfb2; --mech-antibioticmech: #d9a94a;
      --mech-mediaingredientmech: #b08cf2; --mech-culturemech: #63c46f;
      --fleet-edge: rgba(160, 178, 168, .34);
    }
  }
  :root[data-theme="dark"] {
    --mech-habitatmech: #4fbf85; --mech-communitymech: #5c9cf0; --mech-traitmech: #f0696e;
    --mech-cellstructuremech: #8a8ef5; --mech-proteintraitsmech: #3dbfb2; --mech-antibioticmech: #d9a94a;
    --mech-mediaingredientmech: #b08cf2; --mech-culturemech: #63c46f;
    --fleet-edge: rgba(160, 178, 168, .34);
  }

  /* ---- Stat strip ---- */
  .fleet-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .8rem; margin: 1.2rem 0 .4rem; }
  .fleet-stats > div { padding: .9rem 1rem; background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
  .fleet-stats b { display: block; font-size: 1.7rem; font-weight: 800; letter-spacing: -.02em; line-height: 1.1; font-variant-numeric: tabular-nums; color: var(--ink); }
  .fleet-stats span { font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
  @media (max-width: 640px) { .fleet-stats { grid-template-columns: repeat(2, 1fr); } }

  /* ---- Graph shell ---- */
  .fleet-graph { margin: 1.4rem 0 2rem; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
  .fleet-controls { display: flex; flex-wrap: wrap; gap: .5rem .9rem; align-items: center; padding: .8rem 1rem; border-bottom: 1px solid var(--line); background: var(--wash-b); }
  .fleet-controls .grp { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem; }
  .fleet-controls .grp > span { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); margin-right: .2rem; }
  .fleet-chip { font: inherit; font-size: .8rem; font-weight: 600; line-height: 1; padding: .42em .8em; border-radius: 999px; border: 1px solid var(--line); background: var(--card); color: var(--ink); cursor: pointer; transition: background .15s, color .15s, border-color .15s; }
  .fleet-chip:hover { border-color: var(--accent); }
  .fleet-chip[aria-pressed="true"] { background: var(--ink); color: var(--card); border-color: var(--ink); }
  .fleet-chip.voc[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
  .fleet-chip[disabled] { opacity: .45; cursor: default; }
  .fleet-chip.voc.other[aria-pressed="true"] { background: var(--accent-2); border-color: var(--accent-2); }
  .fleet-controls .spacer { flex: 1; }
  .fleet-stage { position: relative; }
  .fleet-stage svg { display: block; width: 100%; height: auto; }
  .fleet-stage svg text { font-family: inherit; fill: var(--ink); }
  .fleet-stage .axis-label { font-size: 11px; fill: var(--muted); letter-spacing: .08em; text-transform: uppercase; font-weight: 700; }
  .fleet-stage .hub-label { font-size: 12px; font-weight: 800; }
  .fleet-stage .hub-sub { font-size: 9px; fill: var(--muted); }
  .fleet-stage .node-label { font-size: 13px; font-weight: 700; pointer-events: none; }
  .fleet-stage .node-sub { font-size: 10.5px; fill: var(--muted); pointer-events: none; font-variant-numeric: tabular-nums; }
  .fleet-stage .node { cursor: pointer; }
  .fleet-stage .node circle { stroke: var(--card); stroke-width: 3; transition: r .2s ease, opacity .2s ease; }
  .fleet-stage .node.adjacent circle { stroke-dasharray: 5 4; stroke: var(--muted); }
  .fleet-stage .node:focus { outline: none; }
  .fleet-stage .node:focus-visible circle { stroke: var(--neon); }
  .fleet-stage .node.dim, .fleet-stage .edge.dim { opacity: .18; }
  .fleet-stage .edge { fill: none; stroke: var(--fleet-edge); stroke-linecap: round; cursor: pointer; transition: opacity .2s ease, stroke .2s ease; }
  .fleet-stage .edge.hit { stroke: transparent; stroke-width: 14; }
  .fleet-stage .edge.xref { stroke: var(--accent); stroke-dasharray: 6 5; stroke-width: 1.8; }
  .fleet-stage .edge.xref.weak { stroke-dasharray: 2 5; opacity: .7; }
  .fleet-stage .edge.hub { stroke: var(--accent-2); stroke-width: 1.6; }
  .fleet-stage .edge.hub.in { stroke-dasharray: 3 4; }
  .fleet-stage .edge.gov { stroke: var(--muted); stroke-width: 1.2; }
  .fleet-stage .edge.lit { stroke: var(--accent); opacity: 1; }
  .fleet-stage .ring { fill: none; stroke: var(--muted); stroke-dasharray: 8 6; stroke-width: 1.2; opacity: .55; }
  .fleet-stage .ring-label { font-size: 11px; fill: var(--muted); font-weight: 700; letter-spacing: .06em; }
  .fleet-stage .hub { fill: var(--wash-a); stroke: var(--accent-2); stroke-width: 2; }
  .fleet-stage .arrow { fill: var(--accent); }
  .fleet-stage .arrow-hub { fill: var(--accent-2); }
  .fleet-tip { position: absolute; z-index: 5; max-width: 300px; padding: .6rem .75rem; font-size: .82rem; line-height: 1.4; color: var(--ink); background: var(--card); border: 1px solid var(--line); border-radius: 10px; box-shadow: var(--shadow-lg); pointer-events: none; opacity: 0; transition: opacity .12s; }
  .fleet-tip.show { opacity: 1; }
  .fleet-tip b { display: block; margin-bottom: .2rem; }
  .fleet-tip .k { color: var(--muted); }
  .fleet-tip em { color: var(--muted); font-style: normal; }
  .fleet-detail { padding: 1rem 1.2rem 1.2rem; border-top: 1px solid var(--line); display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 1rem 1.6rem; align-items: start; }
  .fleet-detail h3 { margin: 0 0 .35rem; padding-left: .6rem; font-size: 1.1rem; }
  .fleet-detail p { margin: .25rem 0 .6rem; font-size: .95rem; }
  .fleet-detail .meta { display: grid; grid-template-columns: max-content 1fr; gap: .25rem .8rem; font-size: .86rem; margin: 0; }
  .fleet-detail .meta dt { color: var(--muted); }
  .fleet-detail .meta dd { margin: 0; font-variant-numeric: tabular-nums; }
  .fleet-detail .links { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .7rem; }
  .fleet-detail .links a { font-size: .8rem; font-weight: 700; padding: .35em .8em; border-radius: 999px; border: 1px solid var(--line); background: var(--wash-b); }
  .page-content .fleet-detail ul { margin: .2rem 0 0; padding-left: 1.2rem; font-size: .88rem; list-style: disc; }
  .page-content .fleet-detail ul > li::before { display: none; }
  .fleet-detail li { margin-bottom: .3rem; }
  .fleet-detail .eyebrow { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); margin: 0 0 .3rem; }
  @media (max-width: 720px) { .fleet-detail { grid-template-columns: 1fr; } }
  .fleet-legend { display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; padding: .55rem 1rem; font-size: .78rem; color: var(--muted); border-top: 1px solid var(--line); }
  .fleet-legend i { display: inline-block; width: 26px; height: 0; margin-right: .4rem; vertical-align: middle; border-top: 3px solid var(--fleet-edge); }
  .fleet-legend i.x { border-top: 2px dashed var(--accent); }
  .fleet-legend i.h { border-top: 2px solid var(--accent-2); }
  .fleet-legend i.g { border-top: 1.5px dashed var(--muted); }

  /* ---- Mech cards ---- */
  .mech-cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; margin: 1.2rem 0 1.6rem; }
  @media (max-width: 720px) { .mech-cards { grid-template-columns: 1fr; } }
  .mech-card { position: relative; display: flex; flex-direction: column; gap: .5rem; padding: 1.1rem 1.2rem 1.1rem 1.35rem; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); transition: box-shadow .15s ease, transform .15s ease; }
  .mech-card::before { content: ""; position: absolute; left: 0; top: 14px; bottom: 14px; width: 5px; border-radius: 0 4px 4px 0; background: var(--c); }
  .mech-card:hover, .mech-card.lit { box-shadow: var(--shadow-lg); transform: translateY(-2px); }
  .mech-card header { display: flex; align-items: baseline; justify-content: space-between; gap: .6rem; }
  .mech-card h3 { margin: 0; padding: 0; border: 0; font-size: 1.15rem; color: var(--c); }
  .mech-card .scale { font-size: .7rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; color: var(--muted); white-space: nowrap; }
  .mech-card .tag { margin: 0; font-size: .93rem; color: var(--ink); }
  .mech-card .num { display: flex; align-items: baseline; gap: .45rem; font-variant-numeric: tabular-nums; }
  .mech-card .num b { font-size: 1.45rem; font-weight: 800; letter-spacing: -.02em; color: var(--ink); }
  .mech-card .num span { font-size: .82rem; color: var(--muted); }
  .mech-card .vocab { display: flex; flex-wrap: wrap; gap: .3rem; }
  .mech-card .vocab span { font-size: .72rem; font-weight: 700; padding: .25em .55em; border-radius: 6px; background: var(--wash-b); color: var(--ink); border: 1px solid var(--line); }
  .mech-card .row { display: flex; flex-wrap: wrap; gap: .35rem .5rem; align-items: center; margin-top: auto; padding-top: .3rem; }
  .mech-card .row a { font-size: .8rem; font-weight: 700; padding: .3em .7em; border-radius: 999px; border: 1px solid var(--line); }
  .mech-card .row a.primary { background: var(--c); border-color: var(--c); color: var(--card); }
  .mech-card .badge { margin-left: auto; font-size: .7rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }
  .mech-card .badge.adj { color: var(--accent); }
  .page-content .mech-card ul { list-style: none; padding: 0; margin: 0; }
  .page-content .mech-card ul > li::before { display: none; }

  /* ---- Scale ladder ---- */
  .fleet-ladder { display: grid; grid-template-columns: repeat(8, 1fr); gap: 4px; margin: 1rem 0 .2rem; }
  .fleet-ladder > div { padding: .55rem .5rem .5rem; border-radius: 8px; background: var(--wash-b); border-top: 4px solid var(--c); font-size: .74rem; line-height: 1.3; }
  .fleet-ladder b { display: block; font-size: .78rem; color: var(--c); }
  .fleet-ladder span { color: var(--muted); }
  @media (max-width: 760px) { .fleet-ladder { grid-template-columns: repeat(4, 1fr); } }
  @media (max-width: 420px) { .fleet-ladder { grid-template-columns: repeat(2, 1fr); } }

  /* ---- Heatmap ---- */
  .fleet-heat-wrap { overflow-x: auto; margin: 1rem 0 .4rem; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); }
  table.fleet-heat { border-collapse: separate; border-spacing: 3px; margin: .6rem; font-size: .8rem; min-width: 740px; }
  table.fleet-heat th { font-weight: 700; color: var(--muted); text-align: left; padding: .2rem .4rem; white-space: nowrap; }
  table.fleet-heat thead th { vertical-align: bottom; }
  table.fleet-heat thead th button { font: inherit; font-weight: 700; color: var(--muted); background: none; border: 0; padding: .2rem .25rem; cursor: pointer; border-radius: 6px; writing-mode: vertical-rl; transform: rotate(180deg); line-height: 1; }
  table.fleet-heat thead th button:hover, table.fleet-heat thead th button[aria-pressed="true"] { color: var(--accent); background: var(--wash-a); }
  table.fleet-heat tbody th { color: var(--ink); }
  table.fleet-heat tbody th i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: .45rem; background: var(--c); vertical-align: -1px; }
  table.fleet-heat td { width: 40px; height: 30px; border-radius: 5px; text-align: center; font-variant-numeric: tabular-nums; font-size: .68rem; color: var(--ink); background: hsl(var(--fleet-heat-hue) 92% / .35); }
  table.fleet-heat td[data-l] { background: color-mix(in oklab, var(--accent-2) calc(var(--l) * 1%), var(--card)); color: var(--ink); }
  table.fleet-heat td[data-l="0"] { background: var(--wash-b); color: var(--muted); }
  table.fleet-heat td.hi { outline: 2px solid var(--accent); }
  .fleet-heat-note { font-size: .82rem; color: var(--muted); margin: .3rem .2rem 0; }

  /* ---- Cross-reference list ---- */
  .fleet-xrefs { display: grid; gap: .55rem; margin: 1rem 0 1.4rem; }
  .fleet-xrefs > div { display: grid; grid-template-columns: 220px 1fr; gap: .25rem 1rem; align-items: start; padding: .7rem .9rem; background: var(--card); border: 1px solid var(--line); border-radius: 10px; font-size: .9rem; }
  .fleet-xrefs .pair { font-weight: 700; display: flex; flex-wrap: wrap; align-items: center; gap: .3rem; }
  .fleet-xrefs .pair i { font-style: normal; color: var(--muted); font-weight: 400; }
  .fleet-xrefs .pair b { color: var(--c); }
  .fleet-xrefs .pair b.to { color: var(--c2); }
  .fleet-xrefs code { font-size: .8em; }
  .fleet-xrefs small { display: block; color: var(--muted); margin-top: .15rem; }
  @media (max-width: 640px) { .fleet-xrefs > div { grid-template-columns: 1fr; } }

  /* ---- Orchestration ---- */
  .fleet-orch { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1rem; margin: 1.2rem 0; }
  @media (max-width: 720px) { .fleet-orch { grid-template-columns: 1fr; } }
  .fleet-orch > div { padding: 1rem 1.1rem; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); }
  .fleet-orch h4 { margin: 0 0 .4rem; }
  .fleet-orch p { margin: 0; font-size: .92rem; }
  .fleet-orch code { font-size: .8em; }
  .fleet-caps-wrap { overflow-x: auto; margin: 1rem 0 .3rem; }
  table.fleet-caps { border-collapse: collapse; font-size: .82rem; min-width: 700px; width: 100%; }
  table.fleet-caps th, table.fleet-caps td { padding: .4rem .5rem; border-bottom: 1px solid var(--line); text-align: center; }
  table.fleet-caps th:first-child, table.fleet-caps td:first-child { text-align: left; white-space: nowrap; }
  table.fleet-caps thead th { font-size: .72rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; vertical-align: bottom; }
  table.fleet-caps td i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; vertical-align: -1px; }
  table.fleet-caps td i.e { background: var(--accent-2); }
  table.fleet-caps td i.d { border: 2px solid var(--accent); box-sizing: border-box; }
  table.fleet-caps td i.n { border: 1.5px solid var(--line); box-sizing: border-box; opacity: .7; }
  table.fleet-caps td i.x { background: none; width: auto; height: auto; color: var(--muted); font-style: normal; }
  .fleet-caps-key { font-size: .8rem; color: var(--muted); display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; margin: .4rem .1rem 0; }
  .fleet-caps-key i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; vertical-align: -1px; margin-right: .35rem; }
  .fleet-caps-key i.e { background: var(--accent-2); }
  .fleet-caps-key i.d { border: 2px solid var(--accent); box-sizing: border-box; }
  .fleet-caps-key i.n { border: 1.5px solid var(--line); box-sizing: border-box; }

  /* ---- Standard ---- */
  .fleet-standard { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .6rem 1.2rem; margin: 1rem 0 1.4rem; padding: 0; }
  @media (max-width: 640px) { .fleet-standard { grid-template-columns: 1fr; } }
  .page-content .fleet-standard > li { padding: .55rem .8rem .55rem 1rem; margin: 0; border-left: 3px solid var(--accent-2); background: var(--wash-b); border-radius: 0 8px 8px 0; font-size: .92rem; }
  .page-content .fleet-standard > li::before { display: none; }
  .page-content .fleet-standard > li b { display: block; }
  .fleet-standard code { font-size: .8em; }

  @media (prefers-reduced-motion: reduce) { .fleet-stage .node circle, .fleet-stage .edge, .mech-card { transition: none; } }
</style>

<div class="fleet-stats" aria-label="Fleet at a glance">
  <div><b>8</b><span>Mech knowledge bases</span></div>
  <div><b>445,478</b><span>curated records</span></div>
  <div><b>39</b><span>ontologies &amp; databases cited</span></div>
  <div><b>1</b><span>orchestrator (claw)</span></div>
</div>

<div class="fleet-ladder" aria-label="Scale ladder, from environment to medium">
  <div style="--c: var(--mech-habitatmech)"><b>Habitat</b><span>where it lives</span></div>
  <div style="--c: var(--mech-communitymech)"><b>Community</b><span>who it lives with</span></div>
  <div style="--c: var(--mech-traitmech)"><b>Traits</b><span>what it does</span></div>
  <div style="--c: var(--mech-cellstructuremech)"><b>Cell structures</b><span>what it is built of</span></div>
  <div style="--c: var(--mech-proteintraitsmech)"><b>Proteins</b><span>the machinery</span></div>
  <div style="--c: var(--mech-antibioticmech)"><b>Antibiotics</b><span>what acts on it</span></div>
  <div style="--c: var(--mech-mediaingredientmech)"><b>Ingredients</b><span>what it is fed</span></div>
  <div style="--c: var(--mech-culturemech)"><b>Media</b><span>where it is grown</span></div>
</div>

<div class="fleet-graph" id="fleet-graph">
  <div class="fleet-controls">
    <div class="grp" role="group" aria-label="Edge layers">
      <span>Layers</span>
      <button class="fleet-chip" data-layer="vocab" aria-pressed="true">Shared vocabulary</button>
      <button class="fleet-chip" data-layer="xref" aria-pressed="true">Cross-references</button>
      <button class="fleet-chip" data-layer="hub" aria-pressed="false">kg-microbe exchange</button>
      <button class="fleet-chip" data-layer="gov" aria-pressed="false">Governance</button>
    </div>
    <div class="spacer"></div>
    <div class="grp" role="group" aria-label="Filter shared vocabulary by ontology">
      <span>Vocabulary</span>
      <button class="fleet-chip voc" data-voc="" aria-pressed="true">All</button>
      <button class="fleet-chip voc" data-voc="CHEBI" aria-pressed="false">ChEBI</button>
      <button class="fleet-chip voc" data-voc="NCBITaxon" aria-pressed="false">NCBITaxon</button>
      <button class="fleet-chip voc" data-voc="GO" aria-pressed="false">GO</button>
      <button class="fleet-chip voc" data-voc="ENVO" aria-pressed="false">ENVO</button>
      <button class="fleet-chip voc" data-voc="METPO" aria-pressed="false">METPO</button>
      <button class="fleet-chip voc" data-voc="ARO" aria-pressed="false">ARO</button>
      <button class="fleet-chip voc" data-voc="UniProt" aria-pressed="false">UniProt</button>
      <button class="fleet-chip voc" data-voc="DOI" aria-pressed="false">Citations</button>
      <button class="fleet-chip voc other" id="fleet-voc-other" data-voc="" aria-pressed="true" hidden></button>
    </div>
  </div>
  <div class="fleet-stage">
    <svg id="fleet-svg" viewBox="0 0 900 760" role="group" aria-labelledby="fleet-svg-title fleet-svg-desc">
      <title id="fleet-svg-title">Relationship graph of the eight Mech knowledge bases</title>
      <desc id="fleet-svg-desc">Nodes are Mechs arranged in a ring from habitat to culture medium; chords are shared ontology terms, dashed arcs are direct cross-references, and spokes connect to the central kg-microbe knowledge graph.</desc>
      <defs>
        <marker id="fleet-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="arrow" d="M0,0 L10,5 L0,10 z"></path></marker>
        <marker id="fleet-arrow-hub" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path class="arrow-hub" d="M0,0 L10,5 L0,10 z"></path></marker>
      </defs>
      <g id="fleet-gov"></g>
      <g id="fleet-edges"></g>
      <g id="fleet-hubedges"></g>
      <g id="fleet-hub"></g>
      <g id="fleet-nodes"></g>
    </svg>
    <div class="fleet-tip" id="fleet-tip" aria-hidden="true"></div>
  </div>
  <div class="fleet-legend">
    <span><i></i>shared ontology terms (width = how many)</span>
    <span><i class="x"></i>direct cross-reference (arrow = who consumes)</span>
    <span><i class="h"></i>export to / input from kg-microbe</span>
    <span><i class="g"></i>fleet manifest membership</span>
  </div>
  <div class="fleet-detail" id="fleet-detail"></div>
</div>

<script>
(function () {
  "use strict";
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); } else { init(); }
  function init() {
  var DATA = {"order":["HabitatMech","CommunityMech","TraitMech","CellStructureMech","ProteinTraitsMech","AntibioticMech","MediaIngredientMech","CultureMech"],"voc":["CHEBI","NCBITaxon","GO","ENVO","METPO","ARO","UniProt","InterPro","Pfam","RHEA","PDB","PATO","UBERON","FOODON","BTO","GTDB","KEGG","CAS","PMID","DOI"],"heat":{"HabitatMech":{"CHEBI":18,"NCBITaxon":13221,"GO":2,"ENVO":3154,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":4,"UBERON":1088,"FOODON":190,"BTO":1353,"GTDB":0,"KEGG":0,"CAS":0,"PMID":513,"DOI":112},"CommunityMech":{"CHEBI":2204,"NCBITaxon":3012,"GO":850,"ENVO":362,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":9,"FOODON":0,"BTO":0,"GTDB":1662,"KEGG":0,"CAS":0,"PMID":4729,"DOI":1122},"TraitMech":{"CHEBI":667,"NCBITaxon":844,"GO":810,"ENVO":22,"METPO":3190,"ARO":0,"UniProt":389,"InterPro":113,"Pfam":0,"RHEA":0,"PDB":0,"PATO":97,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":0,"PMID":412,"DOI":5265},"CellStructureMech":{"CHEBI":16,"NCBITaxon":175,"GO":230,"ENVO":0,"METPO":14,"ARO":0,"UniProt":116,"InterPro":4,"Pfam":15,"RHEA":0,"PDB":4,"PATO":0,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":0,"PMID":67,"DOI":902},"ProteinTraitsMech":{"CHEBI":373461,"NCBITaxon":357752,"GO":417184,"ENVO":0,"METPO":244,"ARO":194924,"UniProt":656717,"InterPro":1477316,"Pfam":520297,"RHEA":613318,"PDB":235943,"PATO":110,"UBERON":43,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":245,"CAS":0,"PMID":654089,"DOI":187928},"AntibioticMech":{"CHEBI":22087,"NCBITaxon":590,"GO":3,"ENVO":0,"METPO":0,"ARO":16653,"UniProt":318,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":3,"PATO":0,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":1835,"PMID":952,"DOI":16},"MediaIngredientMech":{"CHEBI":7497,"NCBITaxon":1,"GO":0,"ENVO":110,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":22,"FOODON":270,"BTO":3,"GTDB":0,"KEGG":53,"CAS":655,"PMID":29,"DOI":5},"CultureMech":{"CHEBI":160660,"NCBITaxon":63,"GO":0,"ENVO":13,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":138,"FOODON":214,"BTO":0,"GTDB":0,"KEGG":1406,"CAS":1,"PMID":68,"DOI":76}},"vocab_edges":[{"a":"CultureMech","b":"MediaIngredientMech","n":608,"by":{"CHEBI":543,"KEGG":53,"FOODON":6,"UBERON":3,"CAS":1,"DOI":1,"ENVO":1},"ex":[{"id":"CHEBI:86202","label":"chalcopyrite"},{"id":"CHEBI:41218","label":"mercaptoethanol"},{"id":"CHEBI:26642","label":"selenous acid"}]},{"a":"CultureMech","b":"CommunityMech","n":165,"by":{"CHEBI":138,"DOI":10,"NCBITaxon":6,"PMID":6,"ENVO":5},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:86202","label":"chalcopyrite"},{"id":"CHEBI:16828","label":"L-tryptophan"}]},{"a":"CultureMech","b":"AntibioticMech","n":30,"by":{"CHEBI":29,"DOI":1},"ex":[{"id":"CHEBI:15882","label":"phenol"},{"id":"CHEBI:132112","label":"sodium thiosulfate"},{"id":"CHEBI:72449","label":"malachite green"}]},{"a":"CultureMech","b":"TraitMech","n":49,"by":{"CHEBI":27,"DOI":12,"NCBITaxon":10},"ex":[{"id":"NCBITaxon:160233","label":"Ignicoccus hospitalis"},{"id":"NCBITaxon:851","label":"Fusobacterium nucleatum"},{"id":"NCBITaxon:210","label":"Helicobacter pylori"}]},{"a":"CultureMech","b":"ProteinTraitsMech","n":246,"by":{"CHEBI":222,"DOI":12,"NCBITaxon":10,"UBERON":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:16870","label":"choline alfoscerate"}]},{"a":"CultureMech","b":"CellStructureMech","n":11,"by":{"DOI":7,"NCBITaxon":2,"CHEBI":2},"ex":[{"id":"NCBITaxon:1148","label":"Synechocystis sp. PCC 6803"},{"id":"NCBITaxon:2261","label":"Pyrococcus furiosus"},{"id":"CHEBI:16526","label":"carbon dioxide"}]},{"a":"CultureMech","b":"HabitatMech","n":32,"by":{"NCBITaxon":13,"ENVO":7,"DOI":7,"UBERON":4,"FOODON":1},"ex":[{"id":"NCBITaxon:210","label":"Helicobacter pylori"},{"id":"ENVO:00005801","label":"rhizosphere"},{"id":"ENVO:00002170","label":"compost"}]},{"a":"MediaIngredientMech","b":"CommunityMech","n":235,"by":{"CHEBI":230,"DOI":3,"ENVO":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:86202","label":"chalcopyrite"},{"id":"CHEBI:16828","label":"L-tryptophan"}]},{"a":"MediaIngredientMech","b":"AntibioticMech","n":334,"by":{"CHEBI":332,"DOI":2},"ex":[{"id":"CHEBI:46742","label":"Nutlin-3"},{"id":"CHEBI:27666","label":"actinomycin D"},{"id":"CHEBI:478164","label":"cefepime"}]},{"a":"MediaIngredientMech","b":"TraitMech","n":61,"by":{"CHEBI":58,"DOI":3},"ex":[{"id":"CHEBI:16842","label":"formaldehyde"},{"id":"CHEBI:15354","label":"choline"},{"id":"CHEBI:16526","label":"carbon dioxide"}]},{"a":"MediaIngredientMech","b":"ProteinTraitsMech","n":792,"by":{"CHEBI":788,"DOI":3,"UBERON":1},"ex":[{"id":"CHEBI:16335","label":"adenosine"},{"id":"UBERON:0000955","label":"brain"}]},{"a":"MediaIngredientMech","b":"CellStructureMech","n":7,"by":{"CHEBI":5,"DOI":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:18248","label":"iron atom"}]},{"a":"MediaIngredientMech","b":"HabitatMech","n":21,"by":{"ENVO":15,"UBERON":4,"CHEBI":1,"DOI":1},"ex":[{"id":"ENVO:00000051","label":"hot spring"},{"id":"ENVO:00001998","label":"soil"},{"id":"ENVO:00002263","label":"garden soil"}]},{"a":"CommunityMech","b":"AntibioticMech","n":50,"by":{"CHEBI":38,"NCBITaxon":8,"DOI":4},"ex":[{"id":"CHEBI:16842","label":"formaldehyde"},{"id":"NCBITaxon:2697049","label":"Severe acute respiratory syndrome coronavirus 2"},{"id":"NCBITaxon:4932","label":"Saccharomyces cerevisiae"}]},{"a":"CommunityMech","b":"TraitMech","n":158,"by":{"CHEBI":59,"NCBITaxon":46,"GO":29,"DOI":23,"PMID":1},"ex":[{"id":"NCBITaxon:382","label":"Sinorhizobium meliloti"},{"id":"NCBITaxon:243232","label":"Methanocaldococcus jannaschii DSM 2661"},{"id":"NCBITaxon:83333","label":"Escherichia coli K-12"}]},{"a":"CommunityMech","b":"ProteinTraitsMech","n":653,"by":{"CHEBI":265,"NCBITaxon":188,"GO":173,"DOI":24,"PMID":2,"UBERON":1},"ex":[{"id":"GO:0046274","label":"lignin catabolic process"},{"id":"GO:0046359","label":"butyrate catabolic process"},{"id":"GO:0010038","label":"response to metal ion"}]},{"a":"CommunityMech","b":"CellStructureMech","n":48,"by":{"NCBITaxon":20,"DOI":16,"CHEBI":7,"GO":5},"ex":[{"id":"NCBITaxon:1515","label":"Acetivibrio thermocellus"},{"id":"NCBITaxon:2","label":"Bacteria"},{"id":"NCBITaxon:203682","label":"Planctomycetota"}]},{"a":"CommunityMech","b":"HabitatMech","n":268,"by":{"NCBITaxon":212,"ENVO":39,"DOI":11,"UBERON":4,"CHEBI":1,"PMID":1},"ex":[{"id":"NCBITaxon:1682","label":"Bifidobacterium longum subsp. infantis"},{"id":"NCBITaxon:1582","label":"Lacticaseibacillus casei"},{"id":"NCBITaxon:382","label":"Sinorhizobium meliloti"}]},{"a":"AntibioticMech","b":"TraitMech","n":21,"by":{"CHEBI":10,"NCBITaxon":6,"DOI":5},"ex":[{"id":"CHEBI:16842","label":"formaldehyde"},{"id":"CHEBI:16240","label":"hydrogen peroxide"},{"id":"NCBITaxon:632","label":"Yersinia pestis"}]},{"a":"AntibioticMech","b":"ProteinTraitsMech","n":2454,"by":{"ARO":1753,"CHEBI":594,"NCBITaxon":41,"PMID":35,"UniProt":24,"DOI":5,"GO":2},"ex":[{"id":"ARO:3004543","label":"mphO"},{"id":"ARO:3002598","label":"ANT(3')-II-AAC(6')-IId bifunctional protein"},{"id":"ARO:3004181","label":"Streptococcus pneumoniae 23S rRNA mutation conferring resistance to macrolides"}]},{"a":"AntibioticMech","b":"CellStructureMech","n":7,"by":{"DOI":4,"NCBITaxon":3},"ex":[{"id":"NCBITaxon:1773","label":"Mycobacterium tuberculosis"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"},{"id":"NCBITaxon:83332","label":"Mycobacterium tuberculosis H37Rv"}]},{"a":"AntibioticMech","b":"HabitatMech","n":13,"by":{"NCBITaxon":10,"DOI":3},"ex":[{"id":"NCBITaxon:1773","label":"Mycobacterium tuberculosis"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"}]},{"a":"TraitMech","b":"ProteinTraitsMech","n":698,"by":{"GO":212,"NCBITaxon":118,"CHEBI":111,"METPO":90,"DOI":52,"UniProt":49,"InterPro":46,"PMID":20},"ex":[{"id":"METPO:1000631","label":"trophic type"},{"id":"METPO:1000846","label":"Homoacetogenesis"},{"id":"METPO:1000626","label":"stenohaline"}]},{"a":"TraitMech","b":"CellStructureMech","n":92,"by":{"GO":30,"NCBITaxon":24,"DOI":21,"CHEBI":6,"METPO":5,"UniProt":4,"InterPro":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"NCBITaxon:224308","label":"Bacillus subtilis 168"}]},{"a":"TraitMech","b":"HabitatMech","n":116,"by":{"NCBITaxon":95,"DOI":14,"ENVO":4,"PATO":2,"PMID":1},"ex":[{"id":"NCBITaxon:382","label":"Sinorhizobium meliloti"},{"id":"NCBITaxon:243232","label":"Methanocaldococcus jannaschii DSM 2661"},{"id":"NCBITaxon:521674","label":"Planctopirus limnophila DSM 3776"}]},{"a":"ProteinTraitsMech","b":"CellStructureMech","n":257,"by":{"GO":92,"UniProt":87,"NCBITaxon":27,"DOI":22,"PMID":10,"Pfam":8,"CHEBI":7,"InterPro":4},"ex":[{"id":"GO:0097589","label":"archaeal-type flagellum"},{"id":"GO:0042651","label":"thylakoid membrane"},{"id":"CHEBI:16526","label":"carbon dioxide"}]},{"a":"ProteinTraitsMech","b":"HabitatMech","n":1261,"by":{"NCBITaxon":1231,"DOI":16,"UBERON":12,"CHEBI":1,"GO":1},"ex":[{"id":"UBERON:0000955","label":"brain"},{"id":"UBERON:0002097","label":"skin of body"}]},{"a":"CellStructureMech","b":"HabitatMech","n":35,"by":{"NCBITaxon":23,"DOI":12},"ex":[{"id":"NCBITaxon:1515","label":"Acetivibrio thermocellus"},{"id":"NCBITaxon:2","label":"Bacteria"},{"id":"NCBITaxon:103690","label":"Nostoc sp. PCC 7120"}]}]};

  var MECHS = {
    HabitatMech: { key: "habitatmech", scale: "Habitat", tag: "Four habitat vocabularies harmonized into ENVO-grounded records that keep every source's attestation.", records: 3213, unit: "habitat records", root: "HabitatRecord", vocab: ["ENVO", "NCBITaxon", "BTO", "UBERON", "FOODON"], github: "https://github.com/CultureBotAI/HabitatMech", site: "https://culturebotai.github.io/HabitatMech/", page: "", license: "CC0-1.0", sources: "JGI GOLD ecosystem paths, BacDive isolation sources, PREGO, Madin et al.; ENVO/UBERON/FOODON/BTO via kg-microbe", member: false, extra: "684 records reviewed (21%); 3,213 seeded from GOLD, BacDive, PREGO and Madin et al.; 174 attested by two or more sources." },
    CommunityMech: { key: "communitymech", scale: "Community", tag: "Curated knowledge base of microbial communities, their interactions, cultivation and evidence.", records: 325, unit: "community records", root: "MicrobialCommunity", vocab: ["NCBITaxon", "CHEBI", "GO", "ENVO", "GTDB"], github: "https://github.com/CultureBotAI/CommunityMech", site: "https://culturebotai.github.io/CommunityMech/", page: "/communitymech/", license: "BSD-3-Clause", sources: "PubMed literature, GTDB, IMG, BioModels, CultureMech media, MediaIngredientMech ingredients", member: true, extra: "Publishes KGX nodes and edges to kg-microbe; 21 community records link their cultivation media to CultureMech by stable id." },
    TraitMech: { key: "traitmech", scale: "Traits", tag: "Microbial ecophysiological trait knowledge base, seeded from METPO, one curated YAML per trait.", records: 477, unit: "trait records", root: "TraitRecord", vocab: ["METPO", "GO", "NCBITaxon", "CHEBI", "UniProt"], github: "https://github.com/CultureBotAI/TraitMech", site: "https://culturebotai.github.io/TraitMech/", page: "", license: "CC0-1.0", sources: "METPO (vendored OWL), GapMind and GTDB genome tables as candidates", member: true, extra: "427 reviewed, 353 carry evidence-backed causal mechanism graphs; METPO term proposals published as SSSOM." },
    CellStructureMech: { key: "cellstructuremech", scale: "Cell structures", tag: "Ontology-grounded microbial cell structures: components, distribution, function and causal mechanism.", records: 39, unit: "structure records", root: "CellStructureRecord", vocab: ["GO", "NCBITaxon", "UniProt", "METPO", "Pfam"], github: "https://github.com/CultureBotAI/CellStructureMech", site: "https://culturebotai.github.io/CellStructureMech/", page: "", license: "CC0-1.0", sources: "GO cellular component, UniProt subcellular location, Complex Portal, EMDB/EMPIAR, PDB, TraitMech", member: true, extra: "Fills the layer between phenotype (TraitMech) and protein (ProteinTraitsMech); 39 causal graphs with 279 evidence-backed edges." },
    ProteinTraitsMech: { key: "proteintraitsmech", scale: "Proteins", tag: "Protein sequence, structure and function trait classes, one curated YAML per trait, evidence-backed.", records: 429271, unit: "protein trait records", root: "ProteinTraitRecord", vocab: ["InterPro", "UniProt", "RHEA", "Pfam", "GO", "CHEBI", "ARO"], github: "https://github.com/CultureBotAI/proteintraitsmech", site: "https://culturebotai.github.io/proteintraitsmech/", page: "", license: "CC0-1.0", sources: "InterPro, Pfam, CATH, SCOPe, ECOD, Rhea, ExPASy ENZYME, CARD/ARO, PROSITE, TCDB, COG, Reactome, METPO", member: true, extra: "Function 163,526 · sequence 147,071 · structure 118,281 · sequence-structure and evolution 393 records; seeds 118 METPO classes with protein-level analogues." },
    AntibioticMech: { key: "antibioticmech", scale: "Antibiotics", tag: "One record per antimicrobial structure, harmonizing ChEBI and CARD with mechanism and evidence.", records: 2909, unit: "antimicrobial structures", root: "AntibioticRecord", vocab: ["CHEBI", "ARO", "CAS", "NCBITaxon", "PubChem", "DrugBank"], github: "https://github.com/CultureBotAI/AntibioticMech", site: "https://culturebotai.github.io/AntibioticMech/", page: "", license: "CC0-1.0 code · CC BY 4.0 data", sources: "ChEBI 3-star antimicrobial roles, CARD/ARO antibiotic molecules, PubChem structures, PHI-base, MIBiG", member: true, extra: "2,669 ChEBI-grounded, 240 minted; 417 with a mode of action, 245 with a molecular target, 16 with a curated causal graph." },
    MediaIngredientMech: { key: "mediaingredientmech", scale: "Ingredients", tag: "LLM-assisted curation of media-ingredient ontology mappings with full audit trails.", records: 2958, unit: "ingredient records", root: "IngredientRecord", vocab: ["CHEBI", "CAS", "NCIT", "FOODON", "ENVO"], github: "https://github.com/CultureBotAI/MediaIngredientMech", site: "https://culturebotai.github.io/MediaIngredientMech/", page: "/mediaingredientmech/", license: "CC0-1.0", sources: "Ingredient strings aggregated from CultureMech recipes; OAK/OLS term services; ChEBI, FOODON, NCIT, MeSH, METPO", member: true, extra: "2,684 mapped (91%); its published SSSOM is the ingredient-mapping contract consumed by kg-microbe." },
    CultureMech: { key: "culturemech", scale: "Media", tag: "Versioned, ontology-grounded knowledge base of microbial culture-media recipes.", records: 6286, unit: "merged recipes", root: "MediaRecipe", vocab: ["CHEBI", "KEGG", "FOODON", "UBERON", "CAS"], github: "https://github.com/CultureBotAI/CultureMech", site: "https://culturebotai.github.io/CultureMech/", page: "/culturemech/", license: "CC0-1.0", sources: "MediaDive/DSMZ, TogoMedium, KOMODO, ATCC, JCM, BacDive (queued)", member: true, extra: "15,877 normalized recipes deduplicated into 6,286 merged canonical records; exports 11 SSSOM mapping sets." }
  };

  // Directed cross-references between Mech records, schemas and curation practice.
  var XREFS = [
    { from: "CultureMech", to: "MediaIngredientMech", kind: "data", what: "Unmapped ingredient strings and occurrence counts feed MIM's curation backlog; MIM records carry CultureMech:NNNNNN back-links by stable id.", ev: "MIM schema CultureMechReference; claw ingredient_curation_pipeline" },
    { from: "MediaIngredientMech", to: "CultureMech", kind: "data", what: "Curated ChEBI/FOODON mappings sync back to recipes; CultureMech vendors MIM's ingredient-role enums and consumes its label index.", ev: "CultureMech src/culturemech/schema/mim_roles.yaml" },
    { from: "CommunityMech", to: "CultureMech", kind: "data", what: "Community records name the medium they were grown in by CultureMech id (culturemech_id on 21 records, 32 links).", ev: "CommunityMech docs/cross_repo_linking.md" },
    { from: "CommunityMech", to: "MediaIngredientMech", kind: "schema", what: "RelatedIngredient.mediaingredientmech_id slot is declared for MIM ingredient ids; no record populates it yet.", ev: "CommunityMech docs/cross_repo_linking.md" },
    { from: "CellStructureMech", to: "TraitMech", kind: "data", what: "Structures list the phenotypes they confer as TraitMech / METPO terms (8 trait links); causal-graph node vocabulary is TraitMech's plus STRUCTURE.", ev: "CellStructureMech schema associated_traits" },
    { from: "CellStructureMech", to: "ProteinTraitsMech", kind: "schema", what: "A single protein is a component, not a record: it grounds to InterPro / UniProtKB and hands off to ProteinTraitsMech.", ev: "CellStructureMech docs/CURATION.md" },
    { from: "HabitatMech", to: "TraitMech", kind: "schema", what: "Habitat causal graphs use a superset of TraitMech's node vocabulary so graphs stay comparable; a node may be a TraitMech or METPO term.", ev: "HabitatMech schema CausalNode" },
    { from: "HabitatMech", to: "CultureMech", kind: "practice", what: "The one overlapping concept, BTO:0000316 culture medium, is handed to CultureMech rather than curated twice.", ev: "HabitatMech curation/decisions.tsv" },
    { from: "AntibioticMech", to: "CellStructureMech", kind: "practice", what: "The licensed source-queue curation pattern was written here and adapted by CellStructureMech.", ev: "claw docs/guides/SOURCE_QUEUE.md" },
    { from: "ProteinTraitsMech", to: "TraitMech", kind: "practice", what: "TraitMech adopted ProteinTraitsMech's download.yaml source catalogue shape; a drift audit keeps shared trait tokens aligned.", ev: "TraitMech download.yaml; ProteinTraitsMech justfile" }
  ];

  // Exchange with the central kg-microbe knowledge graph.
  var HUB = [
    { mech: "CultureMech", dir: "out", what: "SSSOM mapping sets (11 files) and a KGX sample" },
    { mech: "MediaIngredientMech", dir: "out", what: "canonical ingredient SSSOM, the mapping contract kg-microbe consumes" },
    { mech: "CommunityMech", dir: "out", what: "KGX nodes and edges release" },
    { mech: "TraitMech", dir: "out", what: "METPO term proposals as SSSOM" },
    { mech: "HabitatMech", dir: "in", what: "ENVO / UBERON / FOODON / BTO in KGX form plus the curated isolation-source table" },
    { mech: "CommunityMech", dir: "in", what: "merged knowledge-graph edges vendored for the browser" },
    { mech: "MediaIngredientMech", dir: "in", what: "unified entity mappings and alternate labels" }
  ];

  var order = DATA.order, N = order.length;
  var W = 900, H = 760, CX = 450, CY = 372, R = 262;
  var pos = {};
  order.forEach(function (m, i) {
    var a = -Math.PI / 2 + i * (2 * Math.PI / N);
    pos[m] = { x: CX + R * Math.cos(a), y: CY + R * Math.sin(a), a: a };
  });
  function radius(m) { return 14 + 5.5 * Math.log10(MECHS[m].records); }
  function color(m) { return "var(--mech-" + MECHS[m].key + ")"; }
  function fmt(n) { return n.toLocaleString("en-US"); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var SVG = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) {
    var e = document.createElementNS(SVG, tag);
    for (var k in attrs) { if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]); }
    if (parent) parent.appendChild(e);
    return e;
  }
  function chord(a, b, bow) {
    var p = pos[a], q = pos[b], mx = (p.x + q.x) / 2, my = (p.y + q.y) / 2;
    var cx = mx + (CX - mx) * bow, cy = my + (CY - my) * bow;
    return "M" + p.x + "," + p.y + " Q" + cx + "," + cy + " " + q.x + "," + q.y;
  }
  function trimmed(a, b, bow, ra, rb) {
    // Curve between node edges (not centers) so arrowheads land on the circle.
    var p = pos[a], q = pos[b], mx = (p.x + q.x) / 2, my = (p.y + q.y) / 2;
    var cx = mx + (CX - mx) * bow, cy = my + (CY - my) * bow;
    function tow(fromx, fromy, tox, toy, r) { var dx = tox - fromx, dy = toy - fromy, d = Math.hypot(dx, dy); return [fromx + dx / d * r, fromy + dy / d * r]; }
    var s = tow(p.x, p.y, cx, cy, ra), e = tow(q.x, q.y, cx, cy, rb);
    return "M" + s[0] + "," + s[1] + " Q" + cx + "," + cy + " " + e[0] + "," + e[1];
  }

  var svg = document.getElementById("fleet-svg");
  var gGov = document.getElementById("fleet-gov"), gEdges = document.getElementById("fleet-edges"), gHubE = document.getElementById("fleet-hubedges"), gHub = document.getElementById("fleet-hub"), gNodes = document.getElementById("fleet-nodes");
  var tip = document.getElementById("fleet-tip"), detail = document.getElementById("fleet-detail");
  var state = { layers: { vocab: true, xref: true, hub: false, gov: false }, voc: "", sel: null };

  // Governance ring + axis labels
  el("circle", { "class": "ring", cx: CX, cy: CY, r: R + 58 }, gGov);
  var rl = el("text", { "class": "ring-label", x: CX, y: CY - R - 66, "text-anchor": "middle" }, gGov);
  rl.textContent = "CULTUREBOTAI-CLAW · FLEET MANIFEST · VENDORED GOVERNANCE";
  var ticks = {};
  order.forEach(function (m) {
    var p = pos[m], r1 = R + 58, r0 = radius(m) + 6;
    var t = el("line", { "class": "edge gov", x1: CX + Math.cos(p.a) * r0, y1: CY + Math.sin(p.a) * r0, x2: CX + Math.cos(p.a) * r1, y2: CY + Math.sin(p.a) * r1 }, gGov);
    if (!MECHS[m].member) { t.setAttribute("stroke-dasharray", "1 5"); t.setAttribute("opacity", ".45"); }
    ticks[m] = t;
  });

  // Vocabulary chords
  var vocabEls = [];
  DATA.vocab_edges.forEach(function (e) {
    var d = chord(e.a, e.b, 0.55);
    var path = el("path", { "class": "edge vocab", d: d }, gEdges);
    var hit = el("path", { "class": "edge hit", d: d }, gEdges);
    var rec = { e: e, path: path, hit: hit, n: e.n };
    vocabEls.push(rec);
    [path, hit].forEach(function (h) {
      h.addEventListener("mousemove", function (ev) { showTip(ev, vocabTip(rec)); light(rec.path); });
      h.addEventListener("mouseleave", function () { hideTip(); unlight(rec.path); });
      h.addEventListener("click", function () { selectEdge(rec); });
    });
  });
  function vocabWeight(rec) { return state.voc ? (rec.e.by[state.voc] || 0) : rec.e.n; }
  function widthFor(n) { return n <= 0 ? 0 : Math.max(0.9, 1 + 2.3 * Math.log10(n / 4)); }

  // Cross-reference arcs
  var xrefEls = XREFS.map(function (x, i) {
    // A reverse-direction pair gets a deeper bow so the two arcs stay apart.
    var reverse = XREFS.some(function (y, j) { return j < i && y.from === x.to && y.to === x.from; });
    var d = trimmed(x.from, x.to, reverse ? -0.62 : -0.38, radius(x.from) + 3, radius(x.to) + 5);
    var path = el("path", { "class": "edge xref" + (x.kind === "data" ? "" : " weak"), d: d, "marker-end": "url(#fleet-arrow)" }, gEdges);
    var hit = el("path", { "class": "edge hit", d: d }, gEdges);
    var rec = { x: x, path: path, hit: hit };
    [path, hit].forEach(function (h) {
      h.addEventListener("mousemove", function (ev) { showTip(ev, xrefTip(x)); light(path); });
      h.addEventListener("mouseleave", function () { hideTip(); unlight(path); });
      h.addEventListener("click", function () { selectXref(rec); });
    });
    return rec;
  });

  // Hub + spokes
  var hubR = 46;
  var hubEls = HUB.map(function (h) {
    var p = pos[h.mech], dx = CX - p.x, dy = CY - p.y, d = Math.hypot(dx, dy);
    var ux = dx / d, uy = dy / d, off = h.dir === "out" ? 6 : -6; // parallel offset so in/out pairs do not overlap
    var px = -uy * off, py = ux * off;
    var x1 = p.x + ux * (radius(h.mech) + 4) + px, y1 = p.y + uy * (radius(h.mech) + 4) + py;
    var x2 = CX - ux * (hubR + 4) + px, y2 = CY - uy * (hubR + 4) + py;
    var attrs = { "class": "edge hub " + h.dir };
    if (h.dir === "out") { attrs.x1 = x1; attrs.y1 = y1; attrs.x2 = x2; attrs.y2 = y2; } else { attrs.x1 = x2; attrs.y1 = y2; attrs.x2 = x1; attrs.y2 = y1; }
    attrs["marker-end"] = "url(#fleet-arrow-hub)";
    var line = el("line", attrs, gHubE);
    var hit = el("line", { "class": "edge hit", x1: x1, y1: y1, x2: x2, y2: y2 }, gHubE);
    [line, hit].forEach(function (q) {
      q.addEventListener("mousemove", function (ev) { showTip(ev, "<b>" + esc(h.mech) + (h.dir === "out" ? " → kg-microbe" : " ← kg-microbe") + "</b>" + esc(h.what)); });
      q.addEventListener("mouseleave", hideTip);
    });
    return { h: h, line: line, hit: hit };
  });
  el("circle", { "class": "hub", cx: CX, cy: CY, r: hubR }, gHub);
  var ht = el("text", { "class": "hub-label", x: CX, y: CY - 2, "text-anchor": "middle" }, gHub); ht.textContent = "kg-microbe";
  var hs = el("text", { "class": "hub-sub", x: CX, y: CY + 12, "text-anchor": "middle" }, gHub); hs.textContent = "knowledge graph";
  gHub.style.cursor = "pointer";
  gHub.addEventListener("click", function () { state.layers.hub = true; syncLayerChips(); selectHub(); });

  // Nodes
  var nodeEls = {};
  order.forEach(function (m) {
    var p = pos[m], r = radius(m), M = MECHS[m];
    var g = el("g", { "class": "node" + (M.member ? "" : " adjacent"), tabindex: 0, role: "button", "aria-label": m + ", " + fmt(M.records) + " " + M.unit }, gNodes);
    el("circle", { cx: p.x, cy: p.y, r: r, fill: color(m) }, g);
    var outside = Math.cos(p.a) > 0.2 ? "start" : Math.cos(p.a) < -0.2 ? "end" : "middle";
    var lx = p.x + Math.cos(p.a) * (r + 10), ly = p.y + Math.sin(p.a) * (r + 10);
    var dy = Math.sin(p.a) > 0.6 ? 14 : Math.sin(p.a) < -0.6 ? -10 : 4;
    var t = el("text", { "class": "node-label", x: lx, y: ly + dy, "text-anchor": outside }, g); t.textContent = m;
    var s = el("text", { "class": "node-sub", x: lx, y: ly + dy + 14, "text-anchor": outside }, g); s.textContent = fmt(M.records) + " " + M.unit;
    g.addEventListener("click", function () { selectNode(m); });
    g.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectNode(m); } });
    g.addEventListener("mouseenter", function () { hoverNode(m, true); });
    g.addEventListener("mouseleave", function () { hoverNode(m, false); });
    nodeEls[m] = g;
  });

  // ---- Rendering state ----
  function render() {
    gGov.style.display = state.layers.gov ? "" : "none";
    gHubE.style.display = state.layers.hub ? "" : "none";
    vocabEls.forEach(function (rec) {
      var w = vocabWeight(rec), show = state.layers.vocab && w > 0;
      rec.path.style.display = show ? "" : "none"; rec.hit.style.display = show ? "" : "none";
      rec.path.setAttribute("stroke-width", widthFor(w).toFixed(2));
      rec.path.style.stroke = state.voc ? "var(--accent-2)" : "";
    });
    xrefEls.forEach(function (rec) { var s = state.layers.xref ? "" : "none"; rec.path.style.display = s; rec.hit.style.display = s; });
    applySelection();
  }
  function applySelection() {
    var sel = state.sel;
    order.forEach(function (m) { nodeEls[m].classList.toggle("dim", !!sel && sel.type === "node" && sel.m !== m && !connected(sel.m, m)); });
    vocabEls.forEach(function (rec) {
      var on = !sel || (sel.type === "node" ? (rec.e.a === sel.m || rec.e.b === sel.m) : sel.type === "edge" ? sel.rec === rec : false);
      rec.path.classList.toggle("dim", !on);
      rec.path.style.stroke = (sel && sel.type === "node" && on) ? color(sel.m) : (state.voc ? "var(--accent-2)" : "");
    });
    xrefEls.forEach(function (rec) {
      var on = !sel || (sel.type === "node" ? (rec.x.from === sel.m || rec.x.to === sel.m) : sel.type === "xref" ? sel.rec === rec : false);
      rec.path.classList.toggle("dim", !on);
    });
    hubEls.forEach(function (rec) { rec.line.classList.toggle("dim", !!sel && (sel.type === "node" ? rec.h.mech !== sel.m : sel.type !== "hub")); });
    document.querySelectorAll(".mech-card").forEach(function (c) { c.classList.toggle("lit", !!sel && sel.type === "node" && c.dataset.mech === sel.m); });
  }
  function connected(a, b) {
    var w = false;
    vocabEls.forEach(function (rec) { if (vocabWeight(rec) > 0 && state.layers.vocab && ((rec.e.a === a && rec.e.b === b) || (rec.e.a === b && rec.e.b === a))) w = true; });
    XREFS.forEach(function (x) { if (state.layers.xref && ((x.from === a && x.to === b) || (x.from === b && x.to === a))) w = true; });
    return w;
  }
  function light(p) { p.classList.add("lit"); }
  function unlight(p) { p.classList.remove("lit"); }
  function hoverNode(m, on) {
    if (state.sel) return;
    order.forEach(function (o) { nodeEls[o].classList.toggle("dim", on && o !== m && !connected(m, o)); });
    vocabEls.forEach(function (rec) { var mine = rec.e.a === m || rec.e.b === m; rec.path.classList.toggle("dim", on && !mine); rec.path.style.stroke = (on && mine) ? color(m) : (state.voc ? "var(--accent-2)" : ""); });
    xrefEls.forEach(function (rec) { rec.path.classList.toggle("dim", on && rec.x.from !== m && rec.x.to !== m); });
    hubEls.forEach(function (rec) { rec.line.classList.toggle("dim", on && rec.h.mech !== m); });
  }

  // ---- Tooltips ----
  function showTip(ev, html) {
    var stage = svg.parentNode.getBoundingClientRect();
    tip.innerHTML = html; tip.classList.add("show");
    var x = ev.clientX - stage.left + 14, y = ev.clientY - stage.top + 14;
    if (x + 310 > stage.width) x = Math.max(4, ev.clientX - stage.left - 314);
    tip.style.left = x + "px"; tip.style.top = y + "px";
  }
  function hideTip() { tip.classList.remove("show"); }
  function vocabTip(rec) {
    var e = rec.e, parts = [];
    Object.keys(e.by).sort(function (a, b) { return e.by[b] - e.by[a]; }).slice(0, 4).forEach(function (k) { parts.push(k + " " + fmt(e.by[k])); });
    var ex = e.ex.map(function (t) { return t.label; }).join(", ");
    return "<b>" + esc(e.a) + " ↔ " + esc(e.b) + "</b><span class=\"k\">" + fmt(e.n) + " shared terms</span> · " + esc(parts.join(" · ")) + (ex ? "<br><em>e.g. " + esc(ex) + "</em>" : "");
  }
  function xrefTip(x) { return "<b>" + esc(x.from) + " → " + esc(x.to) + "</b>" + esc(x.what); }

  // ---- Detail panel ----
  function linkRow(M) {
    var out = '<div class="links">';
    if (M.page) out += '<a href="' + M.page + '">Page on this site</a>';
    out += '<a href="' + M.site + '">Browse the data</a><a href="' + M.github + '">GitHub</a></div>';
    return out;
  }
  function overview() {
    detail.innerHTML =
      '<div><p class="eyebrow">Reading the graph</p><h3 style="color:var(--ink)">Eight views of one microbe</h3>' +
      '<p>Clockwise from the top the ring walks from the environment a microbe lives in to the medium it is grown in: habitat, community, traits, cell structures, proteins, antibiotics, ingredients, media. A culture medium is a synthetic habitat, so the ring closes.</p>' +
      '<p>Chords through the middle are shared ontology terms: identical ChEBI, NCBITaxon, GO, ENVO, METPO, ARO or UniProt identifiers appearing in both corpora. Dashed arcs outside the ring are direct cross-references, where one Mech\'s records, schema or curation practice name another. Click a node, chord or arc for detail.</p></div>' +
      '<div><p class="eyebrow">Strongest ties' + (state.voc ? ' (' + esc(state.voc) + ')' : '') + '</p>' + strongest() + '</div>';
  }
  function strongest() {
    var rows = vocabEls.map(function (rec) { return { rec: rec, n: vocabWeight(rec) }; }).filter(function (r) { return r.n > 0; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 5);
    if (!rows.length) return '<p>No two Mechs share ' + esc(state.voc) + ' identifiers in their record corpora. The heatmap shows which Mechs use this vocabulary on their own.</p>';
    return '<ul>' + rows.map(function (r) {
      var e = r.rec.e, top = Object.keys(e.by).sort(function (a, b) { return e.by[b] - e.by[a]; })[0];
      return '<li><b>' + esc(e.a) + ' ↔ ' + esc(e.b) + '</b>: ' + fmt(r.n) + ' shared terms' + (state.voc ? '' : ', ' + fmt(e.by[top]) + ' of them ' + esc(top)) + (e.ex.length ? ' <em style="color:var(--muted)">(' + esc(e.ex.slice(0, 2).map(function (t) { return t.label; }).join(", ")) + ')</em>' : '') + '</li>';
    }).join("") + '</ul>';
  }
  function selectNode(m) {
    if (state.sel && state.sel.type === "node" && state.sel.m === m) { state.sel = null; render(); overview(); return; }
    renderNode(m);
  }
  function renderNode(m) {
    state.sel = { type: "node", m: m }; render();
    var M = MECHS[m], rows = [];
    vocabEls.forEach(function (rec) { if (rec.e.a === m || rec.e.b === m) rows.push({ o: rec.e.a === m ? rec.e.b : rec.e.a, n: vocabWeight(rec), top: Object.keys(rec.e.by).sort(function (a, b) { return rec.e.by[b] - rec.e.by[a]; })[0], ex: rec.e.ex }); });
    rows.sort(function (a, b) { return b.n - a.n; });
    var xr = XREFS.filter(function (x) { return x.from === m || x.to === m; });
    var hub = HUB.filter(function (h) { return h.mech === m; });
    detail.innerHTML =
      '<div><p class="eyebrow">' + esc(M.scale) + ' · ' + (M.member ? 'fleet manifest member' : 'fleet-adjacent, not yet in the manifest') + '</p>' +
      '<h3 style="color:' + color(m) + ';border-image:none;border-color:' + color(m) + '">' + esc(m) + '</h3><p>' + esc(M.tag) + ' ' + esc(M.extra) + '</p>' +
      '<dl class="meta"><dt>Records</dt><dd>' + fmt(M.records) + ' ' + esc(M.unit) + '</dd><dt>Root class</dt><dd><code>' + esc(M.root) + '</code></dd><dt>Grounded in</dt><dd>' + esc(M.vocab.join(", ")) + '</dd><dt>Sources</dt><dd>' + esc(M.sources) + '</dd><dt>License</dt><dd>' + esc(M.license) + '</dd></dl>' + linkRow(M) + '</div>' +
      '<div><p class="eyebrow">Shared vocabulary' + (state.voc ? ' (' + esc(state.voc) + ')' : '') + '</p><ul>' +
      rows.filter(function (r) { return r.n > 0; }).slice(0, 5).map(function (r) { return '<li><b>' + esc(r.o) + '</b> · ' + fmt(r.n) + ' terms, mostly ' + esc(r.top) + (r.ex.length ? ' <em style="color:var(--muted)">(' + esc(r.ex.slice(0, 2).map(function (t) { return t.label; }).join(", ")) + ')</em>' : '') + '</li>'; }).join("") +
      '</ul>' + (xr.length ? '<p class="eyebrow" style="margin-top:.8rem">Cross-references</p><ul>' + xr.map(function (x) { return '<li><b>' + esc(x.from) + ' → ' + esc(x.to) + '</b>: ' + esc(x.what) + '</li>'; }).join("") + '</ul>' : '') +
      (hub.length ? '<p class="eyebrow" style="margin-top:.8rem">kg-microbe</p><ul>' + hub.map(function (h) { return '<li>' + (h.dir === "out" ? "Exports " : "Receives ") + esc(h.what) + '</li>'; }).join("") + '</ul>' : '') + '</div>';
  }
  function selectEdge(rec) {
    state.sel = { type: "edge", rec: rec }; render();
    var e = rec.e, keys = Object.keys(e.by).sort(function (a, b) { return e.by[b] - e.by[a]; });
    detail.innerHTML = '<div><p class="eyebrow">Shared vocabulary</p><h3 style="color:var(--ink)">' + esc(e.a) + ' ↔ ' + esc(e.b) + '</h3><p>' + fmt(e.n) + ' identical ontology identifiers occur in both record corpora. Shared identifiers are what let the two knowledge bases be joined without any mapping step.</p>' +
      (e.ex.length ? '<p>For example: ' + esc(e.ex.map(function (t) { return t.label + " (" + t.id + ")"; }).join(", ")) + '.</p>' : '') + '</div>' +
      '<div><p class="eyebrow">By vocabulary</p><dl class="meta">' + keys.map(function (k) { return '<dt>' + esc(k) + '</dt><dd>' + fmt(e.by[k]) + '</dd>'; }).join("") + '</dl></div>';
  }
  function selectXref(rec) {
    state.sel = { type: "xref", rec: rec }; render();
    var x = rec.x;
    detail.innerHTML = '<div><p class="eyebrow">Cross-reference · ' + esc(x.kind) + '</p><h3 style="color:var(--ink)">' + esc(x.from) + ' → ' + esc(x.to) + '</h3><p>' + esc(x.what) + '</p></div><div><p class="eyebrow">Evidence</p><p>' + esc(x.ev) + '</p></div>';
  }
  function selectHub() {
    state.sel = { type: "hub" }; render();
    detail.innerHTML = '<div><p class="eyebrow">Hub</p><h3 style="color:var(--ink)">kg-microbe</h3><p>The Mechs are curated upstream of kg-microbe and publish into it as SSSOM mapping sets or KGX graphs; in turn, kg-microbe supplies harmonized ontologies and mapping tables back to the Mechs that need them.</p><div class="links"><a href="/kg-microbe/">About kg-microbe</a><a href="https://github.com/Knowledge-Graph-Hub/kg-microbe">GitHub</a></div></div>' +
      '<div><p class="eyebrow">Exchange</p><ul>' + HUB.map(function (h) { return '<li><b>' + esc(h.mech) + (h.dir === "out" ? ' →' : ' ←') + '</b> ' + esc(h.what) + '</li>'; }).join("") + '</ul></div>';
  }

  // ---- Controls ----
  function syncLayerChips() { document.querySelectorAll(".fleet-chip[data-layer]").forEach(function (b) { b.setAttribute("aria-pressed", String(state.layers[b.dataset.layer])); }); }
  document.querySelectorAll(".fleet-chip[data-layer]").forEach(function (b) {
    b.addEventListener("click", function () { state.layers[b.dataset.layer] = !state.layers[b.dataset.layer]; syncLayerChips(); render(); });
  });
  function setVoc(v) {
    state.voc = v;
    if (v) state.layers.vocab = true;
    syncLayerChips();
    var other = document.getElementById("fleet-voc-other"), hasChip = !!document.querySelector('.fleet-chip.voc:not(.other)[data-voc="' + v + '"]');
    document.querySelectorAll(".fleet-chip.voc:not(.other)").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.voc === v)); });
    if (other) { other.hidden = hasChip || !v; other.dataset.voc = hasChip ? "" : v; other.textContent = v + " ✕"; other.title = "Clear this filter"; }
    document.querySelectorAll("table.fleet-heat thead button").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.voc === v)); });
    document.querySelectorAll("table.fleet-heat td").forEach(function (td) { td.classList.toggle("hi", !!v && td.dataset.voc === v); });
    render();
    if (state.sel && state.sel.type === "node") renderNode(state.sel.m); else if (!state.sel) overview();
  }
  document.querySelectorAll(".fleet-chip.voc").forEach(function (b) { b.addEventListener("click", function () { setVoc(b.classList.contains("other") ? "" : (b.dataset.voc === state.voc ? "" : b.dataset.voc)); }); });
  svg.addEventListener("click", function (ev) { if (ev.target === svg) { state.sel = null; render(); overview(); } });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && state.sel) { state.sel = null; render(); overview(); } });

  // ---- Cards: link to graph ----
  document.querySelectorAll(".mech-card").forEach(function (c) {
    c.addEventListener("mouseenter", function () { hoverNode(c.dataset.mech, true); });
    c.addEventListener("mouseleave", function () { hoverNode(c.dataset.mech, false); });
    var btn = c.querySelector("[data-show]");
    if (btn) btn.addEventListener("click", function (ev) { ev.preventDefault(); selectNode(c.dataset.mech); document.getElementById("fleet-graph").scrollIntoView({ behavior: "smooth", block: "start" }); });
  });

  // ---- Heatmap ----
  var heat = document.getElementById("fleet-heat");
  if (heat) {
    var VOC = DATA.voc, max = 0;
    order.forEach(function (m) { VOC.forEach(function (v) { max = Math.max(max, DATA.heat[m][v]); }); });
    var lmax = Math.log10(max);
    var html = "<thead><tr><th></th>" + VOC.map(function (v) { return '<th><button type="button" data-voc="' + v + '" aria-pressed="false" title="Filter the graph to ' + v + '">' + esc(v) + "</button></th>"; }).join("") + "</tr></thead><tbody>";
    order.forEach(function (m) {
      html += '<tr><th scope="row" style="--c:' + color(m) + '"><i></i>' + esc(m) + "</th>";
      VOC.forEach(function (v) {
        var n = DATA.heat[m][v], l = n ? Math.round(12 + 88 * Math.log10(n) / lmax) : 0;
        html += '<td data-voc="' + v + '" data-l="' + l + '" style="--l:' + l + '" title="' + esc(m) + " · " + esc(v) + ": " + fmt(n) + ' occurrences">' + (n ? short(n) : "&middot;") + "</td>";
      });
      html += "</tr>";
    });
    heat.innerHTML = html + "</tbody>";
    heat.querySelectorAll("thead button").forEach(function (b) { b.addEventListener("click", function () { var v = b.dataset.voc; setVoc(state.voc === v ? "" : v); }); });
  }
  function short(n) { return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "k" : String(n); }

  render(); overview();
  }
})();
</script>


## The eight Mechs

Each card carries its Mech's own site color. Hover a card to trace its ties in the graph above; use "Show in graph" to select it.

<div class="mech-cards">
  <article class="mech-card" data-mech="HabitatMech" style="--c: var(--mech-habitatmech)">
    <header><h3>HabitatMech</h3><span class="scale">Habitat</span></header>
    <p class="tag">Four habitat vocabularies harmonized into ENVO-grounded records that keep every source's attestation.</p>
    <div class="num"><b>3,213</b><span>habitat records · 684 reviewed</span></div>
    <div class="vocab"><span>ENVO</span><span>NCBITaxon</span><span>BTO</span><span>UBERON</span><span>FOODON</span><span>GOLD</span><span>BacDive</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/HabitatMech/">Browse</a><a href="https://github.com/CultureBotAI/HabitatMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge adj">fleet-adjacent</span></div>
  </article>
  <article class="mech-card" data-mech="CommunityMech" style="--c: var(--mech-communitymech)">
    <header><h3>CommunityMech</h3><span class="scale">Community</span></header>
    <p class="tag">Curated knowledge base of microbial communities, their interactions, cultivation conditions and evidence.</p>
    <div class="num"><b>325</b><span>community records · KGX export</span></div>
    <div class="vocab"><span>NCBITaxon</span><span>ChEBI</span><span>GO</span><span>ENVO</span><span>GTDB</span><span>PMID</span></div>
    <div class="row"><a class="primary" href="/communitymech/">Page</a><a href="https://culturebotai.github.io/CommunityMech/">Browse</a><a href="https://github.com/CultureBotAI/CommunityMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="TraitMech" style="--c: var(--mech-traitmech)">
    <header><h3>TraitMech</h3><span class="scale">Traits</span></header>
    <p class="tag">Microbial ecophysiological trait knowledge base seeded from METPO, one curated YAML per trait, with causal mechanism graphs.</p>
    <div class="num"><b>477</b><span>trait records · 353 with causal graphs</span></div>
    <div class="vocab"><span>METPO</span><span>GO</span><span>NCBITaxon</span><span>ChEBI</span><span>UniProt</span><span>PATO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/TraitMech/">Browse</a><a href="https://github.com/CultureBotAI/TraitMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="CellStructureMech" style="--c: var(--mech-cellstructuremech)">
    <header><h3>CellStructureMech</h3><span class="scale">Cell structures</span></header>
    <p class="tag">Organelles, envelope layers, appendages, microcompartments and complexes: components, distribution, function and causal mechanism.</p>
    <div class="num"><b>39</b><span>structure records · 279 causal edges</span></div>
    <div class="vocab"><span>GO</span><span>NCBITaxon</span><span>UniProt</span><span>METPO</span><span>Pfam</span><span>PDB</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/CellStructureMech/">Browse</a><a href="https://github.com/CultureBotAI/CellStructureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="ProteinTraitsMech" style="--c: var(--mech-proteintraitsmech)">
    <header><h3>ProteinTraitsMech</h3><span class="scale">Proteins</span></header>
    <p class="tag">Protein sequence, structure and function trait classes seeded from InterPro, Pfam, Rhea, CATH, SCOPe, CARD and more.</p>
    <div class="num"><b>429,271</b><span>protein trait records</span></div>
    <div class="vocab"><span>InterPro</span><span>UniProt</span><span>Rhea</span><span>Pfam</span><span>GO</span><span>ChEBI</span><span>ARO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/proteintraitsmech/">Browse</a><a href="https://github.com/CultureBotAI/proteintraitsmech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="AntibioticMech" style="--c: var(--mech-antibioticmech)">
    <header><h3>AntibioticMech</h3><span class="scale">Antibiotics</span></header>
    <p class="tag">One record per antimicrobial chemical structure, harmonizing ChEBI and CARD with targets, mode of action, resistance and evidence.</p>
    <div class="num"><b>2,909</b><span>antimicrobial structures · 92% ChEBI-grounded</span></div>
    <div class="vocab"><span>ChEBI</span><span>ARO</span><span>CAS</span><span>PubChem</span><span>DrugBank</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/AntibioticMech/">Browse</a><a href="https://github.com/CultureBotAI/AntibioticMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="MediaIngredientMech" style="--c: var(--mech-mediaingredientmech)">
    <header><h3>MediaIngredientMech</h3><span class="scale">Ingredients</span></header>
    <p class="tag">LLM-assisted curation of media-ingredient ontology mappings with full audit trails; owns ingredient identity for the fleet.</p>
    <div class="num"><b>2,958</b><span>ingredient records · 91% mapped</span></div>
    <div class="vocab"><span>ChEBI</span><span>CAS</span><span>NCIT</span><span>FOODON</span><span>ENVO</span><span>MeSH</span></div>
    <div class="row"><a class="primary" href="/mediaingredientmech/">Page</a><a href="https://culturebotai.github.io/MediaIngredientMech/">Browse</a><a href="https://github.com/CultureBotAI/MediaIngredientMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
  <article class="mech-card" data-mech="CultureMech" style="--c: var(--mech-culturemech)">
    <header><h3>CultureMech</h3><span class="scale">Media</span></header>
    <p class="tag">Versioned, ontology-grounded knowledge base of culture-media recipes from MediaDive, TogoMedium, KOMODO and the major collections.</p>
    <div class="num"><b>6,286</b><span>merged recipes · 15,877 normalized</span></div>
    <div class="vocab"><span>ChEBI</span><span>KEGG</span><span>FOODON</span><span>UBERON</span><span>CAS</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="/culturemech/">Page</a><a href="https://culturebotai.github.io/CultureMech/">Browse</a><a href="https://github.com/CultureBotAI/CultureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">manifest member</span></div>
  </article>
</div>

## Shared vocabulary

The Mechs are joinable because they ground records in the same public ontologies. The table counts identifier occurrences per vocabulary in each Mech's record corpus; darker cells mean more. Click a column to filter the graph to that vocabulary.

<div class="fleet-heat-wrap"><table class="fleet-heat" id="fleet-heat" aria-label="Ontology identifier occurrences per Mech"></table></div>
<p class="fleet-heat-note">Counts are prefix occurrences in the canonical record directories (merged recipes for CultureMech, communities for CommunityMech, habitat records for HabitatMech) as of September 2026. ChEBI binds the chemistry arm (media, ingredients, antibiotics, proteins); NCBITaxon and ENVO bind the organism arm (habitat, community, traits); GO and METPO bridge phenotype, structure and protein.</p>

## How the Mechs reference each other

Beyond shared vocabulary, Mechs name one another directly, in record fields, in schema slots, and in the curation practices they adopt from each other. Arrows point at the Mech that consumes.

<div class="fleet-xrefs">
  <div style="--c: var(--mech-culturemech); --c2: var(--mech-mediaingredientmech)"><div class="pair"><b>CultureMech</b><i>→</i><b class="to">MediaIngredientMech</b></div><div>Unmapped ingredient strings and occurrence counts become MIM's curation backlog; MIM records link back to recipes by stable id with the <code>CultureMechReference</code> class.<small>Record data · claw ingredient_curation_pipeline</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --c2: var(--mech-culturemech)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">CultureMech</b></div><div>Curated ChEBI and FOODON mappings sync back to recipes. CultureMech vendors MIM's ingredient-role enums and consumes MIM's immutable label index.<small>Record data · src/culturemech/schema/mim_roles.yaml</small></div></div>
  <div style="--c: var(--mech-communitymech); --c2: var(--mech-culturemech)"><div class="pair"><b>CommunityMech</b><i>→</i><b class="to">CultureMech</b></div><div>Community records name the medium they were cultivated in by CultureMech id: 21 records carry 32 <code>culturemech_id</code> links.<small>Record data · docs/cross_repo_linking.md</small></div></div>
  <div style="--c: var(--mech-communitymech); --c2: var(--mech-mediaingredientmech)"><div class="pair"><b>CommunityMech</b><i>→</i><b class="to">MediaIngredientMech</b></div><div>The <code>RelatedIngredient.mediaingredientmech_id</code> slot is declared for MIM ingredient ids; no record populates it yet.<small>Schema slot · docs/cross_repo_linking.md</small></div></div>
  <div style="--c: var(--mech-cellstructuremech); --c2: var(--mech-traitmech)"><div class="pair"><b>CellStructureMech</b><i>→</i><b class="to">TraitMech</b></div><div>A structure lists the phenotypes it confers as TraitMech or METPO terms (8 trait links today), and its causal-graph node vocabulary is TraitMech's plus a STRUCTURE node type.<small>Record data · schema slot associated_traits</small></div></div>
  <div style="--c: var(--mech-cellstructuremech); --c2: var(--mech-proteintraitsmech)"><div class="pair"><b>CellStructureMech</b><i>→</i><b class="to">ProteinTraitsMech</b></div><div>A single protein is a component of a structure, never a record of its own: it grounds to InterPro or UniProtKB and hands off to ProteinTraitsMech.<small>Scope boundary · docs/CURATION.md</small></div></div>
  <div style="--c: var(--mech-habitatmech); --c2: var(--mech-traitmech)"><div class="pair"><b>HabitatMech</b><i>→</i><b class="to">TraitMech</b></div><div>Habitat causal graphs use a superset of TraitMech's node vocabulary so the graphs stay comparable; a node may be a TraitMech or METPO trait.<small>Schema · CausalNode enum</small></div></div>
  <div style="--c: var(--mech-habitatmech); --c2: var(--mech-culturemech)"><div class="pair"><b>HabitatMech</b><i>→</i><b class="to">CultureMech</b></div><div>The single overlapping concept, BTO:0000316 culture medium, is handed to CultureMech rather than curated twice. A culture medium is a synthetic habitat.<small>Curation decision · curation/decisions.tsv</small></div></div>
  <div style="--c: var(--mech-antibioticmech); --c2: var(--mech-cellstructuremech)"><div class="pair"><b>AntibioticMech</b><i>→</i><b class="to">CellStructureMech</b></div><div>AntibioticMech wrote the licensed source-queue pattern (rank candidate sources, verify licences, record decisions); CellStructureMech adapted it.<small>Practice · claw docs/guides/SOURCE_QUEUE.md</small></div></div>
  <div style="--c: var(--mech-proteintraitsmech); --c2: var(--mech-traitmech)"><div class="pair"><b>ProteinTraitsMech</b><i>→</i><b class="to">TraitMech</b></div><div>TraitMech adopted ProteinTraitsMech's licence-bearing <code>download.yaml</code> source catalogue, and a drift audit keeps the trait tokens the two share aligned in meaning.<small>Practice · TraitMech download.yaml</small></div></div>
</div>

## Orchestration: culturebotai-claw

[culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw) is the fleet's coordinator. It does not hold science of its own; it holds the definition of the fleet, the artifacts every Mech must share byte-for-byte, and the cross-repository pipelines that move curation between Mechs safely.

<div class="fleet-orch">
  <div><h4>Fleet manifest</h4><p><code>fleet.yaml</code> is the single source of truth for which repositories form the fleet. Seven Mechs are members today; HabitatMech follows the standard and is not yet a manifest member. Every member declares every capability exactly once as enabled, disabled or not applicable, with a reason, so nothing is silently off.</p></div>
  <div><h4>Vendored governance</h4><p>Shared LinkML modules (<code>mech_shared.yaml</code>, <code>history.yaml</code>), validators and behavioral contracts live in claw and are vendored into each Mech byte-identically, pinned to one immutable claw commit and checked in CI. Fifteen artifacts, all seven members.</p></div>
  <div><h4>Pipelines and skills</h4><p>Three cross-repository pipelines (ingredient curation, unified ingredient mapping, ENVO environment curation) and 24 agent skills. Cross-repo writes resolve exact worktree roots, take a repository lock, default to dry run and validate staged output before replacing source data.</p></div>
</div>

Which fleet contracts each member has adopted, from the manifest:

<div class="fleet-caps-wrap">
<table class="fleet-caps">
  <thead><tr><th>Mech</th><th>Curation history</th><th>Strict validation</th><th>Vendored sync</th><th>Deep research</th><th>Knowledge-gap scan</th><th>Environment coverage</th><th>SSSOM export</th><th>KGX export</th><th>Source queue</th><th>Source catalogue</th><th>Site contract</th></tr></thead>
  <tbody>
    <tr><td>CultureMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td></tr>
    <tr><td>MediaIngredientMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td></tr>
    <tr><td>CommunityMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="n"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="e"></i></td></tr>
    <tr><td>TraitMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="n"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="e"></i></td><td><i class="e"></i></td></tr>
    <tr><td>ProteinTraitsMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="n"></i></td><td><i class="n"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="e"></i></td><td><i class="d"></i></td></tr>
    <tr><td>AntibioticMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="n"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td></tr>
    <tr><td>CellStructureMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="n"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="e"></i></td></tr>
    <tr><td>HabitatMech</td><td colspan="11"><i class="x">not yet a manifest member; vendors mech_shared.yaml without a pinned claw revision</i></td></tr>
  </tbody>
</table>
</div>
<div class="fleet-caps-key"><span><i class="e"></i>enabled</span><span><i class="d"></i>disabled, with a recorded reason</span><span><i class="n"></i>not applicable to this corpus</span></div>

## What makes a Mech

The suite is cohesive because every Mech is built the same way. The fleet standard, documented in claw's `MECH_STANDARD.md`, asks for:

<ul class="fleet-standard">
  <li><b>One YAML record per entity</b>A recipe, an ingredient, a community, a trait, a structure, a protein trait, an antibiotic, a habitat. The file is the unit of curation, review and history.</li>
  <li><b>A LinkML schema per Mech</b>Records validate against the Mech's schema; every schema imports the same vendored <code>mech_shared.yaml</code> for discussions and datasets.</li>
  <li><b>Ontology-grounded identity</b>Records are keyed by a public CURIE (ChEBI, GO, METPO, ENVO, NCBITaxon) where one exists, otherwise a minted content-hashed CURIE that can be re-grounded later.</li>
  <li><b>The ID–label invariant</b>Every identifier is stored with its label, and CI checks that the pair still agrees with the source ontology.</li>
  <li><b>Evidence and provenance</b>Assertions carry evidence items with PMIDs or DOIs; sources are catalogued with their licences before they are ingested.</li>
  <li><b>Causal mechanism graphs</b>Traits, structures, antibiotics and habitats can carry directed, evidence-backed graphs of mechanism, sharing one node vocabulary so graphs compare across Mechs.</li>
  <li><b>Append-only curation history</b>Every change is an event in a conflict-free history directory, so agents and people can curate the same corpus concurrently.</li>
  <li><b>A static browser and an open licence</b>Each Mech publishes a GitHub Pages browser over its records and releases under CC0-1.0 (AntibioticMech data under CC BY 4.0, CommunityMech code under BSD-3-Clause).</li>
</ul>

## Related resources

- **[kg-microbe](/kg-microbe/)** - The central knowledge graph the Mechs publish into and draw from
- **[MicroGrowAgents](/microgrowagents/)** - Multi-agent media design built on CultureMech, MediaIngredientMech and kg-microbe
- **[Resources](/resources/#-ai-curation-tools)** - The full tool catalogue, including MicroMediaParam and the kg-microbe utilities
- **[METPO](https://github.com/berkeleybop/metpo)** - The Microbial Ecophysiological Trait and Phenotype Ontology that seeds TraitMech and grounds trait references across the fleet

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. Naseem S, Miller MA, Martinez-Gomez NC, Sun N, **Joachimiak MP**. MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering. *bioRxiv*. 2026. [doi:10.64898/2026.06.04.729985](https://doi.org/10.64898/2026.06.04.729985)
{: .bibliography}

See the [full bibliography](/publications/#bibliography) on the Publications page.
