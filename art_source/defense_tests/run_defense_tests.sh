#!/usr/bin/env bash
# Runs the defence suite, one mode per process, and prints a line per mode.
#   GODOT=/path/to/Godot.exe bash art_source/defense_tests/run_defense_tests.sh [mode ...]
# With no modes it runs the default set below. A mode that takes an argument is written the way it
# is passed, for example "smoke fight=mason" or "kill_shove fight=eric tier=super", quoted.
# Full output per run lands in art_source/defense_tests/out/.
set -u

GODOT="${GODOT:-godot}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/../.." && pwd)"
SCRIPT="res://art_source/defense_tests/verify_defense.gd"
OUT="$HERE/out"
mkdir -p "$OUT"

# These mash the finisher prompt, which counts presses in real seconds.
REAL_TIME="super_uppercut knockback knockback_computah knockback_boss kill_shove"

DEFAULT_MODES=(
	stamina baseline block_eric behind grab_block dash_through
	guard_break guard_break_timeout guard_break_grab guard_break_lose
	parry_rules parry_window parry_cue parry_freeze parry_rearm parry_streak
	parry_projectiles grab_parry stagger stagger_chain stagger_win stagger_lose tells
	dodge_ring dodge_near dodge_bosses dash_recovery dash_spam
	hype hype_inert super_uppercut prompt_overlap
	knockback knockback_computah
	"knockback_boss fight=mason" "knockback_boss fight=jordan"
	"knockback_boss fight=liam"
	"kill_shove fight=eric tier=normal" "kill_shove fight=eric tier=super"
	status "status_end tier=death" "status_end tier=fight_over" status_dialogue
	locked "locked_end tier=death" "locked_end tier=fight_over"
	"smoke fight=eric" "smoke fight=greyson" "smoke fight=carter"
	"smoke fight=mason" "smoke fight=jordan" "smoke fight=liam"
	"blocks fight=greyson" "blocks fight=carter" "blocks fight=mason"
	"blocks fight=jordan" "blocks fight=liam"
	"dodge_rollout fight=carter"
)

if [ "$#" -gt 0 ]; then
	MODES=("$@")
else
	MODES=("${DEFAULT_MODES[@]}")
fi

total=0
for entry in "${MODES[@]}"; do
	set -- $entry
	mode="$1"
	shift
	args=("mode=$mode")
	for extra in "$@"; do
		args+=("$extra")
	done
	name="$(echo "$entry" | tr ' =' '__')"
	pace="--fixed-fps 60"
	case " $REAL_TIME " in
		*" $mode "*) pace="--max-fps 60" ;;
	esac
	"$GODOT" --headless $pace --path "$PROJECT" --script "$SCRIPT" -- "${args[@]}" > "$OUT/$name.log" 2>&1
	result="$(grep -o 'RESULT mode=[a-z_]* fails=[0-9]*' "$OUT/$name.log" | tail -1)"
	errors="$(grep -c 'SCRIPT ERROR\|Parse Error' "$OUT/$name.log")"
	fails="$(echo "$result" | grep -o '[0-9]*$')"
	total=$((total + ${fails:-1}))
	printf "%-38s %-34s script_errors=%s\n" "$entry" "${result:-no result}" "$errors"
done
echo "== total failures: $total"
exit $((total > 0))
