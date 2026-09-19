---
name: new-project
description: 'Scaffold a new repo in ~/coding the way all of p-arndt''s projects are set up: shared just modules, stamp versioning, reusable CI/release callers from p-arndt/.github, .gitignore, .editorconfig, README, AGENTS.md. Stacks: go-cli, rust, sveltekit, android (KMP/Compose). Use when the user says "neues Projekt", "new project", "leg ein Repo an", "scaffold", or runs /new-project.'
argument-hint: '<name> <go-cli|rust|sveltekit|android> [public|private]'
---

# new-project

Create a new repo that already follows the shared setup, so it never needs a
migration later. Load the `my-stack` skill first: it describes the workflows,
just modules and stamp this scaffold wires together.

```
/new-project ping go-cli            Go CLI in ~/coding/ping
/new-project recipes sveltekit      SvelteKit app with image release
/new-project netscan rust public
```

Missing name or stack: ask once, in one question. Everything else has a default:
visibility `private`, description empty, version `0.1.0`.

## Steps

1. **Target.** `~/coding/<name>` must not exist. If it does, stop and say so.
2. **Stack skeleton**, created by the stack's own tool where there is one:
   - `go-cli`: `go mod init github.com/p-arndt/<name>`, `main.go`, `internal/buildinfo/buildinfo.go` (vars `Version="dev"`, `Commit`, `Date`, set by ldflags; fall back to `runtime/debug.ReadBuildInfo` so `go install` builds report a version), `VERSION` = `0.1.0`.
   - `rust`: `cargo new <name>` (or a workspace if the user asks for several crates).
   - `sveltekit`: `pnpm dlx sv create <name>` with TypeScript, prettier, eslint, vitest; then apply the `sveltekit-modular-monolith` skill. Set `packageManager` in package.json to the installed pnpm (`pnpm --version`).
   - `android`: copy the Gradle/KMP layout from the newest Android repo the user has (check `~/coding/firstless`, `~/coding/mobmo` for a version catalog) rather than guessing versions; `applicationId` `de.parndt.<name>`.
3. **just.** `mkdir .just` and copy from `~/coding/just-common`: `common.just` always, plus `go.just` / `rust.just` / `android.just`, `docker.just` if the project ships an image, `release.just` always. Write a short `justfile`:
   ```just
   # <name> — task runner. Shared recipes live in .just/ (from ~/coding/just-common):
   # edit them there and run `just sync-common`. This file holds only <name>'s own.

   import '.just/common.just'
   import '.just/go.just'
   import '.just/release.just'

   BIN_NAME := "<name>"
   BUILDINFO_PKG := "github.com/p-arndt/<name>/internal/buildinfo"
   ```
   SvelteKit gets thin `dev`, `check`, `test`, `ci` recipes over its pnpm scripts.
4. **stamp.** `stamp current` must print the version. If the version lives somewhere stamp does not detect, run `stamp init --yes`. Rust workspaces get `hooks: after_write: [cargo update --workspace]` in `.stamp.yml`.
5. **CI and release callers** in `.github/workflows/`, copied from `~/coding/dotgithub/examples/` and adjusted (see `my-stack` for inputs):
   - go-cli: `ci.yml` → `go-ci`, `release.yml` → `go-release` (archive, changelog stamp).
   - rust: `ci.yml` → `rust-ci`, `release.yml` → `rust-release`.
   - sveltekit: `ci.yml` → `sveltekit-ci` (with `on: workflow_call` too), `release.yml` → local `ci` job + `container-release` with `needs: ci`.
   - android: no shared workflow yet; skip CI unless asked.
   Also `.github/dependabot.yml` for `github-actions` plus the stack's ecosystem (gomod, cargo, npm, gradle), weekly, grouped.
6. **Dockerfile** only for services/apps that ship an image: follow the `dockerfile` skill. Add `compose.yaml` with `postgres:18` only if the app needs a database.
7. **Repo files:**
   - `.gitignore` for the stack (binaries, `dist/`, `build/`, `target/`, `node_modules/`, `.env`, `*.jks`, `*.keystore`, `.DS_Store`).
   - `.editorconfig`: utf-8, lf, final newline, trim whitespace; tabs for Go, Svelte/TS (matches prettier `useTabs`), justfiles; 4 spaces for Rust and Kotlin.
   - `README.md`: `# <name>`, one-line claim, then `## Install`, `## Quick start`, `## Development` (`just` lists recipes, `just ci` runs checks, `just release` cuts a release), `## License`.
   - `AGENTS.md`: what the project is (one paragraph), layout, `just ci` as the check command, `just release` owns versions. `CLAUDE.md` contains only `@AGENTS.md`. Don't repeat rules from the global CLAUDE.md.
8. **Verify.** Bare `just --dry-run` must print `just --list`. `just ci` must pass. `stamp release patch --dry-run` must show a sane plan (it will fail "working tree clean" before the first commit; that one is expected).
9. **Git.** `git init -b main`, then commit with the `/commit` skill (`chore: scaffold <name>`). Never set git identity.
10. **GitHub** only if the user asked for it or passed `public`/`private` explicitly: `gh repo create p-arndt/<name> --<visibility> --source=. --push`. Otherwise say it is local only.

## Output

One line per created piece that the user will use (`just run`, `just ci`, `just release`), the path, and whether it is on GitHub. Then one next action.
