---
name: repo-ledger
description: Maintain a compact, Git-native implementation ledger for non-trivial coding tasks. Use when implementing features, fixing bugs, refactoring, migrating, debugging across files, or handing work to another coding agent. Read relevant prior ledger entries before broad exploration, create one task entry, record only durable discoveries, decisions, failed approaches, validation, risks, and handoff context, then finalize it. Do not use for trivial edits, read-only explanations, or to store raw reasoning, full diffs, secrets, or routine command output.
license: MIT
compatibility: Requires Python 3.9+ and works best inside a Git repository. No third-party Python packages are required.
metadata:
  version: "0.1.0"
  author: "Padi"
---

# Repo Ledger

Preserve implementation knowledge that Git and the source code do not explain cheaply — why a change was made, which files own the behavior, which constraints and failed approaches were discovered, how the result was validated, and what the next agent should inspect or avoid.

It must never become a transcript, a duplicate diff, or a private reasoning dump.

## The helper script

This skill bundles `scripts/repo_ledger.py`. Resolve this skill's absolute directory and run:

```bash
python3 <skill-directory>/scripts/repo_ledger.py <command>
```

Below, `ledger` stands for that `python3 <skill-directory>/scripts/repo_ledger.py` prefix. On Windows use `python` if `python3` is unavailable. Run from anywhere inside the target repo; the script finds the Git root automatically.

## When to use

Use for: feature work spanning meaningful behavior; bug fixes where the cause or failed approaches matter; refactors or migrations (schema, API, dependency, build, infra) with architectural/compatibility decisions; investigations that uncover non-obvious behavior; work likely continued by another session.

Skip for: typos and formatting; obvious one-line changes; generated files; read-only reviews or explanations; anything that doesn't modify the repo; changes whose intent is fully obvious from code and tests.

When uncertain, create an entry only if it would likely save a future agent several minutes or prevent a repeated mistake.

## Core principles

1. **One task, one file.** Never append unrelated work to an old entry.
2. **Search before broad exploration.** Query the ledger with task terms and likely paths.
3. **Git owns the diff.** Do not copy patches or enumerate obvious line edits.
4. **Durable context only** — constraints, ownership, decisions, failures, risks.
5. **No hidden reasoning.** Store concise conclusions and evidence, never chain-of-thought.
6. **History is a lead, not truth.** Verify old claims against current code.
7. **Keep entries small** — a completed entry normally stays below 150 lines.
8. **No secrets.** Redact credentials, tokens, personal data, private URLs, sensitive payloads.

## Workflow

### 1. Query previous context

Before broad exploration, search with the task wording (add likely paths when known):

```bash
ledger context --query "refresh token race condition" --files src/auth/token-service.ts tests/auth
```

Read only the returned entries or excerpts, and verify anything relevant against current code. If `.agent-ledger/` does not exist yet, continue normally and initialize it when starting.

### 2. Start one task entry

Once the task is clear enough to name (before substantial edits, but don't block urgent diagnosis to fill metadata):

```bash
ledger start "Prevent refresh-token reuse" \
  --goal "Reject reuse of rotated refresh tokens without changing the login API." \
  --tags auth security
```

This records the branch, base commit, and a local-only active-task pointer (ignored by Git). The start time is encoded in the entry's filename/`id`.

### 3. Record only meaningful events

A discovery, only when it changes the approach. Use `--section` for scope/handoff/risks/validation instead of the default (discoveries):

```bash
ledger note "TokenService is also used by the CLI login flow."
ledger note "Do not change the public refresh response schema." --section scope
```

A decision, only when alternatives existed:

```bash
ledger decision "Perform token rotation in one database transaction." \
  --reason "Reuse detection and replacement must be atomic." \
  --tradeoff "Currently relies on PostgreSQL row locking."
```

A failure, only when it teaches a reusable lesson:

```bash
ledger failure "Deleting the old token removed evidence needed for reuse detection." \
  --command "pnpm test tests/auth/refresh-token.test.ts" \
  --error "Expected TOKEN_REUSED, received TOKEN_NOT_FOUND" \
  --lesson "Keep a revoked token record until the cleanup window expires."
```

Do **not** record: every opened file; routine successful commands; full stack traces when one line suffices; speculation stated as fact; raw prompts or reasoning; anything already obvious from the final diff.

### 4. Sync changed files, then validate

`ledger sync` derives changed and untracked files from Git — run it before handoff or when the file set helps another agent orient. Then run the repo's relevant tests, type checks, linters, or builds, and record **only checks you actually observed passing**.

### 5. Finish the entry

```bash
ledger finish \
  --validation "pnpm test tests/auth/refresh-token.test.ts — passed" \
  --risk "Cleanup for old revoked tokens is not implemented." \
  --next "Inspect the concurrency test before replacing row locking."
```

`finish` syncs files, marks the task completed, updates `index.md`, and clears the local pointer. For intentionally incomplete work, add `--status partial` (also: `blocked`, `abandoned`, `superseded`).

Then commit once — your code changes and the ledger entry together. `base_commit` (captured at `start`) plus the recorded `files` list already anchor the work, so `git diff <base_commit>` shows everything the task changed.

### 6. Report to the user

In the final response, mention the ledger only when useful — that the entry was created/updated, the key decision or remaining risk, and validations actually run. Don't dump the whole entry unless asked.

## Quality gate for each fact

Before writing an item, ask: Is it hard to infer from current code or Git history? Could it prevent repeated exploration or failure? Does it explain a constraint, ownership boundary, or decision? Will it still matter after this session? If all are no, omit it.

## Stale or conflicting entries

Trust current verified behavior over old claims. Don't silently rewrite historical task files — add the corrected finding to the current task, note which old assumption is obsolete, and optionally mark the old entry `superseded` only when the relationship is clear.

## Parallel agents and worktrees

Each task is a separate Markdown file, minimizing merge conflicts. The active pointer lives in `.agent-ledger/.active.json` and stays Git-ignored, so separate worktrees keep separate pointers. Don't edit `index.md` by hand — regenerate it with `ledger index`. If parallel branches conflict only in `index.md`, resolve the task files first, then regenerate.

## Further reference

Read `references/ledger-format.md` only when repairing an entry by hand, extending the CLI, integrating with another tool, or checking whether a field/section is appropriate. Use `assets/task-template.md` only when the script cannot run.
