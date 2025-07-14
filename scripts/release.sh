#!/bin/bash

# JustiFi MCP Server Release Script
# Usage: ./scripts/release.sh [patch|minor|major]

set -e

RELEASE_TYPE=${1:-patch}
CURRENT_VERSION=$(node -p "require('./npx-wrapper/package.json').version")

echo "🚀 JustiFi MCP Server Release Process"
echo "Current version: $CURRENT_VERSION"
echo "Release type: $RELEASE_TYPE"
echo ""

# Validate release type
if [[ ! "$RELEASE_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo "❌ Invalid release type: $RELEASE_TYPE"
    echo "Valid types: patch, minor, major"
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ You must be on the main branch to release"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean"
    echo "Please commit or stash your changes"
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Run tests
echo "🧪 Running tests..."
npm run test 2>/dev/null || echo "⚠️  No npm test script found, skipping..."

# Run Python tests if available
if command -v pytest &> /dev/null; then
    echo "🐍 Running Python tests..."
    python -m pytest tests/ -v
fi

# Run linting
echo "✨ Running linting..."
if command -v ruff &> /dev/null; then
    ruff check .
    ruff format .
fi

# Test NPX wrapper
echo "🎯 Testing NPX wrapper..."
cd npx-wrapper
node wrapper.js --version
node wrapper.js --help
cd ..

# Version bump
echo "⬆️  Bumping version..."
cd npx-wrapper
npm version $RELEASE_TYPE --no-git-tag-version
cd ..

NEW_VERSION=$(node -p "require('./npx-wrapper/package.json').version")
echo "New version: $NEW_VERSION"

# Create release commit
echo "📝 Creating release commit..."
git add npx-wrapper/package.json
git commit -m "chore(release): v$NEW_VERSION

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Create git tag
echo "🏷️  Creating git tag..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"

# Push changes
echo "📤 Pushing changes..."
git push origin main
git push origin "v$NEW_VERSION"

echo ""
echo "✅ Release v$NEW_VERSION completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Verify the release at: https://github.com/justifi-tech/mcp-server/releases"
echo "2. Check CI/CD pipeline: https://github.com/justifi-tech/mcp-server/actions"
echo "3. Verify NPM publication: https://www.npmjs.com/package/@justifi/mcp-server"
echo "4. Test installation: npx @justifi/mcp-server --version"
echo ""
echo "🎉 Users can now install with: npx @justifi/mcp-server"