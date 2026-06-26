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

## Status
20 of a planned 70 recipes (Phase 0 starter set). Remaining coverage to add:
more chicken, beef/pork, fish, vegetarian, quick meals, breakfasts, and snacks.
