# Remove redundant release scripts and streamline to tag-only releases

Fixes #39

## 🎯 Problem

The project had redundant release processes creating confusion and potential conflicts:

1. **Multiple release methods**: Scripts + GitHub Actions doing the same thing
2. **Push-to-main releases**: Releases triggered on every push to main
3. **Redundant documentation**: RELEASING.md duplicating docs/VERSIONING.md
4. **Complex workflows**: Multiple ways to create releases instead of one clear path

## 🔧 Solution

### 🗑️ Removed Redundant Files (-487 lines)
- ✅ `scripts/release-automated.sh` (142 lines) - Duplicated GitHub Actions locally
- ✅ `scripts/create-release-tag.sh` (91 lines) - Simple wrapper around git commands
- ✅ `RELEASING.md` (150 lines) - Redundant with docs/VERSIONING.md

### 🔧 Streamlined GitHub Actions
- ✅ Modified `.github/workflows/release.yml` → "CI Tests" (tests only, no releases)
- ✅ **Releases now ONLY trigger on tags** (not on every push to main)
- ✅ Kept `.github/workflows/automated-release.yml` as the ONLY release workflow

### 📝 Updated Documentation
- ✅ Updated `docs/VERSIONING.md` to reflect tag-only releases
- ✅ Updated `scripts/check-version-sync.sh` error messages
- ✅ Removed all references to deleted scripts

## 🎯 Result: Single Tag-Based Release Workflow

Developers now have **ONE simple, clear release process**:

```bash
# Create and push a tag - GitHub Actions handles everything else
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1
```

**GitHub Actions automatically:**
- ✅ Runs tests and validation
- ✅ Syncs NPM package.json version
- ✅ Creates GitHub release with notes
- ✅ Publishes to NPM
- ✅ Handles all version synchronization

## 📊 Impact

| Before | After |
|--------|-------|
| 3 release methods | 1 release method |
| Releases on every push | Releases only on tags |
| 2 documentation files | 1 documentation file |
| Complex manual steps | Zero manual steps |

## 🧪 Testing

- [x] All existing tests pass
- [x] GitHub Actions workflows validate correctly
- [x] Documentation is consistent and accurate
- [x] Version sync validation works properly

## 📁 Files Changed

**Deleted:**
- `scripts/release-automated.sh`
- `scripts/create-release-tag.sh` 
- `RELEASING.md`

**Modified:**
- `.github/workflows/release.yml` (removed release jobs, tests only)
- `docs/VERSIONING.md` (updated for tag-only releases)
- `scripts/check-version-sync.sh` (updated error messages)

**Preserved:**
- `.github/workflows/automated-release.yml` (the ONLY release workflow)
- All core functionality and existing tools

---

**No scripts, no manual steps, no confusion** - exactly one way to release. 🎉