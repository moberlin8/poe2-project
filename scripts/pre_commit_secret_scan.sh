#!/bin/bash
# pre-commit — PoE2 Project Secret Scanner
# This script scans for secrets before allowing a commit
# Registered as a git pre-commit hook

set -uo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "🛡️  Running secret scan..."

# Track if any secrets found
SECRETS_FOUND=0

# Patterns to scan for
# These are regex patterns that catch common secret formats
PATTERNS=(
    # B2 Account IDs
    '00[0-9a-f]{22}'
    # B2 App Keys  
    'K[0-9A-Za-z]{26}'
    # GitHub PATs
    'gh[pousr]_[A-Za-z0-9]{36,}'
    # AWS Access Keys
    'AKIA[0-9A-Z]{16}'
    # API key patterns
    'api[_-]?key[[:space:]]*[:=][[:space:]]*["\x27][A-Za-z0-9]{32,}["\x27]'
    # Password patterns
    'password[[:space:]]*[:=][[:space:]]*["\x27][^"\\x27[:space:]]{4,}["\x27]'
    'passwd[[:space:]]*[:=][[:space:]]*["\x27][^"\\x27[:space:]]{4,}["\x27]'
    # Bearer tokens
    'bearer[[:space:]]+[A-Za-z0-9._-]{20,}'
)

# Files to check (only staged files)
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    echo "No files staged. Skipping scan."
    exit 0
fi

for file in $STAGED_FILES; do
    # Skip if file doesn't exist or is binary
    if [ ! -f "$file" ]; then
        continue
    fi
    
    # Skip actual .env files (secrets) but NOT .env.example (safe to commit)
    if [[ "$file" == ".env" || "$file" == ".env.local" || "$file" == ".env.production" || "$file" == ".env.staging" ]]; then
        echo -e "${YELLOW}⚠️  Skipping $file (environment file)${NC}"
        continue
    fi
    
# Skip the scanner script, secrets config, and docs (docs intentionally contain example patterns)
    if [[ "$file" == "scripts/pre_commit_secret_scan.sh" ]] || [[ "$file" == ".secrets-scan" ]] || [[ "$file" == docs/* ]]; then
        continue
    fi
    
    # Skip cache/data files (fetched API data may contain text matching secret patterns)
    if [[ "$file" == data/cache/* ]]; then
        continue
    fi
    
    # Check file size (skip large files >10MB)
    FILE_SIZE=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo 0)
    if [ "$FILE_SIZE" -gt 10485760 ]; then
        echo -e "${YELLOW}⚠️  Skipping $file (too large: ${FILE_SIZE} bytes)${NC}"
        continue
    fi
    
    for pattern in "${PATTERNS[@]}"; do
        if grep -qiE "$pattern" "$file" 2>/dev/null; then
            # Found a potential secret
            SECRETS_FOUND=1
            MATCHED_LINE=$(grep -nE "$pattern" "$file" | head -1)
            echo -e "${RED}❌ Potential secret found in $file:${NC}"
            echo -e "${RED}   Pattern: $pattern${NC}"
            echo -e "${RED}   Line: $MATCHED_LINE${NC}"
            echo ""
        fi
    done
done

# Double-check: ensure .env is not being committed (belt and suspenders)
# Only match exactly .env, .env.local, .env.production, .env.staging, .env.* (but NOT .env.example)
if git diff --cached --name-only | grep -qE '^.env$|^.env\.(local|production|staging|test)$'; then
    SECRETS_FOUND=1
    echo -e "${RED}❌ .env file detected in commit. This file contains secrets!${NC}"
    echo -e "${RED}   Remove it: git reset HEAD .env*${NC}"
fi

# Check for .env.example to make sure it doesn't contain actual secrets
for env_example in $(echo "$STAGED_FILES" | grep '\.env\.example' || true); do
    if grep -qiE '(K[0-9A-Za-z]{26}|00[0-9a-f]{22}|gh[pousr]_[A-Za-z0-9]{36,})' "$env_example" 2>/dev/null; then
        SECRETS_FOUND=1
        echo -e "${RED}❌ Real secret found in $env_example!${NC}"
        echo -e "${RED}   .env.example should only contain placeholder values.${NC}"
    fi
done

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo -e "${RED}🚨 Commit blocked! Potential secrets detected.${NC}"
    echo -e "${YELLOW}To proceed:${NC}"
    echo "1. Remove the secret from the file"
    echo "2. Use environment variables instead (see .env file)"
    echo "3. If you need to commit the .env file, force with: git commit --no-verify"
    echo "   (NOT RECOMMENDED unless you know what you're doing)"
    echo ""
    echo "💡 Remember: Never store API keys, passwords, or credentials directly in source code."
    echo "   Use environment variables (os.getenv) and .env files (gitignored)."
    exit 1
fi

echo -e "${GREEN}✅ No secrets found. Commit allowed.${NC}"
exit 0
