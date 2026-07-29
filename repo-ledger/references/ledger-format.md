# Repo Ledger format

This document defines the repository data format used by the bundled CLI.

## Directory layout

```text
.agent-ledger/
├── .gitignore
├── .active.json          # local state; never committed
├── index.md              # generated summary
└── tasks/
    ├── 20260722-214200-prevent-refresh-token-reuse.md
    └── ...
```

Task files and `index.md` are intended to be committed.

## Frontmatter

The CLI writes JSON-compatible YAML values so the file remains easy to parse without a YAML dependency.

```yaml
---
id: "20260722-214200-prevent-refresh-token-reuse"
title: "Prevent refresh-token reuse"
status: "completed"
updated: "2026-07-22T22:18:00+02:00"
base_commit: "9fe32a1..."
branch: "feature/token-rotation"
agent: "codex"
tags: ["auth", "security"]
files:
  - "src/auth/token-service.ts"
  - "src/routes/auth.ts"
---
```

### Fields

| Field | Meaning |
|---|---|
| `id` | Stable task identifier and filename stem. |
| `title` | Human-readable task name. |
| `status` | `active`, `completed`, `partial`, `blocked`, `abandoned`, or `superseded`. |
| `updated` | Last CLI write time. The task's start time is encoded in `id`. |
| `base_commit` | Git commit at task start, or `null` outside Git. Diff against it (`git diff <base_commit>`) to see everything the task changed. |
| `branch` | Branch or detached-head marker. |
| `agent` | Optional agent name supplied by argument or environment. |
| `tags` | Small search-oriented vocabulary. |
| `files` | Paths changed since `base_commit`, plus relevant untracked files. |

## Sections

Every entry uses these sections:

### Goal

The intended externally observable result and important non-goals.

### Scope

Constraints, compatibility requirements, and boundaries.

### Discoveries

Non-obvious facts about the codebase that changed the implementation approach.

### Decisions

Choices between plausible alternatives. Include reasons and important trade-offs.

### Failures

Failed approaches worth preventing another agent from repeating. Include compact evidence and a reusable lesson.

### Validation

Checks actually performed and their observed outcome.

### Remaining risks

Known gaps, uncertainty, missing coverage, migration concerns, or follow-up work.

### Handoff

The smallest useful continuation note for a future agent.

## Content rules

Good entries are:

- concise
- factual
- evidence-linked when possible
- durable beyond one session
- useful without reading a transcript

Avoid:

- complete diffs
- full logs or stack traces
- routine shell history
- internal chain-of-thought
- credentials and sensitive payloads
- unverified speculation
- stale TODO lists unrelated to the task

## Status semantics

- `active`: work is ongoing in the current worktree.
- `completed`: intended scope is implemented and validation is sufficient for handoff.
- `partial`: useful work exists, but intended scope is incomplete.
- `blocked`: progress requires an external decision, dependency, permission, or unavailable environment.
- `abandoned`: work should not be continued from this approach.
- `superseded`: a later task explicitly replaces the conclusions or implementation.

Historical entries should normally remain immutable after completion, except for correcting metadata or marking them superseded.
