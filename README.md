# ingredient-checker-data

Open, versioned database of food-ingredient rulings for dietary profiles — **halal first**, with the schema designed to extend to vegan, vegetarian, and kosher.

This repo powers the [IngredientCheck](https://github.com/) iOS app, which scans food barcodes and classifies each ingredient against the user's chosen dietary profile.

## Why this exists

Per-ingredient halal/vegan/kosher rulings are scattered across PDFs from certification bodies, community wikis, and ad-hoc lists embedded in app code. This repo aggregates them into a single machine-readable JSON, citing every source so users can see *who* says an ingredient is allowed or forbidden.

## How it's built

1. **Bootstrap (automated)** — community lists (WorldOfIslam, open-source `halal-checker` packages on GitHub) plus the Open Food Facts ingredient taxonomy (`vegan:yes/no/maybe` flags per ingredient).
2. **Authoritative pass (manual)** — rulings from certification authorities (JAKIM, LPPOM MUI, IFANCA, HFA, HMC, MUIS) are hand-extracted with citations.
3. **Conflict resolution** — when sources disagree, the effective status defaults to the safer call; *all* opinions are preserved so the UI can show disagreement.
4. **Confidence** — `high` when two or more authorities agree, `medium` for community-only, `low` for any unresolved conflict.

## Status values

The schema uses profile-agnostic statuses; each profile (halal / vegan / …) maps them to its own UI label.

| Status | Color | Halal label | Vegan label |
|---|---|---|---|
| `allowed` | green | Halal | Vegan |
| `forbidden` | red | Haram | Not vegan |
| `caution` | orange | Mushbooh | May not be vegan |
| `unknown` | gray | No data | No data |

## Layout

```
data/ingredients.json        # the published database
schema/ingredient.schema.json # JSON Schema for validation
scripts/                     # bootstrap + merge pipeline (TBD)
sources/                     # human-extracted authority rulings
```

## Disclaimer

Informational only. This database is an aggregation of public sources and is not a fatwa. For definitive rulings, consult a qualified scholar or your local certification body.
