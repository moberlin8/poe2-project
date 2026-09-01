# PoE2 API Endpoints Reference

## Currency & Economy

### poe.ninja PoE2 Exchange API
```
https://poe.ninja/poe2/api/economy/exchange/current/overview?league={league}&type={type}
```
- **Auth**: None (public)
- **Rate limit**: ~12 req / 5 min
- **Update frequency**: ~1 hour
- **Types**: Currency, Fragments, Essences, UniqueArmour, UniqueWeapon, etc.
- **Example**: `https://poe.ninja/poe2/api/economy/exchange/current/overview?league=Runes%20of%20Aldur&type=Currency`

### poe.ninja Build Index API
```
https://poe.ninja/poe2/api/data/build-index-state
```
- **Auth**: None
- **Rate limit**: ~12 req / 5 min
- **Returns**: League list with class distribution statistics and character counts

## Game Data

### poe2db.tw Passive Skill Tree
```
https://poe2db.tw/data/passive-skill-tree/4.5/data_us.json
```
- **Auth**: None (requires Referer header: `https://poe2db.tw/`)
- **Data structure**: 
  - `tree` — tree name/version
  - `classes` — class definitions with starting positions
  - `alternate_ascendancies` — ascendancy class data
  - `nodes` — all passive skill nodes
  - `groups` — node groupings
  - `extraImages` — asset references
- **Size**: ~2MB JSON

### poe2db.tw Other JSON Endpoints
Pattern: `https://poe2db.tw/data/{tree_type}/{version}/{type}_{lang}.json`
- Tree types: `passive-skill-tree`, `atlas-skill-tree`, `the-genesis-tree`
- Types: `data`, `kangle`, `preview`, `alternate`
- Langs: `us`, `en`, etc.

### RePoE PoE2 Datamined Data
```
https://repoe-fork.github.io/poe2/{filename}.json
```
- **Available files**: characters.json, ascendancies.json, skills.json, skill_gems.json, mods.json, base_items.json, uniques.json, buffs.json, etc.
- **Auth**: None
- **Rate limit**: ~5 req / min
- **Update frequency**: Each patch

### poe2wiki.net MediaWiki API
```
https://poe2wiki.net/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=5
```
- **Auth**: None
- Standard MediaWiki API limits

## Build Sharing

### pobb.in Raw Build Decode
```
https://pobb.in/{id}/raw
```
- Returns JSON build data

### poe.ninja PoB Hosted Builds
```
https://poe.ninja/poe2/pob/raw/{id}
```
- Returns JSON build data

## GGG Official APIs (require 403 handling via Referer)

### GGG PoE2 Web API Endpoints
- `https://www.pathofexile.com/poe2/api/skills` — Returns HTML wrapper (needs Referer)
- `https://web.poecdn.com/poe2/api/data` — CDN endpoint (403 without auth)

## Key Constants

- **Current league**: Runes of Aldur (as of 2026-09-01)
- **PoE2 version**: 4.5
- **PoE1 version**: 3.29
- **Default language**: us (English)
- **CDN host**: cdn.poe2db.tw
- **Site host**: poe2db.tw
