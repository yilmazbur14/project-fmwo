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

# These mash the finisher prompt or wait out the pause screen's resume grace, both of which are
# counted in real seconds.
REAL_TIME="super_uppercut gamepad_mash knockback knockback_boss kill_shove mash_tiers_live scripted mine_mash pause_mash pause_dialogue pause_no_leak vs_card entrance beam_rush_live"

DEFAULT_MODES=(
	stamina baseline block_eric behind grab_block dash_through
	guard_break guard_break_timeout guard_break_grab guard_break_lose
	parry_rules parry_window parry_cue parry_freeze parry_rearm parry_streak
	parry_projectiles grab_parry stagger stagger_chain stagger_win stagger_lose tells
	dodge_ring dodge_near dodge_bosses dash_recovery dash_spam
	hype hype_inert super_uppercut gamepad_mash prompt_overlap
	knockback
	"knockback_boss fight=computah" "knockback_boss fight=mason"
	"knockback_boss fight=jordan" "knockback_boss fight=liam"
	"kill_shove fight=eric tier=normal" "kill_shove fight=eric tier=super"
	"auto_finisher tier=normal" "auto_finisher tier=super" auto_kill clone_cadence
	beam_rush beam_rush_live
	status "status_end tier=death" "status_end tier=fight_over" status_dialogue
	locked "locked_end tier=death" "locked_end tier=fight_over" scripted
	"smoke fight=eric" "smoke fight=computah" "smoke fight=carter"
	"smoke fight=mason" "smoke fight=jordan" "smoke fight=liam"
	"smoke fight=josh"
	"blocks fight=computah" "blocks fight=carter" "blocks fight=mason"
	"blocks fight=jordan" "blocks fight=liam" "blocks fight=josh"
	"dodge_rollout fight=carter" "dodge_rollout fight=computah" beam
	dash_v2 dash_recovery_v2 dash_spam_v2 dash_parry
	"dash_legacy fight=computah" "dash_legacy fight=mason"
	"dash_layers fight=eric" "dash_layers fight=computah" "dash_layers fight=mason"
	"dash_layers fight=josh" "dash_layers fight=carter" "dash_layers fight=liam"
	"dash_layers fight=jordan"
	"punch_reach fight=eric" "punch_reach fight=mason" "punch_reach fight=jordan"
	punch_contact y_sort_eric v2_cadence delayed_slam whirl_lunges hug_mixup break_gauge break_entry
	mash_tiers mash_tiers_live juggle "juggle_kill tier=1" "juggle_kill tier=2" "juggle_kill tier=3"
	"break_gauge fight=mason" "break_entry fight=mason" "juggle fight=mason"
	"juggle_kill fight=mason tier=1" "juggle_kill fight=mason tier=3"
	juggle_super reflect_auto_v2 sword_gate
	phase_cut p2_mixup p2_leap p2_grab_escape "smoke fight=eric phase=2"
	mine_trap mine_mash computah_overload
	"smoke fight=eric ver=1" "approach fight=eric ver=2"
	pause_basic pause_hitstop pause_freeze pause_mash pause_barrage pause_dialogue
	pause_no_leak pause_blocked pause_restart pause_quit pause_beam_rush
	"vs_card fight=eric" "vs_card fight=computah" "vs_card fight=mason"
	"vs_card fight=josh" "vs_card fight=carter" "vs_card fight=liam"
	"vs_card fight=jordan"
	entrance
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
	result="$(grep -o 'RESULT mode=[a-z0-9_]* fails=[0-9]*' "$OUT/$name.log" | tail -1)"
	errors="$(grep -c 'SCRIPT ERROR\|Parse Error' "$OUT/$name.log")"
	fails="$(echo "$result" | grep -o '[0-9]*$')"
	total=$((total + ${fails:-1}))
	printf "%-38s %-34s script_errors=%s\n" "$entry" "${result:-no result}" "$errors"
done
echo "== total failures: $total"
exit $((total > 0))
