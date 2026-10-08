extends RefCounted

# Mason's gauge spec for verify_defense.gd's gauge modes (break_gauge, break_entry, juggle, juggle_kill
# and gauge_extra with fight=mason). The keys and the optional statics are listed over GAUGE_FIGHTS_DIR
# there. His Break and juggle predate BossBroken and BossJuggled: his juggle plays on his
# AnimationPlayer, and his gauge is on his own tuned numbers rather than on N reads.

const SPEC := {
	"body": "Arena/MasonScene/MasonCharacterBody",
	# Where he is allowed to stand, with room over his head for a juggle and beside him for the player.
	"home": Vector2(960, 700),
	"light": &"mason_poo_blast",
	"strong": &"carter_elbow_drop",
	"foreign": &"eric_quake_wave_v2",
	"punish_state": "Eat",
	"broken_state": "Broken",
	"cycle_states": ["PooSquat"],
	"defeated_state": "Defeated",
	"reads_to_break": 0,
	"art": "res://Scripts/MasonArtLayout.gd",
	"juggle_via": "animation_player",
	"drives_player": true,
}


# The squat is the case that matters: MasonPooSquat's Exit() leaves its squat timer running, and that
# timer drops a bomb whether or not he is still standing over it.
# Phase two's combined attack goes last: its Break starts his next cycle in phase two, and the cases
# before it all run in phase one.
static func entry_cases(t) -> Array:
	var sm = t.sm
	return [
		["the squat, before the bomb drops", func(): sm.start_cycle(), func(): return sm.current_state.name == "PooSquat" and not sm.squat_timer.is_stopped()],
		["a line being laid", func(): sm.start_cycle(), func(): return sm.current_state.name == "Waddle" and sm.line_bombs.size() >= 2],
		["a nugget shower in the sky", func(): sm.on_child_transition(sm.current_state, "NuggetShower"), func(): return t.hazards_of("NuggetMeteorScript.gd").size() >= 2],
		["Carter's drop in the air", func(): sm.on_child_transition(sm.current_state, "CallCarter"), func():
			var drops: Array = t.hazards_of("CarterElbowDropScript.gd")
			return not drops.is_empty() and drops[0].carter_sprite.visible],
		["waiting for the delivery", func(): sm.on_child_transition(sm.current_state, "AwaitDelivery"), func(): return not t.hazards_of("UberDriverScript.gd").is_empty()],
		["the eat window", func(): sm.on_child_transition(sm.current_state, "Eat"), func(): return sm.current_state.name == "Eat"],
		["between two attacks", func(): sm.on_child_transition(sm.current_state, "Idle"), func(): return sm.current_state.name == "Idle"],
		["phase two's shower, Carter in the air under the rain", func():
			t.boss.phase_two = true
			sm.cycle_phase = 1
			sm.on_child_transition(sm.current_state, "NuggetShower"), func():
			var drops: Array = t.hazards_of("CarterElbowDropScript.gd")
			return sm.states["NuggetShower"].with_carter and not drops.is_empty() and drops[0].carter_sprite.visible and t.hazards_of("NuggetMeteorScript.gd").size() >= 2],
	]
