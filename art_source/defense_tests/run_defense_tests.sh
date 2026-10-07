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
REAL_TIME="super_uppercut gamepad_mash knockback knockback_boss kill_shove mash_tiers_live scripted mine_mash pause_mash pause_dialogue pause_no_leak vs_card entrance beam_rush_live matt_entrance matt_deafen matt_deafen_rate burak_entrance burak_laugh danny_entrance danny_sleep danny_sumo jordan_finale jordan_god jordan_maze jordan_kegs jordan_portals jordan_circle josh_summon jordan_final_beam champion_ending jordan_wheel"

DEFAULT_MODES=(
	stamina stamina_costs tired_popup baseline block_eric behind grab_block dash_through
	guard_break guard_break_timeout guard_break_grab guard_break_lose
	parry_rules no_block parry_window parry_cue parry_freeze parry_rearm parry_streak
	"broken_combo fight=burak" "broken_combo fight=eric" "broken_combo fight=computah" "broken_combo fight=matt"
	"broken_combo fight=mason" "broken_combo fight=josh" "broken_combo fight=danny" "broken_combo fight=carter_akuma"
	"broken_combo fight=liam" "broken_combo fight=jordan" "broken_combo fight=greyson"
	combo_art "combo_art tier=off" "combo_art tier=missing"
	combo_reset "combo_reset fight=carter_akuma"
	"pow_always_dazes fight=burak" "pow_always_dazes fight=eric" "pow_always_dazes fight=computah" "pow_always_dazes fight=greyson"
	"pow_always_dazes fight=matt" "pow_always_dazes fight=mason" "pow_always_dazes fight=josh" "pow_always_dazes fight=danny"
	"pow_always_dazes fight=carter_akuma" "pow_always_dazes fight=liam" "pow_always_dazes fight=liam_elements"
	"pow_always_dazes fight=jordan"
	"pow_always_dazes fight=matt tier=settle" "pow_always_dazes fight=danny tier=settle" "pow_always_dazes fight=josh tier=settle"
	"pow_always_dazes fight=carter_akuma tier=settle" "pow_always_dazes fight=jordan tier=settle" "pow_always_dazes fight=eric tier=settle"
	"pow_always_dazes fight=mason tier=race" "pow_always_dazes fight=eric tier=race" "pow_always_dazes fight=matt tier=race"
	parry_projectiles grab_parry stagger stagger_chain stagger_win stagger_lose tells
	dodge_ring dodge_near dodge_bosses dash_recovery dash_spam
	hype hype_inert super_uppercut gamepad_mash prompt_overlap
	knockback
	"knockback_boss fight=computah" "knockback_boss fight=mason"
	"knockback_boss fight=jordan" "knockback_boss fight=liam"
	"kill_shove fight=eric tier=normal" "kill_shove fight=eric tier=super"
	"auto_finisher tier=normal" "auto_finisher tier=super" auto_kill clone_cadence
	beam_rush beam_rush_live carter_hud carter_recover_spot carter_caster_see_through carter_strike_iframes carter_chain
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
	mash_tiers mash_tiers_live mash_rates juggle "juggle_kill tier=1" "juggle_kill tier=2" "juggle_kill tier=3"
	"break_gauge fight=mason" "break_entry fight=mason" "juggle fight=mason"
	"juggle_kill fight=mason tier=1" "juggle_kill fight=mason tier=3"
	mason_contact "mason_contact tier=won" mason_combined "mason_combined tier=won"
	mason_bots "mason_bots tier=still" mason_back_rope
	mason_pitch "mason_pitch tier=reads" "mason_pitch tier=fake" "mason_pitch tier=knockdown" "mason_pitch tier=release"
	"mason_pitch tier=release_won" "mason_pitch tier=fair" "mason_pitch tier=grace" mason_rain
	juggle_super reflect_auto_v2 eric_window_daze sword_gate sword_path slam_point entrance_hud
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
	"combined fight=liam" spin_tell spin_reach
	"bixby_flyby tier=layout" "bixby_flyby tier=still" "bixby_flyby tier=edges" "bixby_flyby tier=run"
	"bixby_flyby tier=late" "bixby_flyby tier=perfect" "bixby_flyby tier=draw" "bixby_flyby tier=break"
	"bixby_flyby tier=release" "bixby_flyby tier=art" "break_entry fight=liam" "gauge_extra fight=liam"
	bixby_inside
	liam_takeover liam_waves liam_pillar liam_window liam_ice liam_tremors liam_maze_bot liam_zip liam_firestorm liam_firestorm_bot
	"liam_lunge tier=flow" "liam_lunge tier=reaction" "liam_lunge tier=impale" "liam_lunge tier=parry" "liam_lunge tier=death"
	liam_loop liam_tsunami_gate liam_firestorm_gate
	"break_gauge fight=liam_elements" "break_entry fight=liam_elements" "juggle fight=liam_elements"
	"juggle_kill fight=liam_elements tier=1" "juggle_kill fight=liam_elements tier=3" "gauge_extra fight=liam_elements"
	josh_layout josh_wild_cards josh_summon
	"josh_hands tier=parry" "josh_hands tier=dash" "josh_hands tier=walk" "josh_hands tier=hit"
	"josh_hands tier=edges" "josh_hands tier=track" "josh_hands tier=portals" "josh_hands tier=break"
	"josh_hands tier=release" "josh_hands tier=rotation" "josh_hands tier=art" "josh_hands tier=back_rope" "josh_hands tier=lead"
	"josh_guns tier=layer" "josh_guns tier=rows" "josh_guns tier=hit" "josh_guns tier=walk" "josh_guns tier=dash"
	"josh_guns tier=edges" "josh_guns tier=escape" "josh_guns tier=break" "josh_guns tier=release" "josh_guns tier=art"
	"josh_monte tier=parry" "josh_monte tier=bite" "josh_monte tier=hit" "josh_monte tier=timing" "josh_monte tier=placement"
	"josh_monte tier=lock" "josh_monte tier=break" "josh_monte tier=release" "josh_monte tier=rotation" "josh_monte tier=window" "josh_monte tier=art"
	"smoke fight=matt" "blocks fight=matt" "approach fight=matt" "vs_card fight=matt"
	"knockback_boss fight=matt"
	matt_pass_through matt_bounces matt_trueshot matt_yell matt_entrance
	"matt_bots tier=still" "matt_bots tier=parry" "matt_bots tier=circle"
	matt_glass_row matt_glass_damage matt_glass_release matt_deafen
	"matt_glass_bots tier=perfect" "matt_glass_bots tier=human" "matt_glass_bots tier=random"
	"matt_glass_bots tier=none" "matt_glass_bots tier=wobble"
	matt_scream matt_glass_rows matt_deafen_rate matt_spots matt_badge matt_yell_chain matt_cover
	matt_echo matt_echo_gaps matt_echo_disc matt_echo_parry matt_echo_boomburst matt_echo_feint matt_echo_stamina
	matt_echo_lazy matt_echo_rotation "matt_echo_bots tier=perfect" "matt_echo_bots tier=human" matt_break_only
	burak_barrels burak_volley burak_ramp
	"burak_bots tier=walk_full" "burak_bots tier=walk_cap" "burak_bots tier=dash_cap"
	"burak_bots tier=dash1_cap" "burak_bots tier=nopunch" "burak_bots tier=partial"
	"burak_bots tier=walk_full_human" "burak_bots tier=walk_cap_human" "burak_bots tier=dash1_human"
	burak_entrance burak_laugh burak_hint burak_laugh_auto
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
	"danny_slams tier=walk" "danny_slams tier=step" "danny_slams tier=trap" "danny_slams tier=parry5"
	"danny_slams tier=finisher5" "danny_slams tier=dash" "danny_slams tier=hit" "danny_slams tier=press"
	"danny_slams tier=top" "danny_slams tier=far_left" "danny_slams tier=far_right" "danny_slams tier=react"
	"danny_slams tier=counts" "danny_slams tier=step_off" "danny_slams tier=trail"
	"danny_bump tier=parry" "danny_bump tier=hit" "danny_bump tier=dash" "danny_bump tier=slip"
	"danny_bump tier=ropes" "danny_bump tier=timing" "danny_bump tier=rooted"
	"danny_bump tier=walkout" "danny_bump tier=vdash" "danny_bump tier=through" "danny_bump tier=punish"
	"danny_sumo tier=win" "danny_sumo tier=loss" "danny_sumo tier=skip" "danny_sumo tier=table"
	"smoke fight=danny" "blocks fight=danny" "approach fight=danny" "vs_card fight=danny"
	"knockback_boss fight=danny"
	"break_gauge fight=danny" "break_entry fight=danny" "juggle fight=danny"
	"juggle_kill fight=danny tier=1" "juggle_kill fight=danny tier=2" "juggle_kill fight=danny tier=3"
	"gauge_extra fight=danny"
	"bounds fight=eric" "bounds fight=computah" "bounds fight=carter" "bounds fight=carter_akuma"
	"bounds fight=josh" "bounds fight=mason" "bounds fight=jordan" "bounds fight=liam"
	"bounds fight=matt" "bounds fight=burak" "bounds fight=danny" "bounds fight=greyson"
	"jordan_kaiju tier=layout" "jordan_kaiju tier=intro" "jordan_kaiju tier=breath" "jordan_kaiju tier=stomp"
	"jordan_kaiju tier=punish" "jordan_kaiju tier=recoil" "jordan_kaiju tier=occlusion" "jordan_kaiju tier=defeat"
	"jordan_kaiju tier=lazy" "jordan_kaiju tier=art art=raw"
	jordan_final_beam
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
