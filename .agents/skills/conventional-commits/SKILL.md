---
name: conventional-commits
description: "Use this skill when making git commits. Enforces conventional commit message format (fix:, feat:, chore:, etc.) to enable automatic version bumping. MUST be followed for every git commit."
---

# Conventional Commits

**MANDATORY**: Every git commit message MUST follow this format. No exceptions.

## Format

```
<type>: <description>
```

## Commit Types & Version Impact

| Type | Version Bump | When to use |
|------|-------------|-------------|
| `fix:` | PATCH (2.2.0 → 2.2.1) | Bug fixes, error corrections, hotfixes |
| `feat:` | MINOR (2.2.0 → 2.3.0) | New features, new functionality |
| `BREAKING:` | MAJOR (2.2.0 → 3.0.0) | Breaking changes, major rewrites |
| `chore:` | none | Maintenance, cleanup, dependency updates |
| `docs:` | none | Documentation changes |
| `style:` | none | Code formatting, no logic change |
| `refactor:` | none | Code restructuring, no behavior change |
| `perf:` | none | Performance improvements |
| `test:` | none | Adding/fixing tests |
| `ci:` | none | CI/CD pipeline changes |

## Rules

1. **Always start with a type prefix** followed by a colon and space
2. **Description must be lowercase** and concise (max 72 chars)
3. **No period** at the end of the description
4. **Use imperative mood**: "add feature" not "added feature"

## Examples

```bash
# Bug fixes → PATCH bump
fix: resolve Mixed Content errors in auth redirect
fix: correct date formatting in loan history
fix: handle null telegram_id in profile serialization

# New features → MINOR bump
feat: add version tracking system to admin settings
feat: implement Excel export for login history
feat: add bulk book import via CSV

# Breaking changes → MAJOR bump
BREAKING: restructure database schema for multi-tenant support
BREAKING: remove legacy API endpoints

# No version change
chore: update dependencies to latest versions
docs: add deployment guide for Railway
style: format code with prettier
refactor: extract auth logic into separate module
perf: optimize book search query with indexes
```

## Multi-line Commits (optional body)

For complex changes, add a body after a blank line:

```bash
feat: add auto-version bump system

Reads git commit message prefixes and automatically
bumps the version in package.json during build.
Supports fix (PATCH), feat (MINOR), BREAKING (MAJOR).
```

## How Auto-Version Works

Projects with `scripts/auto-version.js` will automatically bump the version in `package.json` during `npm run build` based on the latest commit message prefix. This means:

- Your commit message **directly controls** the version number
- The version change happens at **build time** (e.g., during Railway deploy)
- No manual version editing needed

## Checklist Before Committing

- [ ] Message starts with a valid type prefix
- [ ] Description is clear and concise
- [ ] Type matches the actual change (don't use `feat:` for a bug fix)
- [ ] Breaking changes use `BREAKING:` prefix
