# 🚨 SECURITY NOTICE 🚨

## Before Running OpsAiX

**IMPORTANT**: This repository contains example configuration files. You must set up your own environment variables before running the application.

### Required Setup Steps:

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to .env:**
   - OpenAI API key
   - JIRA credentials  
   - Slack bot tokens
   - Database connection strings

3. **Never commit sensitive data:**
   - The `.env` file is ignored by git
   - Always use `.env.example` for documentation
   - Never commit actual API keys or passwords

### What's Protected:
- ✅ All API keys and secrets in `.env`
- ✅ Test files with potentially sensitive data
- ✅ Database files and vector stores
- ✅ Log files and temporary data

### Safe to Commit:
- ✅ Source code without hardcoded secrets
- ✅ Configuration templates (`.env.example`)
- ✅ Documentation and README files
- ✅ Docker and deployment configurations

## Getting Started

After securing your environment variables, run:
```bash
python src/main.py
```

The OpsAiX platform will be available at `http://localhost:8080`