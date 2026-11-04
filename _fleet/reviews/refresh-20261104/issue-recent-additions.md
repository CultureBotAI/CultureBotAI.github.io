The November 4 pre-PR diff review found that the dedicated CommunityMech and MediaIngredientMech pages retained old recent-addition lists after their repository links moved to the new pins. Their displayed short SHA labels also still named the old pins.

The rebuilt `_fleet/data/recent_terms.json` identifies five newer CommunityMech additions from October 31–November 1 and three newer MediaIngredientMech additions from November 1–2. The dedicated pages must repeat those same five-record lists. CultureMech's list remains unchanged at its unchanged pin.

Propagate the existing recent-terms output to all three dedicated pages, keeping the pipeline's history ordering and date semantics unchanged, and verify that each rendered section matches its source data and pin label.
