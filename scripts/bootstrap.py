#!/usr/bin/env python3
"""
bootstrap.py — Scale data/ingredients.json from public sources.

Sources used in this version:
  1. Open Food Facts ingredients taxonomy (primary signal).
     URL: https://static.openfoodfacts.org/data/taxonomies/ingredients.json
     Gives us: per-ingredient vegan / vegetarian flags, multi-language
     name synonyms, E-number identification, English description text.

  2. The existing hand-curated entries in data/ingredients.json.
     These ALWAYS WIN — they are never overwritten by bootstrap data.

Output:
  data/ingredients.json containing the union of:
    - All hand-curated entries (unchanged).
    - Bootstrap entries for every OFF ingredient with at least one
      of {vegan, vegetarian} set, that isn't already hand-curated.

Run from the repo root:
    python3 scripts/bootstrap.py
"""

from __future__ import annotations

import json
import re
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed.json"           # source of truth (hand-curated)
DATA = ROOT / "data" / "ingredients.json"    # build output (seed + bootstrap)
CACHE_DIR = ROOT / "scripts" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OFF_TAXONOMY_URL = "https://static.openfoodfacts.org/data/taxonomies/ingredients.json"
OFF_CACHE = CACHE_DIR / "off-ingredients.json"

CATEGORY_HINTS = {
    "additive": ["en:additive", "en:emulsifier", "en:stabiliser", "en:preservative",
                 "en:colour", "en:thickener", "en:antioxidant", "en:acidifier",
                 "en:sweetener", "en:flavour-enhancer", "en:flour-treatment-agent"],
    "meat":     ["en:meat", "en:poultry"],
    "fish":     ["en:fish", "en:seafood"],
    "dairy":    ["en:milk", "en:dairy", "en:cheese", "en:yogurt"],
    "egg":      ["en:egg"],
    "alcohol":  ["en:alcohol", "en:wine", "en:beer", "en:spirit"],
    "plant":    ["en:vegetable", "en:fruit", "en:nut", "en:legume", "en:cereal",
                 "en:plant", "en:herb", "en:spice", "en:seed"],
    "mineral":  ["en:mineral", "en:water", "en:salt"],
    "insect":   ["en:insect"],
}


def fetch_off_taxonomy(force: bool = False) -> dict:
    if OFF_CACHE.exists() and not force:
        print(f"  Using cached taxonomy at {OFF_CACHE}")
        return json.loads(OFF_CACHE.read_text(encoding="utf-8"))
    print(f"  Downloading from {OFF_TAXONOMY_URL} ...")
    with urllib.request.urlopen(OFF_TAXONOMY_URL, timeout=30) as resp:
        data = resp.read()
    OFF_CACHE.write_bytes(data)
    size_mb = len(data) / 1024 / 1024
    print(f"  Cached at {OFF_CACHE} ({size_mb:.1f} MB)")
    return json.loads(data)


def get_lang_value(field_value, prefer: tuple[str, ...] = ("en",)) -> str | None:
    """OFF stores per-language values as { lang: value }. Pull preferred lang."""
    if not isinstance(field_value, dict):
        return field_value if isinstance(field_value, str) else None
    for lang in prefer:
        v = field_value.get(lang)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # Fallback to any present value
    for v in field_value.values():
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


NAME_LANG_ORDER = (
    "en", "xx",
    "de", "fr", "es", "it", "pt", "nl",
    "tr", "ar", "id", "ms",
)


def collect_names(entry: dict) -> list[str]:
    """All ingredient names across all languages from name + synonyms fields.
    English and a handful of major languages come first; other languages
    follow in whatever order OFF supplies them."""
    names: list[str] = []

    def add_field(field_value):
        if not isinstance(field_value, dict):
            return
        emitted_langs: set[str] = set()
        for lang in NAME_LANG_ORDER:
            v = field_value.get(lang)
            if isinstance(v, str):
                names.append(v); emitted_langs.add(lang)
            elif isinstance(v, list):
                names.extend(x for x in v if isinstance(x, str))
                emitted_langs.add(lang)
        for lang, v in field_value.items():
            if lang in emitted_langs:
                continue
            if isinstance(v, str):
                names.append(v)
            elif isinstance(v, list):
                names.extend(x for x in v if isinstance(x, str))

    add_field(entry.get("name"))
    add_field(entry.get("synonyms"))

    seen: set[str] = set()
    deduped: list[str] = []
    for n in names:
        normalized = n.strip()
        if normalized and normalized.lower() not in seen:
            seen.add(normalized.lower())
            deduped.append(normalized)
    return deduped


def get_flag(entry: dict, field: str) -> str | None:
    """Return 'yes' | 'no' | 'maybe' | None for the entry's own flag."""
    raw = get_lang_value(entry.get(field), prefer=("en", "xx"))
    if raw in ("yes", "no", "maybe"):
        return raw
    return None


def get_inherited_flag(off_id: str, off: dict, field: str,
                       depth: int = 0, max_depth: int = 6,
                       visited: set | None = None) -> str | None:
    """Walk OFF's parent tree if the entry itself doesn't set the flag.
    OFF uses IS-A parent relationships, so inheriting vegan/vegetarian
    is sound (e.g. en:wheat-flour inherits from en:flour)."""
    if depth >= max_depth:
        return None
    if visited is None:
        visited = set()
    if off_id in visited:
        return None
    visited.add(off_id)
    entry = off.get(off_id)
    if not isinstance(entry, dict):
        return None
    own = get_flag(entry, field)
    if own is not None:
        return own
    parents = entry.get("parents") or []
    if not isinstance(parents, list):
        return None
    for p in parents:
        if isinstance(p, str):
            inherited = get_inherited_flag(p, off, field, depth + 1, max_depth, visited)
            if inherited is not None:
                return inherited
    return None


def clean_definition(raw: str | None, names: list[str]) -> str | None:
    """OFF descriptions often start with the ALL-CAPS name followed by
    a dash and the E-number; clean that off to leave a readable sentence."""
    if not raw:
        return None
    text = raw.strip()
    # Strip leading ALL-CAPS NAME ... -E###- refers to / is
    text = re.sub(
        r"^[A-Z0-9][A-Z0-9\s,\-\(\)]+(?:-E\d+-)?\s*(?:refers to|is|describes)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = text.strip()
    if not text:
        return None
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    # Skip if the cleaned text is shorter than 10 chars (junk)
    if len(text) < 10:
        return None
    return text


def derive_category(entry_id: str, entry: dict) -> str:
    if entry_id.startswith("en:e") and len(entry_id) > 4 and entry_id[4].isdigit():
        return "additive"
    parents = entry.get("parents") or []
    if not isinstance(parents, list):
        parents = []
    parent_set = set(p for p in parents if isinstance(p, str))
    classes_raw = get_lang_value(entry.get("additives_classes")) or ""
    classes = [c.strip() for c in classes_raw.split(",") if c.strip()]
    hint_set = parent_set | set(classes)
    for category, keywords in CATEGORY_HINTS.items():
        if any(kw in hint_set for kw in keywords):
            return category
    return "other"


def extract_e_number(entry_id: str, entry: dict) -> str | None:
    e = get_lang_value(entry.get("e_number"))
    if isinstance(e, str) and e.strip():
        e = e.strip()
        if e.upper().startswith("E"):
            return e.upper()
        return f"E{e}"
    if entry_id.startswith("en:e") and len(entry_id) > 4 and entry_id[4].isdigit():
        return entry_id[3:].upper()
    return None


def heuristic_halal_ruling(vegan: str | None, vegetarian: str | None) -> dict | None:
    if vegan == "yes":
        return {
            "effective_status": "allowed",
            "explanation": (
                "Open Food Facts classifies this ingredient as plant-based "
                "(vegan: yes). Plant-based ingredients are generally considered "
                "halal. This automated classification does not detect alcohol-"
                "derived ingredients — when in doubt, verify with the manufacturer."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "allowed",
                "note": "vegan: yes",
            }],
        }
    if vegetarian == "no":
        return {
            "effective_status": "caution",
            "explanation": (
                "Open Food Facts classifies this ingredient as animal-derived "
                "(vegetarian: no). Halal status depends on the source animal "
                "and slaughter method; verify with the manufacturer."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "caution",
                "note": "vegetarian: no",
            }],
        }
    if vegan == "no" and vegetarian == "yes":
        return {
            "effective_status": "caution",
            "explanation": (
                "Open Food Facts classifies this ingredient as non-vegan but "
                "vegetarian (vegan: no, vegetarian: yes) — typically dairy- "
                "or egg-derived. Generally halal, but verification with the "
                "manufacturer is recommended for products with mixed sources."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "caution",
                "note": "vegan: no (dairy or egg)",
            }],
        }
    if vegan == "maybe" or vegetarian == "maybe":
        return {
            "effective_status": "caution",
            "explanation": (
                "Open Food Facts is uncertain about the source of this "
                "ingredient. It may be plant- or animal-derived depending on "
                "the manufacturer. Verify with the manufacturer or a "
                "certification body."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "caution",
                "note": "source uncertain",
            }],
        }
    return None


def build_bootstrap_entry(off_id: str, entry: dict, off: dict) -> dict | None:
    vegan = get_inherited_flag(off_id, off, "vegan")
    vegetarian = get_inherited_flag(off_id, off, "vegetarian")
    ruling = heuristic_halal_ruling(vegan, vegetarian)
    if ruling is None:
        return None

    names = collect_names(entry)
    if not names:
        # Generate a placeholder name from the id
        slug = off_id.split(":", 1)[-1]
        names = [slug.replace("-", " ").capitalize()]

    raw_desc = get_lang_value(entry.get("description"))
    definition = clean_definition(raw_desc, names)

    result = {
        "id": off_id,
        "names": names,
        "e_number": extract_e_number(off_id, entry),
        "category": derive_category(off_id, entry),
    }
    if definition:
        result["definition"] = definition
    result["rulings"] = {"halal": ruling}
    result["last_reviewed"] = str(date.today())
    return result


def main() -> None:
    print(f"Loading seed (hand-curated entries) from {SEED.name} ...")
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    seed_ids = {i["id"] for i in seed["ingredients"]}
    print(f"  {len(seed_ids)} hand-curated entries (kept as-is)")

    print("Fetching OFF ingredient taxonomy ...")
    off = fetch_off_taxonomy()
    print(f"  {len(off)} entries in OFF taxonomy")

    print("Building bootstrap entries ...")
    new_entries: list[dict] = []
    no_id_filter = 0
    no_ruling = 0
    not_dict = 0

    for off_id, entry in off.items():
        if off_id in seed_ids:
            continue
        if not isinstance(entry, dict):
            not_dict += 1
            continue
        if not off_id.startswith("en:"):
            no_id_filter += 1
            continue
        built = build_bootstrap_entry(off_id, entry, off)
        if built is None:
            no_ruling += 1
            continue
        new_entries.append(built)

    print(f"  Generated {len(new_entries)} new entries")
    print(f"  Skipped: non-en id {no_id_filter}, "
          f"no usable ruling {no_ruling}, non-dict {not_dict}")

    merged = seed["ingredients"] + new_entries
    merged.sort(key=lambda x: x["id"])

    dist = Counter(i["rulings"]["halal"]["effective_status"] for i in merged)
    print(f"\nFinal status distribution: {dict(dist)}")
    print(f"Total ingredients: {len(merged)}")

    # Sanity: every entry has at least one halal opinion
    bad = [i["id"] for i in merged if not i["rulings"]["halal"]["opinions"]]
    assert not bad, f"Entries missing opinions: {bad}"

    output = {
        "version": f"{date.today()}.2",
        "profiles": ["halal"],
        "ingredients": merged,
    }
    DATA.write_text(
        json.dumps(output, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {DATA}")


if __name__ == "__main__":
    main()
