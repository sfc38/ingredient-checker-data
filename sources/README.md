# Sources

Human-extracted rulings from certification authorities, one Markdown file per source. These files are the input to the manual authoritative pass — each entry citation in `data/ingredients.json` should be traceable to a row here.

## Planned files

- `jakim.md` — Malaysia Department of Islamic Development published ingredient guidelines
- `ifanca.md` — Islamic Food and Nutrition Council of America reference materials
- `mui.md` — LPPOM MUI (Indonesia) halal standards
- `hfa.md` — Halal Food Authority (UK)
- `hmc.md` — Halal Monitoring Committee (UK)
- `muis.md` — Islamic Religious Council of Singapore guidelines

## Format

Each file follows the same structure:

```markdown
# Source Name

Source document: <URL or filename>
Last updated: YYYY-MM-DD

## Ingredient Name (E-number if applicable)
- Status: allowed | forbidden | caution
- Reasoning: <short quote or paraphrase from the source>
- Ref: <page number or section>
```

## Why this folder is in git

So that every ruling in `data/ingredients.json` can be traced back to a specific paragraph in a specific document. If a citation is later found to be wrong, we can correct it at the source and re-run the merge.
