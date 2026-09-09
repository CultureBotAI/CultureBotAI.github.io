---
layout: default
title: "X-Mech Suite"
description: "Nine ontology-grounded microbial knowledge bases, from habitat to culture medium, orchestrated by culturebotai-claw and connected through shared ontology terms and direct cross-references"
permalink: /mechs/
---

# X-Mech Suite: nine knowledge bases, one standard

The X-Mech suite is a fleet of nine curated, ontology-grounded knowledge bases that together describe a microbe at every scale: the habitat it lives in, the community it belongs to, the traits it expresses, the structures and proteins that implement them, the compounds it makes, the antibiotics that act on it, and the ingredients and media it is grown in. Each Mech follows the same curation model, one validated YAML record per entity with evidence and provenance, and the fleet is coordinated by a single orchestrator, [culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw).

<!-- ===== Mech fleet: interactive component (self-contained: styles, markup, script) ===== -->
<style>
  /* Mech identity colors: each node wears the accent of its own site. */
  :root {
    --mech-habitatmech: #2b6a4d; --mech-communitymech: #3D7DD6; --mech-traitmech: #C5474B;
    --mech-cellstructuremech: #5257C9; --mech-proteintraitsmech: #2E8B84; --mech-antibioticmech: #85551C;
    /* NaturalProductMech publishes no site, so it has no accent of its own to
       borrow. The eight above already fill the hue circle at this lightness --
       every ninth hue tested collided with one of them for normal vision -- so
       this one separates by going deeper instead, which clears both the
       colour-blind and normal-vision floors against all eight. */
    --mech-naturalproductmech: #6A1B7A;
    --mech-mediaingredientmech: #7E5BC4; --mech-culturemech: #4B9E5F;
    --fleet-edge: rgba(90, 99, 94, .34);
    --fleet-heat-hue: 150 22%;
    --voc-chebi: #D9702F; --voc-ncbitaxon: #3B7DD8; --voc-go: #2FA36B; --voc-metpo: #7A5BC7;
    --voc-envo: #1F9BB5; --voc-aro: #C83D6A; --voc-uniprot: #B8860B; --voc-doi: #7F8A96; --voc-other: #A39E97;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --mech-habitatmech: #4fbf85; --mech-communitymech: #5c9cf0; --mech-traitmech: #f0696e;
      --mech-cellstructuremech: #8a8ef5; --mech-proteintraitsmech: #3dbfb2; --mech-antibioticmech: #d9a94a;
      --mech-naturalproductmech: #A64CA6;
      --mech-mediaingredientmech: #b08cf2; --mech-culturemech: #63c46f;
      --fleet-edge: rgba(160, 178, 168, .34);
      --fleet-heat-hue: 150 14%;
      --voc-chebi: #E8925A; --voc-ncbitaxon: #6FA6F2; --voc-go: #5CC48F; --voc-metpo: #A48CE8;
      --voc-envo: #4FBAD3; --voc-aro: #E86F96; --voc-uniprot: #D9AA3F; --voc-doi: #9AA5B1; --voc-other: #8C8780;
    }
  }
  :root[data-theme="dark"] {
    --mech-habitatmech: #4fbf85; --mech-communitymech: #5c9cf0; --mech-traitmech: #f0696e;
    --mech-cellstructuremech: #8a8ef5; --mech-proteintraitsmech: #3dbfb2; --mech-antibioticmech: #d9a94a;
    --mech-naturalproductmech: #A64CA6;
    --mech-mediaingredientmech: #b08cf2; --mech-culturemech: #63c46f;
    --fleet-edge: rgba(160, 178, 168, .34);
    --fleet-heat-hue: 150 14%;
    --voc-chebi: #E8925A; --voc-ncbitaxon: #6FA6F2; --voc-go: #5CC48F; --voc-metpo: #A48CE8;
    --voc-envo: #4FBAD3; --voc-aro: #E86F96; --voc-uniprot: #D9AA3F; --voc-doi: #9AA5B1; --voc-other: #8C8780;
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
  .fleet-chip.voc[data-voc]:not([data-voc=""])::before, .voc-dot { content: ""; display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: .4em; vertical-align: -1px; background: var(--dot, var(--voc-other)); }
  .fleet-chip.voc[data-voc="CHEBI"] { --dot: var(--voc-chebi); } .fleet-chip.voc[data-voc="NCBITaxon"] { --dot: var(--voc-ncbitaxon); } .fleet-chip.voc[data-voc="GO"] { --dot: var(--voc-go); }
  .fleet-chip.voc[data-voc="ENVO"] { --dot: var(--voc-envo); } .fleet-chip.voc[data-voc="METPO"] { --dot: var(--voc-metpo); } .fleet-chip.voc[data-voc="ARO"] { --dot: var(--voc-aro); }
  .fleet-chip.voc[data-voc="UniProt"] { --dot: var(--voc-uniprot); } .fleet-chip.voc[data-voc="DOI"] { --dot: var(--voc-doi); }
  .fleet-chip.voc.other[data-voc]::before { display: none; }
  .fleet-chip.voc.other[aria-pressed="true"] { background: var(--accent-2); border-color: var(--accent-2); }
  .fleet-controls .spacer { flex: 1; }
  .fleet-stage { position: relative; }
  .fleet-stage svg { display: block; width: 100%; height: auto; }
  .fleet-stage svg text { font-family: inherit; fill: var(--ink); }
  .fleet-stage .axis-label { font-size: 11px; fill: var(--muted); letter-spacing: .08em; text-transform: uppercase; font-weight: 700; }
  .fleet-stage .hub-label { font-size: 12px; font-weight: 800; }
  .fleet-stage .hub-sub { font-size: 9px; fill: var(--muted); }
  .fleet-stage .node-label { font-size: 13px; font-weight: 700; }
  .fleet-stage .node-sub { font-size: 10.5px; fill: var(--muted); font-variant-numeric: tabular-nums; }
  .fleet-stage .node { cursor: pointer; }
  .fleet-stage a.node-link { outline: none; }
  .fleet-stage a.node-link:hover .node-label, .fleet-stage a.node-link:focus-visible .node-label { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 3px; }
  .fleet-stage .node circle { stroke: var(--card); stroke-width: 3; transition: r .2s ease, opacity .2s ease; }
  .fleet-stage .node.adjacent circle { stroke-dasharray: 5 4; stroke: var(--muted); }
  .fleet-stage a.node-link:focus-visible circle { stroke: var(--neon); }
  .fleet-stage .node.dim, .fleet-stage .edge.dim { opacity: .18; }
  .fleet-stage .edge { fill: none; stroke: var(--fleet-edge); stroke-linecap: round; cursor: pointer; transition: opacity .2s ease, stroke .2s ease; }
  .fleet-stage .edge.vocab { opacity: .72; }
  .fleet-stage .edge.vocab.lit, .fleet-stage .edge.vocab:focus-visible { opacity: 1; filter: drop-shadow(0 0 3px currentColor); outline: none; }
  .fleet-stage .edge.xref:focus-visible, .fleet-stage .edge.hub:focus-visible { stroke: var(--ink); stroke-width: 3; outline: none; }
  .fleet-stage .hub.dim, .fleet-stage #fleet-hub.dim { opacity: .35; }
  .fleet-stage .edge.hit { stroke: transparent; stroke-width: 14; }
  .fleet-stage .edge.xref { stroke: var(--accent); stroke-dasharray: 6 5; stroke-width: 1.8; }
  .fleet-stage .edge.xref.weak { stroke-dasharray: 2 5; opacity: .7; }
  .fleet-stage .edge.hub { stroke: var(--accent-2); stroke-width: 1.6; }
  .fleet-stage .edge.hub.in { stroke-dasharray: 3 4; }
  .fleet-stage .edge.hub.ns { stroke-dasharray: 1 5; stroke-linecap: round; opacity: .75; }
  .fleet-stage .edge.gov { stroke: var(--muted); stroke-width: 1.2; }
  .fleet-stage .edge.xref.lit, .fleet-stage .edge.hub.lit { stroke: var(--ink); opacity: 1; }
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
  .fleet-detail .links a.go { background: var(--accent); border-color: var(--accent); color: #fff; }
  .page-content .fleet-detail ul { margin: .2rem 0 0; padding-left: 1.2rem; font-size: .88rem; list-style: disc; }
  .page-content .fleet-detail ul > li::before { display: none; }
  .fleet-detail li { margin-bottom: .3rem; }
  .fleet-detail .termbox input { width: 100%; box-sizing: border-box; margin: .4rem 0 .5rem; padding: .45em .7em; font: inherit; font-size: .85rem; color: var(--ink); background: var(--card); border: 1px solid var(--line); border-radius: 8px; }
  .page-content .fleet-detail .termbox ol { margin: 0; padding-left: 1.2rem; font-size: .84rem; max-height: 24rem; overflow-y: auto; }
  .page-content .fleet-detail .termbox ol > li { margin-bottom: .5rem; }
  .fleet-detail .termbox code { font-size: .78em; color: var(--muted); }
  .fleet-detail .termbox .in { color: var(--ink); }
  .fleet-detail .termbox .in span { color: var(--muted); }
  .fleet-detail .termbox .in em { color: var(--muted); font-style: normal; }
  .fleet-detail .termbox .more { margin-top: .5rem; }
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
  .page-content .mech-card .row a { background-image: none; }
  .mech-card .row a.primary { background: var(--c); border-color: var(--c); color: var(--card); }
  .mech-card .badge { margin-left: auto; font-size: .7rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--muted); }
  .mech-card .badge.adj { color: var(--accent); }
  .page-content .mech-card ul { list-style: none; padding: 0; margin: 0; }
  .page-content .mech-card ul > li::before { display: none; }

  /* ---- Scale ladder ---- */
  .fleet-ladder { display: grid; grid-template-columns: repeat(9, 1fr); gap: 4px; margin: 1rem 0 .2rem; }
  .page-content .fleet-ladder > a { display: block; padding: .55rem .5rem .5rem; border-radius: 8px; background: var(--wash-b); border-top: 4px solid var(--c); font-size: .74rem; line-height: 1.3; color: var(--ink); background-image: none; transition: transform .15s ease, box-shadow .15s ease; }
  .page-content .fleet-ladder > a:hover, .page-content .fleet-ladder > a:focus-visible { transform: translateY(-2px); box-shadow: var(--shadow-lg); background-size: 0; }
  .fleet-ladder b { display: block; font-size: .78rem; color: var(--c); }
  .fleet-ladder span { color: var(--muted); }
  @media (max-width: 900px) { .fleet-ladder { grid-template-columns: repeat(5, 1fr); } }
  @media (max-width: 760px) { .fleet-ladder { grid-template-columns: repeat(3, 1fr); } }
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
  table.fleet-heat td.sel { outline: 2px solid var(--ink); }
  table.fleet-heat tbody th a { color: var(--ink); background-image: none; }
  table.fleet-heat tbody th a:hover { color: var(--accent); }
  table.fleet-heat td button { font: inherit; font-size: .68rem; color: inherit; background: none; border: 0; width: 100%; height: 100%; padding: 0; cursor: pointer; border-radius: 5px; }
  table.fleet-heat td button:hover { outline: 2px solid var(--accent); }
  .fleet-cell-panel { margin: .6rem 0 0; padding: 1rem 1.2rem; background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); }
  .fleet-cell-panel h3 { margin: 0 0 .4rem; padding-left: .6rem; font-size: 1.05rem; }
  .fleet-cell-panel p { margin: .2rem 0 .5rem; font-size: .9rem; }
  .fleet-cell-panel .eyebrow { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--muted); margin: 0 0 .3rem; }
  .fleet-cell-panel .links { display: flex; flex-wrap: wrap; gap: .4rem; margin: .3rem 0 .7rem; }
  .fleet-cell-panel .links a { font-size: .8rem; font-weight: 700; padding: .35em .8em; border-radius: 999px; border: 1px solid var(--line); background: var(--wash-b); }
  .fleet-cell-panel .links a.go { background: var(--accent); border-color: var(--accent); color: #fff; }
  .fleet-cell-panel .reclist { max-height: 18rem; overflow-y: auto; font-size: .84rem; line-height: 1.7; padding: .5rem .7rem; background: var(--wash-b); border-radius: 8px; }
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
  <div><b>9</b><span>Mech knowledge bases</span></div>
  <div><b>448,624</b><span>curated records</span></div>
  <div><b>43</b><span>ontologies &amp; databases cited</span></div>
  <div><b>1</b><span>orchestrator (claw)</span></div>
</div>

<div class="fleet-ladder" aria-label="Scale ladder, from environment to medium; each step opens that Mech">
  <a href="https://culturebotai.github.io/HabitatMech/" style="--c: var(--mech-habitatmech)" title="Open HabitatMech"><b>Habitat</b><span>where it lives</span></a>
  <a href="https://culturebotai.github.io/CommunityMech/" style="--c: var(--mech-communitymech)" title="Open CommunityMech"><b>Community</b><span>who it lives with</span></a>
  <a href="https://culturebotai.github.io/TraitMech/" style="--c: var(--mech-traitmech)" title="Open TraitMech"><b>Traits</b><span>what it does</span></a>
  <a href="https://culturebotai.github.io/CellStructureMech/" style="--c: var(--mech-cellstructuremech)" title="Open CellStructureMech"><b>Cell structures</b><span>what it is built of</span></a>
  <a href="https://culturebotai.github.io/proteintraitsmech/" style="--c: var(--mech-proteintraitsmech)" title="Open ProteinTraitsMech"><b>Proteins</b><span>the machinery</span></a>
  <a href="https://github.com/CultureBotAI/NaturalProductMech" style="--c: var(--mech-naturalproductmech)" title="Open NaturalProductMech on GitHub"><b>Natural products</b><span>what it makes</span></a>
  <a href="https://culturebotai.github.io/AntibioticMech/" style="--c: var(--mech-antibioticmech)" title="Open AntibioticMech"><b>Antibiotics</b><span>what acts on it</span></a>
  <a href="https://culturebotai.github.io/MediaIngredientMech/" style="--c: var(--mech-mediaingredientmech)" title="Open MediaIngredientMech"><b>Ingredients</b><span>what it is fed</span></a>
  <a href="https://culturebotai.github.io/CultureMech/" style="--c: var(--mech-culturemech)" title="Open CultureMech"><b>Media</b><span>where it is grown</span></a>
</div>

<div class="fleet-graph" id="fleet-graph">
  <div class="fleet-controls">
    <div class="grp" role="group" aria-label="Edge layers">
      <span>Layers</span>
      <button class="fleet-chip" data-layer="vocab" aria-pressed="false">Shared vocabulary</button>
      <button class="fleet-chip" data-layer="xref" aria-pressed="true">Cross-references</button>
      <button class="fleet-chip" data-layer="hub" aria-pressed="true">kg-microbe exchange</button>
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
      <g id="fleet-xrefs"></g>
      <g id="fleet-edges"></g>
      <g id="fleet-hubedges"></g>
      <g id="fleet-hub"></g>
      <g id="fleet-nodes"></g>
    </svg>
    <div class="fleet-tip" id="fleet-tip" aria-hidden="true"></div>
  </div>
  <div class="fleet-legend">
    <span>shared identifiers, one chord per vocabulary (width = how many):</span>
    <span><i style="border-color:var(--voc-chebi)"></i>ChEBI</span><span><i style="border-color:var(--voc-ncbitaxon)"></i>NCBITaxon</span><span><i style="border-color:var(--voc-go)"></i>GO</span><span><i style="border-color:var(--voc-metpo)"></i>METPO</span><span><i style="border-color:var(--voc-envo)"></i>ENVO</span><span><i style="border-color:var(--voc-aro)"></i>ARO</span><span><i style="border-color:var(--voc-uniprot)"></i>UniProt</span><span><i style="border-color:var(--voc-doi)"></i>citations</span><span><i style="border-color:var(--voc-other)"></i>other</span>
    <span><i class="x"></i>direct cross-reference (arrow = who consumes)</span>
    <span><i class="h"></i>export to / input from kg-microbe (dotted = namespace only)</span>
    <span><i class="g"></i>fleet manifest membership</span>
  </div>
  <div class="fleet-detail" id="fleet-detail"></div>
</div>

<script>
(function () {
  "use strict";
  if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", init); } else { init(); }
  function init() {
  var DATA = {"order":["HabitatMech","CommunityMech","TraitMech","CellStructureMech","ProteinTraitsMech","NaturalProductMech","AntibioticMech","MediaIngredientMech","CultureMech"],"voc":["CHEBI","NCBITaxon","GO","ENVO","METPO","ARO","UniProt","InterPro","Pfam","RHEA","PDB","PATO","UBERON","FOODON","BTO","GTDB","KEGG","CAS","MIBiG","NPAtlas","PMID","DOI"],"heat":{"HabitatMech":{"CHEBI":18,"NCBITaxon":13222,"GO":2,"ENVO":3183,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":4,"UBERON":1089,"FOODON":194,"BTO":1353,"GTDB":0,"KEGG":0,"CAS":0,"MIBiG":0,"NPAtlas":0,"PMID":513,"DOI":112},"CommunityMech":{"CHEBI":2221,"NCBITaxon":3060,"GO":862,"ENVO":366,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":9,"FOODON":0,"BTO":0,"GTDB":1674,"KEGG":0,"CAS":0,"MIBiG":0,"NPAtlas":0,"PMID":4812,"DOI":1123},"TraitMech":{"CHEBI":666,"NCBITaxon":844,"GO":809,"ENVO":22,"METPO":3195,"ARO":0,"UniProt":389,"InterPro":113,"Pfam":0,"RHEA":0,"PDB":0,"PATO":97,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":0,"MIBiG":0,"NPAtlas":0,"PMID":412,"DOI":5319},"CellStructureMech":{"CHEBI":18,"NCBITaxon":351,"GO":398,"ENVO":0,"METPO":14,"ARO":0,"UniProt":238,"InterPro":38,"Pfam":17,"RHEA":0,"PDB":4,"PATO":0,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":0,"MIBiG":0,"NPAtlas":0,"PMID":205,"DOI":1343},"ProteinTraitsMech":{"CHEBI":373461,"NCBITaxon":357752,"GO":417184,"ENVO":0,"METPO":244,"ARO":194924,"UniProt":656717,"InterPro":1477316,"Pfam":520297,"RHEA":613318,"PDB":235943,"PATO":110,"UBERON":43,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":245,"CAS":0,"MIBiG":0,"NPAtlas":0,"PMID":654089,"DOI":187928},"NaturalProductMech":{"CHEBI":1587,"NCBITaxon":13718,"GO":0,"ENVO":0,"METPO":0,"ARO":0,"UniProt":1116,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":0,"MIBiG":10175,"NPAtlas":1756,"PMID":5734,"DOI":8320},"AntibioticMech":{"CHEBI":22066,"NCBITaxon":611,"GO":3,"ENVO":0,"METPO":0,"ARO":16653,"UniProt":278,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":6,"PATO":0,"UBERON":0,"FOODON":0,"BTO":0,"GTDB":0,"KEGG":0,"CAS":1835,"MIBiG":0,"NPAtlas":0,"PMID":1207,"DOI":126},"MediaIngredientMech":{"CHEBI":7681,"NCBITaxon":1,"GO":0,"ENVO":110,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":22,"FOODON":270,"BTO":3,"GTDB":0,"KEGG":53,"CAS":661,"MIBiG":0,"NPAtlas":0,"PMID":29,"DOI":5},"CultureMech":{"CHEBI":160660,"NCBITaxon":63,"GO":0,"ENVO":13,"METPO":0,"ARO":0,"UniProt":0,"InterPro":0,"Pfam":0,"RHEA":0,"PDB":0,"PATO":0,"UBERON":138,"FOODON":214,"BTO":0,"GTDB":0,"KEGG":1406,"CAS":1,"MIBiG":0,"NPAtlas":0,"PMID":68,"DOI":76}},"cells":{"HabitatMech--NCBITaxon":895,"HabitatMech--ENVO":1263,"HabitatMech--CHEBI":9,"HabitatMech--UBERON":702,"HabitatMech--PATO":3,"HabitatMech--FOODON":85,"HabitatMech--BTO":581,"HabitatMech--GO":1,"CommunityMech--CHEBI":279,"CommunityMech--NCBITaxon":330,"CommunityMech--ENVO":319,"CommunityMech--GO":205,"CommunityMech--GTDB":313,"CommunityMech--UBERON":9,"TraitMech--NCBITaxon":344,"TraitMech--GO":232,"TraitMech--METPO":471,"TraitMech--CHEBI":180,"TraitMech--InterPro":59,"TraitMech--UniProt":176,"TraitMech--ENVO":14,"TraitMech--PATO":47,"CellStructureMech--NCBITaxon":57,"CellStructureMech--UniProt":37,"CellStructureMech--GO":57,"CellStructureMech--InterPro":13,"CellStructureMech--METPO":5,"CellStructureMech--PDB":1,"CellStructureMech--CHEBI":8,"CellStructureMech--Pfam":6,"ProteinTraitsMech--GO":110801,"ProteinTraitsMech--CHEBI":29847,"ProteinTraitsMech--METPO":119,"ProteinTraitsMech--UniProt":159304,"ProteinTraitsMech--RHEA":29506,"ProteinTraitsMech--KEGG":231,"ProteinTraitsMech--NCBITaxon":98152,"ProteinTraitsMech--Pfam":107564,"ProteinTraitsMech--InterPro":120094,"ProteinTraitsMech--UBERON":43,"ProteinTraitsMech--PATO":69,"ProteinTraitsMech--ARO":7452,"ProteinTraitsMech--PDB":51717,"NaturalProductMech--NCBITaxon":3115,"NaturalProductMech--MIBiG":3115,"NaturalProductMech--NPAtlas":1740,"NaturalProductMech--CHEBI":371,"NaturalProductMech--UniProt":142,"AntibioticMech--CAS":1804,"AntibioticMech--CHEBI":2795,"AntibioticMech--ARO":568,"AntibioticMech--NCBITaxon":134,"AntibioticMech--UniProt":47,"AntibioticMech--PDB":5,"AntibioticMech--GO":3,"MediaIngredientMech--CHEBI":2224,"MediaIngredientMech--CAS":267,"MediaIngredientMech--KEGG":53,"MediaIngredientMech--FOODON":99,"MediaIngredientMech--ENVO":26,"MediaIngredientMech--UBERON":9,"MediaIngredientMech--BTO":1,"MediaIngredientMech--NCBITaxon":1,"CultureMech--CHEBI":6123,"CultureMech--FOODON":200,"CultureMech--UBERON":72,"CultureMech--NCBITaxon":30,"CultureMech--ENVO":12,"CultureMech--KEGG":329,"CultureMech--CAS":1},"vocab_edges":[{"a":"HabitatMech","b":"CommunityMech","n":258,"by":{"NCBITaxon":213,"ENVO":40,"UBERON":4,"CHEBI":1},"ex":[{"id":"NCBITaxon:2","label":"Bacteria"},{"id":"ENVO:00002123","label":"bioreactor"},{"id":"NCBITaxon:306","label":"Pseudomonas sp."}]},{"a":"HabitatMech","b":"TraitMech","n":103,"by":{"NCBITaxon":95,"ENVO":4,"PATO":2,"DOI":2},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1280","label":"Staphylococcus aureus"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"}]},{"a":"HabitatMech","b":"CellStructureMech","n":26,"by":{"NCBITaxon":26},"ex":[{"id":"NCBITaxon:2","label":"Bacteria"},{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"}]},{"a":"HabitatMech","b":"ProteinTraitsMech","n":1244,"by":{"NCBITaxon":1230,"UBERON":12,"CHEBI":1,"GO":1},"ex":[{"id":"NCBITaxon:1280","label":"Staphylococcus aureus"},{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1869227","label":"bacterium"}]},{"a":"HabitatMech","b":"NaturalProductMech","n":311,"by":{"NCBITaxon":311},"ex":[{"id":"NCBITaxon:56","label":"Sorangium cellulosum"},{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1931","label":"Streptomyces sp."}]},{"a":"HabitatMech","b":"AntibioticMech","n":23,"by":{"NCBITaxon":23},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1280","label":"Staphylococcus aureus"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"}]},{"a":"HabitatMech","b":"MediaIngredientMech","n":20,"by":{"ENVO":15,"UBERON":4,"CHEBI":1},"ex":[{"id":"ENVO:00002149","label":"sea water"},{"id":"ENVO:00001998","label":"soil"},{"id":"ENVO:00002263","label":"garden soil"}]},{"a":"HabitatMech","b":"CultureMech","n":25,"by":{"NCBITaxon":13,"ENVO":7,"UBERON":4,"FOODON":1},"ex":[{"id":"UBERON:0000948","label":"heart"},{"id":"UBERON:0000955","label":"brain"},{"id":"UBERON:0000178","label":"blood"}]},{"a":"CommunityMech","b":"TraitMech","n":135,"by":{"CHEBI":58,"NCBITaxon":47,"GO":30},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:15379","label":"dioxygen"},{"id":"GO:0015977","label":"carbon fixation"}]},{"a":"CommunityMech","b":"CellStructureMech","n":35,"by":{"NCBITaxon":22,"CHEBI":7,"GO":6},"ex":[{"id":"NCBITaxon:2","label":"Bacteria"},{"id":"NCBITaxon:2157","label":"Archaea"},{"id":"NCBITaxon:562","label":"Escherichia coli"}]},{"a":"CommunityMech","b":"ProteinTraitsMech","n":635,"by":{"CHEBI":266,"NCBITaxon":187,"GO":181,"UBERON":1},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:30089","label":"acetate"},{"id":"CHEBI:18276","label":"dihydrogen"}]},{"a":"CommunityMech","b":"NaturalProductMech","n":98,"by":{"NCBITaxon":92,"CHEBI":6},"ex":[{"id":"NCBITaxon:306","label":"Pseudomonas sp."},{"id":"NCBITaxon:286","label":"Pseudomonas"},{"id":"NCBITaxon:562","label":"Escherichia coli"}]},{"a":"CommunityMech","b":"AntibioticMech","n":51,"by":{"CHEBI":38,"NCBITaxon":13},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"CHEBI:33709","label":"amino acid"},{"id":"NCBITaxon:4932","label":"Saccharomyces cerevisiae"}]},{"a":"CommunityMech","b":"MediaIngredientMech","n":234,"by":{"CHEBI":232,"ENVO":2},"ex":[{"id":"CHEBI:17234","label":"glucose"},{"id":"CHEBI:33709","label":"amino acid"},{"id":"CHEBI:18276","label":"dihydrogen"}]},{"a":"CommunityMech","b":"CultureMech","n":153,"by":{"CHEBI":140,"NCBITaxon":6,"ENVO":5,"DOI":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:18276","label":"dihydrogen"},{"id":"CHEBI:30089","label":"acetate"}]},{"a":"TraitMech","b":"CellStructureMech","n":95,"by":{"GO":31,"NCBITaxon":27,"DOI":17,"CHEBI":6,"UniProt":6,"METPO":5,"InterPro":3},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:83333","label":"Escherichia coli (strain K12)"},{"id":"GO:0009288","label":"bacterial-type flagellum"}]},{"a":"TraitMech","b":"ProteinTraitsMech","n":679,"by":{"GO":212,"NCBITaxon":115,"CHEBI":109,"METPO":90,"DOI":58,"UniProt":49,"InterPro":46},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"METPO:1000631","label":"trophic type"}]},{"a":"TraitMech","b":"NaturalProductMech","n":45,"by":{"NCBITaxon":40,"CHEBI":4,"DOI":1},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"},{"id":"NCBITaxon:287","label":"Pseudomonas aeruginosa"}]},{"a":"TraitMech","b":"AntibioticMech","n":24,"by":{"NCBITaxon":14,"CHEBI":10},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1280","label":"Staphylococcus aureus"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"}]},{"a":"TraitMech","b":"MediaIngredientMech","n":57,"by":{"CHEBI":57},"ex":[{"id":"CHEBI:17234","label":"glucose"},{"id":"CHEBI:18276","label":"dihydrogen"},{"id":"CHEBI:16526","label":"carbon dioxide"}]},{"a":"TraitMech","b":"CultureMech","n":36,"by":{"CHEBI":26,"NCBITaxon":10},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:18276","label":"dihydrogen"},{"id":"CHEBI:17234","label":"glucose"}]},{"a":"CellStructureMech","b":"ProteinTraitsMech","n":374,"by":{"UniProt":137,"GO":109,"DOI":57,"NCBITaxon":36,"InterPro":20,"Pfam":8,"CHEBI":7},"ex":[{"id":"NCBITaxon:99287","label":"Salmonella typhimurium (strain LT2 / SGSC1412 / ATCC 700720)"},{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:90371","label":"Salmonella enterica subsp. enterica serovar Typhimurium"}]},{"a":"CellStructureMech","b":"NaturalProductMech","n":10,"by":{"NCBITaxon":10},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"},{"id":"NCBITaxon:224308","label":"Bacillus subtilis (strain 168)"}]},{"a":"CellStructureMech","b":"AntibioticMech","n":6,"by":{"NCBITaxon":6},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:1423","label":"Bacillus subtilis"},{"id":"NCBITaxon:274","label":"Thermus thermophilus"}]},{"a":"CellStructureMech","b":"MediaIngredientMech","n":5,"by":{"CHEBI":5},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:17544","label":"hydrogencarbonate"},{"id":"CHEBI:18248","label":"iron atom"}]},{"a":"CellStructureMech","b":"CultureMech","n":4,"by":{"NCBITaxon":2,"CHEBI":2},"ex":[{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"NCBITaxon:1148","label":"Synechocystis sp. PCC 6803"},{"id":"CHEBI:18248","label":"iron atom"}]},{"a":"ProteinTraitsMech","b":"NaturalProductMech","n":830,"by":{"NCBITaxon":469,"CHEBI":140,"UniProt":133,"DOI":88},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:100226","label":"Streptomyces coelicolor A3(2)"},{"id":"NCBITaxon:227321","label":"Emericella nidulans (strain FGSC A4 / ATCC 38163 / CBS 112.46 / NRRL 194 / M139)"}]},{"a":"ProteinTraitsMech","b":"AntibioticMech","n":2442,"by":{"ARO":1753,"CHEBI":595,"NCBITaxon":70,"UniProt":20,"DOI":2,"GO":2},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"CHEBI:35681","label":"secondary alcohol"},{"id":"NCBITaxon:2697049","label":"Severe acute respiratory syndrome coronavirus 2"}]},{"a":"ProteinTraitsMech","b":"MediaIngredientMech","n":790,"by":{"CHEBI":789,"UBERON":1},"ex":[{"id":"CHEBI:15377","label":"water"},{"id":"CHEBI:15740","label":"formate"},{"id":"CHEBI:33709","label":"amino acid"}]},{"a":"ProteinTraitsMech","b":"CultureMech","n":233,"by":{"CHEBI":221,"NCBITaxon":10,"UBERON":2},"ex":[{"id":"CHEBI:15377","label":"water"},{"id":"CHEBI:16526","label":"carbon dioxide"},{"id":"CHEBI:17754","label":"glycerol"}]},{"a":"NaturalProductMech","b":"AntibioticMech","n":272,"by":{"CHEBI":176,"NCBITaxon":85,"DOI":10,"UniProt":1},"ex":[{"id":"NCBITaxon:562","label":"Escherichia coli"},{"id":"NCBITaxon:330879","label":"Aspergillus fumigatus (strain ATCC MYA-4609 / CBS 101355 / FGSC A1100 / Af293)"},{"id":"NCBITaxon:5518","label":"Fusarium graminearum"}]},{"a":"NaturalProductMech","b":"MediaIngredientMech","n":48,"by":{"CHEBI":48},"ex":[{"id":"CHEBI:15956","label":"biotin"},{"id":"CHEBI:16349","label":"L-citrulline"},{"id":"CHEBI:27592","label":"ectoine"}]},{"a":"NaturalProductMech","b":"CultureMech","n":5,"by":{"CHEBI":3,"NCBITaxon":2},"ex":[{"id":"CHEBI:15956","label":"biotin"},{"id":"CHEBI:16349","label":"L-citrulline"},{"id":"CHEBI:27592","label":"ectoine"}]},{"a":"AntibioticMech","b":"MediaIngredientMech","n":322,"by":{"CHEBI":322},"ex":[{"id":"CHEBI:33709","label":"amino acid"},{"id":"CHEBI:30746","label":"benzoic acid"},{"id":"CHEBI:17334","label":"penicillin"}]},{"a":"AntibioticMech","b":"CultureMech","n":29,"by":{"CHEBI":29},"ex":[{"id":"CHEBI:17334","label":"penicillin"},{"id":"CHEBI:48923","label":"erythromycin"},{"id":"CHEBI:30746","label":"benzoic acid"}]},{"a":"MediaIngredientMech","b":"CultureMech","n":607,"by":{"CHEBI":543,"KEGG":53,"FOODON":6,"UBERON":3,"ENVO":1,"CAS":1},"ex":[{"id":"FOODON:03315426","label":"yeast extract"},{"id":"CHEBI:17234","label":"glucose"},{"id":"CHEBI:2509","label":"agar"}]}]};

  var MECHS = {
    HabitatMech: { key: "habitatmech", scale: "Habitat", tag: "Four habitat vocabularies harmonized into ENVO-grounded records that keep every source's attestation.", records: 3208, unit: "habitat records", root: "HabitatRecord", vocab: ["ENVO", "NCBITaxon", "BTO", "UBERON", "FOODON"], github: "https://github.com/CultureBotAI/HabitatMech", site: "https://culturebotai.github.io/HabitatMech/", page: "", license: "CC0-1.0", sources: "JGI GOLD ecosystem paths, BacDive isolation sources, PREGO, Madin et al.; ENVO/UBERON/FOODON/BTO via kg-microbe", member: true, extra: "684 records reviewed (21%); 3,208 seeded from GOLD, BacDive, PREGO and Madin et al.; 174 attested by two or more sources. Admitted to the claw fleet manifest on 2026-09-07 and pinned to claw like the other members." },
    CommunityMech: { key: "communitymech", scale: "Community", tag: "Curated knowledge base of microbial communities, their interactions, cultivation and evidence.", records: 332, unit: "community records", root: "MicrobialCommunity", vocab: ["NCBITaxon", "CHEBI", "GO", "ENVO", "GTDB"], github: "https://github.com/CultureBotAI/CommunityMech", site: "https://culturebotai.github.io/CommunityMech/", page: "/communitymech/", license: "BSD-3-Clause", sources: "PubMed literature, GTDB, IMG, BioModels, CultureMech media, MediaIngredientMech ingredients", member: true, extra: "Publishes KGX nodes and edges to kg-microbe; 21 community records link their cultivation media to CultureMech by stable id." },
    TraitMech: { key: "traitmech", scale: "Traits", tag: "Microbial ecophysiological trait knowledge base, seeded from METPO, one curated YAML per trait.", records: 477, unit: "trait records", root: "TraitRecord", vocab: ["METPO", "GO", "NCBITaxon", "CHEBI", "UniProt"], github: "https://github.com/CultureBotAI/TraitMech", site: "https://culturebotai.github.io/TraitMech/", page: "", license: "CC0-1.0", sources: "METPO (vendored OWL), GapMind and GTDB genome tables as candidates", member: true, extra: "427 reviewed, 353 carry evidence-backed causal mechanism graphs; METPO term proposals published as SSSOM." },
    CellStructureMech: { key: "cellstructuremech", scale: "Cell structures", tag: "Ontology-grounded microbial cell structures: components, distribution, function and causal mechanism.", records: 57, unit: "structure records", root: "CellStructureRecord", vocab: ["GO", "NCBITaxon", "UniProt", "METPO", "Pfam"], github: "https://github.com/CultureBotAI/CellStructureMech", site: "https://culturebotai.github.io/CellStructureMech/", page: "", license: "CC0-1.0", sources: "GO cellular component, UniProt subcellular location, Complex Portal, EMDB/EMPIAR, PDB, TraitMech", member: true, extra: "Fills the layer between phenotype (TraitMech) and protein (ProteinTraitsMech); every record carries an evidence-backed causal graph." },
    ProteinTraitsMech: { key: "proteintraitsmech", scale: "Proteins", tag: "Protein sequence, structure and function trait classes, one curated YAML per trait, evidence-backed.", records: 429271, unit: "protein trait records", root: "ProteinTraitRecord", vocab: ["InterPro", "UniProt", "RHEA", "Pfam", "GO", "CHEBI", "ARO"], github: "https://github.com/CultureBotAI/proteintraitsmech", site: "https://culturebotai.github.io/proteintraitsmech/", page: "", license: "CC0-1.0", sources: "InterPro, Pfam, CATH, SCOPe, ECOD, Rhea, ExPASy ENZYME, CARD/ARO, PROSITE, TCDB, COG, Reactome, METPO", member: true, extra: "Function 163,526 · sequence 147,071 · structure 118,281 · sequence-structure and evolution 393 records; seeds 118 METPO classes with protein-level analogues." },
    NaturalProductMech: { key: "naturalproductmech", scale: "Natural products", tag: "One record per natural product structure: who makes it, from which gene cluster, and what it does.", records: 3115, unit: "natural product structures", root: "NaturalProductRecord", vocab: ["MIBiG", "NCBITaxon", "ChEBI", "NPAtlas", "PubChem", "UniProt"], github: "https://github.com/CultureBotAI/NaturalProductMech", site: "https://github.com/CultureBotAI/NaturalProductMech", page: "", license: "CC0-1.0 code · CC BY 4.0 data", sources: "ChEBI, MIBiG gene clusters, LOTUS occurrences, CyanoMetDB, NPAtlas, PubChem BioAssay, BindingDB, NCBI Taxonomy", member: false, extra: "Polyketides 869 · amino acids and peptides 655 · alkaloids 509 · terpenoids 213; 362 grounded in ChEBI, 2,744 minted on their InChIKey and 9 under review. Every record names a producer organism and a gene cluster. It vendors claw's governed artifacts, pinned one revision behind the eight, and is not yet declared in the manifest." },
    AntibioticMech: { key: "antibioticmech", scale: "Antibiotics", tag: "One record per antimicrobial structure, harmonizing ChEBI and CARD with mechanism and evidence.", records: 2920, unit: "antimicrobial structures", root: "AntibioticRecord", vocab: ["CHEBI", "ARO", "CAS", "NCBITaxon", "PubChem", "DrugBank"], github: "https://github.com/CultureBotAI/AntibioticMech", site: "https://culturebotai.github.io/AntibioticMech/", page: "", license: "CC0-1.0 code · CC BY 4.0 data", sources: "ChEBI 3-star antimicrobial roles, CARD/ARO antibiotic molecules, PubChem structures, PHI-base, MIBiG", member: true, extra: "2,669 ChEBI-grounded, 240 minted; 417 with a mode of action, 245 with a molecular target, 16 with a curated causal graph." },
    MediaIngredientMech: { key: "mediaingredientmech", scale: "Ingredients", tag: "LLM-assisted curation of media-ingredient ontology mappings with full audit trails.", records: 2958, unit: "ingredient records", root: "IngredientRecord", vocab: ["CHEBI", "CAS", "NCIT", "FOODON", "ENVO"], github: "https://github.com/CultureBotAI/MediaIngredientMech", site: "https://culturebotai.github.io/MediaIngredientMech/", page: "/mediaingredientmech/", license: "CC0-1.0", sources: "Ingredient strings aggregated from CultureMech recipes; OAK/OLS term services; ChEBI, FOODON, NCIT, MeSH, METPO", member: true, extra: "2,684 mapped (91%); its published SSSOM is the ingredient-mapping contract consumed by kg-microbe." },
    CultureMech: { key: "culturemech", scale: "Media", tag: "Versioned, ontology-grounded knowledge base of microbial culture-media recipes.", records: 6286, unit: "merged recipes", root: "MediaRecipe", vocab: ["CHEBI", "KEGG", "FOODON", "UBERON", "CAS"], github: "https://github.com/CultureBotAI/CultureMech", site: "https://culturebotai.github.io/CultureMech/", page: "/culturemech/", license: "CC0-1.0", sources: "MediaDive/DSMZ, TogoMedium, KOMODO, ATCC, JCM, BacDive (queued)", member: true, extra: "15,877 normalized recipes deduplicated into 6,286 merged canonical records; exports 11 SSSOM mapping sets." }
  };

  // Directed cross-references between Mech records, schemas and curation practice.
  var XREFS = [
    { from: "CultureMech", to: "MediaIngredientMech", kind: "data", what: "Unmapped ingredient strings and occurrence counts feed MIM's curation backlog; MIM records carry CultureMech:NNNNNN back-links by stable id.", ev: "MIM schema CultureMechReference; claw ingredient_curation_pipeline", url: "https://github.com/CultureBotAI/MediaIngredientMech/blob/main/src/mediaingredientmech/schema/mediaingredientmech.yaml" },
    { from: "MediaIngredientMech", to: "CultureMech", kind: "data", what: "Curated ChEBI/FOODON mappings sync back to recipes; CultureMech vendors MIM's ingredient-role enums and consumes its label index.", ev: "CultureMech src/culturemech/schema/mim_roles.yaml", url: "https://github.com/CultureBotAI/CultureMech/blob/main/src/culturemech/schema/mim_roles.yaml" },
    { from: "CommunityMech", to: "CultureMech", kind: "data", what: "Community records name the medium they were grown in by CultureMech id (culturemech_id on 21 records, 32 links).", ev: "CommunityMech docs/cross_repo_linking.md", url: "https://github.com/CultureBotAI/CommunityMech/blob/main/docs/cross_repo_linking.md" },
    { from: "CommunityMech", to: "MediaIngredientMech", kind: "schema", what: "RelatedIngredient.mediaingredientmech_id slot is declared for MIM ingredient ids; no record populates it yet.", ev: "CommunityMech docs/cross_repo_linking.md" },
    { from: "CellStructureMech", to: "TraitMech", kind: "data", what: "Structures list the phenotypes they confer as TraitMech / METPO terms (8 trait links); causal-graph node vocabulary is TraitMech's plus STRUCTURE.", ev: "CellStructureMech schema associated_traits", url: "https://github.com/CultureBotAI/CellStructureMech/blob/main/src/cellstructuremech/schema/cellstructuremech.yaml" },
    { from: "CellStructureMech", to: "ProteinTraitsMech", kind: "schema", what: "A single protein is a component, not a record: it grounds to InterPro / UniProtKB and hands off to ProteinTraitsMech.", ev: "CellStructureMech docs/CURATION.md", url: "https://github.com/CultureBotAI/CellStructureMech/blob/main/docs/CURATION.md" },
    { from: "HabitatMech", to: "TraitMech", kind: "schema", what: "Habitat causal graphs use a superset of TraitMech's node vocabulary so graphs stay comparable; a node may be a TraitMech or METPO term.", ev: "HabitatMech schema CausalNode", url: "https://github.com/CultureBotAI/HabitatMech/blob/main/src/habitatmech/schema/habitatmech.yaml" },
    { from: "HabitatMech", to: "CultureMech", kind: "practice", what: "The one overlapping concept, BTO:0000316 culture medium, is handed to CultureMech rather than curated twice.", ev: "HabitatMech curation/decisions.tsv", url: "https://github.com/CultureBotAI/HabitatMech/blob/main/curation/decisions.tsv" },
    { from: "AntibioticMech", to: "NaturalProductMech", kind: "data", what: "Antimicrobial classification comes from AntibioticMech: its structures are matched on InChIKey to say which natural products are antimicrobial.", ev: "NaturalProductMech data/raw/antibioticmech_inchikeys.tsv", url: "https://github.com/CultureBotAI/NaturalProductMech/blob/main/PLAN.md" },
    { from: "AntibioticMech", to: "CellStructureMech", kind: "practice", what: "The licensed source-queue curation pattern was written here and adapted by CellStructureMech.", ev: "claw docs/guides/SOURCE_QUEUE.md", url: "https://github.com/CultureBotAI/culturebotai-claw/blob/main/docs/guides/SOURCE_QUEUE.md" },
    { from: "ProteinTraitsMech", to: "TraitMech", kind: "practice", what: "TraitMech adopted ProteinTraitsMech's download.yaml source catalogue shape; a drift audit keeps shared trait tokens aligned.", ev: "TraitMech download.yaml; ProteinTraitsMech justfile", url: "https://github.com/CultureBotAI/TraitMech/blob/main/download.yaml" }
  ];

  // Exchange with the central kg-microbe knowledge graph.
  var HUB = [
    { mech: "CultureMech", dir: "out", kind: "export", what: "SSSOM mapping sets (11 files) and a KGX sample" },
    { mech: "MediaIngredientMech", dir: "out", kind: "export", what: "canonical ingredient SSSOM, the mapping contract kg-microbe consumes" },
    { mech: "CommunityMech", dir: "out", kind: "export", what: "KGX nodes and edges release" },
    { mech: "TraitMech", dir: "out", kind: "export", what: "METPO term proposals as SSSOM" },
    { mech: "HabitatMech", dir: "in", kind: "input", what: "ENVO / UBERON / FOODON / BTO in KGX form plus the curated isolation-source table" },
    { mech: "CommunityMech", dir: "in", kind: "input", what: "merged knowledge-graph edges vendored for the browser" },
    { mech: "MediaIngredientMech", dir: "in", kind: "input", what: "unified entity mappings and alternate labels" },
    { mech: "CultureMech", dir: "in", kind: "input", what: "grounding checks against kg-microbe entities (match-kg-microbe)" },
    { mech: "AntibioticMech", dir: "out", kind: "namespace", what: "schema minted under the kg-microbe namespace (w3id.org/kg-microbe/antibioticmech); no data release into the graph yet" },
    { mech: "ProteinTraitsMech", dir: "out", kind: "namespace", what: "shares the kg-microbe mech-shared schema modules; no data release into the graph yet" },
    { mech: "CellStructureMech", dir: "out", kind: "namespace", what: "shares the kg-microbe mech-shared schema modules; no data release into the graph yet" },
    { mech: "NaturalProductMech", dir: "out", kind: "namespace", what: "schema minted under the kg-microbe namespace (w3id.org/kg-microbe/naturalproductmech); no data release into the graph yet" }
  ];

  var order = DATA.order, N = order.length;
  order.forEach(function (m) { MECHS[m].name = m; });
  // Vocabularies drawn as their own chords; anything else folds into "other".
  var VOCS = ["CHEBI", "NCBITaxon", "GO", "METPO", "ENVO", "ARO", "UniProt", "DOI"];
  var VOC_LABEL = { CHEBI: "ChEBI", NCBITaxon: "NCBITaxon", GO: "GO", METPO: "METPO", ENVO: "ENVO", ARO: "ARO", UniProt: "UniProt", DOI: "citations", other: "other vocabularies" };
  var W = 900, H = 760, CX = 450, CY = 372, R = 262;
  var pos = {};
  order.forEach(function (m, i) {
    var a = -Math.PI / 2 + i * (2 * Math.PI / N);
    pos[m] = { x: CX + R * Math.cos(a), y: CY + R * Math.sin(a), a: a };
  });
  function radius(m) { return 14 + 5.5 * Math.log10(MECHS[m].records); }
  function color(m) { return "var(--mech-" + MECHS[m].key + ")"; }
  function vocColor(v) { return "var(--voc-" + (VOCS.indexOf(v) >= 0 ? v.toLowerCase() : "other") + ")"; }
  function fmt(n) { return n.toLocaleString("en-US"); }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  var SVG = "http://www.w3.org/2000/svg";
  function el(tag, attrs, parent) {
    var e = document.createElementNS(SVG, tag);
    for (var k in attrs) { if (attrs[k] !== undefined && attrs[k] !== null) e.setAttribute(k, attrs[k]); }
    if (parent) parent.appendChild(e);
    return e;
  }
  // Quadratic curve between two nodes. bow > 0 pulls the control point toward the hub,
  // bow < 0 pushes it outside the ring; spread shifts it sideways so parallel chords fan apart.
  function curve(a, b, bow, spread, ra, rb) {
    var p = pos[a], q = pos[b], mx = (p.x + q.x) / 2, my = (p.y + q.y) / 2;
    var dx = q.x - p.x, dy = q.y - p.y, d = Math.hypot(dx, dy), nx = -dy / d, ny = dx / d;
    var cx = mx + (CX - mx) * bow + nx * spread, cy = my + (CY - my) * bow + ny * spread;
    function tow(fx, fy, tx, ty, r) { var ddx = tx - fx, ddy = ty - fy, dd = Math.hypot(ddx, ddy); return [fx + ddx / dd * r, fy + ddy / dd * r]; }
    var s = tow(p.x, p.y, cx, cy, ra || 0), e = tow(q.x, q.y, cx, cy, rb || 0);
    return "M" + s[0] + "," + s[1] + " Q" + cx + "," + cy + " " + e[0] + "," + e[1];
  }

  var svg = document.getElementById("fleet-svg");
  var gGov = document.getElementById("fleet-gov"), gEdges = document.getElementById("fleet-edges"), gXrefs = document.getElementById("fleet-xrefs"), gHubE = document.getElementById("fleet-hubedges"), gHub = document.getElementById("fleet-hub"), gNodes = document.getElementById("fleet-nodes");
  var tip = document.getElementById("fleet-tip"), detail = document.getElementById("fleet-detail");
  // Single source of truth for what is drawn and what is selected.
  var state = { layers: { vocab: false, xref: true, hub: true, gov: false }, voc: "", sel: null };

  // ---- Governance ring ----
  el("circle", { "class": "ring", cx: CX, cy: CY, r: R + 58 }, gGov);
  var rl = el("text", { "class": "ring-label", x: CX, y: CY - R - 66, "text-anchor": "middle" }, gGov);
  rl.textContent = "CULTUREBOTAI-CLAW · FLEET MANIFEST · VENDORED GOVERNANCE";
  order.forEach(function (m) {
    var p = pos[m], r1 = R + 58, r0 = radius(m) + 6;
    var t = el("line", { "class": "edge gov", x1: CX + Math.cos(p.a) * r0, y1: CY + Math.sin(p.a) * r0, x2: CX + Math.cos(p.a) * r1, y2: CY + Math.sin(p.a) * r1 }, gGov);
    if (!MECHS[m].member) { t.setAttribute("stroke-dasharray", "1 5"); t.setAttribute("opacity", ".45"); }
  });

  // ---- Shared-vocabulary chords: one per (pair, vocabulary) ----
  var pairs = DATA.vocab_edges.map(function (e) {
    var present = VOCS.filter(function (v) { return e.by[v] > 0; });
    var otherN = 0; Object.keys(e.by).forEach(function (k) { if (VOCS.indexOf(k) < 0) otherN += e.by[k]; });
    var vocs = present.map(function (v) { return { voc: v, n: e.by[v] }; });
    if (otherN) vocs.push({ voc: "other", n: otherN });
    var pair = { e: e, chords: [] };
    vocs.forEach(function (c, k) {
      var spread = (k - (vocs.length - 1) / 2) * 9;
      var d = curve(e.a, e.b, 0.55, spread);
      var path = el("path", { "class": "edge vocab", d: d, tabindex: 0, role: "button", "aria-label": e.a + " and " + e.b + " share " + fmt(c.n) + " " + VOC_LABEL[c.voc] + " identifiers" }, gEdges);
      path.style.stroke = vocColor(c.voc); path.style.color = vocColor(c.voc);
      path.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectEdge(pair, c.voc); } });
      var hit = el("path", { "class": "edge hit", d: d }, gEdges);
      var chord = { pair: pair, voc: c.voc, n: c.n, path: path, hit: hit };
      [path, hit].forEach(function (h) {
        h.addEventListener("mousemove", function (ev) { showTip(ev, chordTip(chord)); path.classList.add("lit"); });
        h.addEventListener("mouseleave", function () { hideTip(); path.classList.remove("lit"); });
        h.addEventListener("click", function (ev) { ev.stopPropagation(); selectEdge(pair, chord.voc); });
      });
      pair.chords.push(chord);
    });
    return pair;
  });
  var chords = []; pairs.forEach(function (p) { p.chords.forEach(function (c) { chords.push(c); }); });
  function chordVisible(c) { return state.layers.vocab && (!state.voc || c.voc === state.voc || (c.voc === "other" && VOCS.indexOf(state.voc) < 0 && c.pair.e.by[state.voc] > 0)); }
  function pairWeight(pair) { return state.voc ? (pair.e.by[state.voc] || 0) : pair.e.n; }
  function widthFor(n) { return n <= 0 ? 0 : Math.max(0.9, 1 + 2.3 * Math.log10(n / 4)); }

  // ---- Cross-reference arcs ----
  var xrefEls = XREFS.map(function (x, i) {
    var reverse = XREFS.some(function (y, j) { return j < i && y.from === x.to && y.to === x.from; });
    var d = curve(x.from, x.to, reverse ? -0.62 : -0.38, 0, radius(x.from) + 3, radius(x.to) + 5);
    var path = el("path", { "class": "edge xref" + (x.kind === "data" ? "" : " weak"), d: d, "marker-end": "url(#fleet-arrow)", tabindex: 0, role: "button", "aria-label": x.from + " to " + x.to + ": " + x.what }, gXrefs);
    var hit = el("path", { "class": "edge hit", d: d }, gXrefs);
    path.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectXref(rec); } });
    var rec = { x: x, path: path, hit: hit };
    [path, hit].forEach(function (h) {
      h.addEventListener("mousemove", function (ev) { showTip(ev, xrefTip(x)); path.classList.add("lit"); });
      h.addEventListener("mouseleave", function () { hideTip(); path.classList.remove("lit"); });
      h.addEventListener("click", function (ev) { ev.stopPropagation(); selectXref(rec); });
    });
    return rec;
  });

  // ---- Hub and spokes ----
  var hubR = 46;
  var hubEls = HUB.map(function (h) {
    var p = pos[h.mech], dx = CX - p.x, dy = CY - p.y, d = Math.hypot(dx, dy);
    var ux = dx / d, uy = dy / d, off = h.dir === "out" ? 6 : -6;
    var px = -uy * off, py = ux * off;
    var x1 = p.x + ux * (radius(h.mech) + 4) + px, y1 = p.y + uy * (radius(h.mech) + 4) + py;
    var x2 = CX - ux * (hubR + 4) + px, y2 = CY - uy * (hubR + 4) + py;
    var attrs = { "class": "edge hub " + h.dir + (h.kind === "namespace" ? " ns" : ""), "marker-end": "url(#fleet-arrow-hub)" };
    if (h.dir === "out") { attrs.x1 = x1; attrs.y1 = y1; attrs.x2 = x2; attrs.y2 = y2; } else { attrs.x1 = x2; attrs.y1 = y2; attrs.x2 = x1; attrs.y2 = y1; }
    attrs.tabindex = 0; attrs.role = "button"; attrs["aria-label"] = h.mech + (h.dir === "out" ? " to " : " from ") + "kg-microbe: " + h.what;
    var line = el("line", attrs, gHubE);
    line.addEventListener("keydown", function (ev) { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selectHub(); } });
    var hit = el("line", { "class": "edge hit", x1: x1, y1: y1, x2: x2, y2: y2 }, gHubE);
    [line, hit].forEach(function (q) {
      q.addEventListener("mousemove", function (ev) { showTip(ev, "<b>" + esc(h.mech) + (h.dir === "out" ? " → kg-microbe" : " ← kg-microbe") + " · " + esc(h.kind) + "</b>" + esc(h.what)); line.classList.add("lit"); });
      q.addEventListener("mouseleave", function () { hideTip(); line.classList.remove("lit"); });
      q.addEventListener("click", function (ev) { ev.stopPropagation(); selectHub(); });
    });
    return { h: h, line: line, hit: hit };
  });
  var hubLink = el("a", { "class": "node-link", href: "/kg-microbe/", "aria-label": "About kg-microbe" }, gHub);
  el("circle", { "class": "hub", cx: CX, cy: CY, r: hubR }, hubLink);
  var ht = el("text", { "class": "hub-label", x: CX, y: CY - 2, "text-anchor": "middle" }, hubLink); ht.textContent = "kg-microbe";
  var hs = el("text", { "class": "hub-sub", x: CX, y: CY + 12, "text-anchor": "middle" }, hubLink); hs.textContent = "knowledge graph";
  hubLink.addEventListener("mouseenter", selectHub);
  hubLink.addEventListener("focus", selectHub);

  // ---- Nodes: hover or focus shows detail, click opens the Mech ----
  var nodeEls = {};
  order.forEach(function (m) {
    var p = pos[m], r = radius(m), M = MECHS[m];
    var a = el("a", { "class": "node-link", href: M.site, "aria-label": "Open " + m + ", " + fmt(M.records) + " " + M.unit }, gNodes);
    var g = el("g", { "class": "node" + (M.member ? "" : " adjacent") }, a);
    el("circle", { cx: p.x, cy: p.y, r: r, fill: color(m) }, g);
    var anchor = Math.cos(p.a) > 0.2 ? "start" : Math.cos(p.a) < -0.2 ? "end" : "middle";
    var lx = p.x + Math.cos(p.a) * (r + 10), ly = p.y + Math.sin(p.a) * (r + 10);
    var dy = Math.sin(p.a) > 0.6 ? 14 : Math.sin(p.a) < -0.6 ? -10 : 4;
    var t = el("text", { "class": "node-label", x: lx, y: ly + dy, "text-anchor": anchor }, g); t.textContent = m;
    var s = el("text", { "class": "node-sub", x: lx, y: ly + dy + 14, "text-anchor": anchor }, g); s.textContent = fmt(M.records) + " " + M.unit;
    a.addEventListener("mouseenter", function () { selectNode(m); });
    a.addEventListener("focus", function () { selectNode(m); });
    nodeEls[m] = g;
  });

  // ---- Rendering: everything derives from state ----
  function touches(sel, a, b) { return sel.type === "node" && (a === sel.m || b === sel.m); }
  function render() {
    var sel = state.sel;
    gGov.style.display = state.layers.gov ? "" : "none";
    gHubE.style.display = state.layers.hub ? "" : "none";
    chords.forEach(function (c) {
      var show = chordVisible(c);
      c.path.style.display = show ? "" : "none"; c.hit.style.display = show ? "" : "none";
      c.path.setAttribute("stroke-width", widthFor(c.n).toFixed(2));
      var on = !sel || (sel.type === "edge" ? sel.pair === c.pair : sel.type === "node" ? touches(sel, c.pair.e.a, c.pair.e.b) : false);
      c.path.classList.toggle("dim", !on);
    });
    xrefEls.forEach(function (rec) {
      var show = state.layers.xref;
      rec.path.style.display = show ? "" : "none"; rec.hit.style.display = show ? "" : "none";
      var on = !sel || (sel.type === "xref" ? sel.rec === rec : sel.type === "node" ? touches(sel, rec.x.from, rec.x.to) : false);
      rec.path.classList.toggle("dim", !on);
    });
    hubEls.forEach(function (rec) {
      var on = !sel || (sel.type === "hub" ? true : sel.type === "node" ? rec.h.mech === sel.m : false);
      rec.line.classList.toggle("dim", !on);
    });
    order.forEach(function (m) {
      var on = !sel || (sel.type === "node" ? (m === sel.m || connected(sel.m, m)) : sel.type === "edge" ? (sel.pair.e.a === m || sel.pair.e.b === m) : sel.type === "xref" ? (sel.rec.x.from === m || sel.rec.x.to === m) : sel.type === "hub" ? HUB.some(function (h) { return h.mech === m; }) : true);
      nodeEls[m].classList.toggle("dim", !on);
    });
    gHub.classList.toggle("dim", !!sel && sel.type === "node" && !HUB.some(function (h) { return h.mech === sel.m; }));
    document.querySelectorAll(".mech-card").forEach(function (c) { c.classList.toggle("lit", !!sel && sel.type === "node" && c.dataset.mech === sel.m); });
  }
  // Two Mechs are connected if any currently drawn edge joins them.
  function connected(a, b) {
    return chords.some(function (c) { return chordVisible(c) && ((c.pair.e.a === a && c.pair.e.b === b) || (c.pair.e.a === b && c.pair.e.b === a)); }) ||
      (state.layers.xref && XREFS.some(function (x) { return (x.from === a && x.to === b) || (x.from === b && x.to === a); }));
  }
  function clearSelection() { state.sel = null; render(); overview(); }

  // ---- Tooltips ----
  function showTip(ev, html) {
    var stage = svg.parentNode.getBoundingClientRect();
    tip.innerHTML = html; tip.classList.add("show");
    var x = ev.clientX - stage.left + 14, y = ev.clientY - stage.top + 14;
    if (x + 310 > stage.width) x = Math.max(4, ev.clientX - stage.left - 314);
    tip.style.left = x + "px"; tip.style.top = y + "px";
  }
  function hideTip() { tip.classList.remove("show"); }
  function chordTip(c) {
    var e = c.pair.e, ex = e.ex.filter(function (t) { return c.voc === "other" ? VOCS.indexOf(t.id.split(":")[0]) < 0 : t.id.indexOf(c.voc + ":") === 0; }).map(function (t) { return t.label; }).join(", ");
    return "<b>" + esc(e.a) + " ↔ " + esc(e.b) + " · " + esc(VOC_LABEL[c.voc]) + "</b><span class=\"k\">" + fmt(c.n) + " shared " + (c.voc === "DOI" ? (c.n === 1 ? "citation" : "citations") : (c.n === 1 ? "identifier" : "identifiers")) + "</span> of " + fmt(e.n) + " in total" + (ex ? "<br><em>e.g. " + esc(ex) + "</em>" : "") + "<br><em>Click to list the records behind this chord.</em>";
  }
  function xrefTip(x) { return "<b>" + esc(x.from) + " → " + esc(x.to) + "</b>" + esc(x.what); }

  // ---- Detail panel ----
  function linkRow(M) {
    var out = '<div class="links"><a class="go" href="' + M.site + '">Open ' + esc(M.name) + ' ↗</a>';
    if (M.page) out += '<a href="' + M.page + '">Page on this site</a>';
    return out + '<a href="' + M.github + '">GitHub</a></div>';
  }
  function strongest() {
    var rows = pairs.map(function (p) { return { p: p, n: pairWeight(p) }; }).filter(function (r) { return r.n > 0; }).sort(function (a, b) { return b.n - a.n; }).slice(0, 5);
    if (!rows.length) return '<p>No two Mechs share ' + esc(state.voc) + ' identifiers in their record corpora. The heatmap shows which Mechs use this vocabulary on their own.</p>';
    return '<ul>' + rows.map(function (r) {
      var e = r.p.e, top = Object.keys(e.by).sort(function (a, b) { return e.by[b] - e.by[a]; })[0];
      return '<li><b>' + esc(e.a) + ' ↔ ' + esc(e.b) + '</b>: ' + fmt(r.n) + ' shared terms' + (state.voc ? '' : ', ' + fmt(e.by[top]) + ' of them ' + esc(top)) + (e.ex.length ? ' <em style="color:var(--muted)">(' + esc(e.ex.slice(0, 2).map(function (t) { return t.label; }).join(", ")) + ')</em>' : '') + '</li>';
    }).join("") + '</ul>';
  }
  function overview() {
    detail.innerHTML =
      '<div><p class="eyebrow">Reading the graph</p><h3 style="color:var(--ink)">Eight views of one microbe</h3>' +
      '<p>Clockwise from the top the ring walks from the environment a microbe lives in to the medium it is grown in: habitat, community, traits, cell structures, proteins, antibiotics, ingredients, media. A culture medium is a synthetic habitat, so the ring closes.</p>' +
      '<p>Dashed arcs outside the ring are direct cross-references, where one Mech\'s records, schema or curation practice name another; spokes tie each Mech to the central kg-microbe graph. Turn on the shared-vocabulary layer to see one colored chord per ontology that two Mechs both cite. Hover a node for its detail and click it to open that Mech; click a chord, arc or spoke to see what it carries and to jump to the matching records.</p></div>' +
      '<div><p class="eyebrow">Strongest shared vocabulary' + (state.voc ? ' (' + esc(state.voc) + ')' : '') + '</p>' + strongest() + '</div>';
  }
  function selectNode(m) {
    state.sel = { type: "node", m: m }; render();
    var M = MECHS[m], rows = [];
    pairs.forEach(function (p) { var e = p.e; if (e.a === m || e.b === m) rows.push({ o: e.a === m ? e.b : e.a, n: pairWeight(p), top: Object.keys(e.by).sort(function (x, y) { return e.by[y] - e.by[x]; })[0], ex: e.ex }); });
    rows.sort(function (a, b) { return b.n - a.n; });
    var xr = XREFS.filter(function (x) { return x.from === m || x.to === m; });
    var hub = HUB.filter(function (h) { return h.mech === m; });
    detail.innerHTML =
      '<div><p class="eyebrow">' + esc(M.scale) + ' · ' + (M.member ? 'in the claw fleet manifest' : 'not yet in the claw fleet manifest') + '</p>' +
      '<h3 style="color:' + color(m) + ';border-image:none;border-color:' + color(m) + '">' + esc(m) + '</h3><p>' + esc(M.tag) + ' ' + esc(M.extra) + '</p>' +
      '<dl class="meta"><dt>Records</dt><dd>' + fmt(M.records) + ' ' + esc(M.unit) + '</dd><dt>Root class</dt><dd><code>' + esc(M.root) + '</code></dd><dt>Grounded in</dt><dd>' + esc(M.vocab.join(", ")) + '</dd><dt>Sources</dt><dd>' + esc(M.sources) + '</dd><dt>License</dt><dd>' + esc(M.license) + '</dd></dl>' + linkRow(M) + '</div>' +
      '<div>' + (xr.length ? '<p class="eyebrow">Cross-references</p><ul>' + xr.map(function (x) { return '<li><b>' + esc(x.from) + ' → ' + esc(x.to) + '</b>: ' + esc(x.what) + '</li>'; }).join("") + '</ul>' : '') +
      (hub.length ? '<p class="eyebrow" style="margin-top:.8rem">kg-microbe</p><ul>' + hub.map(function (h) { return '<li>' + (h.dir === "out" ? (h.kind === "namespace" ? "Namespace: " : "Exports ") : "Receives ") + esc(h.what) + '</li>'; }).join("") + '</ul>' : '') +
      '<p class="eyebrow" style="margin-top:.8rem">Shared vocabulary' + (state.voc ? ' (' + esc(state.voc) + ')' : '') + (state.layers.vocab ? '' : ' · layer off') + '</p><ul>' +
      rows.filter(function (r) { return r.n > 0; }).slice(0, 5).map(function (r) { return '<li><b>' + esc(r.o) + '</b> · ' + fmt(r.n) + ' terms, mostly ' + esc(r.top) + (r.ex.length ? ' <em style="color:var(--muted)">(' + esc(r.ex.slice(0, 2).map(function (t) { return t.label; }).join(", ")) + ')</em>' : '') + '</li>'; }).join("") + '</ul></div>';
  }
  var FLEET_DATA_URL = "/assets/fleet/";
  var subsetCache = {};
  var LIVE = location.hostname === "culturebotai.github.io";
  function loadFailed(extra) { return (LIVE ? 'The record list could not be loaded. Reload the page to try again.' : 'Record lists load on the live site (<a href="https://culturebotai.github.io/mechs/">culturebotai.github.io/mechs</a>); this preview cannot fetch them.') + (extra || ''); }
  function loadJSON(path) {
    if (subsetCache[path]) return subsetCache[path];
    var p = fetch(FLEET_DATA_URL + path).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
    subsetCache[path] = p;
    p["catch"](function () { delete subsetCache[path]; });
    return p;
  }
  function recLinks(base, refs, more) {
    var out = refs.map(function (r) { return '<a href="' + esc(base + r[0]) + '" title="' + esc(r[1]) + '">' + esc(r[1].length > 38 ? r[1].slice(0, 36) + "…" : r[1]) + '</a>'; }).join(", ");
    if (more > refs.length) out += ' <em>+' + fmt(more - refs.length) + ' more</em>';
    return out;
  }
  function renderTermList(box, doc) {
    var q = (box.querySelector("input") || {}).value || "", shown = parseInt(box.dataset.shown || "40", 10);
    var terms = doc.terms.filter(function (t) { return !q || (t.id + " " + t.l).toLowerCase().indexOf(q.toLowerCase()) >= 0; });
    box.querySelector("ol").innerHTML = terms.slice(0, shown).map(function (t) {
      return '<li><b>' + esc(t.l || t.id) + '</b> <code>' + esc(t.id) + '</code><div class="in"><span>' + esc(doc.a) + ' (' + fmt(t.na) + '):</span> ' + recLinks(doc.base[doc.a], t.a, t.na) + '</div><div class="in"><span>' + esc(doc.b) + ' (' + fmt(t.nb) + '):</span> ' + recLinks(doc.base[doc.b], t.b, t.nb) + '</div></li>';
    }).join("") || '<li><em>No terms match.</em></li>';
    var more = box.querySelector(".more");
    more.hidden = terms.length <= shown; more.textContent = "Show " + Math.min(40, terms.length - shown) + " more of " + fmt(terms.length);
    box.querySelector(".count").textContent = fmt(terms.length) + " shared term" + (terms.length === 1 ? "" : "s") + (q ? " matching “" + q + "”" : "") + ", each linked to the records that carry it";
  }
  function selectEdge(pair, voc, keep) {
    state.sel = { type: "edge", pair: pair }; render();
    var e = pair.e, keys = Object.keys(e.by).sort(function (a, b) { return e.by[b] - e.by[a]; });
    var initial = keep ? keep.q : (voc && voc !== "other" ? voc + ":" : "");
    detail.innerHTML = '<div><p class="eyebrow">Shared vocabulary</p><h3 style="color:var(--ink)">' + esc(e.a) + ' ↔ ' + esc(e.b) + '</h3><p>' + fmt(e.n) + ' identical ontology identifiers occur in both record corpora, so the two knowledge bases join on them without any mapping step.</p>' +
      '<div class="links"><a class="go" href="' + MECHS[e.a].site + '">Open ' + esc(e.a) + ' ↗</a><a class="go" href="' + MECHS[e.b].site + '">Open ' + esc(e.b) + ' ↗</a></div>' +
      '<dl class="meta" style="margin-top:.8rem">' + keys.map(function (k) { return '<dt><i class="voc-dot" style="background:' + vocColor(k) + '"></i>' + esc(k) + '</dt><dd>' + fmt(e.by[k]) + '</dd>'; }).join("") + '</dl></div>' +
      '<div class="termbox" id="fleet-termbox"><p class="eyebrow">The records behind this edge</p><p class="count">Loading the shared terms…</p></div>';
    var box = document.getElementById("fleet-termbox");
    loadJSON("edges/" + e.a + "--" + e.b + ".json").then(function (doc) {
      if (!(state.sel && state.sel.type === "edge" && state.sel.pair === pair)) return; // selection moved on
      box.innerHTML = '<p class="eyebrow">The records behind this edge</p><p class="count"></p><input type="search" placeholder="Filter terms, e.g. glucose or CHEBI:17234" aria-label="Filter shared terms"><ol></ol><button type="button" class="fleet-chip more" hidden></button>';
      box.dataset.shown = keep ? keep.shown : 40;
      var input = box.querySelector("input"); input.value = initial;
      input.addEventListener("input", function () { box.dataset.shown = 40; renderTermList(box, doc); });
      box.querySelector(".more").addEventListener("click", function () { box.dataset.shown = parseInt(box.dataset.shown, 10) + 40; renderTermList(box, doc); });
      renderTermList(box, doc);
    })["catch"](function () {
      box.querySelector(".count").innerHTML = loadFailed(e.ex.length ? ' Examples: ' + esc(e.ex.map(function (t) { return t.label + " (" + t.id + ")"; }).join(", ")) + '.' : '');
    });
  }
  function selectXref(rec) {
    state.sel = { type: "xref", rec: rec }; render();
    var x = rec.x;
    detail.innerHTML = '<div><p class="eyebrow">Cross-reference · ' + esc(x.kind) + '</p><h3 style="color:var(--ink)">' + esc(x.from) + ' → ' + esc(x.to) + '</h3><p>' + esc(x.what) + '</p>' +
      '<div class="links"><a class="go" href="' + MECHS[x.from].site + '">Open ' + esc(x.from) + ' ↗</a><a href="' + MECHS[x.to].site + '">Open ' + esc(x.to) + '</a></div></div>' +
      '<div><p class="eyebrow">Evidence</p><p>' + esc(x.ev) + '</p>' + (x.url ? '<div class="links"><a href="' + x.url + '">View the source on GitHub</a></div>' : '') + '</div>';
  }
  function selectHub() {
    state.sel = { type: "hub" }; render();
    detail.innerHTML = '<div><p class="eyebrow">Hub</p><h3 style="color:var(--ink)">kg-microbe</h3><p>The Mechs are curated upstream of kg-microbe and publish into it as SSSOM mapping sets or KGX graphs; in turn, kg-microbe supplies harmonized ontologies and mapping tables back to the Mechs that need them. Three Mechs share only the kg-microbe namespace so far and do not yet release data into the graph.</p><div class="links"><a class="go" href="/kg-microbe/">About kg-microbe ↗</a><a href="https://github.com/Knowledge-Graph-Hub/kg-microbe">GitHub</a></div></div>' +
      '<div><p class="eyebrow">Exchange</p><ul>' + HUB.map(function (h) { return '<li><b>' + esc(h.mech) + (h.dir === "out" ? ' →' : ' ←') + '</b> ' + esc(h.what) + '</li>'; }).join("") + '</ul></div>';
  }
  // Re-render whatever is selected after a filter change.
  function refreshDetail() {
    var sel = state.sel;
    if (!sel) overview();
    else if (sel.type === "node") selectNode(sel.m);
    else if (sel.type === "edge") { var old = document.getElementById("fleet-termbox"), inp = old && old.querySelector("input"); selectEdge(sel.pair, state.voc, inp ? { q: inp.value, shown: old.dataset.shown || 40 } : null); }
    else if (sel.type === "xref") selectXref(sel.rec);
    else selectHub();
  }

  // ---- Controls ----
  function syncLayerChips() { document.querySelectorAll(".fleet-chip[data-layer]").forEach(function (b) { b.setAttribute("aria-pressed", String(state.layers[b.dataset.layer])); }); }
  document.querySelectorAll(".fleet-chip[data-layer]").forEach(function (b) {
    b.addEventListener("click", function () { state.layers[b.dataset.layer] = !state.layers[b.dataset.layer]; syncLayerChips(); render(); refreshDetail(); });
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
    render(); refreshDetail();
  }
  document.querySelectorAll(".fleet-chip.voc").forEach(function (b) { b.addEventListener("click", function () { setVoc(b.classList.contains("other") ? "" : (b.dataset.voc === state.voc ? "" : b.dataset.voc)); }); });
  svg.addEventListener("click", function (ev) { if (ev.target === svg) clearSelection(); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape" && state.sel) clearSelection(); });

  // ---- Cards ----
  document.querySelectorAll(".mech-card").forEach(function (c) {
    c.addEventListener("mouseenter", function () { selectNode(c.dataset.mech); });
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
      html += '<tr><th scope="row" style="--c:' + color(m) + '"><i></i><a href="' + MECHS[m].site + '" title="Open ' + esc(m) + '">' + esc(m) + "</a></th>";
      VOC.forEach(function (v) {
        var n = DATA.heat[m][v], l = n ? Math.round(12 + 88 * Math.log10(n) / lmax) : 0, recs = DATA.cells[m + "--" + v];
        var cell = !n ? "&middot;" : recs ? '<button type="button" data-mech="' + m + '" data-voc="' + v + '" aria-label="' + fmt(recs) + ' records in ' + esc(m) + ' grounded in ' + esc(v) + '">' + short(n) + "</button>" : '<span>' + short(n) + '</span>';
        html += '<td data-voc="' + v + '" data-l="' + l + '" style="--l:' + l + '" title="' + esc(m) + " · " + esc(v) + ": " + fmt(n) + ' occurrences' + (recs ? ' in ' + fmt(recs) + ' records' : '') + '">' + cell + "</td>";
      });
      html += "</tr>";
    });
    heat.innerHTML = html + "</tbody>";
    heat.querySelectorAll("thead button").forEach(function (b) { b.addEventListener("click", function () { var v = b.dataset.voc; setVoc(state.voc === v ? "" : v); }); });
    var cellPanel = document.getElementById("fleet-cell-panel"), cellSel = null;
    heat.querySelectorAll("tbody button").forEach(function (b) {
      b.addEventListener("click", function () {
        var m = b.dataset.mech, v = b.dataset.voc, key = m + "--" + v; cellSel = key;
        heat.querySelectorAll("tbody td").forEach(function (td) { td.classList.toggle("sel", td.contains(b)); });
        cellPanel.hidden = false;
        cellPanel.innerHTML = '<p class="eyebrow">' + esc(m) + ' · ' + esc(v) + '</p><p>Loading records…</p>';
        loadJSON("cells/" + key + ".json").then(function (doc) {
          if (cellSel !== key) return; // a later click replaced this one
          var cap = doc.records.length < doc.total;
          cellPanel.innerHTML = '<p class="eyebrow">' + esc(m) + ' · ' + esc(v) + '</p><h3 style="color:' + color(m) + ';border-image:none;border-color:' + color(m) + '">' + fmt(doc.total) + ' record' + (doc.total === 1 ? '' : 's') + ' in ' + esc(m) + ' cite ' + esc(v) + ' identifiers</h3>' +
            '<p>' + (cap ? 'Showing the first ' + fmt(doc.records.length) + '. ' : '') + 'Each link opens the record' + (m === "CultureMech" || m === "MediaIngredientMech" ? ' source file on GitHub' : ' page') + '.</p>' +
            '<div class="links"><a class="go" href="' + MECHS[m].site + '">Open ' + esc(m) + ' ↗</a></div><p class="reclist">' + recLinks(doc.base, doc.records, doc.records.length) + '</p>';
        })["catch"](function () { if (cellSel !== key) return; cellPanel.innerHTML = '<p class="eyebrow">' + esc(m) + ' · ' + esc(v) + '</p><p>' + loadFailed() + '</p>'; });
      });
    });
  }
  function short(n) { return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "k" : String(n); }

  render(); overview();
  }
})();
</script>


## The nine Mechs

Each card carries its Mech's own site color. Hover a card to trace its ties in the graph above; use "Show in graph" to select it.

<div class="mech-cards">
  <article class="mech-card" data-mech="HabitatMech" style="--c: var(--mech-habitatmech)">
    <header><h3>HabitatMech</h3><span class="scale">Habitat</span></header>
    <p class="tag">Four habitat vocabularies harmonized into ENVO-grounded records that keep every source's attestation.</p>
    <div class="num"><b>3,208</b><span>habitat records · 684 reviewed</span></div>
    <div class="vocab"><span>ENVO</span><span>NCBITaxon</span><span>BTO</span><span>UBERON</span><span>FOODON</span><span>GOLD</span><span>BacDive</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/HabitatMech/">Browse</a><a href="https://github.com/CultureBotAI/HabitatMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="CommunityMech" style="--c: var(--mech-communitymech)">
    <header><h3>CommunityMech</h3><span class="scale">Community</span></header>
    <p class="tag">Curated knowledge base of microbial communities, their interactions, cultivation conditions and evidence.</p>
    <div class="num"><b>332</b><span>community records · KGX export</span></div>
    <div class="vocab"><span>NCBITaxon</span><span>ChEBI</span><span>GO</span><span>ENVO</span><span>GTDB</span><span>PMID</span></div>
    <div class="row"><a class="primary" href="/communitymech/">Page</a><a href="https://culturebotai.github.io/CommunityMech/">Browse</a><a href="https://github.com/CultureBotAI/CommunityMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="TraitMech" style="--c: var(--mech-traitmech)">
    <header><h3>TraitMech</h3><span class="scale">Traits</span></header>
    <p class="tag">Microbial ecophysiological trait knowledge base seeded from METPO, one curated YAML per trait, with causal mechanism graphs.</p>
    <div class="num"><b>477</b><span>trait records · 353 with causal graphs</span></div>
    <div class="vocab"><span>METPO</span><span>GO</span><span>NCBITaxon</span><span>ChEBI</span><span>UniProt</span><span>PATO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/TraitMech/">Browse</a><a href="https://github.com/CultureBotAI/TraitMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="CellStructureMech" style="--c: var(--mech-cellstructuremech)">
    <header><h3>CellStructureMech</h3><span class="scale">Cell structures</span></header>
    <p class="tag">Organelles, envelope layers, appendages, microcompartments and complexes: components, distribution, function and causal mechanism.</p>
    <div class="num"><b>57</b><span>structure records · evidence-backed causal graphs</span></div>
    <div class="vocab"><span>GO</span><span>NCBITaxon</span><span>UniProt</span><span>METPO</span><span>Pfam</span><span>PDB</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/CellStructureMech/">Browse</a><a href="https://github.com/CultureBotAI/CellStructureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="ProteinTraitsMech" style="--c: var(--mech-proteintraitsmech)">
    <header><h3>ProteinTraitsMech</h3><span class="scale">Proteins</span></header>
    <p class="tag">Protein sequence, structure and function trait classes seeded from InterPro, Pfam, Rhea, CATH, SCOPe, CARD and more.</p>
    <div class="num"><b>429,271</b><span>protein trait records</span></div>
    <div class="vocab"><span>InterPro</span><span>UniProt</span><span>Rhea</span><span>Pfam</span><span>GO</span><span>ChEBI</span><span>ARO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/proteintraitsmech/">Browse</a><a href="https://github.com/CultureBotAI/proteintraitsmech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="NaturalProductMech" style="--c: var(--mech-naturalproductmech)">
    <header><h3>NaturalProductMech</h3><span class="scale">Natural products</span></header>
    <p class="tag">One record per natural product structure: who makes it, from which gene cluster, what it does, and the evidence for all three.</p>
    <div class="num"><b>3,115</b><span>structures · every one with a producer</span></div>
    <div class="vocab"><span>MIBiG</span><span>NCBITaxon</span><span>ChEBI</span><span>NPAtlas</span><span>PubChem</span><span>UniProt</span></div>
    <div class="row"><a class="primary" href="https://github.com/CultureBotAI/NaturalProductMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge adj">not yet in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="AntibioticMech" style="--c: var(--mech-antibioticmech)">
    <header><h3>AntibioticMech</h3><span class="scale">Antibiotics</span></header>
    <p class="tag">One record per antimicrobial chemical structure, harmonizing ChEBI and CARD with targets, mode of action, resistance and evidence.</p>
    <div class="num"><b>2,920</b><span>antimicrobial structures · 92% ChEBI-grounded</span></div>
    <div class="vocab"><span>ChEBI</span><span>ARO</span><span>CAS</span><span>PubChem</span><span>DrugBank</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/AntibioticMech/">Browse</a><a href="https://github.com/CultureBotAI/AntibioticMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="MediaIngredientMech" style="--c: var(--mech-mediaingredientmech)">
    <header><h3>MediaIngredientMech</h3><span class="scale">Ingredients</span></header>
    <p class="tag">LLM-assisted curation of media-ingredient ontology mappings with full audit trails; owns ingredient identity for the fleet.</p>
    <div class="num"><b>2,958</b><span>ingredient records · 91% mapped</span></div>
    <div class="vocab"><span>ChEBI</span><span>CAS</span><span>NCIT</span><span>FOODON</span><span>ENVO</span><span>MeSH</span></div>
    <div class="row"><a class="primary" href="/mediaingredientmech/">Page</a><a href="https://culturebotai.github.io/MediaIngredientMech/">Browse</a><a href="https://github.com/CultureBotAI/MediaIngredientMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
  <article class="mech-card" data-mech="CultureMech" style="--c: var(--mech-culturemech)">
    <header><h3>CultureMech</h3><span class="scale">Media</span></header>
    <p class="tag">Versioned, ontology-grounded knowledge base of culture-media recipes from MediaDive, TogoMedium, KOMODO and the major collections.</p>
    <div class="num"><b>6,286</b><span>merged recipes · 15,877 normalized</span></div>
    <div class="vocab"><span>ChEBI</span><span>KEGG</span><span>FOODON</span><span>UBERON</span><span>CAS</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="/culturemech/">Page</a><a href="https://culturebotai.github.io/CultureMech/">Browse</a><a href="https://github.com/CultureBotAI/CultureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><span class="badge">in fleet manifest</span></div>
  </article>
</div>

## Shared vocabulary

The Mechs are joinable because they ground records in the same public ontologies. The table counts identifier occurrences per vocabulary in each Mech's record corpus; darker cells mean more. Click a Mech name to open it, a cell to list the records behind it, or a column heading to filter the graph to that vocabulary.

<div class="fleet-heat-wrap"><table class="fleet-heat" id="fleet-heat" aria-label="Ontology identifier occurrences per Mech"></table></div>
<div class="fleet-cell-panel" id="fleet-cell-panel" hidden></div>
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
  <div><h4>Fleet manifest</h4><p><code>fleet.yaml</code> is the single source of truth for which repositories form the fleet. Eight of the nine are declared; HabitatMech, the last to join, was admitted on 2026-09-07, and NaturalProductMech is the one still outside. Every member declares every capability exactly once as enabled, disabled or not applicable, with a reason that names the files behind it, so nothing is silently off.</p></div>
  <div><h4>Vendored governance</h4><p>Shared LinkML modules (<code>mech_shared.yaml</code>, <code>history.yaml</code>), validators and behavioral contracts live in claw and are vendored into each Mech byte-identically, pinned to one immutable claw commit and checked in CI. Fifteen artifacts. NaturalProductMech already vendors them, one revision behind the eight, which is what a repository does before the manifest declares it.</p></div>
  <div><h4>Pipelines and skills</h4><p>Three cross-repository pipelines (ingredient curation, unified ingredient mapping, ENVO environment curation) and 24 agent skills. Cross-repo writes resolve exact worktree roots, take a repository lock, default to dry run and validate staged output before replacing source data.</p></div>
</div>

Which fleet contracts each member has adopted, from the manifest. Every disabled entry records a file-level reason, such as no download.yaml or no source queue yet:

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
    <tr><td>HabitatMech</td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="e"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td><td><i class="d"></i></td></tr>
    <tr><td>NaturalProductMech</td><td colspan="11"><i class="x">not yet a manifest member, so it declares no capabilities; it vendors the governed artifacts and pins the fleet's current revision</i></td></tr>
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
