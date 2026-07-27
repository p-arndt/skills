---
name: interview
description: 'Interview the user with structured questions before starting work, so both sides agree on scope, constraints, and done-criteria. Two modes: /interview quick (one sharp round) and /interview deep (rounds that build on each answer until nothing is left that changes the work). Defaults to quick.'
argument-hint: '[quick|deep] [topic]'
disable-model-invocation: true
---

# interview

Do not start the work. Ask questions first, then write down what was agreed.

## Usage

```
/interview                          quick mode, topic = whatever we were just discussing
/interview <topic>                  quick mode on that topic
/interview quick <topic>            one round, max 3 questions
/interview deep <topic>             rounds that build on each other until nothing is open
/interview deep                     deep mode on the current work
```

The first word of the argument is the mode if it is `quick` or `deep`; otherwise the whole argument is the topic and the mode is `quick`.

Examples:

```
/interview deep migrate the billing service off Stripe Checkout
/interview quick the new /export endpoint
/interview deep                     (after a long design discussion, to pin it down)
```

If the topic is empty and there is no obvious current work, ask one plain question: "What are we aligning on?" Then start.

## Rules for every mode

1. Use the `AskUserQuestion` tool. One call per round, up to 4 questions per call.
2. Never ask what you can find out yourself. Read the code, the config, the git history first. Ask only what the repo cannot answer: intent, priorities, taste, constraints that exist only in the user's head.
3. Never ask a question whose answer would not change what you build. If both answers lead to the same work, drop it.
4. Every question gets concrete options, not open prompts. "Which auth?" with four real choices beats "tell me about your auth needs." The user can always pick Other.
5. Lead each option list with your recommendation, marked `(Recommended)`, and say why in the description.
6. Use `multiSelect: true` when the choices are not exclusive (which features, which platforms).
7. Ask about one decision per question. If a question needs "and", it is two questions.
8. Reflect answers back before acting. End with an agreement block, then ask to proceed.

## Building each round on the last

This is what separates a good interview from a survey. Between rounds, do three things:

1. **Investigate.** Open the files, configs, or dependencies the last answers pointed at. An answer that names a system is a lead, not a fact — go read it.
2. **Propagate.** Every answer kills some questions and creates others. Drop what the answer settled. Add what it exposed.
3. **Narrow.** Each round's options should be more specific than the last, because you know more. Round 1 asks between architectures; round 3 asks between two named functions.

Concretely, an answer should trigger a follow-up when it:

- **Implies a constraint you have not costed** — "must keep the old API working" → next round asks which clients, for how long, and whether a shim counts.
- **Names something you have not read** — "it goes through the legacy importer" → go read it, then ask about the specific branch that will break.
- **Reveals a hidden fork** — "just make it faster" → is the budget latency, throughput, or cost, and what is the current number.
- **Is Other or free text** — always follow up. Free text means your options missed the real shape. Ask what you got wrong.
- **Conflicts with an earlier answer** — surface both, ask which wins. Do not quietly pick one.
- **Is a strong preference with no stated reason** — ask for the reason once, when the reason would change the design. A preference you understand generalizes to the next fifty decisions; one you don't have to re-ask.

Do not follow up when the answer closed the question, when the follow-up is a detail you can decide yourself, or when you are asking only to look thorough. State assumptions instead and let the user correct them.

## Quick mode

One round. At most 3 questions — the three whose answers most change the shape of the work, usually scope, approach, and done-criteria.

One exception: if an answer comes back as Other, or contradicts the premise of the request, take a second round of at most 2 questions. Say why: "That changes the shape — two more."

Then output:

```
Agreed:
- Goal: <one line>
- Scope: <in / out>
- Approach: <one line>
- Done when: <observable condition>
```

Then ask: "Start?" Wait for yes.

## Deep mode

Rounds of up to 4 questions until no open question would change the work. There is no round limit — the stopping condition is that nothing open would change what gets built, not a count. Simple work may settle in two rounds; a gnarly migration may take ten or more. Never stop while a real fork is still open, and never pad rounds to hit a number.

Announce where you are each round by what it covers, not by a countdown: "Round 4 — constraints on the importer." Only estimate a total if you are genuinely near the end ("one or two more").

Cover in roughly this order, skipping what is already settled and letting answers pull topics earlier:

1. **Outcome** — what is true when this is done, in observable terms. Who is it for.
2. **Scope** — what is explicitly out. What is deferred rather than dropped.
3. **Constraints** — deadlines, stack, compatibility, things that must not break, decisions already made that are not up for relitigation.
4. **Approach** — the real fork in the road, with the trade-off on each branch.
5. **Done-criteria** — how it gets verified. Tests, manual check, review, deploy.
6. **Risks** — what would make this the wrong thing to build. What was tried before and failed.

Round 1 is always outcome and scope; you cannot ask a good approach question before you know what "done" means.

Between rounds, give one line of what you learned before asking again: "The importer has two entry points, so the migration is not one switch." That line is how the user catches a wrong turn early.

Stop when a round would only produce questions that do not change the work. Say so plainly: "No open questions left that change the plan." Length is not a reason to stop, and neither is the user having answered a lot already — if a round exposes three new forks, ask about them. Conversely, if round 2 settles everything, stop at round 2.

If the interview runs long, keep it cheap to follow: before each round, restate in one line what is already locked so the user is not re-deriving it from scratch.

Then write the agreement — to a file if the work spans sessions (`NOTES.md`, a scratchpad file, or wherever the project keeps such things; ask if unclear), otherwise inline:

```
## Agreement

**Goal:** <one line>
**For:** <who>

**In scope:** <bullets>
**Out of scope:** <bullets>

**Constraints:** <bullets>
**Approach:** <2-4 lines, plus the alternative rejected and why>

**Assumptions:** <what you decided yourself instead of asking — the user's last chance to object>
**Done when:** <observable, checkable conditions>
**Open risks:** <bullets, or "none">
```

Then ask to proceed.

## After the interview

Once the user says go, build to the agreement. If reality contradicts it mid-work, stop and say which part broke and what you propose instead — do not silently rewrite the agreement.
