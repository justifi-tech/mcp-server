# JustiFi MCP Server Development Guide

## Project Overview
This is a **JustiFi MCP (Model Context Protocol) server** designed for AI-assisted payment management. The server provides comprehensive tools for payment processing, payment methods, payouts, refunds, disputes, checkouts, and balance transactions through the JustiFi API.

## Technology Stack
- **Protocol**: Model Context Protocol (MCP) with JSON-RPC 2.0 over stdio
- **API Integration**: JustiFi Payments API with OAuth2 Client-Credentials flow
- **Authentication**: OAuth2 token caching with automatic 401 retry
- **Package Management**: uv (not pip)
- **Testing**: pytest + pytest-asyncio (36/36 tests passing)

## Branch Naming Conventions
- Use lowercase with hyphens (kebab-case)
- Format: [type]/[issue-number]-[brief-description]
- Types: feature/, bugfix/, hotfix/, docs/, refactor/, test/
- Keep descriptions under 50 characters
- Examples:
  * feature/123-user-authentication
  * bugfix/456-fix-login-error
  * docs/789-update-api-documentation

## Code Standards
- Use async/await for all I/O operations
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Use @traceable decorators for external API calls
- Never log sensitive data (API keys, payment details, tokens)
- Use environment variables for all API credentials

## Documentation Standards

### README Synchronization (Single Source of Truth)
- **Main README.md** is the authoritative source for all documentation
- **NPM README** (`npx-wrapper/README.md`) must be identical to main README.md
- **Never edit** npx-wrapper/README.md directly - always edit main README.md
- **Automatic sync**: CI validates synchronization on all PRs
- **To update NPM README**: `cp README.md npx-wrapper/README.md`

**Rationale**: Prevents documentation drift between main project and NPM package, ensuring NPM users see complete 20-tool documentation instead of outdated subset.

## Package Management
- **ALWAYS use `uv` instead of `pip`**
- Install packages: `uv pip install package_name`
- Install project with dev dependencies: `uv pip install -e ".[dev]"`
- Use `make setup` for development environment setup

## Testing
- Run `make test` to execute all tests
- All 36 tests must pass before PR creation
- Use pytest + pytest-asyncio
- Focus on error scenarios and authentication failures
- Mock external API calls using respx

## Required Environment Variables
- `JUSTIFI_CLIENT_ID` - JustiFi API Client ID
- `JUSTIFI_CLIENT_SECRET` - JustiFi API Client Secret
- `JUSTIFI_BASE_URL` - JustiFi API Base URL (default: https://api.justifi.ai)

## Common Commands
```bash
# Development setup
make setup

# Run tests
make test

# Code quality checks
make lint format check-all

# Start MCP server with auto-restart
make dev
```

## Commit Message Conventions
- Use conventional commit format: [type]: brief description
- Types: feat, fix, docs, style, refactor, test, chore
- Keep first line under 72 characters
- Examples:
  * feat: add user authentication middleware
  * fix: resolve login validation error
  * docs: update API documentation

## Security Considerations
- Validate all user inputs before API calls
- Use environment variables for all secrets
- Never log sensitive information
- Implement proper error handling without exposing internal details
- Use OAuth2 token caching with secure expiration handling

## PR Workflow Requirements
When implementing changes via GitHub Actions:
1. **Verify All Changes**: Always use `git diff` and `Read` tool to confirm file modifications were applied
2. **Run Tests**: Execute `make test` before committing - all tests must pass
3. **Run Linting**: Execute `make lint` to ensure code quality
4. **Commit Format**: Follow the conventional commit format specified above
5. **Push Changes**: Only push after verifying changes and passing tests

## File Change Verification Process
🚨 **CRITICAL**: After making ANY file changes, you MUST:
1. Use `git diff` to verify your changes were actually applied to files
2. Use `git status` to see which files were modified
3. Use `Read` tool to verify file contents match your intended changes
4. ONLY proceed to testing/committing if changes are confirmed applied
5. If changes weren't applied, retry the file modifications

## Available MCP Tools
For the current list of available tools and their descriptions, see:
- Tool implementations: `python/tools/` directory
- Tool documentation: Run `python -m python.toolkit --list-tools`
- Test files: `tests/test_*_tools.py` for usage examples

## GitHub Workflows
This project uses Claude-powered GitHub Actions for automated assistance:
- **PR Review**: Comment `@claude review` on any PR for code review
- **PR Implementation**: Comment `@claude implement [description]` to make changes
- **Issue to PR**: Comment `@claude implement` on issues to create implementation PRs

All workflows read this CLAUDE.md file for project conventions and standards. 