#!/bin/bash

# Simple Release Tag Creator
# Creates a Git tag and pushes it - GitHub Actions handles the rest
# Usage: ./scripts/create-release-tag.sh v1.0.1

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 v1.0.1"
    echo ""
    echo "This script creates a Git tag and pushes it."
    echo "GitHub Actions will automatically handle:"
    echo "  - Running tests"
    echo "  - Syncing NPM package.json (if NPM_TOKEN is set)"
    echo "  - Creating GitHub release"
    echo "  - Publishing to NPM (if NPM_TOKEN is set)"
    exit 1
fi

VERSION=$1

# Validate version format (should start with v)
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be in format vX.Y.Z (e.g., v1.0.1)"
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch to create a release"
    echo "Current branch: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    exit 1
fi

# Check if tag already exists
if git tag -l | grep -q "^$VERSION$"; then
    echo "❌ Error: Tag $VERSION already exists"
    exit 1
fi

echo "🚀 Creating release tag $VERSION..."
echo ""

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Create and push the Git tag
echo "🏷️  Creating Git tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION

🎯 Single Source of Truth Versioning:
- Git tag: $VERSION (authoritative)
- Python version: auto-derived via setuptools-scm
- NPM version: synced via GitHub Actions (if NPM_TOKEN is set)

🤖 GitHub Actions will automatically:
- Run tests and validation
- Sync NPM package.json version
- Create GitHub release
- Publish to NPM (if NPM_TOKEN is configured)

✅ All versions automatically synchronized"

# Push the tag
echo "📤 Pushing tag $VERSION..."
git push origin "$VERSION"

echo ""
echo "✅ Tag $VERSION created and pushed successfully!"
echo ""
echo "🤖 GitHub Actions will now automatically:"
echo "  1. Run tests and validation"
echo "  2. Sync NPM package.json (if NPM_TOKEN is set in secrets)"
echo "  3. Create GitHub release with generated notes"
echo "  4. Publish to NPM (if NPM_TOKEN is set in secrets)"
echo ""
echo "🔗 Monitor progress at:"
echo "  https://github.com/justifi-tech/mcp-server/actions"
echo ""
echo "🎉 Release will be available at:"
echo "  https://github.com/justifi-tech/mcp-server/releases/tag/$VERSION" 