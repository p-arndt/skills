---
name: my-stack
description: 'Reference for p-arndt''s shared project tooling: the reusable GitHub workflows in p-arndt/.github, the just modules in ~/coding/just-common, the stamp release tool, and the conventions every repo follows. Load it before touching CI, release, versioning, Dockerfiles, compose files or justfiles in any of the user''s repos, and before creating or migrating a repo. Also use when the user asks "how do my repos release", "which workflow/just module do I use", or mentions stamp, just-common, sync-common or p-arndt/.github.'
---

# my-stack

The user's repos share three pieces of tooling. Use them instead of writing CI,
release scripts or task-runner recipes from scratch; a repo-local copy is only
right when the shared piece genuinely cannot express the need, and then say so.

Current migration status per repo: `~/notes/workflow-status.md`.

## 1. Reusable workflows: `p-arndt/.github` (public)

Local checkout: `~/coding/dotgithub/`. Callers pin `@v1` (a moving tag; releases
are `v1.x.y`). Every third-party action inside is SHA-pinned.

| Workflow | For | Key inputs |
|---|---|---|
| `go-ci.yml` | Go CLIs | `os` (JSON), `race`, `gofmt` (on), `lint` (`auto` = if `.golangci.yml`), `configure-git` |
| `go-release.yml` | Go CLIs | `binary`, `main`, `targets`, `artifact-style` archive\|raw, `changelog` stamp\|git-cliff, `sign`+`sign-command`, `move-major-tag`, `verify-tag` |
| `rust-ci.yml` | Cargo | `os`, `fmt`, `clippy`, `test` |
| `rust-release.yml` | Cargo | `name`, `binaries`, `targets`, `extra-files` (`src=dest` renames), `images` (Dockerfile targets → GHCR) |
| `container-release.yml` | any image | `image`, `target`, `platforms`, `cache` gha\|registry, `changelog` |
| `sveltekit-ci.yml` | SvelteKit | `env` placeholders, `check`/`lint`/`test`/`build` toggles + commands, `setup-command` |

Caller examples: `~/coding/dotgithub/examples/`. Read the workflow file for the
full input list before writing a caller.

Rules:
- Release callers grant `permissions: contents: write` (+ `packages: write` for images).
- Gate a release on repo-specific CI with a local job: `ci: uses: ./.github/workflows/ci.yml` and `needs: ci` (ci.yml must have `on: workflow_call`).
- Repo-specific jobs the shared workflow can't do (Postgres e2e, smoke tests, db drift, govulncheck, installers) stay as **local jobs** next to the reusable call. Never drop coverage.
- `sveltekit-ci` takes the pnpm version from `packageManager` in package.json; it must exist.
- A job that calls a reusable workflow cannot declare `environment:`.
- Changing the shared repo: edit in `~/coding/dotgithub`, commit, tag `v1.x.y`, move `v1` (`git tag -f v1 && git push -f origin v1`). Callers pick it up without edits.

## 2. just modules: `~/coding/just-common`

Each project keeps a **committed copy** in `.just/` (CI and Windows need the files
in the repo). `just sync-common` refreshes the modules a project already has.

| Module | Recipes | Project sets |
|---|---|---|
| `common.just` | `default` (list), `sync-common`, pwsh on Windows | — |
| `go.just` | `run build build-release test vet fmt fmt-check lint ci clean` | `BIN_NAME`, `BUILDINFO_PKG`, opt. `MAIN` |
| `rust.just` | `run build build-release check test fmt fmt-check clippy/lint ci clean` | opt. `CARGO_SCOPE`, `RUN_PKG` |
| `android.just` | `emulator android apk apk-release test logcat clean doctor` | `APP_ID`, opt. `GRADLE_MODULE`, `ACTIVITY`, `AVD`, `APK_DIR` |
| `docker.just` | `image push up down logs ps` | `IMAGE`, opt. `REGISTRY`, `DOCKERFILE`, `TARGET`, `COMPOSE` |
| `release.just` | `version set-version release release-dry prerelease note changelog` | — (uses `stamp` on PATH) |

Rules:
- Import `common.just` first. Overriding a default variable needs `set allow-duplicate-variables`; overriding a shared recipe needs `set allow-duplicate-recipes`.
- The project justfile holds only project-specific recipes and variables.
- Recipe bodies stay plain command calls so they parse in sh and pwsh. Use just built-ins (`read()`, `datetime_utc()`, `os_family()`, `env()`) instead of shell for versions, dates, `.exe`. Only real shell logic gets a `[unix]`/`[windows]` pair.
- A recipe whose comment spans several lines gets `[doc('one line')]`, otherwise `just --list` shows the wrong line.
- Fix a shared module in `~/coding/just-common`, commit there, then `just sync-common` in every project and commit `.just/` per repo. Never edit `.just/` in a project by hand.
- Known gaps: `docker.just` has no buildx/`PLATFORM` (orbit keeps a local `docker-push` for amd64). `android.just` assumes Gradle; cooking-diary's mobile uses the Kotlin toolchain (`./kotlin`, Amper) and overrides most recipes.
- In repos with a `mobile` module: root `just release` = stamp release, `just mobile release` = app build.

## 3. Versioning and releases: `stamp`

`~/coding/stamp`, installed at `~/.local/bin/stamp` (`stamp self-update`).
stamp owns the version files, the release commit (`release: v1.2.3`), the tag and
the push. Never hand-edit VERSION / version fields / CHANGELOG.md.

- Detects `VERSION`, `package.json#version`, `Cargo.toml` without config; `.stamp.yml` (`stamp init`) for anything else.
- `stamp note <added|changed|fixed|…> "text"` records changelog entries; `stamp release <patch|minor|major|x.y.z>`; `--dry-run` shows plan and checks.
- `hooks.after_write` in `.stamp.yml` runs commands after the version is written and commits the tracked files they change (e.g. `cargo update --workspace` for Cargo.lock).
- Tag template is `v{{ version }}` everywhere except uprox (no `v`).
- CI verifies tag == committed version with the `p-arndt/stamp` action (inside the shared release workflows).

## Conventions

- Code, comments, commits in English; user-facing copy may be German.
- Conventional Commits, lowercase imperative subject.
- Go module path `github.com/p-arndt/<repo>`; build info via ldflags into `internal/buildinfo` (Version, Commit, Date).
- Self-updating Go CLIs use `github.com/p-arndt/selfupdate` (command `self-update`). shenv still has its own updater.
- Images: `ghcr.io/p-arndt/<repo>`, scratch (Go/Rust static) or `gcr.io/distroless/*:nonroot`; see the `dockerfile` skill.
- Compose: `compose.yaml` (+ `compose.prod.yaml`), `postgres:18`, dev IdP/mail/S3 via `ghcr.io/p-arndt/minisuite`.
- SvelteKit apps: see the `sveltekit-modular-monolith` skill; pnpm pinned via `packageManager`.
- Agent docs: `AGENTS.md` holds the content, `CLAUDE.md` is just `@AGENTS.md`.

## Pitfalls seen during migrations

- The shared go-ci enforces gofmt: run `gofmt -l .` first; fix in a separate `style: gofmt` commit.
- Tests or install scripts may grep `release.yml` for asset names (hop's `scripts/install_test.go`, shenv's updater). Keep asset names identical and point the tests at the caller inputs.
- Dependabot often merged into `main` meanwhile: `git pull --ff-only` / rebase before pushing.
- Manual `workflow_dispatch` pre-release buttons are gone; pre-releases go through `stamp prerelease`.
- Before pushing a repo, check how far it is ahead of origin: unrelated unpushed work (orbit, shenv) is the user's call.
