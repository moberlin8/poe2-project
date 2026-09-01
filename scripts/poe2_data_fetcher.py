#!/usr/bin/env python3
"""
poe2_data_fetcher.py — Fetches PoE2 game data from multiple API sources.

All data is sourced from public APIs — no API keys required for basic usage.
Environment variables for credentials if available:

    POE2_NINJA_API_KEY, POE2_SCOUT_API_KEY, B2_ACCOUNT_ID, B2_APP_KEY

Data sources:
  - poe.ninja PoE2 Exchange API (currency prices)
  - poe.ninja Build Index API (class distribution stats)
  - poe2db.tw (skill tree, datamined game data)
  - poe2wiki.net (community wiki articles)
  - RePoE PoE2 (datamined JSON — full item/gem/mod databases)
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote_plus

# ─── Configuration ───────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Default league (can be overridden by env var)
DEFAULT_LEAGUE = os.getenv("POE2_DEFAULT_LEAGUE", "Runes of Aldur")
POE2_VERSION = "4.5"
POE1_VERSION = "3.29"
DEFAULT_LANG = "us"

# Rate limiting
REQUEST_DELAY = float(os.getenv("POE2_REQUEST_DELAY", "1.0"))

# Headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

# poe2db.tw-specific headers (requires Referer)
POE2DB_HEADERS = {
    **HEADERS,
    "Referer": "https://poe2db.tw/",
    "Origin": "https://poe2db.tw",
}

# ─── Logging ─────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(PROJECT_DIR / "scripts" / "fetcher.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def _delay():
    """Apply rate-limit delay between requests."""
    time.sleep(REQUEST_DELAY)


def _save_json(data, filename, cache=True):
    """Save JSON data to data/ or data/cache/ directory."""
    filepath = CACHE_DIR / filename if cache else DATA_DIR / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    file_size = filepath.stat().st_size
    logger.info(f"Saved: {filepath} ({file_size:,} bytes)")
    return filepath


def _load_json(filepath):
    """Load JSON data from file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── poe.ninja APIs ──────────────────────────────────────────────────

class NinjaFetcher:
    """Fetches data from poe.ninja PoE2 API."""

    BASE = "https://poe.ninja/poe2/api"

    def __init__(self, league: str = DEFAULT_LEAGUE):
        self.league = league

    def get_currency_overview(self, category: str = "Currency") -> dict:
        """Fetch currency exchange overview for a league.
        
        Categories: Currency, Fragments, Essences, Resonators, Oils,
                    Fossils, Catalysts, Scarabs, Maps, etc.
        """
        _delay()
        url = (
            f"{self.BASE}/economy/exchange/current/overview"
            f"?league={quote_plus(self.league)}&type={category}"
        )
        logger.info(f"Fetching currency overview: {self.league} / {category}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        filename = f"ninja_currency_{self.league.replace(' ', '_')}_{category.lower()}.json"
        _save_json(data, filename)
        return data

    def get_item_overview(self, category: str = "UniqueArmour") -> dict:
        """Fetch unique item prices for a category.
        
        Categories: UniqueArmour, UniqueWeapon, UniqueAccessory,
                    UniqueJewel, UniqueFlask, UniqueMap, UniqueGem
        """
        _delay()
        url = (
            f"{self.BASE}/economy/exchange/current/overview"
            f"?league={quote_plus(self.league)}&type={category}"
        )
        logger.info(f"Fetching item overview: {self.league} / {category}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        filename = f"ninja_items_{self.league.replace(' ', '_')}_{category.lower()}.json"
        _save_json(data, filename)
        return data

    def get_build_index(self) -> dict:
        """Fetch build index state with class distribution stats for all leagues."""
        _delay()
        url = f"{self.BASE}/data/build-index-state"
        logger.info("Fetching build index state")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        _save_json(data, "ninja_build_index.json")
        return data

    def get_build_links(self, league: str = None, limit: int = 100) -> list:
        """Fetch build links (PoB codes) for a league.
        
        NOTE: This endpoint may not be publicly documented.
        Requires understanding of poe.ninja's internal API.
        """
        league = league or self.league
        _delay()
        # Try the build link endpoint
        url = f"{self.BASE}/data/character-build-links?league={quote_plus(league)}&limit={limit}"
        logger.info(f"Fetching build links: {league}")
        resp = requests.get(url, headers=HEADERS, timeout=30)

        if resp.status_code == 404:
            logger.warning(f"Build links endpoint not available (404)")
            return []

        resp.raise_for_status()
        data = resp.json()
        _save_json(data, f"ninja_build_links_{league.replace(' ', '_')}.json")
        return data


# ─── poe2db.tw APIs ──────────────────────────────────────────────────

class Poe2DBFetcher:
    """Fetches datamined game data from poe2db.tw."""

    BASE = "https://poe2db.tw"
    CDN_BASE = "https://cdn.poe2db.tw"

    def get_skill_tree(self, version: str = POE2_VERSION, lang: str = DEFAULT_LANG) -> dict:
        """Fetch the passive skill tree data.
        
        Uses the poe2db.tw data endpoint discovered from JS analysis:
        /data/passive-skill-tree/{version}/data_{lang}.json
        """
        _delay()
        url = f"{self.BASE}/data/passive-skill-tree/{version}/data_{lang}.json"
        logger.info(f"Fetching skill tree (v{version}, lang={lang})")
        resp = requests.get(url, headers=POE2DB_HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        _save_json(data, f"skill_tree_poe2_v{version}_{lang}.json", cache=False)
        return data

    def get_atlas_tree(self, version: str = POE2_VERSION, lang: str = DEFAULT_LANG) -> dict:
        """Fetch the Atlas skill tree (for mapping progression)."""
        _delay()
        url = f"{self.BASE}/data/atlas-skill-tree/{version}/data_{lang}.json"
        logger.info(f"Fetching Atlas tree (v{version})")
        resp = requests.get(url, headers=POE2DB_HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        _save_json(data, f"atlas_tree_poe2_v{version}_{lang}.json", cache=False)
        return data

    def search(self, query: str, lang: str = DEFAULT_LANG) -> dict:
        """Search poe2db.tw for items, skills, etc."""
        _delay()
        url = f"{self.BASE}/{lang}/{quote_plus(query)}"
        logger.info(f"Searching poe2db: {query}")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = {"url": url, "status_code": resp.status_code, "content_length": len(resp.text)}
        _save_json(data, f"poe2db_search_{query.replace(' ', '_')}.json")
        return data

    def get_gems(self, version: str = POE2_VERSION) -> dict:
        """Fetch skill gem data from poe2db.tw."""
        _delay()
        url = f"{self.CDN_BASE}/data/skills/{version}/skills_{DEFAULT_LANG}.json"
        logger.info(f"Fetching skills/gems (v{version})")
        resp = requests.get(url, headers=POE2DB_HEADERS, timeout=30)

        if resp.status_code == 404:
            # Try alternate pattern
            url = f"{self.BASE}/skills"
            resp = requests.get(url, headers=HEADERS, timeout=30)

        if resp.status_code == 200:
            data = resp.json()
            _save_json(data, f"skills_poe2_v{version}.json", cache=False)
            return data
        else:
            logger.warning(f"Skills fetch failed: {resp.status_code}")
            return {"error": f"Status {resp.status_code}"}


# ─── RePoE Datamined Data ─────────────────────────────────────────────

class RepoeFetcher:
    """Fetches datamined game data from RePoE PoE2 fork."""

    BASE = "https://repoe-fork.github.io/poe2"

    def get_all_filenames(self) -> list:
        """Get list of all available JSON data files."""
        _delay()
        url = f"{self.BASE}/"
        logger.info("Fetching RePoE PoE2 file listing")
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()

        # Parse JSON filenames from the HTML page
        import re
        filenames = re.findall(r'href="([^"]+\.json)"', resp.text)
        logger.info(f"Found {len(filenames)} RePoE data files")
        _save_json({"files": filenames}, "repoe_file_list.json")
        return filenames

    def fetch(self, name: str) -> dict:
        """Fetch a specific RePoE data file (e.g., 'uniques', 'mods', 'skills')."""
        _delay()
        url = f"{self.BASE}/{name}.json"
        logger.info(f"Fetching RePoE: {name}.json")
        resp = requests.get(url, headers=HEADERS, timeout=60)

        if resp.status_code == 404:
            logger.error(f"RePoE file not found: {name}.json")
            return {}

        resp.raise_for_status()
        data = resp.json()
        _save_json(data, f"repoe_{name}.json", cache=False)
        return data


# ─── poe2wiki.net APIs ────────────────────────────────────────────────

class WikiFetcher:
    """Fetches content from poe2wiki.net via MediaWiki API."""

    API_URL = "https://poe2wiki.net/w/api.php"

    def search(self, query: str, limit: int = 5) -> dict:
        """Search the wiki for a query term."""
        _delay()
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": limit,
        }
        logger.info(f"Wiki search: {query}")
        resp = requests.get(self.API_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _save_json(data, f"wiki_search_{query.replace(' ', '_')}.json")
        return data

    def get_page(self, title: str) -> dict:
        """Fetch a full wiki page by title."""
        _delay()
        params = {
            "action": "parse",
            "page": title,
            "prop": "wikitext",
            "format": "json",
        }
        logger.info(f"Wiki page: {title}")
        resp = requests.get(self.API_URL, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        _save_json(data, f"wiki_page_{title.replace(' ', '_')}.json")
        return data


# ─── pobb.in Build Decode ──────────────────────────────────────────────

class PoBDecoder:
    """Decodes Path of Building (PoB) builds from paste codes."""

    def decode(self, code: str) -> dict:
        """Decode a PoB build from a pobb.in short code or full paste string."""
        # If it's a short code (like 'abc123'), fetch from pobb.in
        if not code.startswith("---") and len(code) < 100:
            _delay()
            url = f"https://pobb.in/{code}/raw"
            logger.info(f"Fetching PoB build: {code}")
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                _save_json(data, f"pob_build_{code}.json", cache=False)
                return data
            else:
                logger.error(f"Failed to fetch PoB build: {resp.status_code}")
                return {}

        # If it's a raw paste string, parse directly
        # TODO: Implement local PoB string parsing using the same format as PoB Community Fork
        return {"error": "Raw PoB string parsing not yet implemented"}


# ─── Main CLI ─────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="PoE2 Data Fetcher")
    parser.add_argument(
        "--source", "-s",
        choices=["ninja", "poe2db", "repoe", "wiki", "pob", "all"],
        default="all",
        help="Data source to fetch from"
    )
    parser.add_argument(
        "--league", "-l",
        default=DEFAULT_LEAGUE,
        help=f"League name (default: {DEFAULT_LEAGUE})"
    )
    parser.add_argument(
        "--what", "-w",
        default="currency",
        help="What to fetch (currency, items, builds, skilltree, etc.)"
    )
    parser.add_argument(
        "--query", "-q",
        help="Search query (for wiki/poe2db search)"
    )
    parser.add_argument(
        "--pob-code",
        help="pobb.in short code to decode"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory override"
    )

    args = parser.parse_args()

    if args.output:
        global DATA_DIR
        DATA_DIR = Path(args.output)
        CACHE_DIR = DATA_DIR / "cache"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"PoE2 Data Fetcher — League: {args.league}")

    # ── poe.ninja fetcher ──
    ninja = NinjaFetcher(league=args.league)

    if args.source in ("ninja", "all"):
        if args.what in ("currency", "all"):
            for cat in ["Currency", "Fragments", "Essences"]:
                try:
                    ninja.get_currency_overview(cat)
                except Exception as e:
                    logger.error(f"Currency fetch failed for {cat}: {e}")

        if args.what in ("items", "all"):
            for cat in ["UniqueArmour", "UniqueWeapon", "UniqueAccessory", "UniqueJewel"]:
                try:
                    ninja.get_item_overview(cat)
                except Exception as e:
                    logger.error(f"Item fetch failed for {cat}: {e}")

        if args.what in ("builds", "all"):
            try:
                ninja.get_build_index()
            except Exception as e:
                logger.error(f"Build index fetch failed: {e}")

    # ── poe2db.tw fetcher ──
    poe2db = Poe2DBFetcher()

    if args.source in ("poe2db", "all"):
        if args.what in ("skilltree", "all"):
            try:
                poe2db.get_skill_tree()
            except Exception as e:
                logger.error(f"Skill tree fetch failed: {e}")

        if args.what in ("atlas", "all"):
            try:
                poe2db.get_atlas_tree()
            except Exception as e:
                logger.error(f"Atlas tree fetch failed: {e}")

        if args.query:
            poe2db.search(args.query)

    # ── RePoE fetcher ──
    repoe = RepoeFetcher()

    if args.source in ("repoe", "all"):
        if args.what == "repoe":
            files = repoe.get_all_filenames()
            for f in files[:10]:  # Just the first 10 for demo
                name = f.replace(".json", "").replace(".min.json", "")
                try:
                    repoe.fetch(name)
                except Exception as e:
                    logger.error(f"RePoE fetch failed for {name}: {e}")

    # ── Wiki fetcher ──
    wiki = WikiFetcher()

    if args.source in ("wiki", "all"):
        if args.query:
            wiki.search(args.query)
        if args.what == "wiki-page" and args.query:
            wiki.get_page(args.query)

    # ── PoB decoder ──
    pob = PoBDecoder()

    if args.source in ("pob", "all") and args.pob_code:
        pob.decode(args.pob_code)

    logger.info("Fetch complete.")


if __name__ == "__main__":
    main()
