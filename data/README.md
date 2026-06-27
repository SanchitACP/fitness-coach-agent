# Data conventions

## `recipes.json`

Each recipe follows the schema in the product spec (Section 6). Two fields drive
the recipe filter's restriction logic, so the tag vocabulary must stay consistent:

- **`restrictions_contains`** — allergens / animal products actually present.
  The filter **hard-blocks** any recipe whose `restrictions_contains` intersects
  the user's restrictions (allergy safety, no flexibility). Tags in use:
  `meat` (poultry/beef/pork/turkey), `pork`, `fish`, `shellfish`, `gluten`,
  `dairy`, `eggs`, `soy`, `peanuts`, `tree_nuts`.

- **`restrictions_safe`** — positive diet labels the recipe satisfies:
  `vegetarian`, `vegan`, `gluten_free`, `dairy_free`. A `vegan` recipe is also
  `vegetarian` and `dairy_free`.

Diet filters map to `restrictions_contains` blocks: **vegetarian** excludes
`meat`/`fish`/`shellfish`; **vegan** additionally excludes `dairy`/`eggs`.

### Macros
`calories` is kept consistent with `protein_g*4 + carbs_g*4 + fat_g*9` (within a
few cal of rounding). `macro_source` currently reads *"Estimated; pending
spot-check"* — values are reasonable estimates and should be verified against
USDA FoodData Central / MyFitnessPal before submission (spot-check ~10).

## Filter requirements (Sprint 1b)
Two rules to honor when building `filter_recipes()`:

1. **Never silently violate a hard restriction.** Allergen/diet blocks
   (`restrictions_contains`) must never bend to fill a slot — better to return a
   partial plan with a clear message than to serve a vegan eggs.
2. **Graceful degradation.** If a (slot x diet x cuisine) pool can't meet the
   macro tolerance, widen the tolerance window and/or tell the user, rather than
   crashing or returning empty slots.

The recipe set is sized so the common diets clear these bars (see coverage
below), but narrow stacked constraints can still thin a pool.

## Status
70 recipes (full target). Coverage verified so no diet x meal-slot combination is
starved (the earlier gap: vegan had 0 breakfast/snack options). Available per
slot:

| diet | breakfast | lunch | dinner | snack |
|------|-----------|-------|--------|-------|
| (none) | 14 | 25 | 35 | 14 |
| gluten_free | 7 | 13 | 19 | 12 |
| vegetarian | 12 | 10 | 12 | 11 |
| vegan | 4 | 8 | 8 | 6 |

One recipe intentionally contains peanuts so the allergy-restriction test has
something to exclude. Macros remain estimated; spot-check ~10 vs USDA/MFP before
submission.
