---
name: commit
description: 'Commit the changes this session made, and nothing else: the files you created, edited, or deleted. Split them into logical Conventional Commits on the current branch, with no questions, no new branches, and no push unless asked. Use whenever the user says "commit", "commit your changes", "commit this", "commit das", "committe", "mach einen commit", or runs /commit (optionally /commit push).'
argument-hint: '[push]'
---

# commit

Commit **your own** changes on the **current branch**. Don't ask questions or offer options, and don't write a summary afterward. The user has had to repeat "only commit YOUR changes", "commit to main, not a branch", and "stop asking" too many times.

```
/commit          commit this session's changes on the current branch
/commit push     same, then push the current branch
```

## Hard rules

- **Scope is this session.** Only commit files you created, edited, or deleted through your own tool calls in this conversation. Changes made by the user or by other sessions stay untouched. Don't stage them, stash them, reset them, or revert them.
- **Never `git add -A`, `git add .`, or `git commit -a`.** Always stage explicit paths.
- **Stay on the current branch.** Never create or switch branches, even on `main`. Never ask which branch to use.
- **Never override git identity.** Don't pass `-c user.name`/`-c user.email`, don't set `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, and don't write `user.*` to any config. If git reports no identity, stop and tell the user in one line.
- **Don't push by default.** Push only when the args contain `push`. Never force-push.
- **Never use `--no-verify`**, and never `--amend` or rebase an existing commit unless the user asked for it.
- **Don't run the test suite.** This skill commits. Hooks run whatever checks they run.

## Steps

### 1. Collect the session's files

From this conversation's own `Write`/`Edit`/`NotebookEdit` calls and any Bash commands that created, moved, or deleted files (`rm`, `mv`, generators, formatters you ran), list the absolute paths. Group them by repository with `git -C <dir> rev-parse --show-toplevel`. If files span several repos, run steps 2-6 once per repo.

- No path is inside a git repo → print `Not a git repository.` and stop.
- A repo has none of your paths changed in `git status --porcelain` → nothing to do there. If no repo has any → print `Nothing to commit.` and stop.

### 2. Filter secrets

Never stage `.env*` (except `.env.example`/`.env.sample`), `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `id_rsa*`, `*credentials*`, `*.secret*`, or any file whose diff contains an obvious live token or private key. Leave them out and add one line to the output: `skipped (secret): <path>`.

### 3. Separate foreign hunks

For each of your files, check whether its diff contains changes you didn't make. You know what you wrote, and anything else in `git diff -- <file>` came from someone else.

- **All hunks are yours** → `git add -- <file>` (use `git rm`/`git add` for deletions and renames).
- **Mixed and separable** → stage only your hunks. Write a patch containing just those hunks and run `git apply --cached <patch>`, then check it with `git diff --cached -- <file>`. The foreign hunks stay in the working tree, unstaged.
- **Mixed and inseparable** (the same lines, or overlapping hunks) → stage the whole file and add one line: `committed whole file (mixed changes): <path>`.

If files were already staged before you started and they aren't yours, leave them staged but keep them out of your commits: run `git commit -- <paths>` only with explicit pathspecs, or unstage and restore them afterward. If that isn't possible, mention it in one line.

### 4. Plan the commits

Group the files by concern, one concern per commit, such as a feature, a fix, a refactor, docs, config, or deps. Order the commits so each one builds on the one before it, for example a schema before the code that uses it. **Don't over-split.** One change of one concern is one commit, and five files for one feature is still one commit. Split only when the concerns really are separate.

### 5. Write the messages

First run `git log --oneline -20`. If the repo has a clear convention of its own (ticket prefixes, gitmoji, capitalized subjects, another language), follow it. Otherwise use Conventional Commits:

```
type(scope): lowercase imperative subject
```

- `type` is one of `feat` `fix` `refactor` `perf` `docs` `test` `build` `ci` `chore` `style`.
- `scope` is optional, short, and taken from the module or directory.
- The subject is 72 characters or fewer, in English, with no trailing period.
- Add a body only when the *why* isn't obvious from the diff, and wrap it at 72 characters.
- Don't add AI attribution lines unless the repo's history already uses them.

### 6. Commit

For each planned commit, stage exactly its paths or hunks, then run `git commit -m "<subject>" [-m "<body>"]`.

**If a hook fails:** read the output, fix the cause (lint, format, types) in the files involved, restage, and run a **new** `git commit`. If the hook changed or formatted files itself, restage those files and commit again. Don't bypass hooks and don't amend. If the failure is outside your changes and can't be fixed reasonably, stop and report the hook error in one line.

**If `push` is in the args:** after all commits succeed, run `git push`. If there's no upstream, use `git push -u origin <current-branch>`. If the push is rejected, report it in one line. Don't pull, rebase, or force.

## Output

After committing, print only this, per repo, with a repo header line only when there is more than one repo:

```
a1b2c3d feat(auth): add refresh token rotation
e4f5a6b docs: document token lifetime settings
left uncommitted: src/foo.ts, README.md
```

- Print one line per commit as `<short sha> <subject>`.
- Print one `left uncommitted:` line listing modified or untracked files you deliberately didn't commit because they are someone else's changes. Leave it out if there are none.
- Add any `skipped (secret)`, `committed whole file`, or push-result lines.
- Don't add any other prose, recap, or question.
