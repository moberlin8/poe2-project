# PoE2 Expertise Toolkit

A comprehensive toolkit for Path of Exile 2 analysis — currency tracking, build indexing, skill tree visualization, and RAG-powered build recommendations.

## Data Sources

| Source | API Endpoint | Auth | Rate Limit |
|--------|-------------|------|------------|
| poe.ninja PoE2 Exchange | `https://poe.ninja/poe2/api/economy/exchange/current/overview?league={league}&type={type}` | None | ~12 req/5min |
| poe.ninja Build Index | `https://poe.ninja/poe2/api/data/build-index-state` | None | ~12 req/5min |
| poe2db.tw | `https://poe2db.tw/{lang}/{slug}` | None | ~15 req/min |
| poe2wiki.net | `https://poe2wiki.net/w/api.php?action=query` | None | Standard MW |
| RePoE PoE2 Datamined | `https://repoe-fork.github.io/poe2/*.json` | None | ~5 req/min |
| GGG Skill Tree (CDN) | `https://web.poecdn.com/poe2/api/skills` | None | ~15 req/min |

## Directory Structure

```
poe2-project/
├── data/              # JSON data files (scraped + downloaded)
├── scripts/           # Python scripts for scraping/API calls
├── scrapers/          # Web scrapers for various PoE2 data sources
├── index/             # FAISS index builds + query scripts
├── bot/               # MCP server for LLM integration
├── output/            # Generated reports and visualizations
├── images/            # Screenshots and visual assets
└── docs/              # Project documentation
```

## Current Status

- **Project initialized**: 2026-09-01
- **Current league**: Runes of Aldur
- **Skill tree data**: Pending download from GGG CDN
- **Currency exchange**: Available via poe.ninja API
- **Meta builds**: Available via poe.ninja build index

## Quick Start

```bash
cd /home/mao/DaveMatt/poe2-project
# Get skill tree
/usr/bin/python3 scripts/fetch_skill_tree.py
# Get currency data  
/usr/bin/python3 scripts/fetch_ninja_data.py --league "Runes of Aldur"
# Build FAISS index
/usr/bin/python3 index/build_index.py
# Query
/usr/bin/python3 index/query_poe2.py --q "best budget mapper build"
```
