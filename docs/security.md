# Security Best Practices

## GitHub Safety Guide

This document covers the multi-layered approach to prevent secret leakage in this repository.

### 1. Environment Variable Pattern

**Never hard-code secrets.** All credentials must come from environment variables.

```python
# BAD — never commit this
API_KEY = "ghp_abc123secretkey"

# GOOD — uses environment variable
import os
API_KEY = os.getenv("POE2_API_KEY")
```

### 2. .env Files (Never Committed)

- `.env` is excluded via `.gitignore`
- Use `.env.example` as a template — it only contains placeholder values
- Team members copy `.env.example` → `.env` and fill in real values locally

### 3. Pre-Commit Secret Scanner

A git pre-commit hook (`.git/hooks/pre-commit`) runs automatically on every commit. It scans staged files for:

| Pattern | Example |
|---------|---------|
| B2 Account IDs | `0053f81fbe1ed4e0000000001` |
| B2 App Keys | `K005dBlnzfDjzMxlrzYu/DmN/POMPjs` |
| GitHub PATs | `ghp_abcdefghijklmnopqrstuvwxyz0123456789AB` |
| AWS Access Keys | `AKIAIOSFODNN7EXAMPLE` |
| API key assignments | `api_key = "32+ char string"` |
| Password assignments | `password = "plaintext"` |
| Bearer tokens | `bearer abc123...` |
| `.env` file staging | Blocks accidental `.env` commits |

**To bypass (NOT recommended):**
```bash
git commit --no-verify -m "message"
```

### 4. GitHub Repository Settings

If this repo is pushed to GitHub, enable these settings:

- **Settings → Code security and analysis →** Enable:
  - ✅ Secret scanning (GitHub-native, free for public repos)
  - ✅ Push protection (requires GitHub Advanced)
- **Settings → Code security and analysis →** Enable for private repos:
  - ✅ Secret scanning
  - ✅ Push protection

### 5. B2 Credential Safety

The B2 backup script reads credentials from the rclone config at `~/.config/rclone/rclone.conf`, NOT from environment variables in code. The backup script never contains actual credentials.

### 6. CI/CD Considerations

If adding CI/CD pipelines:
- Use repository secrets (Settings → Secrets and variables → Actions)
- Never echo secrets in CI logs
- Use `***` redaction patterns

### 7. Emergency Response

If a secret IS committed:
1. **Immediately rotate** the exposed key/password
2. Run: `git log --all --full-history -- <filename>` to find commits with the secret
3. Use `git filter-branch` or `BFG Repo-Cleaner` to purge history
4. Push the cleaned history and notify all collaborators

### 8. Additional Tools (Optional)

For extra safety:
- **git-secrets**: Install and run `git secrets --install`
- **trufflehog**: Scan entire git history: `trufflehog git file://.`
- **gitleaks**: Comprehensive secret scanner: `gitleaks detect --source .`

## Summary

| Layer | What | How |
|-------|------|-----|
| Prevention (1) | No secrets in code | Use `os.getenv()` |
| Prevention (2) | .env excluded | Via `.gitignore` |
| Detection (3) | Pre-commit scan | `.git/hooks/pre-commit` |
| Detection (4) | GitHub scanning | Repository settings |
| Response (5) | Emergency plan | Rotate + purge history |
