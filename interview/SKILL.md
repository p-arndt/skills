---
name: interview
description: 'Interview the user with structured questions before starting work, so both sides agree on scope, constraints, and done-criteria. Two modes: /interview quick (one sharp round) and /interview deep (rounds that build on each answer until nothing is left that changes the work). Defaults to quick.'
argument-hint: '[quick|deep] [topic]'
disable-model-invocation: true
---

# interview

Ask first, then write down what was agreed. Do not start the work.

## Usage

```
/interview                  quick, on whatever we were just discussing
/interview <topic>          quick, on that topic
/interview quick <topic>    one round, max 3 questions
/interview deep <topic>     rounds until nothing open would change the work
```

The first word is the mode if it is `quick` or `deep`; otherwise it is all topic and the mode is quick. If there is no topic and no obvious current work, ask "What are we aligning on?" and start.

## Rules

1. `AskUserQuestion`, one call per round, up to 4 questions per call.
2. Never ask what the repo can answer — read the code, config, and history first. Ask only for intent, priorities, taste, and constraints that exist solely in the user's head.
3. Never ask a question whose answers all lead to the same work.
4. Concrete options, never open prompts. "Which auth?" with four real choices beats "tell me about your auth needs."
5. Lead with your recommendation, marked `(Recommended)`, and say why in the description.
6. One decision per question. If it needs "and", it is two questions.
7. `multiSelect: true` when the choices are not exclusive.

## Quick mode

One round, at most 3 questions — the three that most change the shape of the work, usually scope, approach, and done-criteria.

If an answer comes back as Other or contradicts the premise, take one more round of at most 2. Say why: "That changes the shape — two more." Then the agreement.

## Deep mode

Rounds of up to 4 questions until nothing open would change what gets built. Two rounds or ten, whichever the work needs — never stop on an open fork, never pad to hit a number. Name each round by what it covers ("Round 4 — constraints on the importer"), not by a countdown.

Round 1 is always outcome and scope; you cannot ask a good approach question before you know what "done" means. From there: constraints, approach, done-criteria, risks — skipping what is settled and letting answers pull topics earlier.

Between rounds:

1. **Investigate.** An answer that names a system is a lead, not a fact. Go read it.
2. **Propagate.** Drop what the answer settled, add what it exposed.
3. **Narrow.** Round 1 asks between architectures; round 3 asks between two named functions.

Then open the next round with one line of what you learned — that is how the user catches a wrong turn early — plus one line of what is already locked if the interview is running long.

Follow up when an answer:

- **implies an uncosted constraint** — "keep the old API working" → which clients, for how long, does a shim count.
- **names something you have not read** — go read it, then ask about the branch that will break.
- **hides a fork** — "just make it faster" → latency, throughput, or cost, and what is the number now.
- **is Other or free text** — always. Your options missed the real shape; ask what you got wrong.
- **conflicts with an earlier answer** — surface both, ask which wins. Do not quietly pick one.
- **is a strong preference with no reason** — ask once, when the reason would change the design. A preference you understand generalizes to the next fifty decisions.

Do not follow up on a closed question, on a detail you can decide yourself, or to look thorough. State the assumption and let the user correct it.

## The agreement

Every interview ends with one, reflected back before any work starts. Write it to a file if the work spans sessions (`NOTES.md`, or wherever the project keeps such things), otherwise inline.

```
**Goal:** <one line>
**Scope:** <in / out>
**Approach:** <one line>
**Done when:** <observable, checkable conditions>
```

Deep mode adds: **For** (who) after Goal, **Constraints** after Scope, the rejected alternative and why under Approach, and **Assumptions** (what you decided yourself instead of asking — the user's last chance to object) plus **Open risks** at the end.

Then ask to proceed and wait for yes. Once the user says go, build to the agreement — if reality contradicts it mid-work, stop and say which part broke and what you propose instead, rather than silently rewriting it.
