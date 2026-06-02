# Bootstrap pipeline

Produces `data/ingredients.json` by merging the hand-curated seed with public sources.

## Layout

```
data/
  seed.json          ← source of truth: hand-curated entries (28 today)
  ingredients.json   ← BUILD OUTPUT: seed + bootstrap. Do not edit by hand;
                       it is overwritten on every run.
scripts/
  bootstrap.py       ← the pipeline
  cache/             ← gitignored scratch (downloaded taxonomies, etc.)
```

To add hand-curated entries: edit `data/seed.json` and re-run.
To regenerate: `python3 scripts/bootstrap.py`.

## Sources currently implemented

| Stage | Source | Status |
|---|---|---|
| 1 | Open Food Facts ingredient taxonomy | **Done.** Pulls 6014 OFF entries with parent-tree inheritance of `vegan` / `vegetarian` flags. Generates ~4670 bootstrap entries. |
| 1 | WorldOfIslam E-number list | Not yet — needs verified URL. |
| 1 | GitHub `halal-checker` packages | Not yet — needs verified URLs. |
| 2 | Normalization to OFF canonical IDs | **Done.** OFF IDs are already canonical; bootstrap entries use them directly. |
| 3 | Conflict resolution | **Done.** Seed entries always win — bootstrap never overwrites a hand-curated entry. Confidence on bootstrap entries is always `low` since they come from a single community source. |
| 5 | Validate against schema | Manual via Python `json.load` in `bootstrap.py`. JSON Schema validation not yet automated. |

## Heuristic used for OFF-derived halal rulings

| OFF `vegan` | OFF `vegetarian` | Halal status | Note |
|---|---|---|---|
| `yes` | (any) | `allowed` | Plant-based |
| `no` | `yes` | `caution` | Dairy / egg — generally halal but verify |
| (any) | `no` | `caution` | Animal-derived — slaughter method matters |
| `maybe` or `maybe` | | `caution` | Source uncertain |
| nothing | nothing | (entry skipped) | No useful signal |

Parent-tree inheritance: if an entry doesn't set a flag itself, the script walks `parents` up to depth 6 and inherits the first flag it finds. OFF uses IS-A relationships (`en:wheat-flour` → `en:flour` → ...), so inheritance is sound.

## Output stats (current run)

```
Seed:      28 hand-curated entries (4 forbidden, 4 allowed, 20 caution)
Bootstrap: 4672 new entries from OFF
Total:     4700 ingredients

Distribution:
  allowed:   2991 (mostly plant-based)
  caution:   1705 (animal-derived, dairy, egg, uncertain)
  forbidden: 4    (pork, lard, ethanol, wine — all from seed)
```

## Conflict-resolution philosophy

Bootstrap entries are always tagged `confidence: low` because they derive from a single community source (Open Food Facts taxonomy). The authoritative-citation pass (task #7) upgrades the highest-impact entries to `medium` or `high` by adding opinions from JAKIM / IFANCA / MUI / HFA / HMC / MUIS.

When that pass adds opinions to entries that *already* have a seed entry, the conflict-resolution rules in the main `README.md` apply.

## Excluded sources

- **Kaggle datasets** — no per-entry citation, provenance not verifiable.

## How to add a new source

1. Add a fetcher (e.g. `bootstrap_worldofislam.py`) that produces `cache/<source>.json` keyed by OFF canonical id.
2. In `bootstrap.py`, after building the OFF-derived entries, merge in the new source's opinions. If an opinion conflicts with an existing one, apply the conflict-resolution rules in the main README.
3. Bump confidence per the rules in the main README.
