---
name: parallel
description: 'Fan a task out across a handful of subagents in one shot, then synthesize their results. The lightweight alternative to a full Workflow: no script, no phases, no orchestration layer — just N independent agents launched together. Use for searches, reviews, or edits that split cleanly into parts.'
argument-hint: '[nN] <task>'
disable-model-invocation: true
---

# parallel

Split the task into independent parts, launch one subagent per part **in a single message**, then merge the results yourself.

This is deliberately smaller than `Workflow`. No script, no phases, no pipelines, no resume. One fan-out, one synthesis, done.

## Usage

```
/parallel <task>              you pick the split and the agent count
/parallel n6 <task>           force 6 agents
/parallel n3 review the auth module for bugs, perf, and API design
/parallel audit every package.json for outdated deps
```

A leading `nN` sets the agent count. Otherwise pick it yourself: **3 to 6 is the sweet spot**. Below 3, just do it inline. Above 8, the synthesis costs more than the parallelism saves — say so and suggest `Workflow` instead.

## When this is the wrong tool

Say so in one line and do that instead.

- **The parts depend on each other** — part B needs part A's output. Do it sequentially, or use `Workflow`'s `pipeline()`.
- **It needs loops, retries, or conditional stages** — that is `Workflow`.
- **It is one file or one question** — do it inline. Spawning an agent to read a file you could read is pure overhead.
- **The user has not opted into multi-agent work and this would balloon** — invoking `/parallel` *is* the opt-in for this task. It does not extend to the next one.

## How to split

Find the axis where the parts genuinely do not overlap. Good axes:

- **By file or directory** — one agent per module. The most reliable split.
- **By dimension** — one agent per lens over the same code: correctness, performance, security, API design. Each is blind to the others, which is the point.
- **By question** — one agent per independent unknown.
- **By candidate** — N agents each attempt the same task differently, you pick the best and graft in the good parts from the rest. Use for design and naming, not for edits.

Bad splits: parts that all read the same file (one agent, one read), or parts that are really one sequence chopped up.

Scout first when you don't know the shape. One cheap `Grep`/`Glob`/`ls` to get the actual list of files or modules beats guessing at the split — then fan out over the real list.

## Writing the prompts

Each subagent starts with **zero** of this conversation. The prompt is the whole world it gets.

Every prompt must carry:

1. **Absolute paths.** Never "the auth file" — `/Users/.../src/auth.ts`.
2. **Its slice, and the fact that it is a slice.** "You cover ONLY `src/api/`. Other agents cover the rest — do not stray."
3. **What to return, and in what shape.** Be explicit: "Return a list of findings, each as `file:line — one-sentence problem`. No preamble, no summary. Return the raw list; your final text is the data, not a message to a person."
4. **Read-only or write.** State which. If read-only, say "Do not edit any files."

Pick `subagent_type` per part: `Explore` for read-only searching, `general-purpose` for anything that edits or runs commands.

Launch all of them in **one message with multiple `Agent` tool calls** — separate messages run them serially and waste the entire point.

## Writes

If more than one agent edits files, keep them in disjoint file sets — assign paths explicitly in each prompt. If the sets can't be made disjoint, pass `isolation: "worktree"` so each agent gets its own copy, then merge the diffs yourself.

Never let two agents edit the same file. There is no lock, and the last write wins silently.

## Synthesis

Their results are input, not output. Do not paste them back.

1. **Merge and dedupe.** The same issue found by three agents is one issue, reported once.
2. **Resolve conflicts.** When two agents disagree, check the code yourself and say who was right. Do not report both and let the user referee.
3. **Spot-check before you repeat.** Verify at least the load-bearing claims against the actual files. A subagent's confident wrong answer looks exactly like a right one.
4. **Report the gaps.** If an agent returned nothing, failed, or covered less than its slice, say which part is uncovered. Silence reads as "clean" when it means "unchecked."

Output one merged answer, ordered by what matters most — not one section per agent.
