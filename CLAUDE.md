# CLAUDE.md

Guidance for Claude Code and other agents working in this repository. It is
tracked, so changes to it go through a pull request like any other file (#173).
Before #173 this guidance lived in an untracked `CLAUDE.md` one directory above
the repository, where edits were never reviewed or shared; that file now only
points here.

## Repository overview

The CultureBotAI organization's GitHub Pages website, showcasing the kg-microbe
knowledge graph and the X-Mech suite of autonomous knowledge factories for
microbial cultivation research. The site is led by Dr. Marcin P. Joachimiak at
Lawrence Berkeley National Laboratory.

- Website: https://culturebotai.github.io
- This directory (`CultureBotAI.github.io/`) is the git repository root. All
  paths below are relative to it.

## Technology stack

- Static site generator: Jekyll on GitHub Pages, Minima theme, Kramdown.
- Deployment: GitHub Pages builds and serves `main`; merging to `main` deploys.
- Jekyll is not installed in most working copies, so rendering cannot be checked
  locally; the deployed page is the rendering evidence.

```bash
bundle install
bundle exec jekyll serve      # http://localhost:4000
bundle exec jekyll build
```

## Git workflow

Branch before the first edit, open a pull request for every change, review it
adversarially as a separate read-only pass, file each finding as an issue, and
merge only with the maintainer's go-ahead. Changes merged to `main` deploy.

## Site structure

### Content pages
- `index.md` - homepage with the kg-microbe overview
- `about.md` - PI and laboratory information
- `research.md` - research focus areas and projects
- `resources.md` - tools, databases and kg-microbe documentation
- `publications.md` - papers, preprints and presentations; the canonical numbered bibliography
- `kg-microbe.md` - the kg-microbe knowledge graph
- `marcin-joachimiak.md` - PI profile
- `culturemech.md` - CultureMech: 15,878 normalized culture-media recipes deduplicated into 6,288 canonical media
- `mediaingredientmech.md` - MediaIngredientMech: LLM-assisted ingredient curation and ontology mapping
- `communitymech.md` - CommunityMech: LinkML-based microbial community modelling
- `microgrowagents.md` - MicroGrowAgents, the multi-agent media-design system
- `mechs.md` - the X-Mech Suite hub page; generated, see below
- `IMPLEMENTATION_SUMMARY.md` - internal change log for the X-Mech page additions; listed in `exclude:` in `_config.yml`, so it is not deployed

### Configuration and templates
- `_config.yml` - site configuration, `header_pages` navigation order, plugins, `exclude:`
- `Gemfile` - Ruby dependencies
- `_layouts/default.html`, `_layouts/home.html`, `_layouts/page.html`, `_includes/head.html`, `_includes/footer.html` - Minima overrides; the site header comes from the Minima theme itself
- `assets/custom.css` - the site palette and styles (`--ink`, `--muted`, `--accent`, `--card` and the rest), which the fleet page also uses; the ten Mech identity colours (`--mech-<name>` and their `-ink` variants) are defined in `_fleet/fleet_fragment.html`

### Other
- `.github/workflows/fleet-page.yml` - the only CI; runs the tests and the fleet page checks, and the card check nightly
- `.claude/skills/` - `update-xmech-page` (the refresh procedure) and `review-open-issues` (backlog triage)
- `robots.txt`, `README.md`
- The organization profile README, which also enumerates the suite, lives in the
  separate `CultureBotAI/.github` repository (`profile/README.md`), not here.

## Architecture notes

### Content management
Content pages use Jekyll front matter with `layout`, `title`, `description` and
`permalink`. Navigation follows `header_pages` in `_config.yml`; the X-Mech pages
(culturemech, mediaingredientmech, communitymech) sit between `research.md` and
`resources.md` to follow the data flow from recipes to ingredients to communities.

### The X-Mech Suite page
The suite has ten Mechs, all under https://github.com/CultureBotAI, plus the
orchestrator `culturebotai-claw`. Three have pages here; the others have their own
GitHub Pages sites and are linked.

`mechs.md` (`/mechs/`) is **generated**. Edit its sources, never the page:
`_fleet/mechs_template.md` (prose, cards, the cross-reference list),
`_fleet/fleet_fragment.html` (the self-contained graph: `MECHS`, `XREFS`, `HUB`),
and the data in `_fleet/data/`, assembled by `scripts/fleet/assemble_page.py`.
The pipeline is `prefix_census.py` then `build_subsets.py`, `build_data.py`,
`mech_stats.py` and `assemble_page.py`; `_fleet/README.md` describes it, and
`.claude/skills/update-xmech-page/` is the refresh procedure. The record-subset
indexes the page fetches on demand are `assets/fleet/{edges,cells}/*.json`,
about 10.5 MB since TaxonMech joined the census.

Three sources, refreshed differently:
- **Fleet membership and capabilities:** the membership badges and the
  capability table come from a snapshot of culturebotai-claw's fleet manifest,
  `_fleet/data/manifest.json`, refreshed with
  `scripts/fleet/refresh_manifest.py --claw-root <claw checkout>`, separately
  from the census. Its tooltips quote claw's reasons verbatim.
- **Derived:** the census, overlaps, stats and stat strip, regenerated by the
  pipeline over snapshots of each Mech pinned at its GitHub `main`. The census, the subsets, the stats and `_fleet/data/site_audit.json`
  record the revisions they read, and tests fail if they disagree.
- **Hand-curated:** card figures, graph panels, the cross-reference arrows and the
  kg-microbe ties, checked claim by claim against each Mech's live site and its
  repository at the pin. `scripts/fleet/check_cards.py` compares the card figures
  with the live sites nightly.

Last refreshed on 2026-09-24 (#120). The corpora move fast: TraitMech went
477, 618, 694, 763 records and CellStructureMech 57, 338, 421, 542 over successive
runs, and both moved again during that run. The census covers all ten Mechs since
TaxonMech was added (#87). Taxa tie TaxonMech to the fleet through shared NCBI
Taxonomy identifiers, drawn as vocabulary chords; the arrows are direct
references only, and `_fleet/README.md` states what counts as one.

### The ten Mechs
- **CultureMech** (`/culturemech/`) - versioned, ontology-grounded culture-media recipes from MediaDive, TogoMedium, KOMODO and the major collections.
- **MediaIngredientMech** (`/mediaingredientmech/`) - LLM-assisted curation of media-ingredient mappings; its records map mostly to ChEBI, then MeSH, NCIT, MicrO, FOODON and ENVO. Where no ontology term exists, about 175 mapped ingredients carry kg-microbe registry ids, mostly for preparations and mixtures, and about 85 carry CAS Registry Numbers; about 55 more carry kg-microbe placeholder ids pending curation. None map to PubChem or METPO (#150, #186).
- **CommunityMech** (`/communitymech/`) - microbial communities, their interactions and cultivation conditions, in LinkML.
- **TraitMech** (https://culturebotai.github.io/TraitMech/) - microbial ecophysiological traits seeded from METPO.
- **ProteinTraitsMech** (https://culturebotai.github.io/proteintraitsmech/) - protein sequence, structure and function trait classes.
- **AntibioticMech** (https://culturebotai.github.io/AntibioticMech/) - one record per antimicrobial structure, harmonizing ChEBI and CARD/ARO; record content is CC BY 4.0.
- **CellStructureMech** (https://culturebotai.github.io/CellStructureMech/) - microbial cell structures, between the trait and protein layers.
- **HabitatMech** (https://culturebotai.github.io/HabitatMech/) - habitats harmonized from GOLD, BacDive, PREGO and Madin et al. into ontology-grounded records (ENVO, UBERON, FOODON, BTO).
- **NaturalProductMech** (https://culturebotai.github.io/NaturalProductMech/) - one record per natural product structure with producer, gene cluster and bioactivity; grounded in ChEBI, MIBiG and NCBI Taxonomy. NPAtlas is a cross-reference target only: its CC BY-NC licence (from release 2024_09) bars ingestion into a CC BY 4.0 corpus.
- **TaxonMech** (https://culturebotai.github.io/TaxonMech/) - taxa and strains at species level and below, resolving NCBI Taxonomy, GTDB, LPSN and BacDive onto one NCBI-grounded identity.

Wherever the suite is enumerated (index.md, resources.md, each page's Related
Tools), list all ten and link to `/mechs/`. Name ontologies consistently across
pages (ChEBI, NCBITaxon, METPO, ENVO and so on), and describe a Mech's groundings
by what its records actually use, checked at its pinned revision.

Several Mech site roots are client-side meta-refresh shells that return 200, and
`curl -L` does not follow them; read the `pages/` or `app/` URL.

### MicroGrowAgents
`microgrowagents.md` documents the multi-agent media-design system. Its repository
is private; its preprint is Naseem et al. (2026) bioRxiv,
https://doi.org/10.64898/2026.06.04.729985.

### Heading anchors (gotcha)
Headings that start with an emoji render with a leading hyphen in their id:
`## 🤖 AI Curation Tools` becomes `id="-ai-curation-tools"`, so in-page links are
written `#-ai-curation-tools`. That is what GitHub Pages emits; verify against the
deployed HTML rather than a local kramdown, which strips the emoji instead:

```bash
curl -s https://culturebotai.github.io/resources/ | grep -oE '<h2[^>]*id="[^"]*"'
```

Headings without an emoji behave normally (`## Bibliography` becomes `#bibliography`).

### Bibliography sections
Every content page ends with a `## Bibliography` section listing its references
and linking to `/publications/#bibliography`. Lists carry the kramdown class
`{: .bibliography}`, styled in `assets/custom.css`. Verify citation metadata
against Crossref, Europe PMC, the bioRxiv API or DOE CODE before adding an entry,
and for preprints check which version matches the title and author list.

### SEO and metadata
`jekyll-seo-tag` generates the metadata from `_config.yml`, overridden per page in
front matter.

## Content guidelines

### kg-microbe
- A modular knowledge graph for microbial cultivation, and the site's primary focus.
- Repository: https://github.com/Knowledge-Graph-Hub/kg-microbe
- Publication: Santangelo et al. (2026) GigaScience, giag077, https://doi.org/10.1093/gigascience/giag077
- Licence: BSD-3-Clause

### METPO
- Microbial Ecophysiological Trait and Phenotype Ontology
- BioPortal: https://bioportal.bioontology.org/ontologies/METPO
- Repository: https://github.com/berkeleybop/metpo

### Principal investigator
- Dr. Marcin P. Joachimiak, Environmental Genomics and Systems Biology Division, LBNL
- Contact: mjoachimiak@lbl.gov
- Profile: https://biosciences.lbl.gov/profiles/marcin-p-joachimiak/

### Research focus
- Cultivation of isolated and novel organisms
- Culture optimization through data-driven approaches
- Growth preference prediction with ML and AI methods

## Dependencies
- `github-pages`, the meta-gem with GitHub Pages' Jekyll and plugins
- `jekyll-feed`, `jekyll-sitemap`, `jekyll-seo-tag`
- The fleet pipeline needs Python 3.12 and `scripts/fleet/requirements.txt`
