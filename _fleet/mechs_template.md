---
layout: default
title: "X-Mech Suite"
description: "Nine ontology-grounded microbial knowledge bases, from habitat to culture medium, orchestrated by culturebotai-claw and connected through shared ontology terms and direct cross-references"
permalink: /mechs/
---

# X-Mech Suite: nine knowledge bases, one standard

The X-Mech suite is a fleet of nine curated, ontology-grounded knowledge bases that together describe a microbe at every scale: the habitat it lives in, the community it belongs to, the traits it expresses, the structures and proteins that implement them, the compounds it makes, the antibiotics that act on it, and the ingredients and media it is grown in. Each Mech follows the same curation model, one validated YAML record per entity with evidence and provenance, and the fleet is coordinated by a single orchestrator, [culturebotai-claw](https://github.com/CultureBotAI/culturebotai-claw).

<!--FLEET_FRAGMENT-->

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

The Mechs are joinable because they ground records in the same public ontologies. The table counts identifier occurrences per vocabulary in each Mech's record corpus; darker cells mean more. Columns run from the most widely shared vocabulary to the least, so the left edge is the fleet's common ground and the right edge is what a single Mech needs alone. Click a Mech name to open it, a cell to list the records behind it, or a column heading to filter the graph to that vocabulary.

<div class="fleet-heat-wrap"><table class="fleet-heat" id="fleet-heat" aria-label="Ontology identifier occurrences per Mech"></table></div>
<div class="fleet-cell-panel" id="fleet-cell-panel" hidden></div>
<p class="fleet-heat-note">Counts are prefix occurrences in the canonical record directories (merged recipes for CultureMech, communities for CommunityMech, habitat records for HabitatMech) as of September 2026. Columns are ordered by how many Mechs ground anything in each vocabulary, then by the total records citing it across the fleet; PMID and DOI sit at the right because every Mech cites literature. ChEBI binds the chemistry arm (media, ingredients, antibiotics, proteins); NCBITaxon and ENVO bind the organism arm (habitat, community, traits); GO and METPO bridge phenotype, structure and protein.</p>

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
    <tr><td>NaturalProductMech</td><td colspan="11"><i class="x">not yet a manifest member, so it declares no capabilities; it vendors the governed artifacts, pinned one revision behind the eight</i></td></tr>
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
