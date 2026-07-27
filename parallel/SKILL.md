---
name: parallel
description: 'Fan a task out across a handful of subagents in one shot, then synthesize their results. The lightweight alternative to a full Workflow: no script, no phases, no orchestration layer — just N independent agents launched together. Use for searches, reviews, or edits that split cleanly into parts.'
argument-hint: '[nN] <task>'
disable-model-invocation: true
---

# parallel

Split the task into independent parts, launch one subagent per part **in a single message**, then merge the results yourself. One fan-out, one synthesis, no script.

## Usage

```
/parallel <task>      you pick the split and the count
/parallel n6 <task>   force 6 agents
/parallel n3 review the auth module for bugs, perf, and API design
```

Default to 3–6 agents. Below 3, do it inline — spawning an agent to read a file you could read is pure overhead. Above 6, or if the parts depend on each other or need loops and retries, say so in one line and use `Workflow` instead.

## The split

Find the axis where parts genuinely do not overlap:

- **By file or directory** — one agent per module. The most reliable split.
- **By dimension** — one lens each over the same code: correctness, perf, security, API design. Each is blind to the others, which is the point.
- **By candidate** — N attempts at the same task, you pick the best and graft in the good parts of the rest. For design and naming, not for edits.

Bad splits: parts that all read the same file, or one sequence chopped up. When you don't know the shape, scout with one `Grep`/`ls` and fan out over the real list instead of a guessed one.

## The prompts

Each subagent starts with **zero** of this conversation. Every prompt carries:

1. **Absolute paths** — never "the auth file".
2. **Its slice, and that it is a slice** — "You cover ONLY `src/api/`. Other agents cover the rest."
3. **The return shape** — "each finding as `file:line — one-sentence problem`, no preamble. Your final text is the data, not a message to a person."
4. **Read-only or write.**

If agents write, assign disjoint paths explicitly. If they can't be disjoint, pass `isolation: "worktree"` and merge the diffs yourself — two agents on one file is a silent last-write-wins.

## Synthesis

Their results are input, not output. Never paste them back.

- **Dedupe** — the same issue from three agents is one issue.
- **Resolve** — when two disagree, check the code and say who was right. Don't make the user referee.
- **Spot-check** — verify the load-bearing claims. A confident wrong answer looks exactly like a right one.
- **Cover the gaps** — an agent that died returns `null`; re-run its slice. Silence reads as "clean" when it means "unchecked."

Output one merged answer ordered by what matters most, not one section per agent.
