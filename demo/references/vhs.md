# VHS command surface

Verified against `vhs 0.11.0` (`vhs manual`, `vhs new`). Check `vhs --version` if something
below is rejected.

## Commands

| Command | Notes |
|---|---|
| `Output <path>.(gif\|webm\|mp4)` | Repeatable — one tape can emit several formats. |
| `Require <program>` | Fails the run early if missing. Declare every binary the tape assumes. |
| `Set <setting> <value>` | Must come before output begins. |
| `Sleep <time>` | `2s`, `1500ms`. |
| `Type "<string>"` | Respects `TypingSpeed`. |
| `Enter Tab Space Escape Backspace Delete Insert` | All take an optional `[repeat]`. |
| `Up Down Left Right PageUp PageDown` | Optional `[repeat]` — `Down 3`. |
| `ScrollUp ScrollDown` | Optional `[repeat]`. |
| `Ctrl[+Alt][+Shift]+<char>` | `Ctrl+o`, `Ctrl+Shift+c`. |
| `Alt+<key>` | **`Alt+<digit>` does not work.** Reach the state another way, comment why. |
| `Hide` / `Show` | Everything between is executed but not recorded. |
| `Wait[+Screen][@<timeout>] /<regexp>/` | Blocks until the regex matches. `Wait+Screen@10s /READY/`. |
| `Screenshot <path>.png` | Captures the current frame. |
| `Copy "<string>"` / `Paste` | Puts the whole string on screen in one frame. Uses the **real system clipboard** — recording overwrites the user's. `Copy` needs a literal. |
| `Source <path>.tape` | Include another tape. Also how a driver feeds in a value generated at record time: write `Copy "..."` to a fragment, `Source` it. Path resolves from vhs's cwd. |

## Settings

| Setting | House value | |
|---|---|---|
| `Shell` | `"bash"` | Never the user's shell — their prompt, aliases and theme would leak in. |
| `FontSize` | `15` | |
| `FontFamily` | — | Leave default; a missing font silently falls back and shifts layout. |
| `Width` / `Height` | `1500x800` TUI · `1200x900` CLI | Pixels, not cells. |
| `Padding` | `26` | |
| `Margin` / `MarginFill` | `18` / `"#1a1420"` | `Margin` does nothing unless `MarginFill` is set. |
| `BorderRadius` | `10` | |
| `Theme` | `"Catppuccin Mocha"` | `vhs themes` lists all. Set before any output. |
| `TypingSpeed` | `55ms` | Default 50ms. Slower reads as deliberate, faster as frantic. |
| `Framerate` | `24` | Drop to `20` to shrink an oversized GIF. |
| `PlaybackSpeed` | — | Prefer fixing the beats over speeding up the tape. |
| `LoopOffset` | — | `<float>%` — starts the loop past the intro so it opens on the good part. |
| `WindowBar` / `WindowBarSize` | — | `Rings`, `RingsRight`, `Colorful`, `ColorfulRight`. Unused in house style. |
| `LetterSpacing` / `LineHeight` | — | Leave alone. |

## CLI

```
vhs <tape>              record
vhs validate <tape>     parse-check without recording — run before every record
vhs themes              list themes
vhs record              interactively capture a tape from real keystrokes
vhs new <name>          template with inline docs
vhs publish <gif>       upload to vhs.charm.sh
```

`vhs record` is the fastest way to draft a TUI tape: drive the tool by hand once, then clean up
the generated keystrokes and replace every `Sleep` with a `Wait+Screen`.

## Timing

`Wait+Screen` matches only against the **currently visible screen**, not scrollback. A tape that
prints more than one screenful will see every wait after that point time out, reporting a stale
"last value". Insert a hidden `clear` between acts.

`Wait+Screen` defaults to a 5s timeout; raise it with `@` when a build or connection is in the
path. A timeout aborts the run, which is the correct behaviour — a tape that silently records
the wrong screen is worse than one that fails.

Pattern per beat:

```
Type "some command" Enter
Wait+Screen /expected output/    # ready
Sleep 2s                         # readable
Screenshot assets/screens/beat.png
```

## Sizing

GIF size scales with `Width × Height × Framerate × duration`. In order of least damage:
drop `Framerate` to 20 → cut a beat → narrow the window → shorten sleeps. Never `PlaybackSpeed`
as a size fix; it makes the demo unreadable while barely helping.
