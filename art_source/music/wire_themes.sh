#!/usr/bin/env bash
# Puts freshly cut theme loops into the game and proves they imported as looping streams.
#
#   GODOT=/path/to/Godot.exe CUT=/where/the/cuts/are bash art_source/music/wire_themes.sh [name ...]
#
# The .import files already carry edit/loop_mode=2, and replacing a source WAV changes its md5, so
# Godot re-imports on its own - no .sample or .md5 needs deleting here. That dance is only for a
# params-only edit, where the source is untouched and Godot sees nothing to redo.
#
# `--import` walks everything under the project, including .claude/worktrees, and quietly appends
# every .dialogue it finds there to locale/translations_pot_files. Those paths do not exist for
# anyone else, so they are stripped again before this returns.
set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/../.." && pwd)"
GODOT="${GODOT:-godot}"
CUT="${CUT:-$HERE/cut}"
MUSIC="$PROJECT/Assets/Audio/Music"

NAMES=("$@")
if [ "${#NAMES[@]}" -eq 0 ]; then
	NAMES=(eric greyson carter mason josh liam jordan danny)
fi

copied=0
for name in "${NAMES[@]}"; do
	src="$CUT/${name}_theme.wav"
	if [ ! -f "$src" ]; then
		echo "!! no cut for $name at $src"
		continue
	fi
	dest="$MUSIC/${name}_theme.wav"
	# A theme the user swapped for a track of their own (Jordan's, 2026-09-28) lives in OriginalThemes/ now.
	[ -f "$MUSIC/OriginalThemes/${name}_theme.wav" ] && dest="$MUSIC/OriginalThemes/${name}_theme.wav"
	cp "$src" "$dest"
	echo "   $name <- $(basename "$src") ($(du -h "$src" | cut -f1))"
	copied=$((copied + 1))
done
echo "== copied $copied"
[ "$copied" -gt 0 ] || exit 1

echo "== importing"
"$GODOT" --headless --path "$PROJECT" --import >/dev/null 2>&1 || true

echo "== stripping worktree paths out of the POT list"
python - "$PROJECT/project.godot" <<'PY'
import io, re, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
m = re.search(r'^(locale/translations_pot_files=PackedStringArray\()(.*)(\)\s*)$', s, re.M)
if not m:
    print("   no POT list; nothing to strip")
    raise SystemExit
items = re.findall(r'"([^"]*)"', m.group(2))
keep = [i for i in items if ".claude/worktrees" not in i]
dropped = len(items) - len(keep)
if dropped:
    s = s[:m.start()] + m.group(1) + ", ".join('"%s"' % i for i in keep) + m.group(3) + s[m.end():]
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("   dropped %d worktree entries, kept %d" % (dropped, len(keep)))
PY

echo "== verifying every theme imports as a looping stream"
"$GODOT" --headless --path "$PROJECT" --script res://art_source/music/loopcheck.gd
