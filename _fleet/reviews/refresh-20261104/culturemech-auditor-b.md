# CultureMech deployment recheck — 2026-11-04

Corpus pin `a74dd489720c9df96cc073ffd11568d407d3c06c` retained; served deployment `09f908802989670d2cc799f75f67cf56f7834178`.

- search: **present**. CultureMech:000252 returns one recipe and Halophilic medium returns four, with individual recipe links.
- facets: **present**. The category facet selects 14,332 bacterial recipes; combining it with Halophilic medium leaves two. Clear All restores all 15,915.
- result_counts: **present**. The live count distinguishes one identifier match, four label matches, two bacterial label matches and zero for an unmatched query.
- sorting: **missing**. The recipe browser has no reader-facing sort selector, sort button or sortable table. Its facet lists are internally ordered, which does not provide record sorting.
- shareable_state: **present**. Search and property filters restore from the URL: Halophilic medium with category=bacterial reloads with the same two recipes.
- full_catalogue: **partial**. The main browser covers 15,915 normalized recipes. The landing also counts 6,325 merged recipes, whose separate pages/index.html listing is outside the main browser navigation.
- suite_nav: **present**. Visible All Mech projects links connect the reviewed landing, browser, records and visualizations to the central suite directory.
- record_pages: **present**. Normalized and merged recipes have stable individual URLs; sampled normalized pages display composition, organisms and provenance.
- term_links: **partial**. Ingredient and organism terms have labels and resolver links, but mediadive.medium:1399 on recipe 000252 is shown as source link unavailable.
- evidence: **partial**. Sampled records link formal DOI references, but source URLs embedded in Notes remain plain text.
- review_status: **missing**. Sampled recipe pages do not state record curation or review status. The separate growth-evidence report does not provide a status for each recipe.
- curation_history: **present**. Recipe Provenance tables show timestamps, curators or scripts, actions and notes.
- source_link: **partial**. The source YAML path appears as plain text in sampled record footers rather than as a link to that file.
- domain_view: **present**. Text and chemically derived media maps and an ingredient map render interactive corpus views.
- cross_mech_links: **present**. Recipe 015438 links CommunityMech:000064 to the specific pinned Soybean_N_Fixation_sfSynCom.yaml record.
- corpus_stats: **present**. The landing shows 15,915 normalized recipes, 6,325 merged recipes and five populated categories.
- category_browse: **partial**. Categories are browser facets and headed sections on long indexes; the landing does not link separate category pages.
- downloads: **partial**. The landing links JSON and TSV indexes covering 15,915 normalized recipes, but these omit full compositions and record evidence; a complete bulk record export is not linked.
- schema_docs: **present**. The linked app/schema.html guide documents 51 classes and 34 enumerations, including MediaRecipe and growth-evidence structures.
- license: **partial**. The reviewed landing, schema and record footers identify BSD-3-Clause but do not consistently distinguish the project data license from the code license.
- build_provenance: **missing**. The reviewed landing, browser and recipe footers do not state a site build, deployment revision or dated corpus version; recipe curation dates describe individual events.
- theme_toggle: **partial**. Dark mode persists through the core browser, indexes, maps and records. The linked growth-evidence report has no toggle and does not adopt the saved choice.
- responsive: **partial**. Core reviewed pages and the normalized index fit 390px. The linked growth-evidence report still widens the document to 520px.
- load_failure: **present**. Blocking data.js shows Recipes could not be loaded and a retry control rather than a zero-record catalogue.
