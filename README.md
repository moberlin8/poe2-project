# Path of Exile 2 Expertise Toolkit

A comprehensive toolkit for Path of Exile 2 analysis — currency tracking, build indexing, skill tree visualization, and RAG-powered build recommendations.

## ⚠️ Security Notice

**Never commit secrets to this repository.** This project follows strict security practices:

### What's Protected
- `.env` files are excluded via `.gitignore`
- Pre-commit hook scans for secrets before every commit
- GitHub secret scanning is enabled (if repo is on GitHub)
- All API credentials use environment variables

### How to Use
1. Copy `.env.example` to `.env`
2. Fill in your credentials (if any) in `.env`
3. Use `python3 -c "from dotenv import load_dotenv; load_dotenv()"` in your scripts
4. Access via `os.getenv('VAR_NAME')`

### Secrets Scanning
- **Pre-commit**: Automatically runs `.git/hooks/pre-commit` to scan for secrets
- **Pattern coverage**: B2 keys, GitHub PATs, AWS keys, API keys, passwords, bearer tokens
- **Override**: Only use `git commit --no-verify` if you're certain (NOT recommended)

## Installation

```bash
# Clone and install dependencies
git clone git@github.com:mauriciogp/poe2-expertise-toolkit.git
cd poe2-expertise-toolkit
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
```

## Project Structure

```
poe2-project/
├── data/              # JSON data (gitignored - downloaded/fetched data)
├── scripts/           # Utility scripts (backup, pre-commit scanner)
├── scrapers/          # Web scrapers for PoE2 data sources
├── index/             # FAISS index builds + query engines
├── bot/               # MCP server for LLM integration
├── output/            # Generated reports (gitignored)
├── images/            # Screenshots (gitignored)
├── .env.example       # Template for environment variables
├── .gitignore         # Excludes .env, data/, logs, IDE files
├── requirements.txt   # Python dependencies
└── PROJECT.md         # Project overview
```
