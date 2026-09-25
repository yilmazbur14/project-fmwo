extends RefCounted

# greyson_bomb (coder C): the spirit bomb (GreysonSpiritBomb, GreysonSpiritBombFx) in his test fight, fired from
# Idle on a full meter with the player standing in the ring. Each part loads the fight afresh.
#   watched  the beats on the bomb's own clock - out, in at (960, 800), the arm up, the gather, the grin, the
#            throw, the blast - and the loss at most 6.5 s after the meter filled; a pause mid-gather holding it
#            all; his HUD gone and the player held, facing him on their standing frame; the sphere on his spirit
#            muzzle; the fighters, the ropes and the gates cooled with the light and back after it; white only on
#            the blast's f0, f3 and f6, at least 0.34 s apart and never more than 3 in a second; the player coming
#            apart from the blast's f1 in their facing's row, their sprite hidden from the sheet's f1; one
#            player_lost outro, him in Victory.
#   holds    a held ESC mid-teleport, mid-gather, mid-launch and mid-blast: each lands where the watched bomb
#            ends - the player gone, the light out, the view level, him on his cast spot, one player_lost outro.
#   spared   with playtest_invincible the bomb spares the player: their sprite never hidden, then his meter empty,
#            his HUD back, him home and the player free, and the fight going on from Idle with no outro.

const BODY := "Arena/GreysonScene/GreysonCharacterBody"
const FRAME := 1.0 / 60.0
const STANDING := Vector2(600, 700)
const WHITE_GAP := 0.34
const LONGEST := 6.5
# Where each hold comes in, on the bomb's clock: mid-teleport, mid-gather, mid-launch and mid-blast.
const HOLDS := {"mid-teleport": 0.15, "mid-gather": 2.0, "mid-launch": 4.2, "mid-blast": 5.0}


static func run(t) -> void:
	await watched(t)
	for label in HOLDS:
		await hold(t, label, HOLDS[label])
	await spared(t)


static func enter(t) -> void:
	var outro: Node = t.root.get_node_or_null("FightOutro")
	if outro != null:
		outro.free()
	await t.load_fight("greyson")
	t.boss = t.current_scene.get_node(BODY)
	t.sm = t.boss.state_machine
	t.player.playerHealth = 1000000
	t.sm.on_child_transition(t.sm.current_state, "Idle")
	t.stop_boss_timers()
	t.player.global_position = STANDING
	await t.wait(3)


# A full meter, and the bomb from Idle.
static func fire(t) -> Node:
	t.boss.add_hype(t.boss.HYPE_MAX)
	t.sm.enter_spirit_bomb()
	return t.sm.states["SpiritBomb"]


static func outros(t) -> Array:
	return t.root.get_children().filter(func(node): return node.name.begins_with("FightOutro"))


# What the bomb's light cools: him, the player, the ropes and the gates.
static func lit(t) -> Array:
	return [t.boss, t.player, t.current_scene.get_node("Arena/wallBoundaries"), t.current_scene.get_node("Arena/Gates")]


static func level_view(t) -> bool:
	var view = load("res://Scripts/ScreenView.gd")
	return view.zoom == 1.0 and t.root.canvas_transform == Transform2D.IDENTITY


static func watched(t) -> void:
	await enter(t)
	t.log_p("-- watched, paused once mid-gather")
	var bomb: Node = fire(t)
	var cast: Vector2 = t.sm.BOMB_CAST
	var seen := {"at_cast": false, "hud_gone": false, "held": true, "sphere_on_muzzle": false, "cooled": false,
		"standing": false, "remains_row": -1, "remains_from": -1.0, "hidden_from": -1.0, "white_peaks": [],
		"paused_held": false, "blast_at": -1.0}
	var fx: Node = null
	var paused_once := false
	for i in 900:
		await t.wait(1)
		if bomb.fx != null:
			fx = bomb.fx
		var beat: String = bomb.Beat.keys()[bomb.beat]
		if beat == "IN" or beat == "ARM":
			seen.at_cast = t.boss.global_position == cast
		if beat == "GATHER":
			seen.hud_gone = is_zero_approx(t.boss.health_bar.modulate.a) and is_zero_approx(t.boss.hype_meter.modulate.a)
			if not seen.sphere_on_muzzle:
				seen.sphere_on_muzzle = fx.sphere.global_position == t.boss.muzzle_point(&"spirit")
			if not paused_once and bomb.clock >= 2.0:
				paused_once = true
				var at: Array = [bomb.clock, fx.clock, fx.light_amount, fx.sphere.frame]
				t.paused = true
				await t.wait(30)
				seen.paused_held = at == [bomb.clock, fx.clock, fx.light_amount, fx.sphere.frame]
				t.paused = false
		if beat in ["GATHER", "GRIN", "LAUNCH", "BLAST"]:
			seen.held = seen.held and t.player.is_talking
		if beat == "LAUNCH":
			seen.cooled = lit(t).all(func(item): return item.modulate.is_equal_approx(Color(0.8, 0.88, 1.0)))
		if beat == "BLAST":
			if seen.blast_at < 0.0:
				seen.blast_at = bomb.clock
				var facing_to: Vector2 = t.player.global_position.direction_to(cast)
				seen.standing = t.player.sprite.frame_coords == Vector2i(0, t.player.facing) and t.player.facing == t.player._facing_toward(facing_to)
			if fx.remains.visible and seen.remains_from < 0.0:
				seen.remains_from = bomb.blast_clock
				seen.remains_row = fx.remains.frame_coords.y
			if not t.player.sprite.visible and seen.hidden_from < 0.0:
				seen.hidden_from = bomb.blast_clock
			seen.white_peaks = fx.white_peaks.duplicate()
		if bomb.ended_at >= 0.0:
			break
	await t.wait(3)
	var times: Dictionary = bomb.beat_times
	var expected := {"OUT": 0.0, "IN": 0.3, "ARM": 0.45, "GATHER": 0.95, "GRIN": 3.45, "LAUNCH": 3.95, "BLAST": 4.55}
	var on_clock := true
	for beat in expected:
		on_clock = on_clock and absf(times.get(beat, -1.0) - expected[beat]) <= FRAME + 0.0001
	t.log_p("beats %s, ended at %.3f (total %.2f); %s" % [times, bomb.ended_at, bomb.total_time(), seen])
	t.check(on_clock, "the beats on their clock: out 0, in 0.3, arm 0.45, gather 0.95, grin 3.45, throw 3.95, blast 4.55")
	t.check(bomb.ended_at <= LONGEST and absf(bomb.ended_at - bomb.total_time()) <= FRAME + 0.0001, "the loss %.2f s after the meter filled, no more than %.1f" % [bomb.ended_at, LONGEST])
	t.check(seen.paused_held, "a pause mid-gather holds the bomb, the sphere and the light")
	t.check(seen.at_cast, "he teleports to his cast spot, (960, 800)")
	t.check(seen.hud_gone, "his HUD gone")
	t.check(seen.held and seen.standing, "the player held through it, facing him on their standing frame")
	t.check(seen.sphere_on_muzzle, "the sphere forms on his spirit muzzle")
	t.check(seen.cooled and lit(t).all(func(item): return item.modulate == Color.WHITE), "the fighters, the ropes and the gates cooled with the light, and back after it")
	var peaks: Array = seen.white_peaks
	var apart := peaks.size() == 3
	var most := 0
	for k in peaks.size():
		if k > 0:
			apart = apart and peaks[k] - peaks[k - 1] >= WHITE_GAP
		most = maxi(most, peaks.filter(func(p): return p >= peaks[k] and p < peaks[k] + 1.0).size())
	t.check(apart and most <= 3, "white on f0, f3 and f6 only: %s, at least %.2f s apart, %d in a second at most" % [peaks.map(func(p): return snappedf(p, 0.001)), WHITE_GAP, most])
	t.check(absf(seen.remains_from - 0.10) <= FRAME + 0.0001 and seen.remains_row == t.player.facing, "the player comes apart from the blast's f1, in their facing's row (%.3f, row %d)" % [seen.remains_from, seen.remains_row])
	t.check(absf(seen.hidden_from - 0.18) <= FRAME + 0.0001 and not t.player.sprite.visible, "their sprite hidden from the sheet's f1, and gone for good (%.3f)" % seen.hidden_from)
	var shown: Array = outros(t)
	t.check(shown.size() == 1 and not shown[0].player_won, "one player_lost outro (%d)" % shown.size())
	t.check(t.sm.current_state == t.sm.states["Victory"], "and him in Victory (%s)" % t.sm.current_state.name)


static func hold(t, label: String, at: float) -> void:
	await enter(t)
	t.log_p("-- a held ESC %s (%.2f s in)" % [label, at])
	var bomb: Node = fire(t)
	await t.wait_until(func(): return bomb.clock >= at, 600)
	t.press(KEY_ESCAPE)
	await t.wait_until(func(): return bomb.skipped, 60)
	t.release(KEY_ESCAPE)
	await t.wait(3)
	var shown: Array = outros(t)
	t.log_p("skipped %s at %.3f; the player %s; outros %d; view level %s; he is at %s in %s" % [bomb.skipped, bomb.ended_at, "hidden" if not t.player.sprite.visible else "SHOWN", shown.size(), level_view(t), t.boss.global_position, t.sm.current_state.name])
	t.check(bomb.skipped and not t.player.sprite.visible, "%s: the player gone" % label)
	t.check(bomb.fx == null and lit(t).all(func(item): return item.modulate == Color.WHITE) and level_view(t), "%s: the light out and the view level" % label)
	t.check(t.boss.global_position == t.sm.BOMB_CAST and t.boss.sprite.visible, "%s: him on his cast spot, seen" % label)
	t.check(shown.size() == 1 and not shown[0].player_won and t.sm.current_state == t.sm.states["Victory"], "%s: one player_lost outro, him in Victory" % label)


static func spared(t) -> void:
	await enter(t)
	t.log_p("-- spared: playtest_invincible")
	var progress: Node = t.root.get_node("GameProgress")
	var was: bool = progress.playtest_invincible
	progress.playtest_invincible = true
	var bomb: Node = fire(t)
	var always_seen := true
	var ended := false
	for i in 900:
		await t.wait(1)
		always_seen = always_seen and t.player.sprite.visible
		ended = ended or bomb.ended_at >= 0.0
		if ended and t.sm.current_state != bomb:
			break
	await t.wait(20)
	var hud: float = t.boss.health_bar.modulate.a
	t.log_p("the player always seen %s; hype %.1f; HUD %.2f; he is at %s in %s; talking %s; outros %d" % [always_seen, t.boss.hype, hud, t.boss.global_position, t.sm.current_state.name, t.player.is_talking, outros(t).size()])
	t.check(always_seen, "the bomb spares the player: their sprite never hidden")
	t.check(is_zero_approx(t.boss.hype) and is_equal_approx(hud, 1.0), "his meter empty and his HUD back")
	t.check(t.boss.global_position == t.sm.HOME and t.sm.current_state == t.sm.states["Idle"], "him home, and the fight on from Idle")
	t.check(not t.player.is_talking and outros(t).is_empty(), "the player free, and no outro")
	progress.playtest_invincible = was
