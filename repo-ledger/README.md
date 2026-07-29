# Repo Ledger Skill

A compact, Git-native implementation ledger for coding agents.

It preserves what Git does not explain well:

- implementation intent
- non-obvious file ownership
- architectural decisions
- failed approaches and lessons
- executed validation
- remaining risks and handoff notes

The bundle follows the open Agent Skills directory format and has no third-party runtime dependencies.

## Install

### Codex

Repository-local:

```bash
mkdir -p .agents/skills
cp -R repo-ledger .agents/skills/repo-ledger
```

User-wide:

```bash
mkdir -p ~/.agents/skills
cp -R repo-ledger ~/.agents/skills/repo-ledger
```

### Claude Code

Repository-local:

```bash
mkdir -p .claude/skills
cp -R repo-ledger .claude/skills/repo-ledger
```

The same folder can also be symlinked into both locations.

## Invoke

Mention the skill explicitly or ask the agent to maintain the repo ledger while implementing a task.

Manual CLI usage:

```bash
python3 path/to/repo-ledger/scripts/repo_ledger.py start \
  "Fix concurrent refresh-token reuse" \
  --goal "Make refresh rotation atomic." \
  --tags auth security

python3 path/to/repo-ledger/scripts/repo_ledger.py note \
  "TokenService is shared by web and CLI login."

python3 path/to/repo-ledger/scripts/repo_ledger.py decision \
  "Use a database transaction." \
  --reason "Rotation and reuse detection must be atomic."

python3 path/to/repo-ledger/scripts/repo_ledger.py sync

python3 path/to/repo-ledger/scripts/repo_ledger.py finish \
  --validation "pnpm test — passed" \
  --risk "Revoked-token cleanup is still missing."
```

The repository receives:

```text
.agent-ledger/
├── index.md
└── tasks/
    └── <timestamp>-<task>.md
```

Local active-task state is stored in `.agent-ledger/.active.json` and ignored by Git.
