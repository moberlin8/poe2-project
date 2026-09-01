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

## GGG Official APIs

### OAuth API (requires GGG registration)
- **Base URL**: `https://www.pathofexile.com`
- **Auth endpoint**: `POST /oauth/token`
- **Authorize endpoint**: `GET /oauth/authorize`
- **Scopes required for character data**: `account:profile`, `account:characters`, `account:leagues`
- **Scopes**:
  - `account:profile` — basic profile (name, UUID, locale, twitch link)
  - `account:leagues` — available leagues
  - `account:characters` — list characters, get specific character data (equipment, inventory, passives, skills)
  - `account:stashes` — stash tabs (PoE1 only)
  - `account:item_filter` — manage item filters
  - `account:league_accounts` — atlas passives (PoE1 only)
- **IMPORTANT**: GGG docs state: "We are currently unable to process new applications." New OAuth registrations are paused.
- **OAuth flow**: Authorization Code Grant (PKCE) or Client Credentials Grant (for service-level access)
- **Token management**: Access tokens expire; refresh tokens last 90 days

### Build Planner API (PoE2 only)
- **Docs**: `https://www.pathofexile.com/developer/docs/game#build-planner`
- **IMPORTANT**: "Editing or creating builds within Path of Exile 2 is currently not supported" via the game/launcher
- **Website**: Subscribe to build guides at `pathofexile2.com`
- **File format**: `.build` files (JSON) placed in `BuildPlanner` directory:
  - Windows: `C:\Users\<Name>\Documents\My Games\Path of Exile 2\BuildPlanner\`
  - Linux (Proton): `~/.local/share/Steam/steamapps/compatdata/2315204395/pfx/drive_c/users/steamuser/Documents/My Games/Path of Exile 2/BuildPlanner/`
- **Schema**: Single root `Build` JSON object with:
  - `name` (string), `description` (?string), `ascendancy` (?string)
  - `passives` (?array of string or BuildPassive)
  - `skills` (?array of string or BuildSkill)
  - `items` (?array of BuildItem)
- **Tools**: `scripts/build_generator.py` generates .build files from GGG schema
- **Example**: `builds/shield_wall_mercenary.build`

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
