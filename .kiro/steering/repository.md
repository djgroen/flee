# Repository Management

## Git Repository Rules

### Fork Management

- **ALWAYS commit to mjpuma/flee.git (your fork)**
- **NEVER commit directly to djgroen/flee (upstream)**
- Use `myfork` remote for all pushes
- Use `origin` remote only for pulling upstream changes

### Remote Configuration

```bash
# Correct remote setup:
myfork  https://github.com/mjpuma/flee.git (fetch)
myfork  https://github.com/mjpuma/flee.git (push)
origin  https://github.com/djgroen/flee (fetch)
origin  https://github.com/djgroen/flee (push)
```

### Push Commands

- **Correct**: `git push myfork feature/dual-process-experiments`
- **WRONG**: `git push origin feature/dual-process-experiments`

### Branch Strategy

- Work on feature branches: `feature/dual-process-experiments`
- Keep main branch clean for upstream sync
- Create pull requests from your fork to upstream when ready

### File Size Management

- PNG/image files are ignored to prevent push failures
- Archive directories are ignored (too large for GitHub)
- Keep individual commits under 50MB
- Use Git LFS for large data files if needed

## Workflow

1. **Development**: Work on feature branch in your fork
2. **Commit**: Regular commits to your fork (`myfork`)
3. **Sync**: Periodically pull from upstream (`origin`) to stay current
4. **Pull Request**: When ready, create PR from your fork to upstream

## Emergency Recovery

If you accidentally push to wrong remote:
1. Check `git remote -v` to verify configuration
2. Use `git remote set-url` to fix if needed
3. Force push to correct remote if necessary

## File Management

- Large files (>10MB) should be avoided in commits
- Use `.gitignore` to exclude generated files, images, and archives
- Prefer small, focused commits over large bulk commits