# Bootstrap pipeline

Scripts that produce `data/ingredients.json` by aggregating sources, normalizing names, and applying conflict-resolution rules.

## Planned scripts

| Script | Purpose |
|---|---|
| `bootstrap-github.ts` | Pull E-number tables from open-source `halal-checker` repos on GitHub |
| `bootstrap-worldofislam.ts` | Pull the WorldOfIslam E-number list |
| `bootstrap-off.ts` | Pull the Open Food Facts ingredient taxonomy (`vegan:yes/no/maybe` flags) |
| `normalize.ts` | Map every name to an Open Food Facts canonical ID (e.g. `en:e471`); deduplicate |
| `merge.ts` | Collect all opinions per ID; apply conflict-resolution rules to compute `effective_status` and `confidence` |
| `validate.ts` | Validate the output against `schema/ingredient.schema.json` |

## Conflict-resolution rules

| Source consensus | `effective_status` | `disputed` | Notes |
|---|---|---|---|
| All sources say `allowed` | `allowed` | false | |
| All sources say `forbidden` | `forbidden` | false | |
| All sources say `caution` | `caution` | false | |
| Mix of `allowed` and `caution` | `caution` | false | Safer call |
| Mix of `caution` and `forbidden` | `caution` | false | UI shows "may be forbidden" |
| Mix of `allowed` and `forbidden` | `caution` | **true** | UI shows full disagreement |
| Authority source disagrees with community | Authority wins | depends | Community shown as secondary |

## Confidence assignment

| Sources | Confidence |
|---|---|
| ≥2 authorities agree | `high` |
| 1 authority, or ≥2 community agree | `medium` |
| Community-only with disagreement | `low` |

## Excluded sources

- **Kaggle datasets** — no per-entry citation, provenance not verifiable.

## Source hierarchy (authority weight, descending)

1. JAKIM (Malaysia)
2. LPPOM MUI (Indonesia)
3. IFANCA (USA)
4. HFA (UK)
5. HMC (UK)
6. MUIS (Singapore)
7. Open Food Facts taxonomy (`vegan` / `vegetarian` flags)
8. WorldOfIslam community list
9. Open-source `halal-checker` packages on GitHub
