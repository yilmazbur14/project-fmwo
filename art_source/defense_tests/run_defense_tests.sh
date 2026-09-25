#!/usr/bin/env bash
# Runs the defence suite, one mode per process, and prints a line per mode.
#   GODOT=/path/to/Godot.exe bash art_source/defense_tests/run_defense_tests.sh [mode ...]
# With no modes it runs the default set below. A mode that takes an argument is written the way it
# is passed, for example "smoke fight=mason" or "kill_shove fight=eric tier=super", quoted.
# Full output per run lands in art_source/defense_tests/out/, or in OUT_DIR when it is set, so runs
# made at the same time can each keep their own logs:
#   OUT_DIR=/some/folder GODOT=/path/to/Godot.exe bash art_source/defense_tests/run_defense_tests.sh [mode ...]
set -u

GODOT="${GODOT:-godot}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$HERE/../.." && pwd)"
SCRIPT="res://art_source/defense_tests/verify_defense.gd"
OUT="${OUT_DIR:-$HERE/out}"
mkdir -p "$OUT"

# These mash the finisher prompt or wait out the pause screen's resume grace, both of which are
# counted in real seconds.
REAL_TIME="super_uppercut gamepad_mash knockback knockback_boss kill_shove mash_tiers_live scripted mine_mash pause_mash pause_dialogue pause_no_leak vs_card entrance beam_rush_live matt_entrance matt_deafen burak_entrance burak_laugh danny_entrance danny_sleep danny_sumo"

DEFAULT_MODES=(
	stamina baseline block_eric behind grab_block dash_through
	guard_break guard_break_timeout guard_break_grab guard_break_lose
	parry_rules no_block parry_window parry_cue parry_freeze parry_rearm parry_streak
	"broken_combo fight=burak" "broken_combo fight=eric" "broken_combo fight=computah" "broken_combo fight=matt"
	"broken_combo fight=mason" "broken_combo fight=josh" "broken_combo fight=danny" "broken_combo fight=carter_akuma"
	"broken_combo fight=liam" "broken_combo fight=jordan" "broken_combo fight=greyson"
	parry_projectiles grab_parry stagger stagger_chain stagger_win stagger_lose tells
	dodge_ring dodge_near dodge_bosses dash_recovery dash_spam
	hype hype_inert super_uppercut gamepad_mash prompt_overlap
	knockback
	"knockback_boss fight=computah" "knockback_boss fight=mason"
	"knockback_boss fight=jordan" "knockback_boss fight=liam"
	"kill_shove fight=eric tier=normal" "kill_shove fight=eric tier=super"
	"auto_finisher tier=normal" "auto_finisher tier=super" auto_kill clone_cadence
	beam_rush beam_rush_live carter_hud
	messatsu messatsu_live "messatsu_live tier=death" "messatsu_live tier=defeated"
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
	punch_contact y_sort_eric v2_cadence delayed_slam whirl_lunges hug_mixup hug_reach break_gauge break_entry
	mash_tiers mash_tiers_live juggle "juggle_kill tier=1" "juggle_kill tier=2" "juggle_kill tier=3"
	"break_gauge fight=mason" "break_entry fight=mason" "juggle fight=mason"
	"juggle_kill fight=mason tier=1" "juggle_kill fight=mason tier=3"
	mason_contact "mason_contact tier=won" mason_combined "mason_combined tier=won"
	mason_bots "mason_bots tier=still"
	juggle_super reflect_auto_v2 sword_gate
	mine_trap mine_mash computah_overload
	"smoke fight=eric ver=1" "approach fight=eric ver=2"
	pause_basic pause_hitstop pause_freeze pause_mash pause_barrage pause_dialogue
	pause_no_leak pause_blocked pause_restart pause_quit pause_beam_rush pause_messatsu
	"vs_card fight=eric" "vs_card fight=computah" "vs_card fight=mason"
	"vs_card fight=josh" "vs_card fight=carter" "vs_card fight=liam"
	"vs_card fight=jordan"
	entrance
	drift inferno "inferno tier=death" "inferno tier=defeated" static_dodge
	"smoke fight=liam phase=2" "blocks fight=liam phase=2" "approach fight=liam phase=2"
	"combined fight=liam"
	josh_layout
	"smoke fight=matt" "blocks fight=matt" "approach fight=matt" "vs_card fight=matt"
	"knockback_boss fight=matt"
	matt_pass_through matt_bounces matt_trueshot matt_yell matt_entrance
	"matt_bots tier=still" "matt_bots tier=parry" "matt_bots tier=circle"
	matt_glass_row matt_glass_damage matt_glass_release matt_deafen
	"matt_glass_bots tier=perfect" "matt_glass_bots tier=human" "matt_glass_bots tier=random"
	"matt_glass_bots tier=none" "matt_glass_bots tier=wobble"
	burak_barrels burak_volley burak_ramp
	"burak_bots tier=walk_full" "burak_bots tier=walk_cap" "burak_bots tier=dash_cap"
	"burak_bots tier=dash1_cap" "burak_bots tier=nopunch" "burak_bots tier=partial"
	"burak_bots tier=walk_full_human" "burak_bots tier=walk_cap_human" "burak_bots tier=dash1_human"
	burak_entrance burak_laugh
	"burak_shots tier=parry" "burak_shots tier=block" "burak_shots tier=hit"
	"burak_cutlass tier=walk" "burak_cutlass tier=guard" "burak_cutlass tier=dash"
	"burak_cutlass tier=parry" "burak_cutlass tier=mixed"
	"smoke fight=burak" "blocks fight=burak" "approach fight=burak" "vs_card fight=burak"
	"knockback_boss fight=burak"
	"juggle fight=burak" "juggle_kill fight=burak tier=1" "juggle_kill fight=burak tier=2"
	"juggle_kill fight=burak tier=3" "break_entry fight=burak" "gauge_extra fight=burak"
	danny_entrance "danny_sleep tier=afk" "danny_sleep tier=hurry" "danny_sleep tier=slow" danny_spit
	"danny_headbutt tier=parry" "danny_headbutt tier=hit" "danny_headbutt tier=guard"
	"danny_headbutt tier=from_sleep" "danny_headbutt tier=from_slams" "danny_headbutt tier=ropes"
	"danny_slams tier=parry" "danny_slams tier=hit" "danny_slams tier=dash" "danny_slams tier=walk"
	"danny_slams tier=step" "danny_slams tier=still" "danny_slams tier=rooted"
	"danny_sumo tier=win" "danny_sumo tier=loss" "danny_sumo tier=skip" "danny_sumo tier=table"
	"smoke fight=danny" "blocks fight=danny" "approach fight=danny" "vs_card fight=danny"
	"knockback_boss fight=danny"
	"break_gauge fight=danny" "break_entry fight=danny" "juggle fight=danny"
	"juggle_kill fight=danny tier=1" "juggle_kill fight=danny tier=2" "juggle_kill fight=danny tier=3"
	"gauge_extra fight=danny"
	"bounds fight=eric" "bounds fight=computah" "bounds fight=carter" "bounds fight=carter_akuma"
	"bounds fight=josh" "bounds fight=mason" "bounds fight=jordan" "bounds fight=liam"
	"bounds fight=matt" "bounds fight=burak" "bounds fight=danny" "bounds fight=greyson"
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
