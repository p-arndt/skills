#!/usr/bin/env bash
# Tile a recording into one contact sheet, so a single image shows the whole demo.
#
#   contact-sheet.sh <gif> [out.png] [cols] [rows] [tile-width]
#
# Frame choice is the whole problem. Two obvious approaches both fail:
#
#   - Even sampling lands on dead moments — a prompt just after a `clear`, or a
#     half-typed command — and can miss a short beat entirely.
#   - Scene detection (select='gt(scene,N)') is worse: the biggest pixel change in a
#     terminal recording is a screen wipe, so it returns precisely the empty frames.
#
# So: sample densely, then keep the *fullest* frame in each slice, using PNG size as a
# free proxy for how much text is on screen. Settled screens win over empty ones.
#
# NOTE: colours must be 0xRRGGBB — ffmpeg treats # as a comment inside a filtergraph.
set -euo pipefail

# C locale throughout: under a comma-decimal locale (de_DE et al) awk prints "0,21"
# and the comma splits the ffmpeg filtergraph, which then fails looking for a filter
# named after the fraction. Cost an afternoon once.
export LC_ALL=C

gif="${1:?usage: contact-sheet.sh <gif> [out.png] [cols] [rows] [tile-width]}"
out="${2:-contact-sheet.png}"
cols="${3:-3}"
rows="${4:-4}"
tw="${5:-760}"
n=$(( cols * rows ))

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# ~3 candidates a second is enough to land on every settled screen without the
# extraction itself becoming the slow part.
ffmpeg -v error -i "$gif" -vf "fps=3,scale=${tw}:-1:flags=lanczos" "$tmp/c_%05d.png" -y

cands=("$tmp"/c_*.png)
total=${#cands[@]}
[ "$total" -ge 1 ] || { echo "no frames extracted from $gif" >&2; exit 1; }

size_of() { stat -f%z "$1" 2>/dev/null || stat -c%s "$1"; }

per=$(( (total + n - 1) / n ))
idx=0
for (( i = 0; i < n; i++ )); do
  start=$(( i * per ))
  [ "$start" -ge "$total" ] && break
  end=$(( start + per )); [ "$end" -gt "$total" ] && end=$total
  best=""; best_size=-1
  for (( j = start; j < end; j++ )); do
    s="$(size_of "${cands[$j]}")"
    if [ "$s" -gt "$best_size" ]; then best_size="$s"; best="${cands[$j]}"; fi
  done
  cp "$best" "$(printf '%s/pick_%03d.png' "$tmp" "$idx")"
  idx=$(( idx + 1 ))
done

ffmpeg -v error -start_number 0 -i "$tmp/pick_%03d.png" \
  -vf "tile=${cols}x${rows}:margin=8:padding=8:color=0x1a1420" \
  -frames:v 1 "$out" -y

dur="$(ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$gif")"
echo "$out  (${idx} frames from ${dur}s, ${cols}x${rows}, fullest-in-slice)"
