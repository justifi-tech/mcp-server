# Release Process

This document describes how to release new versions of the JustiFi MCP Server.

## Prerequisites

1. **NPM Access**: You must have publish access to the `@justifi/mcp-server` package
2. **GitHub Access**: Push access to the main branch
3. **Clean Working Directory**: No uncommitted changes
4. **Main Branch**: Must be on the main branch with latest changes

## Release Types

- **Patch** (1.0.0 → 1.0.1): Bug fixes, small improvements
- **Minor** (1.0.0 → 1.1.0): New features, non-breaking changes
- **Major** (1.0.0 → 2.0.0): Breaking changes

## Methods

### Method 1: Automated Release (Recommended)

The automated release process runs on every push to main and handles version bumping, changelog generation, and NPM publishing.

1. **Ensure proper commit messages** (uses conventional commits):
   ```bash
   git commit -m "feat: add new payment tool"     # minor release
   git commit -m "fix: resolve authentication bug" # patch release
   git commit -m "feat!: change API structure"     # major release
   ```

2. **Push to main**:
   ```bash
   git push origin main
   ```

3. **Monitor the release**:
   - Check [GitHub Actions](https://github.com/justifi-tech/mcp-server/actions)
   - Verify [NPM publication](https://www.npmjs.com/package/@justifi/mcp-server)
   - Check [GitHub Releases](https://github.com/justifi-tech/mcp-server/releases)

### Method 2: Manual Release

If you need to create a release manually:

1. **Create and push a Git tag**:
   ```bash
   # For patch release (1.0.0 → 1.0.1)
   git tag -a v1.0.1 -m "Release v1.0.1"
   
   # For minor release (1.0.0 → 1.1.0)
   git tag -a v1.1.0 -m "Release v1.1.0"
   
   # For major release (1.0.0 → 2.0.0)
   git tag -a v2.0.0 -m "Release v2.0.0"
   
   # Push the tag to trigger GitHub Actions
   git push origin <tag-name>
   ```

2. **Verify the release**:
   - Check [GitHub Actions](https://github.com/justifi-tech/mcp-server/actions) completed successfully
   - Verify the GitHub release was created
   - Test NPX installation: `npx @justifi/mcp-server --version`

### Method 3: Manual NPM Publish

For emergency releases or troubleshooting:

1. **Update version**:
   ```bash
   cd npx-wrapper
   npm version patch  # or minor, major
   ```

2. **Publish to NPM**:
   ```bash
   npm publish
   ```

3. **Create git tag**:
   ```bash
   git add npx-wrapper/package.json
   git commit -m "chore(release): v$(node -p "require('./npx-wrapper/package.json').version")"
   git tag -a "v$(node -p "require('./npx-wrapper/package.json').version")" -m "Release v$(node -p "require('./npx-wrapper/package.json').version")"
   git push origin main --tags
   ```

## Release Checklist

Before releasing:

- [ ] All tests pass locally
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if manual)
- [ ] No breaking changes without version bump
- [ ] NPX wrapper tested locally

After releasing:

- [ ] GitHub release created
- [ ] NPM package published
- [ ] Version tag created
- [ ] CI/CD pipeline succeeded
- [ ] Test installation: `npx @justifi/mcp-server --version`

## Troubleshooting

### NPM Publish Fails

1. **Check NPM token**: Ensure `NPM_TOKEN` secret is set in GitHub
2. **Check permissions**: Verify you have publish access to `@justifi/mcp-server`
3. **Version conflict**: Ensure version number is higher than published version

### GitHub Release Fails

1. **Check GitHub token**: Ensure `GITHUB_TOKEN` has proper permissions
2. **Branch protection**: Verify you can push to main branch
3. **Semantic release**: Check commit message format

### Manual Override

If automated release fails, you can always fall back to manual NPM publishing:

```bash
cd npx-wrapper
npm login
npm publish
```

## Post-Release

After a successful release:

1. **Update documentation** if needed
2. **Announce the release** to users
3. **Monitor for issues** in the first few hours
4. **Update examples** if new features were added

## Emergency Rollback

If a release has critical issues:

1. **Deprecate the version**:
   ```bash
   npm deprecate @justifi/mcp-server@1.0.1 "Critical bug - use 1.0.0"
   ```

2. **Publish a hotfix**:
   ```bash
   # Create a hotfix tag
   git tag -a v1.0.2 -m "Hotfix v1.0.2"
   git push origin v1.0.2
   ```

3. **Update documentation** with the fix