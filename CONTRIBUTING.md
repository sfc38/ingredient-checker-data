# Contributing

Corrections and additions are welcome. Religious accuracy matters more than coverage — please err on the side of caution.

## Adding or correcting an entry

1. Edit `data/ingredients.json`.
2. Every `opinion` must have a real `source` and a real `ref` (page, section, or URL). No anonymous claims.
3. If you're adding an authoritative ruling, also add a row to the relevant file in `sources/` so the citation is reproducible.
4. Update `last_reviewed` on the entry.
5. Run validation (TBD).
6. Open a pull request.

## What we won't accept

- Rulings without a verifiable source.
- Personal opinions presented as rulings.
- Sweeping changes to many entries based on a single source. Aggregation, not replacement.

## Reporting a wrong ruling

If you find a ruling that contradicts a published authority, open an issue with:
- The ingredient ID (e.g. `en:e471`)
- The contradicting source (with a citation)
- A short explanation

## Out of scope

- Per-product certifications (this database is per-ingredient).
- Country-specific regulatory differences beyond the citation note.
