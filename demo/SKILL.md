---
name: demo
description: 'Record a README demo GIF for a terminal tool with VHS: build an isolated fixture harness, write the tape, record assets/demo.gif plus stills, and wire it into the README and justfile. Use for TUIs and CLIs that have no demo, or to re-record one that has drifted.'
argument-hint: '[repo path] [--stills] [--rerecord]'
disable-model-invocation: true
---

# demo

A demo GIF is a story, not a feature tour. One narrative, told once, that answers "what is this
and why would I want it" before the reader scrolls to Install.

The reference implementations are `hop/demo/hop.tape` (TUI) and `stamp/demo/stamp.tape` (CLI).
Read whichever matches before writing a new one.

## Usage

```
/demo                  the repo in the current directory
/demo <path>           that repo
/demo --stills         also capture assets/screens/*.png at each beat
/demo --rerecord       tape exists; rebuild fixtures and re-run it
```

## The rule that outranks everything

**Never record against real data.** Not the user's hosts, keys, databases, servers, or
`$HOME`. Every host, file, row and command answer on screen is invented, so that anyone can
re-run the recording without exposing anything of their own.

That means the tape is never run directly — it runs through a driver that stands up a
throwaway world first. If you cannot isolate the tool, stop and say so rather than
recording something that leaks.

**And invented is not enough — fake secrets must not match a real provider's pattern.** A
convincing `sk_live_` followed by 24 alphanumerics *is* Stripe's published key format, so secret
scanners flag it and GitHub push protection rejects the entire repository, even though the value
is meaningless. Break the pattern deliberately:

```
STRIPE_SECRET_KEY=sk_live_EXAMPLE_ONLY_not_a_real_key    # underscores break the alnum run
SESSION_SECRET=example_only_not_a_real_session_secret
```

Same reasoning as never committing a generated keypair: **anything shaped like a credential will
be treated as one.** Say so in a comment next to the fixture, or someone will later make the
values look "more realistic" and re-break the push.

## Procedure

1. **Classify.** TUI (keys, panes, live redraw) or CLI (commands, output, prompts)? Different
   tape shape, different dimensions.
2. **Find the story.** Read the README's opening pitch. The demo proves *that* sentence — nothing
   else. `hop` pitches "never leave your terminal", so its tape hops. `stamp` pitches "one
   command sets the version everywhere", so its tape releases once.
3. **Build the harness first.** A driver (`scripts/demo.mjs`, or `demo/setup.sh` exported as
   `$DEMO_SETUP`) that builds the binary, seeds fake data in `$TMPDIR`, points `HOME`/config at
   a throwaway directory, starts any fake server, then calls `vhs`. Wire it to `just demo`.
4. **Write the tape** into `demo/<tool>.tape` — house style below.
5. **Validate, then record.** `vhs validate <tape>` catches syntax errors in a second instead
   of after a two-minute run. Then record — and **watch the GIF**, not the exit code.
6. **Wire it in**: `## 🎬 What it looks like` section in the README, centered `<img>`, width 900.
7. **Clean up** the throwaway world unless `--keep`.

## House style

Every tape opens with a comment saying what the driver does and why nothing on screen is real,
then this block — copy it verbatim, changing only `Output`, `Require`, and the dimensions:

```
Output assets/demo.gif

Require <tool>

Set Shell "bash"
Set FontSize 15
Set Width 1500          # see sizing below
Set Height 800
Set Padding 26
Set Margin 18
Set MarginFill "#1a1420"
Set BorderRadius 10
Set Theme "Catppuccin Mocha"
Set TypingSpeed 55ms
Set Framerate 24
```

Then:

1. **Hide the setup.** `Hide` → `source $DEMO_SETUP` / `clear` → `Show`. The GIF opens on a clean
   prompt, never on scaffolding.
2. **`Wait+Screen /regex/` instead of blind sleeps.** Match text the tool actually prints. A
   `Sleep` that is long enough on your machine is a race on someone else's. Exception, and write
   it in a comment: output that streams progress lines races with the pattern — use a plain
   `Sleep` there.
3. **Then a `Sleep` to let the eye land.** Wait for *ready*, sleep for *readable* — 1.2–2.5s per
   beat. The reader has never seen this screen.
4. **Section the tape** with `# ---- the host list ----` headers, in narrative order.
5. **Comment the why, not the what.** `Down 3` needs no comment; *why the cursor must end on
   `prod-web-1`* does. Future-you re-recording after a UI change needs the intent.
6. **`Screenshot assets/screens/<beat>.png`** at each beat when `--stills`. Free during the same
   run, and they give the README real section images instead of prose.
7. **Rest at the end.** A final `Sleep 1500ms` so the loop does not snap on the last keystroke.

## The harness

The driver, not the tape, is where recordings actually break. Five things that will bite:

1. **Interactive prompts need a pty.** Seeding a tool that asks for a passphrase fails with `EOF`
   under a plain pipe. Wrap it: `script -q /dev/null <cmd>` on BSD/macOS, `script -qec "<cmd>"
   /dev/null` on Linux. Pick the branch from `uname`, **never by probing** — a probe run of
   `script` swallows the piped stdin the real call needs, and the prompt then hangs forever.
2. **`Require` is checked against vhs's own PATH**, before any shell exists to source your setup.
   Export the built binary's directory in the driver too, or the tape fails on line one.
3. **Set `PS1` explicitly.** Bash's default prompt puts the real user and hostname in the
   recording. This is a leak, and it is the easiest one to miss because it looks like a prompt.
4. **Silence update checks and nags** (`SHENV_NO_UPDATE_CHECK=1`, `PAGER=cat`, `GIT_PAGER=cat`).
   A "new version available" line recorded into the GIF dates it permanently.
5. **Anything generated at record time must be regenerated by the driver**, not committed —
   fixed keys in a repo look like leaked keys. Prove it by copying the tree without the generated
   file and running the driver there; if it needs a manual step, a fresh clone is broken.

## Sizing

Start from 1500x800 (TUI) or 1400x640 (CLI), then **size to the tallest act plus a few lines of
headroom**. Both directions cost you:

- **Too tall** — dead space under the prompt is dead pixels in the README, and the GIF is heavier
  for nothing. A 900px window whose content stops at 500px wastes 40% of every frame.
- **Too short** — the act scrolls, and every `Wait+Screen` after that point silently stops
  matching (see Gotchas).

Width is set by the longest line you do not want wrapped — usually a key, hash, or path in a
confirmation prompt. Count it in **columns, including the prompt**: a 129-character command
behind a 17-character prompt needs 146, and the prompt is the part everyone forgets. Usable
columns are roughly

```
(Width - 2*Padding - 2*Margin) / 9.7px      # at FontSize 15
```

so 1500px yields ~145 — one short, and it wraps. Leave ~10 columns of slack rather than sizing
to the exact fit, and re-check whenever the prompt or the value changes length.

## Type what is typed, paste what is pasted

`TypingSpeed` applies per character, so a long literal is expensive: 130 characters at 55ms is
**7 seconds** of cursor crawl. But speeding the typing up is the wrong fix — nobody types a key,
hash, URL or base64 blob by hand. `Copy`/`Paste` puts the whole string on screen in one frame,
which is both faster and what actually happens:

```
Copy "shenv add-member alice age1... <signing-key>"
Paste
Sleep 900ms          # let it be seen before it is run
Enter
```

Reserve `Type` for the short commands you want read as they appear. Two caveats: `Copy` takes a
literal, so a value generated at record time has to be written into a fragment the tape pulls in
with `Source`; and it writes to the **real system clipboard**, so recording clobbers whatever the
user had on it — say so in the driver's header.

## Length

40–60 seconds. Under 30 and it reads as a teaser; over 75 and the GIF is too heavy for a README
and nobody watches it twice. If the story needs more, it is two demos.

## Verify before wiring in

Actually look at the frames — a zero exit code only means VHS did not crash. Reading the `.gif`
directly is useless: it renders **frame one only**, which is a bare prompt.

```
scripts/contact-sheet.sh assets/demo.gif /tmp/sheet.png 3 4     # whole demo, one image
ffprobe -v error -show_entries stream=width,height \
        -show_entries format=duration,size -of default=nw=1 assets/demo.gif
ffmpeg -v error -ss <seconds> -i assets/demo.gif -frames:v 1 /tmp/frame.png -y   # one beat, full size
```

Read the sheet first — it shows structure (every act present, nothing wrapped, no dead space) in
one image. Drop to a full-size frame only when you need to read small text.

Ignore a single frame showing a half-drawn pasted line: a large write can straddle a frame
boundary. Check the next frame before calling it a bug.

- Does it tell the story, or is it a cursor wandering a menu?
- File size under ~3MB. Over that: drop `Framerate` to 20, cut a beat, or narrow the window.
- Any real hostname, path, token, or `$USER` on screen? Re-record.
- Does it loop cleanly?

## Gotchas

- **`Wait+Screen` only matches what is still on the visible screen.** Once output scrolls off,
  every later wait times out even though its text was printed — and the error is misleading
  ("last value was:" shows a stale line). Wipe between acts:

  ```
  Hide
  Type "clear" Enter
  Show
  ```

  Verified on 0.11.0: a 45-line screen fails, a 5-line screen passes. Any tape longer than about
  one screenful needs act wipes, which read as scene changes anyway.
- VHS cannot type `alt+<digit>`. Reach the same state another way and comment why.
- `Require` fails the run early with a clear message — declare every binary the tape assumes.
- Screenshots flush on the *next* frame; a `Sleep` after the last one or it is dropped.
- `Set Theme` must precede any output, or the first frames render in the default theme.

See `references/vhs.md` for the command surface.
