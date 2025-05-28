# Release Checklist

## Version Update Locations

When releasing a new version, update the version number in these THREE files:

1. **VERSION** - The main version file
2. **CHANGELOG.md** - Add new version section with date
3. **balena.yml** - Update the version field

## Release Process

1. Update version in all three files above
2. Document changes in CHANGELOG.md
3. Commit with message: `Release vX.Y.Z - <brief description>`
4. Tag the release: `git tag vX.Y.Z`
5. Push to origin: `git push origin <branch> --tags`
6. Merge to main if on feature branch
7. Deploy to Balena fleet

## Version Numbering

- **Major (X.0.0)**: Breaking changes or major features
- **Minor (0.Y.0)**: New features, backwards compatible
- **Patch (0.0.Z)**: Bug fixes and minor improvements 