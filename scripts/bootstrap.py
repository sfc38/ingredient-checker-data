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

WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
WIKI_CACHE = CACHE_DIR / "wikipedia.json"
WIKI_USER_AGENT = (
    "IngredientCheck/2.2 "
    "(https://github.com/sfc38/ingredient-checker-data; "
    "fatihcatpinar@gmail.com)"
)

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


def load_wiki_cache() -> dict:
    if WIKI_CACHE.exists():
        try:
            return json.loads(WIKI_CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_wiki_cache(cache: dict) -> None:
    WIKI_CACHE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _is_useful_wiki_entry(entry: dict) -> bool:
    """Filter out entries that redirected to the generic 'E number' article
    (Wikipedia's catch-all when no dedicated page exists for the E-number)."""
    if not isinstance(entry, dict) or "extract" not in entry:
        return False
    url = (entry.get("url") or "").lower()
    if url.endswith("/e_number") or url.endswith("/e_numbers") or "/wiki/e_number" in url:
        return False
    extract_lower = entry["extract"].lower()
    if extract_lower.startswith("e numbers") or extract_lower.startswith("e number,"):
        return False
    return True


def fetch_wiki_redirects(title: str, cache: dict) -> list[str]:
    """Return all titles that redirect to this Wikipedia title.
    e.g. for "Pumpkin seed" this returns ["Pepita", "Pumpkin kernel",
    "Pepitas", ...] — Wikipedia-curated synonyms for free.
    Cached on disk between runs."""
    cache_key = f"_redirects::{title}"
    if cache_key not in cache:
        import urllib.parse as urlparse
        api_url = (
            "https://en.wikipedia.org/w/api.php"
            "?action=query"
            f"&titles={urlparse.quote(title, safe='')}"
            "&prop=redirects&rdlimit=max&format=json"
        )
        req = urllib.request.Request(api_url, headers={"User-Agent": WIKI_USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            titles: list[str] = []
            for page_data in pages.values():
                for r in page_data.get("redirects", []):
                    t = r.get("title")
                    if isinstance(t, str):
                        titles.append(t)
            cache[cache_key] = {"titles": titles}
        except Exception as e:
            cache[cache_key] = {"error": str(e), "titles": []}
        save_wiki_cache(cache)
    return cache[cache_key].get("titles") or []


def fetch_wiki(title: str, cache: dict) -> dict | None:
    """Return {'extract': ..., 'url': ...} for a Wikipedia title, or None.
    Caches responses on disk between runs. Returns None when the lookup
    redirected to the generic 'E number' article (i.e. no dedicated page)."""
    if title not in cache:
        import urllib.parse as urlparse
        url = WIKI_API + urlparse.quote(title, safe="")
        req = urllib.request.Request(url, headers={"User-Agent": WIKI_USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract")
            page_url = (
                data.get("content_urls", {})
                    .get("desktop", {})
                    .get("page")
            )
            if extract and page_url:
                entry = {"extract": extract.strip(), "url": page_url}
            else:
                entry = {"error": "no extract"}
        except Exception as e:  # network error, 404, etc.
            entry = {"error": str(e)}
        cache[title] = entry
        save_wiki_cache(cache)

    entry = cache[title]
    return entry if _is_useful_wiki_entry(entry) else None


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
            "effective_status": "allowed",
            "explanation": (
                "Open Food Facts classifies this ingredient as non-vegan but "
                "vegetarian (vegan: no, vegetarian: yes) — typically dairy "
                "or egg. Milk, butter, eggs, yogurt, and standard dairy "
                "products are halal under Islamic dietary law. Caveat: "
                "cheese (and whey from cheese-making) made with animal "
                "rennet from a non-halal-slaughtered animal is mushbooh; "
                "if this product contains specific cheese with unclear "
                "rennet, verify with the manufacturer."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "allowed",
                "note": "vegan: no, vegetarian: yes — dairy/egg generally halal",
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


def find_seed_ancestor(off_id: str, off: dict, seed_ids: set[str],
                       max_depth: int = 8) -> str | None:
    """BFS through OFF parents to find the nearest ancestor that is in seed.
    Returns the seed ancestor id or None. Used to inherit hand-curated
    rulings to derivative ingredients (en:cane-sugar -> en:sugar)."""
    visited = {off_id}
    queue: list[tuple[str, int]] = [(off_id, 0)]
    while queue:
        current, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        entry = off.get(current, {})
        if not isinstance(entry, dict):
            continue
        parents = entry.get("parents", [])
        if not isinstance(parents, list):
            continue
        for p in parents:
            if not isinstance(p, str) or p in visited:
                continue
            visited.add(p)
            if p in seed_ids:
                return p
            queue.append((p, depth + 1))
    return None


def inherited_ruling_from_seed(seed_id: str, seed_by_id: dict, off_id: str) -> dict:
    """Build a ruling that inherits the seed's effective_status, with an
    explanation citing the inheritance."""
    seed_entry = seed_by_id[seed_id]
    seed_ruling = seed_entry["rulings"]["halal"]
    seed_name = seed_entry["names"][0] if seed_entry.get("names") else seed_id
    return {
        "effective_status": seed_ruling["effective_status"],
        "explanation": (
            f"Inherits its halal ruling from {seed_name} ({seed_id}), which "
            f"is a hand-curated entry in our database. "
            f"{seed_ruling['explanation']}"
        ),
        "disputed": seed_ruling.get("disputed", False),
        "confidence": "medium",
        "opinions": [{
            "source": f"Inherited from curated entry {seed_id}",
            "type": "community",
            "status": seed_ruling["effective_status"],
            "note": f"Derivative ingredient of {seed_name}",
        }],
    }


def build_bootstrap_entry(off_id: str, entry: dict, off: dict,
                          seed_ids: set[str] | None = None,
                          seed_by_id: dict | None = None,
                          wiki_cache: dict | None = None) -> dict | None:
    # 1. Check if any ancestor is in the seed — inherit if so.
    if seed_ids and seed_by_id:
        seed_ancestor = find_seed_ancestor(off_id, off, seed_ids)
        if seed_ancestor is not None:
            ruling = inherited_ruling_from_seed(seed_ancestor, seed_by_id, off_id)
            names = collect_names(entry) or [off_id.split(":", 1)[-1].replace("-", " ").capitalize()]
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

    # 2. Otherwise fall back to OFF vegan/vegetarian heuristic.
    vegan = get_inherited_flag(off_id, off, "vegan")
    vegetarian = get_inherited_flag(off_id, off, "vegetarian")
    ruling = heuristic_halal_ruling(vegan, vegetarian)
    if ruling is None:
        return None

    # Attach the OFF ingredient page URL as a tappable source ref.
    off_page_url = f"https://world.openfoodfacts.org/ingredient/{off_id}"
    for op in ruling.get("opinions", []):
        if op.get("source") == "Open Food Facts taxonomy" and "ref" not in op:
            op["ref"] = off_page_url

    # If this is an E-number, add a Wikipedia citation. The URL pattern
    # https://en.wikipedia.org/wiki/E<num> redirects to the appropriate
    # Wikipedia article for every E-number Wikipedia covers.
    e_num = extract_e_number(off_id, entry)
    if e_num:
        already_has_wiki = any(op.get("source") == "Wikipedia"
                               for op in ruling.get("opinions", []))
        if not already_has_wiki:
            ruling["opinions"].insert(0, {
                "source": "Wikipedia",
                "type": "scientific",
                "status": ruling["effective_status"],
                "ref": f"https://en.wikipedia.org/wiki/{e_num}",
            })

    names = collect_names(entry)
    if not names:
        # Generate a placeholder name from the id
        slug = off_id.split(":", 1)[-1]
        names = [slug.replace("-", " ").capitalize()]

    raw_desc = get_lang_value(entry.get("description"))
    definition = clean_definition(raw_desc, names)

    e_num = extract_e_number(off_id, entry)

    # Try Wikipedia for a definition. For E-numbers: first the "E<num>"
    # page, then fall back to the primary English ingredient name.
    # For non-E ingredients: try the primary name directly.
    wiki_url_for_definition: str | None = None
    wiki_canonical_title: str | None = None
    if wiki_cache is not None:
        candidate_titles: list[str] = []
        if e_num:
            candidate_titles.append(e_num)
        if names:
            candidate_titles.append(names[0])
        for title in candidate_titles:
            wiki = fetch_wiki(title, wiki_cache)
            if wiki and wiki.get("extract"):
                if definition is None:
                    definition = wiki["extract"]
                wiki_url_for_definition = wiki.get("url")
                # Extract canonical Wikipedia title for redirect lookup
                if wiki_url_for_definition and "/wiki/" in wiki_url_for_definition:
                    import urllib.parse as urlparse
                    raw = wiki_url_for_definition.rsplit("/wiki/", 1)[-1]
                    wiki_canonical_title = urlparse.unquote(raw).replace("_", " ")
                break

    # Pull Wikipedia redirect titles into names[] — gives us
    # crowd-curated synonyms (e.g. "Pepita" -> "Pumpkin seed").
    if wiki_canonical_title and wiki_cache is not None:
        redirects = fetch_wiki_redirects(wiki_canonical_title, wiki_cache)
        if redirects:
            seen = {n.lower() for n in names}
            for r in redirects:
                if r.lower() not in seen:
                    names.append(r)
                    seen.add(r.lower())

    result = {
        "id": off_id,
        "names": names,
        "e_number": e_num,
        "category": derive_category(off_id, entry),
    }
    if definition:
        result["definition"] = definition
    result["rulings"] = {"halal": ruling}
    result["last_reviewed"] = str(date.today())

    if wiki_url_for_definition:
        # Override the generic E<num> Wikipedia URL with the actual
        # post-redirect page URL we now have.
        for op in result["rulings"]["halal"].get("opinions", []):
            if op.get("source") == "Wikipedia":
                op["ref"] = wiki_url_for_definition

    return result


def main() -> None:
    print(f"Loading seed (hand-curated entries) from {SEED.name} ...")
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    seed_ids = {i["id"] for i in seed["ingredients"]}
    seed_by_id = {i["id"]: i for i in seed["ingredients"]}
    print(f"  {len(seed_ids)} hand-curated entries (kept as-is)")

    print("Fetching OFF ingredient taxonomy ...")
    off = fetch_off_taxonomy()
    print(f"  {len(off)} entries in OFF taxonomy")

    print("Loading Wikipedia cache ...")
    wiki_cache = load_wiki_cache()
    print(f"  {len(wiki_cache)} cached Wikipedia summaries")

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
        built = build_bootstrap_entry(off_id, entry, off, seed_ids, seed_by_id, wiki_cache)
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

    # Build output version: take seed's version (assumed to be the latest
    # hand-curated bump) so the bootstrap output tracks seed changes.
    output = {
        "version": seed.get("version", str(date.today())),
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
