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
SOURCES_DIR = ROOT / "sources"               # community + authority extracts
CACHE_DIR = ROOT / "scripts" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

WORLDOFISLAM_URL = "https://special.worldofislam.info/Food/numbers.html"
HEURISTICS_URL = "https://github.com/sfc38/ingredient-checker-data/blob/main/scripts/README.md#halal-aware-pattern-heuristics"

# Patterns that flag halal-specific concerns OFF's vegan/vegetarian
# flags don't capture. Each entry is (regex, short note shown to users,
# pattern_id for the citation). Patterns only apply when the entry's
# current ruling is "allowed" — they push toward caution; they never
# overrule an already-cautious or forbidden ruling.
import re as _re
HALAL_CAUTION_PATTERNS: list[tuple[_re.Pattern, str, str]] = [
    (_re.compile(r'\bnatural\s+\w*\s*flavou?r', _re.IGNORECASE),
     "Natural flavors are typically extracted using ethyl alcohol as a "
     "carrier. The underlying ingredient is usually halal, but the "
     "alcohol carrier is disputed across madhhabs.",
     "natural-flavor-extract"),
    (_re.compile(r'\b(vanilla|almond|lemon|orange|peppermint|coffee|coconut|maple)\s+extract\b', _re.IGNORECASE),
     "Extracts typically use ethyl alcohol as a solvent. Whether trace "
     "residual alcohol is halal is disputed across madhhabs.",
     "alcohol-extract"),
    (_re.compile(r'\bhydrolyzed\s+\w+\s+protein\b', _re.IGNORECASE),
     "Hydrolyzed proteins are processed with enzymes. The enzyme source "
     "can be microbial (halal) or animal (mushbooh); the label rarely "
     "declares which.",
     "hydrolyzed-protein"),
    (_re.compile(r'\bmodified\s+\w*\s*(starch|corn\s+starch|food\s+starch)\b', _re.IGNORECASE),
     "Starch modification can involve enzymes; the enzyme source is "
     "usually unspecified on the label.",
     "modified-starch"),
    (_re.compile(r'\b(wine\s+vinegar|red\s+wine\s+vinegar|white\s+wine\s+vinegar)\b', _re.IGNORECASE),
     "Wine vinegars are produced from wine. Most scholars permit the "
     "vinegar after full acetic-acid conversion; others avoid any "
     "wine-derived product. Disputed.",
     "wine-vinegar"),
    (_re.compile(r'^(natural|artificial)\s+(colou?r|flavou?ring|flavou?r)s?$', _re.IGNORECASE),
     "Generic 'flavoring' or 'coloring' labels are opaque — the "
     "underlying ingredient can be plant, animal, or alcohol-extracted.",
     "opaque-flavoring"),
]


def apply_halal_patterns(name_candidates: list[str], ruling: dict) -> bool:
    """If any candidate name matches a halal-caution pattern, append a
    pattern-source opinion to ruling.opinions[] and force the
    effective_status to 'caution' if it was 'allowed'.
    Returns True if a pattern fired."""
    if ruling.get("effective_status") not in ("allowed", None):
        return False
    for name in name_candidates:
        if not isinstance(name, str):
            continue
        for pattern, reason, pid in HALAL_CAUTION_PATTERNS:
            if pattern.search(name):
                ruling["opinions"].append({
                    "source": "Ingredient-checker halal pattern heuristic",
                    "type": "scientific",
                    "status": "caution",
                    "note": reason,
                    "ref": HEURISTICS_URL + "#" + pid,
                })
                if ruling.get("effective_status") == "allowed":
                    ruling["effective_status"] = "caution"
                    ruling["disputed"] = True
                    # Also tighten the explanation so the chip's
                    # detail sheet leads with the halal concern.
                    ruling["explanation"] = (
                        reason + " " + ruling.get("explanation", "")
                    ).strip()
                return True
    return False

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


def parse_worldofislam_md() -> dict[str, dict]:
    """Parse sources/worldofislam.md into a dict keyed by E-number.
    Returns: {"e100": {"name": "...", "status": "mushbooh|halal|haram|halal_or_haram", "reason": "..."}}"""
    path = SOURCES_DIR / "worldofislam.md"
    if not path.exists():
        return {}
    status_map = {
        "halal": "allowed",
        "haram": "forbidden",
        "mushbooh": "caution",
        "halal_or_haram": "caution",
    }
    result: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) != 4:
            continue
        e_num, name, status, reason = cells
        if not e_num.upper().startswith("E"):
            continue
        if status not in status_map:
            continue
        key = e_num.lower().replace(" ", "")  # "e100", "e160a"
        result[key] = {
            "name": name,
            "status": status_map[status],
            "raw_status": status,
            "reason": reason,
        }
    return result


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


def get_lang_value(field_value, prefer: tuple[str, ...] = ("en",),
                   allow_fallback: bool = True) -> str | None:
    """OFF stores per-language values as { lang: value }. Pull preferred lang.
    If allow_fallback is False and no preferred language is present, return
    None (rather than picking some arbitrary language). Useful for fields
    like `description` where showing a Swedish description to an English
    audience is worse than showing nothing."""
    if not isinstance(field_value, dict):
        return field_value if isinstance(field_value, str) else None
    for lang in prefer:
        v = field_value.get(lang)
        if isinstance(v, str) and v.strip():
            return v.strip()
    if allow_fallback:
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


def is_descendant_of_any(off_id: str, off: dict, ancestor_ids: set[str],
                         depth: int = 0, max_depth: int = 6,
                         visited: set | None = None) -> bool:
    """True if off_id is `ancestor_ids` itself, or transitively descends
    from any of them via OFF's parent tree."""
    if off_id in ancestor_ids:
        return True
    if depth >= max_depth:
        return False
    if visited is None:
        visited = set()
    if off_id in visited:
        return False
    visited.add(off_id)
    entry = off.get(off_id)
    if not isinstance(entry, dict):
        return False
    parents = entry.get("parents") or []
    if not isinstance(parents, list):
        return False
    for p in parents:
        if isinstance(p, str) and is_descendant_of_any(
            p, off, ancestor_ids, depth + 1, max_depth, visited
        ):
            return True
    return False


# Sunni majority view (and explicitly Shafi'i, Maliki, Hanbali): all fish
# are halal regardless of slaughter method; the Quranic basis is
# "Lawful to you is the game of the sea and its food" (5:96). Hanafi
# school restricts to fish (not other sea creatures), which is what
# `en:fish` covers — shellfish/crustaceans live under `en:seafood`
# alongside fish, so we only override the strict fish branch.
HALAL_FISH_ANCESTORS = {"en:fish"}


def apply_fish_halal_override(off_id: str, off: dict, ruling: dict) -> None:
    """If this ingredient descends from `en:fish`, replace a caution
    verdict driven by OFF's `vegetarian: no` flag with `allowed`,
    because fish do not require Islamic ritual slaughter."""
    if ruling.get("effective_status") != "caution":
        return
    if not is_descendant_of_any(off_id, off, HALAL_FISH_ANCESTORS):
        return
    # Only override the "vegetarian: no" caution path — leave other
    # caution reasons (e.g. halal-aware pattern matches) untouched.
    opinions = ruling.get("opinions", [])
    triggered_by_off = any(
        op.get("source") == "Open Food Facts taxonomy"
        and op.get("note") == "vegetarian: no"
        for op in opinions
    )
    if not triggered_by_off:
        return
    ruling["effective_status"] = "allowed"
    ruling["explanation"] = (
        "Fish do not require Islamic ritual slaughter (dhabihah) to be "
        "permissible. The Quran (5:96) explicitly permits seafood, and "
        "all four Sunni schools — Hanafi, Shafi'i, Maliki, Hanbali — "
        "agree that fish is halal regardless of how it was caught or "
        "killed. Open Food Facts marks fish as non-vegetarian for "
        "dietary classification purposes, but that flag does not "
        "translate to a halal concern for fish."
    )
    for op in opinions:
        if (op.get("source") == "Open Food Facts taxonomy"
                and op.get("note") == "vegetarian: no"):
            op["status"] = "allowed"
            op["note"] = (
                "vegetarian: no, but classified as fish — fish is halal "
                "in all Sunni schools without ritual slaughter"
            )


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
    if vegan == "maybe" and vegetarian == "yes":
        # Chocolate, baked goods, etc. — vegetarian:yes means no meat/fish,
        # vegan:maybe usually means "may contain milk or egg". Both are
        # halal as a class.
        return {
            "effective_status": "allowed",
            "explanation": (
                "Open Food Facts marks this ingredient as vegetarian but "
                "possibly non-vegan — meaning it may contain dairy or egg, "
                "both of which are halal under Islamic dietary law. Halal "
                "by default unless the product also contains forbidden "
                "ingredients (alcohol, pork derivatives, etc.) elsewhere."
            ),
            "disputed": False,
            "confidence": "low",
            "opinions": [{
                "source": "Open Food Facts taxonomy",
                "type": "community",
                "status": "allowed",
                "note": "vegan: maybe, vegetarian: yes — may contain dairy/egg, both halal",
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


def _normalize_name(name: str) -> str:
    """Lower + collapse British/American spelling variants so the same
    ingredient under either locale matches a single seed entry."""
    n = name.strip().lower()
    n = n.replace("flavouring", "flavoring").replace("flavour", "flavor")
    n = n.replace("colouring", "coloring").replace("colour", "color")
    # strip trailing 's' so "natural flavors" matches "natural flavor"
    if n.endswith("s") and len(n) > 3:
        n = n[:-1]
    return n


def build_seed_name_index(seed_ingredients: list[dict]) -> dict[str, str]:
    """Map every normalized name from every seed entry back to its id."""
    idx: dict[str, str] = {}
    for entry in seed_ingredients:
        for n in entry.get("names", []):
            if not isinstance(n, str):
                continue
            key = _normalize_name(n)
            # First-write wins so primary names beat aliases on conflicts.
            idx.setdefault(key, entry["id"])
    return idx


def find_seed_by_name(entry: dict, seed_name_index: dict[str, str],
                      self_id: str) -> str | None:
    """Look up an OFF taxonomy entry's names against the seed name index.
    Catches cases where en:natural-flavouring (British) refers to the
    same ingredient as the seed's en:natural-flavoring (American) but
    isn't a taxonomy descendant."""
    names = collect_names(entry)
    for name in names:
        seed_id = seed_name_index.get(_normalize_name(name))
        if seed_id and seed_id != self_id:
            return seed_id
    return None


def resolve_wikipedia_definition(names: list[str], e_num: str | None,
                                 wiki_cache: dict | None) -> tuple[str | None, str | None, str | None]:
    """Try to find a Wikipedia article whose extract we can use as a
    definition. Returns (extract, url, canonical_title). For E-numbers
    we try the "E<num>" page first. For everything we try the primary
    English name plus a series of suffix-stripped variations: "pecan
    nut" -> "pecan", "tomato paste" -> "tomato", etc. Deliberately *not*
    falling back to the first word alone, because "atlantic salmon" ->
    "Atlantic" lands on Atlantic Ocean and "natural flavour" -> "Natural"
    lands on Nature."""
    if wiki_cache is None:
        return None, None, None
    candidate_titles: list[str] = []
    if e_num:
        candidate_titles.append(e_num)
    if names:
        primary = names[0]
        candidate_titles.append(primary)
        suffix_stripped = primary
        for suffix in (" nut", " nuts", " seed", " seeds", " kernel",
                       " flour", " meal", " powder", " oil",
                       " butter", " extract", " paste", " puree",
                       " syrup", " juice"):
            if suffix_stripped.lower().endswith(suffix):
                suffix_stripped = suffix_stripped[: -len(suffix)].strip()
        if suffix_stripped and suffix_stripped != primary:
            candidate_titles.append(suffix_stripped)
    for title in candidate_titles:
        wiki = fetch_wiki(title, wiki_cache)
        if wiki and wiki.get("extract"):
            url = wiki.get("url")
            canonical_title = None
            if url and "/wiki/" in url:
                import urllib.parse as urlparse
                raw = url.rsplit("/wiki/", 1)[-1]
                canonical_title = urlparse.unquote(raw).replace("_", " ")
            return wiki["extract"], url, canonical_title
    return None, None, None


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
                          wiki_cache: dict | None = None,
                          worldofislam: dict | None = None,
                          seed_name_index: dict[str, str] | None = None) -> dict | None:
    # 1. Check if any ancestor is in the seed — inherit if so.
    seed_match: str | None = None
    if seed_ids and seed_by_id:
        seed_match = find_seed_ancestor(off_id, off, seed_ids)
        # 1b. If no taxonomy ancestor matched, check for a name-based
        # match — handles British/American spelling siblings (e.g.
        # en:natural-flavouring -> en:natural-flavoring) that aren't
        # parent/child in OFF's taxonomy.
        if seed_match is None and seed_name_index is not None:
            seed_match = find_seed_by_name(entry, seed_name_index, off_id)
        if seed_match is not None:
            ruling = inherited_ruling_from_seed(seed_match, seed_by_id, off_id)
            names = collect_names(entry) or [off_id.split(":", 1)[-1].replace("-", " ").capitalize()]
            raw_desc = get_lang_value(entry.get("description"), allow_fallback=False)
            definition = clean_definition(raw_desc, names)
            # Inherit e_number from the seed when OFF doesn't have one
            # directly. en:soya-lecithin doesn't carry an E-code in OFF
            # but its seed parent en:soy-lecithin is E322 — without
            # this, the iOS sub-ingredient filter can't tell that an
            # "E322" sub is the same additive as the parent.
            e_num = extract_e_number(off_id, entry)
            if not e_num:
                e_num = seed_by_id[seed_match].get("e_number")
            # Fall through to Wikipedia for a definition when OFF has
            # no English description — without this, inheriting entries
            # like en:thiamin-mononitrate would have an empty "What it is"
            # section even though Wikipedia has a good article.
            if definition is None:
                wiki_extract, _, _ = resolve_wikipedia_definition(names, e_num, wiki_cache)
                if wiki_extract:
                    definition = wiki_extract
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
            return result

    # 2. Otherwise fall back to OFF vegan/vegetarian heuristic.
    vegan = get_inherited_flag(off_id, off, "vegan")
    vegetarian = get_inherited_flag(off_id, off, "vegetarian")
    ruling = heuristic_halal_ruling(vegan, vegetarian)
    if ruling is None:
        return None

    # Fish are halal regardless of slaughter — override the
    # vegetarian:no caution before the rest of the pipeline runs.
    apply_fish_halal_override(off_id, off, ruling)

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

    # Only accept English OFF descriptions. Showing a Swedish/French/etc
    # paragraph to an English-only UI is worse than falling through to
    # Wikipedia (which is what `definition is None` triggers below).
    raw_desc = get_lang_value(entry.get("description"), allow_fallback=False)
    definition = clean_definition(raw_desc, names)

    e_num = extract_e_number(off_id, entry)

    wiki_extract, wiki_url_for_definition, wiki_canonical_title = \
        resolve_wikipedia_definition(names, e_num, wiki_cache)
    if definition is None and wiki_extract:
        definition = wiki_extract

    # Apply halal-aware pattern heuristics BEFORE we expand names[] with
    # Wikipedia redirects. Reason: a Wikipedia redirect for "Almond" can
    # include "Almond extract", which would otherwise falsely flag the
    # raw almond entry as containing alcohol.
    apply_halal_patterns(names, ruling)

    # Pull Wikipedia redirect titles into names[] — gives us
    # crowd-curated synonyms (e.g. "Pepita" -> "Pumpkin seed").
    # Skipped for halal pattern matching above.
    if wiki_canonical_title and wiki_cache is not None:
        redirects = fetch_wiki_redirects(wiki_canonical_title, wiki_cache)
        if redirects:
            seen = {n.lower() for n in names}
            for r in redirects:
                if r.lower() not in seen:
                    names.append(r)
                    seen.add(r.lower())

    # Merge WorldOfIslam community opinion if available for this E-number.
    if e_num and worldofislam:
        woi = worldofislam.get(e_num.lower())
        if woi:
            ruling["opinions"].append({
                "source": "WorldOfIslam E-number list",
                "type": "community",
                "status": woi["status"],
                "note": woi["reason"],
                "ref": WORLDOFISLAM_URL,
            })

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
        opinions = result["rulings"]["halal"].setdefault("opinions", [])
        wiki_op = next((op for op in opinions if op.get("source") == "Wikipedia"), None)
        if wiki_op:
            # We already had a generic E<num> Wikipedia ref. Replace with
            # the actual post-redirect article URL.
            wiki_op["ref"] = wiki_url_for_definition
        else:
            # No Wikipedia opinion yet (typical for non-E-number entries
            # like en:cocoa-powder). The definition came from Wikipedia,
            # so attribute it.
            opinions.insert(0, {
                "source": "Wikipedia",
                "type": "scientific",
                "status": ruling["effective_status"],
                "note": "Source of the 'What it is' description",
                "ref": wiki_url_for_definition,
            })

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

    print("Loading WorldOfIslam community rulings ...")
    worldofislam = parse_worldofislam_md()
    print(f"  {len(worldofislam)} E-number rulings")

    print("Indexing seed names for cross-locale aliasing ...")
    seed_name_index = build_seed_name_index(seed["ingredients"])
    print(f"  {len(seed_name_index)} unique normalized seed names")

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
        built = build_bootstrap_entry(off_id, entry, off, seed_ids, seed_by_id,
                                      wiki_cache, worldofislam, seed_name_index)
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
