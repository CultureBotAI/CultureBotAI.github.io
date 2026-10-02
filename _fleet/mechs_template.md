---
layout: default
title: "X-Mech Suite"
description: "A fleet of <!--FLEET_COUNT_WORD--> ontology-grounded autonomous knowledge factories for microbial science, from taxon identity and habitat to culture medium, orchestrated by culturebotai-claw and connected through shared ontology terms and direct cross-references"
permalink: /mechs/
---

# X-Mech Suite: <!--FLEET_COUNT_WORD--> autonomous knowledge factories, one shared standard

The X-Mech suite brings together <!--FLEET_COUNT_WORD--> autonomous knowledge factories that describe a microbe at every scale: its taxon and strain identity, habitat, community, traits, pathways, cellular structures, protein functions and unresolved domains, natural products, antibiotics, ingredients and culture media. Established corpora curate structured records with evidence and provenance; DUFMech begins with an InterPro/Pfam seed worklist. [culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw) coordinates the <!--FLEET_MANIFEST_COUNT_WORD--> projects currently declared in its fleet manifest.

Each X-Mech is an **autonomous knowledge factory** that curates, validates, and connects scientific evidence to enable discovery, with human oversight. Its knowledge base is the collection of structured records it produces and maintains.

<!--FLEET_FRAGMENT-->

## The <!--FLEET_COUNT_WORD--> Mechs

Each card carries its Mech's identity color. Hover a card to trace its ties in the graph above; use "Show in graph" to select it. The small print under each headline number gives reviewed records and merged pull requests; a Mech whose schema has no field recording review shows only the pull-request count, rather than a zero that would claim more than it knows. Counts were checked on October 1, 2026, with all twelve Mechs included in the vocabulary census and repository statistics. DUFMech's 6,532 seed families are labeled separately from curated mechanism records. Each Browse link is the source for its numbered card, except CultureMech, whose count comes from its <a href="https://github.com/CultureBotAI/CultureMech/blob/ec49c9da275414572c4b9800313265d907aecf8a/README.md#corpus-snapshot">repository's corpus snapshot</a>, and DUFMech, whose count comes from its linked seed snapshot. CommunityMech lists 456 communities online and keeps four additional isolate records in its repository; its landing page's category tile reads 16, while its schema, records and browser facet have 15. These published-browser totals may differ from the record-corpus census below. Fleet membership and capability declarations come from <!--FLEET_MANIFEST_SOURCE-->.

<div class="mech-cards">
  <article class="mech-card" data-mech="HabitatMech" style="--c: var(--mech-habitatmech); --ci: var(--mech-habitatmech-ink)">
    <header><h3>HabitatMech</h3><span class="scale">Habitat</span></header>
    <p class="tag">Four habitat vocabularies harmonized into ontology-grounded records that keep every source's attestation.</p>
    <div class="num"><b>3,206</b><span>habitat records · 686 reviewed</span></div>
    <p class="prov"><!--FLEET_STATS:HabitatMech--></p>
    <div class="vocab"><span>ENVO</span><span>NCBITaxon</span><span>BTO</span><span>UBERON</span><span>FOODON</span><span>GOLD</span><span>BacDive</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/HabitatMech/">Browse</a><a href="https://github.com/CultureBotAI/HabitatMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:HabitatMech--></div>
  </article>
  <article class="mech-card" data-mech="CommunityMech" style="--c: var(--mech-communitymech); --ci: var(--mech-communitymech-ink)">
    <header><h3>CommunityMech</h3><span class="scale">Community</span></header>
    <p class="tag">Autonomous knowledge factory for microbial communities, their interactions, cultivation conditions and evidence.</p>
    <div class="num"><b>456</b><span>community records · 15 categories</span></div>
    <p class="prov"><!--FLEET_STATS:CommunityMech--></p>
    <div class="vocab"><span>NCBITaxon</span><span>ChEBI</span><span>GO</span><span>ENVO</span><span>GTDB</span><span>PMID</span></div>
    <div class="row"><a class="primary" href="/communitymech/">Page</a><a href="https://culturebotai.github.io/CommunityMech/">Browse</a><a href="https://github.com/CultureBotAI/CommunityMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:CommunityMech--></div>
  </article>
  <article class="mech-card" data-mech="TaxonMech" style="--c: var(--mech-taxonmech); --ci: var(--mech-taxonmech-ink)">
    <header><h3>TaxonMech</h3><span class="scale">Taxa and strains</span></header>
    <p class="tag">Microbial taxa and strains identified by NCBI Taxonomy, harmonized with GTDB, LPSN and BacDive, with evidence for strain-to-genome links.</p>
    <div class="num"><b>625,960</b><span>taxon records · 100,745 listed strains</span></div>
    <p class="prov"><!--FLEET_STATS:TaxonMech--></p>
    <div class="vocab"><span>NCBITaxon</span><span>GTDB</span><span>LPSN</span><span>BacDive</span><span>NCBI Assembly</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/TaxonMech/">Browse</a><a href="https://github.com/CultureBotAI/TaxonMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:TaxonMech--></div>
  </article>
  <article class="mech-card" data-mech="TraitMech" style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink)">
    <header><h3>TraitMech</h3><span class="scale">Traits</span></header>
    <p class="tag">Autonomous knowledge factory for microbial ecophysiological traits, seeded from METPO, with one curated YAML per trait and causal mechanism graphs.</p>
    <div class="num"><b>922</b><span>trait records · 10 categories</span></div>
    <p class="prov"><!--FLEET_STATS:TraitMech--></p>
    <div class="vocab"><span>METPO</span><span>GO</span><span>NCBITaxon</span><span>ChEBI</span><span>UniProt</span><span>PATO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/TraitMech/">Browse</a><a href="https://github.com/CultureBotAI/TraitMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:TraitMech--></div>
  </article>
  <article class="mech-card" data-mech="PathwayMech" style="--c: var(--mech-pathwaymech); --ci: var(--mech-pathwaymech-ink)">
    <header><h3>PathwayMech</h3><span class="scale">Pathways</span></header>
    <p class="tag">Microbial pathway mechanisms with explicit participants, reactions, causal edges and reference-backed evidence.</p>
    <div class="num"><b>152</b><span>pathway records · 15 taxa</span></div>
    <p class="prov"><!--FLEET_STATS:PathwayMech--></p>
    <div class="vocab"><span>ChEBI</span><span>NCBITaxon</span><span>Rhea</span><span>EC</span><span>UniProtKB</span><span>MetaCyc</span><span>WikiPathways</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/PathwayMech/pages/browse.html">Browse</a><a href="https://github.com/CultureBotAI/PathwayMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:PathwayMech--></div>
  </article>
  <article class="mech-card" data-mech="CellStructureMech" style="--c: var(--mech-cellstructuremech); --ci: var(--mech-cellstructuremech-ink)">
    <header><h3>CellStructureMech</h3><span class="scale">Cell structures</span></header>
    <p class="tag">Organelles, envelope layers, appendages, microcompartments and complexes: components, distribution, function and causal mechanism.</p>
    <div class="num"><b>781</b><span>structure records · 711 GO-grounded</span></div>
    <p class="prov"><!--FLEET_STATS:CellStructureMech--></p>
    <div class="vocab"><span>GO</span><span>NCBITaxon</span><span>UniProt</span><span>METPO</span><span>Pfam</span><span>PDB</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/CellStructureMech/">Browse</a><a href="https://github.com/CultureBotAI/CellStructureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:CellStructureMech--></div>
  </article>
  <article class="mech-card" data-mech="ProteinTraitsMech" style="--c: var(--mech-proteintraitsmech); --ci: var(--mech-proteintraitsmech-ink)">
    <header><h3>ProteinTraitsMech</h3><span class="scale">Protein traits</span></header>
    <p class="tag">Protein sequence, structure and function trait classes seeded from InterPro, Pfam, Rhea, CATH, SCOPe, CARD and more.</p>
    <div class="num"><b>429,293</b><span>protein trait records · 34 sources</span></div>
    <p class="prov"><!--FLEET_STATS:ProteinTraitsMech--></p>
    <div class="vocab"><span>InterPro</span><span>UniProt</span><span>Rhea</span><span>Pfam</span><span>GO</span><span>ChEBI</span><span>ARO</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/proteintraitsmech/">Browse</a><a href="https://github.com/CultureBotAI/proteintraitsmech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:ProteinTraitsMech--></div>
  </article>
  <article class="mech-card" data-mech="DUFMech" style="--c: var(--mech-dufmech); --ci: var(--mech-dufmech-ink)">
    <header><h3>DUFMech</h3><span class="scale">Unknown functions</span></header>
    <p class="tag">Evidence gathering for domains and protein families whose functions remain unresolved.</p>
    <div class="num"><b>6,532</b><span>seed families · 4,533 unknown candidates</span></div>
    <p>The worklist separates 4,533 unknown candidates from 1,999 historical DUFs. These families are candidates for investigation, not curated mechanism records.</p>
    <p class="prov"><!--FLEET_STATS:DUFMech--></p>
    <div class="vocab"><span>Pfam</span><span>InterPro</span></div>
    <div class="row"><a class="primary" href="https://github.com/CultureBotAI/DUFMech">Explore repository</a><a href="https://github.com/CultureBotAI/DUFMech/blob/90c74d5806ead534cd437fa6ae70c9102d5bc7d3/data/worklists/interpro-pfam-duf-2026-10-01.manifest.json">Seed snapshot</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:DUFMech--></div>
  </article>
  <article class="mech-card" data-mech="NaturalProductMech" style="--c: var(--mech-naturalproductmech); --ci: var(--mech-naturalproductmech-ink)">
    <header><h3>NaturalProductMech</h3><span class="scale">Natural products</span></header>
    <p class="tag">One record per natural product structure: who makes it, from which gene cluster, what it does, and the evidence for all three.</p>
    <div class="num"><b>3,115</b><span>natural product structures · 9 sources</span></div>
    <p class="prov"><!--FLEET_STATS:NaturalProductMech--></p>
    <div class="vocab"><span>MIBiG</span><span>NCBITaxon</span><span>ChEBI</span><span>NPAtlas</span><span>PubChem</span><span>UniProt</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/NaturalProductMech/">Browse</a><a href="https://github.com/CultureBotAI/NaturalProductMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:NaturalProductMech--></div>
  </article>
  <article class="mech-card" data-mech="AntibioticMech" style="--c: var(--mech-antibioticmech); --ci: var(--mech-antibioticmech-ink)">
    <header><h3>AntibioticMech</h3><span class="scale">Antibiotics</span></header>
    <p class="tag">One record per antimicrobial chemical structure, harmonizing ChEBI and CARD with targets, mode of action, resistance and evidence.</p>
    <div class="num"><b>2,939</b><span>antimicrobial structures · 2,669 grounded</span></div>
    <p class="prov"><!--FLEET_STATS:AntibioticMech--></p>
    <div class="vocab"><span>ChEBI</span><span>ARO</span><span>CAS</span><span>PubChem</span><span>DrugBank</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="https://culturebotai.github.io/AntibioticMech/">Browse</a><a href="https://github.com/CultureBotAI/AntibioticMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:AntibioticMech--></div>
  </article>
  <article class="mech-card" data-mech="MediaIngredientMech" style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink)">
    <header><h3>MediaIngredientMech</h3><span class="scale">Ingredients</span></header>
    <p class="tag">LLM-assisted curation of media-ingredient ontology mappings with full audit trails; owns ingredient identity for the fleet.</p>
    <div class="num"><b>2,953</b><span>ingredient records · 2,611 mapped</span></div>
    <p class="prov"><!--FLEET_STATS:MediaIngredientMech--></p>
    <div class="vocab"><span>ChEBI</span><span>CAS</span><span>NCIT</span><span>FOODON</span><span>ENVO</span><span>MeSH</span></div>
    <div class="row"><a class="primary" href="/mediaingredientmech/">Page</a><a href="https://culturebotai.github.io/MediaIngredientMech/">Browse</a><a href="https://github.com/CultureBotAI/MediaIngredientMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:MediaIngredientMech--></div>
  </article>
  <article class="mech-card" data-mech="CultureMech" style="--c: var(--mech-culturemech); --ci: var(--mech-culturemech-ink)">
    <header><h3>CultureMech</h3><span class="scale">Media</span></header>
    <p class="tag">Autonomous knowledge factory curating versioned, ontology-grounded culture-media recipes from MediaDive, TogoMedium, KOMODO and the major collections.</p>
    <div class="num"><b>6,288</b><span>canonical media · 5 categories</span></div>
    <p class="prov"><!--FLEET_STATS:CultureMech--></p>
    <div class="vocab"><span>ChEBI</span><span>KEGG</span><span>FOODON</span><span>UBERON</span><span>CAS</span><span>NCBITaxon</span></div>
    <div class="row"><a class="primary" href="/culturemech/">Page</a><a href="https://culturebotai.github.io/CultureMech/">Browse</a><a href="https://github.com/CultureBotAI/CultureMech">GitHub</a><a href="#fleet-graph" data-show>Show in graph</a><!--FLEET_BADGE:CultureMech--></div>
  </article>
</div>

## Explore the current sites

Alongside record browsing, the Mechs publish complementary ways to explore their data:

- **Pathway mechanisms:** browse [PathwayMech's 152 pathways](https://culturebotai.github.io/PathwayMech/pages/browse.html), their participants, reactions and cited evidence. The repository also provides [KGX nodes and edges](https://github.com/CultureBotAI/PathwayMech/tree/3dc787604a53c15982af761ef537ab2b39863cd9/output/kgx) and [SSSOM source mappings](https://github.com/CultureBotAI/PathwayMech/blob/3dc787604a53c15982af761ef537ab2b39863cd9/output/sssom/source_mappings.sssom.tsv).
- **Unknown protein families:** explore [DUFMech's InterPro/Pfam worklist](https://github.com/CultureBotAI/DUFMech/blob/90c74d5806ead534cd437fa6ae70c9102d5bc7d3/data/worklists/interpro-pfam-duf-2026-10-01.tsv). Its family identifiers connect the worklist to the other Mechs through the shared-vocabulary graph and heatmap.
- **Taxa and strains:** TaxonMech lists the [20,648 taxa with a type strain](https://culturebotai.github.io/TaxonMech/pages/type-strains.html), each naming the BacDive deposit that LPSN records as the type. Taxon pages carry strain-level NCBI, GTDB, BV-BRC/PATRIC, IMG and AllTheBacteria genome identifiers, plus StrainInfo references and their evidence. The [source catalogue](https://culturebotai.github.io/TaxonMech/pages/sources.html) describes provenance.
- **Community, trait, cell structure and media similarity:** explore [CommunityMech](https://culturebotai.github.io/CommunityMech/community_umap.html), [TraitMech](https://culturebotai.github.io/TraitMech/pages/umap.html), [cell structures](https://culturebotai.github.io/CellStructureMech/pages/embedding-map.html), [ingredients](https://culturebotai.github.io/MediaIngredientMech/ingredient_umap.html) and [culture media](https://culturebotai.github.io/CultureMech/app/umap.html) through their embedding browsers.
- **Protein traits, proteins and sequences:** ProteinTraitsMech provides a [text-embedding corpus map](https://culturebotai.github.io/proteintraitsmech/map.html), a [map of 68,657 Swiss-Prot proteins by their traits](https://culturebotai.github.io/proteintraitsmech/map.html#proteins), and an [ESM-2 sequence map](https://culturebotai.github.io/proteintraitsmech/map.html#sequences) of canonical-example proteins.
- **Chemical structures:** compare compounds in the [AntibioticMech chemical map](https://culturebotai.github.io/AntibioticMech/pages/chemical-map.html) and the [NaturalProductMech structure map](https://culturebotai.github.io/NaturalProductMech/pages/chemical-map.html). Both Mechs also offer a corpus map that places compounds by their record text rather than their structure: [AntibioticMech](https://culturebotai.github.io/AntibioticMech/pages/map.html) and [NaturalProductMech](https://culturebotai.github.io/NaturalProductMech/pages/map.html).
- **Habitat meaning:** HabitatMech offers a [semantic text map](https://culturebotai.github.io/HabitatMech/pages/text-map/) alongside its ontology-grounded record browser.


## How the Mechs reference each other

Beyond shared vocabulary, Mechs name one another directly, in record fields, in schema slots, and in the curation practices they adopt from each other. Arrows point at the Mech that consumes, or at the one a scope decision defers to. Taxa tie TaxonMech to much of the fleet through shared NCBI Taxonomy identifiers, while DUFMech connects to ProteinTraitsMech records through shared Pfam and InterPro families. Those links appear as chords in the graph's shared-vocabulary layer. Direct-reference arrows require a committed record, schema or curation practice naming the other Mech.

<div class="fleet-xrefs">
  <div style="--c: var(--mech-taxonmech); --ci: var(--mech-taxonmech-ink); --ci2: var(--mech-pathwaymech-ink)"><div class="pair"><b>TaxonMech</b><i>→</i><b class="to">PathwayMech</b></div><div>PathwayMech's optional CurationEvent has the same shape as TaxonMech's; no pathway record carries curation history at this pin.<small>Schema · <a href="https://github.com/CultureBotAI/PathwayMech/blob/3dc787604a53c15982af761ef537ab2b39863cd9/src/pathwaymech/schema/pathwaymech.yaml#L84">PathwayMech curation_history description</a></small></div></div>

  <div style="--c: var(--mech-habitatmech); --ci: var(--mech-habitatmech-ink); --ci2: var(--mech-taxonmech-ink)"><div class="pair"><b>HabitatMech</b><i>→</i><b class="to">TaxonMech</b></div><div>TaxonMech's causal-graph node types are the same 16 as HabitatMech's. A habitat node may be a HabitatMech or ENVO term, the schema declares the <code>habitatmech:</code> prefix, and TaxonMech's curation-event helper and closed-schema write gate are ported from HabitatMech's and CellStructureMech's; no TaxonMech record has a causal graph yet.<small>Schema · TaxonMech schema CausalNodeTypeEnum and prefixes; src/taxonmech/curate/curation_event.py, src/taxonmech/validation/write_validated.py</small></div></div>
  <div style="--c: var(--mech-habitatmech); --ci: var(--mech-habitatmech-ink); --ci2: var(--mech-cellstructuremech-ink)"><div class="pair"><b>HabitatMech</b><i>→</i><b class="to">CellStructureMech</b></div><div>CellStructureMech's curation-event helper and closed-schema write gate are ported from HabitatMech's modules of the same names, which HabitatMech had itself ported from TraitMech. 17 of CellStructureMech's writer scripts use both.<small>Practice · CellStructureMech src/cellstructuremech/curate/curation_event.py; validation/write_validated.py</small></div></div>
  <div style="--c: var(--mech-habitatmech); --ci: var(--mech-habitatmech-ink); --ci2: var(--mech-antibioticmech-ink)"><div class="pair"><b>HabitatMech</b><i>→</i><b class="to">AntibioticMech</b></div><div>AntibioticMech's static-site generator is ported from HabitatMech's <code>render_pages.py</code>, including its paged category pages that filter through a JSON index, and its stylesheet is ported from HabitatMech's. Together they render AntibioticMech's whole browser. Its curation-event helper and closed-schema write gate are HabitatMech's copies as well; their docstrings still credit TraitMech, which HabitatMech ported them from.<small>Practice · AntibioticMech scripts/render_pages.py; src/antibioticmech/templates/style.css; src/antibioticmech/curate/curation_event.py</small></div></div>
  <div style="--c: var(--mech-communitymech); --ci: var(--mech-communitymech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>CommunityMech</b><i>→</i><b class="to">TraitMech</b></div><div>TraitMech's Edison deep-research runner and skill are ports of CommunityMech's <code>research_community_edison.py</code> and deep-research-community skill. Its METPO proposal skill takes CommunityMech's v1 proposal cohort as the worked example to follow, and keeps TraitMech's placeholder ID blocks clear of that cohort's.<small>Practice · TraitMech scripts/research_trait_edison.py; .claude/skills/deep-research-trait and metpo-proposal</small></div></div>
  <div style="--c: var(--mech-communitymech); --ci: var(--mech-communitymech-ink); --ci2: var(--mech-mediaingredientmech-ink)"><div class="pair"><b>CommunityMech</b><i>→</i><b class="to">MediaIngredientMech</b></div><div>MediaIngredientMech imported 17 growth-media ingredient names that CommunityMech could not match to an existing ingredient. Each record keeps the name as a synonym from <code>communitymech-unmapped</code> and cites its CommunityMech source id (<code>communitymech.ingredient:name</code>). 10 records are still live; the other 7 were merged into existing records.<small>Record data · MIM data/ingredients (synonym source communitymech-unmapped)</small></div></div>
  <div style="--c: var(--mech-communitymech); --ci: var(--mech-communitymech-ink); --ci2: var(--mech-culturemech-ink)"><div class="pair"><b>CommunityMech</b><i>→</i><b class="to">CultureMech</b></div><div>CultureMech turned CommunityMech growth media into recipes that keep their CommunityMech ids as provenance. It also backfilled recipe source environments from the ENVO terms of CommunityMech records that point at those recipes.<small>Record data · CultureMech scripts/import_from_communitymech.py, scripts/backfill_source_environment.py; schema SourceData.community_ids</small></div></div>
  <div style="--c: var(--mech-taxonmech); --ci: var(--mech-taxonmech-ink); --ci2: var(--mech-habitatmech-ink)"><div class="pair"><b>TaxonMech</b><i>→</i><b class="to">HabitatMech</b></div><div>TaxonMech's curation rules leave a taxon's habitats and its strains' isolation sources to HabitatMech. A TaxonMech record keeps only source attestation counts, and none of its records carries habitat data.<small>Practice · TaxonMech docs/CURATION.md (record-scope table, Strains); README Known limitations</small></div></div>
  <div style="--c: var(--mech-taxonmech); --ci: var(--mech-taxonmech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>TaxonMech</b><i>→</i><b class="to">TraitMech</b></div><div>TaxonMech's curation rules leave the traits and phenotypes of a taxon or strain to TraitMech, so they are never TaxonMech records. A TaxonMech record keeps only a count of the Madin and BactoTraits trait assertions about the taxon, never the trait values.<small>Practice · TaxonMech docs/CURATION.md record table; README Known limitations</small></div></div>
  <div style="--c: var(--mech-taxonmech); --ci: var(--mech-taxonmech-ink); --ci2: var(--mech-culturemech-ink)"><div class="pair"><b>TaxonMech</b><i>→</i><b class="to">CultureMech</b></div><div>TaxonMech's curation rules leave a taxon's growth media to CultureMech. A record keeps only a MediaDive count of the media linked to the taxon or to each strain, never the media themselves.<small>Practice · TaxonMech docs/CURATION.md</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-habitatmech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">HabitatMech</b></div><div>Habitat causal graphs reuse most of TraitMech's node types so the graphs stay comparable, and a trait node may be a TraitMech or METPO term (the 10 trait nodes in use are label-only so far). HabitatMech's deep-research runner deliberately follows TraitMech's conventions, and its curation-event and write-validation helpers are ported from TraitMech's.<small>Schema · HabitatMech schema CausalNodeTypeEnum; scripts/research_habitat.py</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-communitymech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">CommunityMech</b></div><div>CommunityMech's <code>/ground-or-propose-metpo</code> curation command is adapted from TraitMech's command of the same name, and treats community interaction graphs as the analog of TraitMech's causal graphs. Its strict validator, writer audit and curation-event helper also name TraitMech as a source, alongside CultureMech and MediaIngredientMech.<small>Practice · CommunityMech .claude/commands/ground-or-propose-metpo.md; scripts/validate_strict.py, scripts/audit_writers.py</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-taxonmech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">TaxonMech</b></div><div>TaxonMech's schema lets a trait node in a causal graph be a TraitMech or METPO term and declares the <code>traitmech:</code> prefix; no TaxonMech record has a causal graph yet.<small>Schema · TaxonMech schema CausalNodeTypeEnum and prefixes</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-cellstructuremech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">CellStructureMech</b></div><div>Structures list the phenotypes they confer as TraitMech or METPO trait ids, and a CI check tests each id and label against TraitMech's published trait index. The causal-graph node types are TraitMech's plus STRUCTURE.<small>Record data · CellStructureMech scripts/check_trait_links.py + schema associated_traits</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-proteintraitsmech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">ProteinTraitsMech</b></div><div>ProteinTraitsMech keeps a reviewed snapshot of TraitMech's TraitCategoryEnum. A CI audit that also fetches TraitMech's live schema reports a notice, never a failure, when the snapshot goes stale or when UPPER or OTHER, the only tokens both vocabularies use, is described differently (UPPER currently is). Its fallback history-record scaffolder is adapted from TraitMech's <code>new_history_record.py</code>.<small>Schema · ProteinTraitsMech conf/traitmech_category_vocabulary.yaml; scripts/audit_cross_mech_categories.py; scripts/new_history_record.py</small></div></div>
  <div style="--c: var(--mech-traitmech); --ci: var(--mech-traitmech-ink); --ci2: var(--mech-mediaingredientmech-ink)"><div class="pair"><b>TraitMech</b><i>→</i><b class="to">MediaIngredientMech</b></div><div>TraitMech leaves chemicals to MediaIngredientMech: its METPO seeder skips the material-entity subtree, which its docs say belongs in MIM rather than TraitMech. MIM's <code>/ground-or-propose-ingredient</code> curation command is ported from TraitMech's <code>/ground-or-propose-metpo</code>, re-aimed at chemical identity instead of phenotype.<small>Practice · TraitMech docs/SCHEMA.md, README.md, scripts/seed_from_metpo.py; MIM .claude/commands/ground-or-propose-ingredient.md (MIM#92)</small></div></div>
  <div style="--c: var(--mech-cellstructuremech); --ci: var(--mech-cellstructuremech-ink); --ci2: var(--mech-taxonmech-ink)"><div class="pair"><b>CellStructureMech</b><i>→</i><b class="to">TaxonMech</b></div><div>TaxonMech's closed-schema write gate and its curation-history helper are ported from CellStructureMech's modules, which the code credits jointly to HabitatMech and CellStructureMech. Every TaxonMech record is written through them.<small>Practice · TaxonMech src/taxonmech/validation/write_validated.py; src/taxonmech/curate/curation_event.py</small></div></div>
  <div style="--c: var(--mech-cellstructuremech); --ci: var(--mech-cellstructuremech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>CellStructureMech</b><i>→</i><b class="to">TraitMech</b></div><div>CellStructureMech's scope rule leaves the phenotypes a structure confers, such as motile, flagellated or Gram-negative, to TraitMech. They are never CellStructureMech records, only <code>associated_traits</code> links to TraitMech or METPO terms.<small>Practice · CellStructureMech docs/CURATION.md (record-scope table); schema description</small></div></div>
  <div style="--c: var(--mech-cellstructuremech); --ci: var(--mech-cellstructuremech-ink); --ci2: var(--mech-proteintraitsmech-ink)"><div class="pair"><b>CellStructureMech</b><i>→</i><b class="to">ProteinTraitsMech</b></div><div>CellStructureMech's scope rule makes a single protein or protein family a component of a structure, never a record of its own: it grounds to InterPro, Pfam or UniProtKB and is left to ProteinTraitsMech. The schema also declares a <code>proteintraitsmech:</code> prefix, but no record uses it.<small>Practice · CellStructureMech docs/CURATION.md; schema components slot</small></div></div>
  <div style="--c: var(--mech-proteintraitsmech); --ci: var(--mech-proteintraitsmech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>ProteinTraitsMech</b><i>→</i><b class="to">TraitMech</b></div><div>TraitMech's <code>download.yaml</code> source catalogue follows the shape of ProteinTraitsMech's, and its <code>check_sources.py</code> validator is adapted from ProteinTraitsMech's. Unlike the original, it fails a source that records no licence.<small>Practice · TraitMech download.yaml; scripts/check_sources.py; justfile sources-check</small></div></div>
  <div style="--c: var(--mech-naturalproductmech); --ci: var(--mech-naturalproductmech-ink); --ci2: var(--mech-antibioticmech-ink)"><div class="pair"><b>NaturalProductMech</b><i>→</i><b class="to">AntibioticMech</b></div><div>NaturalProductMech leaves antimicrobial mechanism to AntibioticMech. For the 205 compounds that share a structure with an AntibioticMech record, it links to that record and does not copy its targets, resistance determinants or MIC data.<small>Practice · NaturalProductMech schema molecular_targets; CLAUDE.md; docs/HARMONIZATION.md</small></div></div>
  <div style="--c: var(--mech-antibioticmech); --ci: var(--mech-antibioticmech-ink); --ci2: var(--mech-cellstructuremech-ink)"><div class="pair"><b>AntibioticMech</b><i>→</i><b class="to">CellStructureMech</b></div><div>CellStructureMech's source-queue skill, which ranks the sources in its curation/source_queue.tsv, is adapted from AntibioticMech's skill and keeps its ranking rule and adoption gate. Its stylesheet contract test is ported from AntibioticMech's.<small>Practice · CellStructureMech .claude/skills/source-queue/SKILL.md; tests/test_stylesheet_contract.py</small></div></div>
  <div style="--c: var(--mech-antibioticmech); --ci: var(--mech-antibioticmech-ink); --ci2: var(--mech-naturalproductmech-ink)"><div class="pair"><b>AntibioticMech</b><i>→</i><b class="to">NaturalProductMech</b></div><div>NaturalProductMech pins AntibioticMech's structures in an InChIKey inventory. A natural product that shares an InChIKey with an AntibioticMech record links to it and takes its antimicrobial class, but not its targets or resistance data. NaturalProductMech also used AntibioticMech as its template: its source-queue, add-natural-product (from add-antibiotic), curate-yaml-record and review-open-issues skills, its curation-event helper and its closed-schema write gate are adapted from AntibioticMech's.<small>Record data · NaturalProductMech scripts/extract_antibioticmech.py; data/raw/antibioticmech_inchikeys.tsv; .claude/skills</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink); --ci2: var(--mech-habitatmech-ink)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">HabitatMech</b></div><div>HabitatMech's seeder checks the label claimed by each upstream kg-microbe isolation-source mapping and, following MediaIngredientMech's SSSOM Rule B4, accepts an exact ontology synonym as well as the canonical label. Per the code, the rule changes no current record.<small>Practice · HabitatMech src/habitatmech/seed.py verified_mapping_target; tests/test_seed_harmonization.py</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink); --ci2: var(--mech-communitymech-ink)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">CommunityMech</b></div><div>CommunityMech growth-media components cite MIM ingredients by id (<code>media_ingredient_mech_id</code>), but they use MIM's retired <code>MediaIngredientMech:NNNNNN</code> scheme, so the ids no longer resolve. Its environment-matching tools read MIM's ingredient records and SSSOM mappings. They join on the exactMatch CHEBI term, which is what MIM's CURIE standard recommends; MIM wrote that standard for CommunityMech (MIM#119).<small>Record data · CommunityMech schema GrowthMediaComponent, src/communitymech/cross_repo_environment.py; MIM docs/CURIE_STANDARD.md</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">TraitMech</b></div><div>TraitMech ported its write-time validation gate and curation-event helper from CultureMech by way of MediaIngredientMech's versions, and its composite qc target mirrors MIM's. Its FAPROTAX synonym script follows MIM's rule: correct the label and keep the raw string.<small>Practice · TraitMech src/traitmech/validation/write_validated.py; src/traitmech/curate/curation_event.py; justfile qc; scripts/add_faprotax_synonyms.py</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink); --ci2: var(--mech-proteintraitsmech-ink)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">ProteinTraitsMech</b></div><div>ProteinTraitsMech's trait-merge rules, where only an exact identity match is merged and a similar name is only flagged for review, are adapted from MediaIngredientMech's same-ChEBI merge rule. Its oaklib version-pin test is ported from MediaIngredientMech's test of the same name.<small>Practice · ProteinTraitsMech .claude/skills/merge-traits/SKILL.md (just analyze-merges); tests/test_oaklib_semsql_pin.py</small></div></div>
  <div style="--c: var(--mech-mediaingredientmech); --ci: var(--mech-mediaingredientmech-ink); --ci2: var(--mech-culturemech-ink)"><div class="pair"><b>MediaIngredientMech</b><i>→</i><b class="to">CultureMech</b></div><div>5,696 of CultureMech's 6,288 canonical media link ingredients to their curated MIM records through <code>mediaingredientmech_chebi_term</code>, about 70% of all ingredient rows, and older records keep legacy <code>MediaIngredientMech:NNNNNN</code> ids. CultureMech also resolves ingredient labels against a pinned copy of MIM's label index, types its role slots with MIM's vendored role enums and took over stock solutions from MIM's complex-media list, while MIM's schema leaves recipe bodies to CultureMech.<small>Record data · CultureMech schema mediaingredientmech_chebi_term, mim_roles.yaml; src/culturemech/ingredients/mim_label_index.py</small></div></div>
  <div style="--c: var(--mech-culturemech); --ci: var(--mech-culturemech-ink); --ci2: var(--mech-communitymech-ink)"><div class="pair"><b>CultureMech</b><i>→</i><b class="to">CommunityMech</b></div><div>Community records name the CultureMech medium they were grown in, or an environment-matched one, by <code>culturemech_id</code>, and CommunityMech's media linker copies CultureMech recipe components into them. CommunityMech also ported CultureMech's schema-validated writer and its Edison deep-research runner.<small>Record data · CommunityMech schema GrowthMedia/RelatedMedia culturemech_id; scripts/link_growth_media.py; src/communitymech/validation/write_validated.py</small></div></div>
  <div style="--c: var(--mech-culturemech); --ci: var(--mech-culturemech-ink); --ci2: var(--mech-traitmech-ink)"><div class="pair"><b>CultureMech</b><i>→</i><b class="to">TraitMech</b></div><div>TraitMech's curation-history helper and its schema-validated YAML writer are ports of CultureMech's, by way of MediaIngredientMech's versions, and nearly every TraitMech write script goes through them. TraitMech's qc recipe also mirrors CultureMech's.<small>Practice · TraitMech src/traitmech/curate/curation_event.py; src/traitmech/validation/write_validated.py</small></div></div>
  <div style="--c: var(--mech-culturemech); --ci: var(--mech-culturemech-ink); --ci2: var(--mech-mediaingredientmech-ink)"><div class="pair"><b>CultureMech</b><i>→</i><b class="to">MediaIngredientMech</b></div><div>MIM reads CultureMech's ingredient-occurrence table to set each record's occurrence counts, to publish a recipe-membership edge list keyed on <code>CultureMech:NNNNNN</code> ids, and to turn labels it cannot resolve into new records and synonyms. CultureMech leaves questions about an ingredient's chemical form to MIM, and MIM's validated record writer and curation-event helper are ported from CultureMech.<small>Record data · MIM mappings/culturemech_recipe_membership.tsv, scripts/refresh_occurrence_statistics.py; CultureMech docs/DATA_LAYERS.md</small></div></div>
</div>

## Orchestration: culturebotai-claw

[culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw) is the fleet's coordinator. It does not hold science of its own; it holds the definition of the fleet, the artifacts every Mech must share byte-for-byte, and tooling for cross-repository curation and validation.

<div class="fleet-orch">
  <div><h4>Fleet manifest</h4><p><code>fleet.yaml</code> is the single source of truth for which repositories form the fleet. The manifest declares <!--FLEET_MANIFEST_COUNT_WORD--> of the <!--FLEET_COUNT_WORD--> projects shown here, including PathwayMech. DUFMech is listed here and is not yet declared in the manifest. Every member declares every capability exactly once as enabled, disabled or not applicable, and every disabled or not-applicable entry gives a reason, so nothing is silently off.</p></div>
  <div><h4>Vendored governance</h4><p>Shared LinkML modules (<code>mech_shared.yaml</code>, <code>history.yaml</code>), validators and behavioral contracts live in claw and are vendored into its declared members byte-identically, pinned to one immutable claw commit and checked in CI. The canonical registry defines <!--FLEET_ARTIFACT_COUNT--> artifacts, with each member receiving the contracts that apply to it.</p></div>
  <div><h4>Pipelines and skills</h4><p>CLAW provides pipeline discovery, repository checks, shared curation tools and validated dry runs. Agent and pipeline execution through <code>openclaw-cli</code> is not implemented; environment-curation and unified ingredient-mapping apply modes are disabled pending transactional writers. Deep-research tooling supports provider triage and dry-run result capture; provider execution is not implemented.</p></div>
</div>

The <a href="https://github.com/CultureBotAI/culturebotai-claw#current-support-status">current support matrix</a> distinguishes supported tools from planned execution. The autonomous knowledge factory label describes each Mech's curation model with human oversight; it does not imply that every CLAW workflow runs unattended.

Which fleet contracts each Mech has adopted, from the manifest. Every disabled entry records a reason, such as no download.yaml or no source queue yet. DUFMech is included with undeclared capabilities because it is not yet a manifest member:

<div class="fleet-caps-wrap" tabindex="0" role="region" aria-label="Fleet capability adoption, one column per capability">
<table class="fleet-caps">
  <thead><!--FLEET_CAPABILITY_HEAD--></thead>
  <tbody>
<!--FLEET_CAPABILITIES-->
  </tbody>
</table>
</div>
<div class="fleet-caps-key"><span><i class="e"></i>enabled</span><span><i class="d"></i>disabled, with a recorded reason</span><span><i class="n"></i>not applicable to this corpus</span><span><i class="u"></i>not declared in CLAW</span></div>

## What makes a Mech

The established Mechs share curation conventions, with adoption recorded per capability in the table above. DUFMech currently provides a seed worklist; the record and schema conventions below describe the structured corpora. The fleet standard is documented in [CLAW's MECH_STANDARD.md](https://github.com/CultureBotAI/culturebotai-claw/blob/main/docs/guides/MECH_STANDARD.md):

<ul class="fleet-standard">
  <li><b>One YAML record per entity</b>A recipe, an ingredient, a community, a taxon, a trait, a pathway, a structure, a protein trait, a natural product, an antibiotic, a habitat. The file is the unit of curation, review and history.</li>
  <li><b>A LinkML schema per Mech</b>Records validate against the Mech's schema; shared modules such as <code>mech_shared.yaml</code> are vendored where applicable. PathwayMech defines its own closed record schema.</li>
  <li><b>Ontology-grounded identity</b>Records are keyed by a public CURIE (ChEBI, GO, METPO, ENVO, NCBITaxon) where one exists, otherwise by a local identifier whose form varies by Mech.</li>
  <li><b>The ID–label invariant</b>Where a record stores an identifier with its label, most Mechs check in CI that the pair still agrees with the source ontology.</li>
  <li><b>Evidence and provenance</b>Evidence cites its source, such as a publication (PMID or DOI), a database record or a web page, as each Mech's schema allows. Mechs that adopt the source-catalogue or source-queue contract record each source's licence before ingesting it.</li>
  <li><b>Causal mechanism graphs</b>Traits, pathways, protein traits, structures, natural products, antibiotics, habitats and taxa can carry directed, evidence-backed graphs of mechanism, and community records chain their ecological interactions into causal interaction graphs. Each of these Mechs defines its own node types; most share a core set, such as chemical, pathway and biological process. DUFMech's seed worklist supplies candidate families for evidence gathering.</li>
  <li><b>Append-only curation history</b>Mechs adopting the history contract record changes as append-only events, preserving provenance across agent and human curation.</li>
  <li><b>A static browser and an open licence</b>Established corpora publish GitHub Pages browsers; DUFMech currently links to its repository. The suite licensing policy is CC BY 4.0 for data and BSD-3-Clause for code. Redistributed source material retains its applicable terms.</li>
</ul>

## Related resources

- **[kg-microbe](/kg-microbe/)** - The central knowledge graph several Mechs draw from; MediaIngredientMech's ingredient mappings feed into it
- **[MicroGrowAgents](/microgrowagents/)** - Multi-agent media design built on kg-microbe
- **[Resources](/resources/#-ai-curation-tools)** - The full tool catalogue, including MicroMediaParam and the kg-microbe utilities
- **[METPO](https://github.com/berkeleybop/metpo)** - The Microbial Ecophysiological Trait and Phenotype Ontology that seeds TraitMech and grounds trait references across the fleet

## Bibliography

1. Santangelo BE, Hegde H, Caufield JH, Reese J, Kliegr T, Hunter LE, Lozupone CA, Mungall CJ, **Joachimiak MP**. KG-Microbe — Building Modular and Scalable Knowledge Graphs for Microbiome and Microbial Sciences. *GigaScience*. 2026;giag077. [doi:10.1093/gigascience/giag077](https://doi.org/10.1093/gigascience/giag077)
2. Naseem S, Miller MA, Martinez-Gomez NC, Sun N, **Joachimiak MP**. MicroGrowAgents: An Agentic AI System for Microbial Cultivation Engineering. *bioRxiv*. 2026. [doi:10.64898/2026.06.04.729985](https://doi.org/10.64898/2026.06.04.729985)
{: .bibliography}

See the [full bibliography](/publications/#bibliography) on the Publications page.
