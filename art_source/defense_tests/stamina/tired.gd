extends RefCounted

# tired_popup: the TIRED! word CombatPopupUI puts over the player's head when the stamina bar refuses a dash or a
# parry press (the user, 2026-09-27), beside the bar's red flash and the tired breath. --fixed-fps 60.
#   dash      on Eric's fight, a punch landed and the combo counter up over the head: a refused dash puts TIRED!
#             up over the counter, centred on the head, clear of the counter and of the HUD
#             (DefenseHypeArtLayout.POPUP_KEEP_OUT, which has to be CarterArtLayout.HUD_KEEP_OUT's rects), in the
#             stamina bar's low-look colours
#   parry     a refused parry press with it still up holds that one: the same word, not a second
#   mash      a second of dash and parry presses on an empty bar: one TIRED! the whole time, never fading and never
#             dropping back, then gone once the presses stop
#   corners   in the ring's bottom-left corner it stands clear above the hearts and stamina; below the boss's bar
#             block, where its rise would reach the block, it goes under the feet
#   brawl     in Greyson's Punch-Out brawl, the player drawn twice the size from behind: over the top of their hair
#             as the sheet draws it, centred on it

const DefenseHypeArtLayout := preload("res://Scripts/DefenseHypeArtLayout.gd")
const FinisherArtLayout := preload("res://Scripts/FinisherArtLayout.gd")
const ScreenView := preload("res://Scripts/ScreenView.gd")
const BRAWL := "res://art_source/defense_tests/greyson/brawl.gd"

const FRAME := 1.0 / 60.0
const WORD_LIFE := DefenseHypeArtLayout.POPUP_RISE_TIME + DefenseHypeArtLayout.POPUP_HOLD_TIME + DefenseHypeArtLayout.POPUP_FADE_TIME


static func run(t) -> void:
	load(t.PLAYER_DEFENSE).BLOCKING_ENABLED = false
	t.check(DefenseHypeArtLayout.POPUP_KEEP_OUT == load("res://Scripts/CarterArtLayout.gd").HUD_KEEP_OUT,
		"the words' HUD keep-outs are the ones carter_hud measures off the live HUD")
	await t.load_eric()
	t.park_eric()
	t.health_ok()
	await dash(t)
	await parry(t)
	await mash(t)
	await corners(t)
	await brawl(t)


# The words up now of `kind`.
static func words(t, kind := &"tired") -> Array:
	return t.player.get_parent().get_node("CanvasLayer/CombatPopups").popups.filter(func(p): return p.kind == kind)


static func rect_of(word: Dictionary) -> Rect2:
	return Rect2(word.node.position, word.size)


# An empty bar that stays empty: the refill held off.
static func empty(t) -> void:
	t.defense._set_stamina(0.0)
	t.defense.last_spend_time = t.defense.clock + 100.0


# Nothing of the last word left, and no dash cooling down, which a dash press would be refused for silently.
static func settled(t) -> void:
	await t.wait_until(func(): return words(t).is_empty() and not t.defense.is_dash_cooling_down(), roundi(WORD_LIFE / FRAME) + 60)


# Clear of the HUD by the clearance, and whole on the screen.
static func clear_of_hud(t, rect: Rect2) -> bool:
	var screen: Rect2 = t.player.get_viewport_rect()
	if not screen.encloses(rect):
		return false
	for keep_out in DefenseHypeArtLayout.POPUP_KEEP_OUT:
		if keep_out.grow(DefenseHypeArtLayout.POPUP_HUD_CLEARANCE).intersects(rect):
			return false
	return true


static func dash(t) -> void:
	t.log_p("-- a refused dash, the combo counter up")
	var counter: Control = t.player.get_parent().get_node("CanvasLayer/ComboCounter")
	t.boss.boss_health = t.boss.get_max_health()
	t.sm.parry_stagger(60.0, t.boss.global_position)
	await t.wait(5)
	for timer in t.boss.find_children("*", "Timer", true, false):
		timer.stop()
	t.hold_gauge()
	t.player.combo.reset()
	t.place_under(t.boss.get_finisher_hurtbox())
	await t.wait(6)
	await t.swing_any()
	empty(t)
	t.tap(KEY_W)
	await t.wait(2)
	var up: Array = words(t)
	var counter_up: bool = counter.visible and counter.modulate.a > 0.5 and counter.text == "1 HIT"
	t.check(up.size() == 1 and counter_up, "TIRED! up, with the counter's 1 HIT (%d words, the counter up %s)" % [up.size(), counter_up])
	if up.size() != 1:
		return
	var word: Dictionary = up[0]
	var label: Label = word.node
	var spec: Dictionary = DefenseHypeArtLayout.popup(&"tired")
	t.check(label.text == "TIRED!" and label.get_theme_font_size("font_size") == 44 and spec.colors.has(label.get_theme_color("font_color")),
		"it says TIRED! at 44 in the stamina bar's low-look colours (%s, %d, %s)" % [label.text, label.get_theme_font_size("font_size"), label.get_theme_color("font_color")])
	await t.wait(roundi(DefenseHypeArtLayout.POPUP_RISE_TIME / FRAME) + 2)
	var rect := rect_of(word)
	var box := Rect2(counter.position, counter.size)
	var head: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_HEAD)
	t.log_p("TIRED! at %s, the counter at %s, the head on screen %s" % [rect, box, head])
	t.check(not rect.intersects(box) and rect.end.y <= box.position.y, "stacked over the counter, not on it")
	t.check(absf(rect.get_center().x - head.x) <= 1.0 and rect.end.y <= head.y - DefenseHypeArtLayout.POPUP_GAP + 1.0, "centred over the head")
	t.check(clear_of_hud(t, rect), "clear of the HUD and whole on the screen")


static func parry(t) -> void:
	t.log_p("-- a refused parry press, TIRED! still up")
	var before: Array = words(t)
	empty(t)
	t.tap(KEY_SHIFT)
	await t.wait(2)
	var after: Array = words(t)
	t.check(before.size() == 1 and after.size() == 1 and after[0].node == before[0].node, "the same word held, not a second (%d before, %d after)" % [before.size(), after.size()])
	t.log_p("-- a refused parry press on its own")
	await settled(t)
	t.player.combo.reset()
	empty(t)
	t.tap(KEY_SHIFT)
	await t.wait(2)
	var up: Array = words(t)
	var head: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var rect: Rect2 = rect_of(up[0]) if up.size() == 1 else Rect2()
	# A pixel either way for the word's snap to whole pixels.
	t.check(up.size() == 1 and absf(rect.get_center().x - head.x) <= 1.0 and rect.end.y <= head.y - DefenseHypeArtLayout.POPUP_GAP + 1.0,
		"TIRED! up over the head (%d words, at %s, the head %s)" % [up.size(), rect, head])


static func mash(t) -> void:
	t.log_p("-- mashing dash and parry on an empty bar")
	await settled(t)
	empty(t)
	var most := 0
	var nodes := {}
	var faded := false
	var dropped := 0.0
	var last_y := INF
	for i in 60:
		if i % 3 == 0:
			t.tap(KEY_W if i % 6 == 0 else KEY_SHIFT)
		await t.physics_frame
		var up: Array = words(t)
		most = maxi(most, up.size())
		for word in up:
			nodes[word.node.get_instance_id()] = true
			faded = faded or word.node.modulate.a < 1.0
			if last_y != INF:
				dropped = maxf(dropped, word.node.position.y - last_y)
			last_y = word.node.position.y
	t.log_p("mashed: at most %d words, %d nodes, faded %s, dropped back %.0f px" % [most, nodes.size(), faded, dropped])
	t.check(most == 1 and nodes.size() == 1, "one TIRED! the whole time")
	t.check(not faded and dropped <= 0.0, "held up: never fading, never dropping back")
	var gone: bool = await t.wait_until(func(): return words(t).is_empty(), roundi(WORD_LIFE / FRAME) + 10)
	t.check(gone, "and gone once the presses stop")


static func corners(t) -> void:
	var ring: Rect2 = t.player.ring_origins
	t.log_p("-- the bottom-left corner, over the hearts and stamina")
	await settled(t)
	await t.settle_player(Vector2(ring.position.x, ring.end.y))
	empty(t)
	t.tap(KEY_W)
	# Its first frames, before it rises: as low as it goes.
	await t.wait(2)
	var low: Array = words(t)
	var head: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_HEAD)
	var height := 0.0
	if low.size() == 1:
		var rect := rect_of(low[0])
		height = rect.size.y
		t.log_p("at %s, the head on screen %s: TIRED! at %s" % [t.player.global_position, head, rect])
		t.check(clear_of_hud(t, rect) and rect.end.y <= head.y - DefenseHypeArtLayout.POPUP_GAP + 1.0, "it stands over the head, clear above the hearts and stamina")
	else:
		t.check(false, "TIRED! up in the corner (%d words)" % low.size())
	t.log_p("-- below the boss's bar block")
	await settled(t)
	# The head where the word's rise would reach 40 px under POPUP_TOP_LIMIT's line: into the block, not over the line.
	var head_y: float = DefenseHypeArtLayout.POPUP_TOP_LIMIT + 40.0 + DefenseHypeArtLayout.POPUP_RISE + height + DefenseHypeArtLayout.POPUP_GAP
	var at := Vector2(960, head_y - FinisherArtLayout.PLAYER_HEAD.y)
	await t.settle_player(at)
	empty(t)
	t.tap(KEY_W)
	await t.wait(roundi(DefenseHypeArtLayout.POPUP_RISE_TIME / FRAME) + 2)
	var high: Array = words(t)
	var feet: Vector2 = ScreenView.world_to_screen(t, t.player.global_position + FinisherArtLayout.PLAYER_FEET)
	if high.size() == 1:
		var rect := rect_of(high[0])
		t.log_p("at %s, the feet on screen %s: TIRED! at %s" % [t.player.global_position, feet, rect])
		t.check(clear_of_hud(t, rect) and rect.position.y >= feet.y, "it goes under the feet, clear of the bar block")
	else:
		t.check(false, "TIRED! up under the bar block (%d words)" % high.size())


static func brawl(t) -> void:
	t.log_p("-- Greyson's Punch-Out brawl")
	var brawl_tests = load(BRAWL)
	var fight: Node = await brawl_tests.to_boxing(t, [[&"L", &"R"], [&"R", &"L"], [&"L", &"R"]])
	if fight == null:
		return
	# At a tell, so the word is up and risen before the punch resolves: the guard pose all the while.
	await t.wait_until(func(): return not fight.punch.is_empty() and not fight.punch.resolved and fight.punch.clock < 0.05, 300)
	empty(t)
	t.tap(KEY_SHIFT)
	await t.wait(roundi(DefenseHypeArtLayout.POPUP_RISE_TIME / FRAME) + 2)
	var up: Array = words(t)
	var sprite: Sprite2D = t.player.sprite
	var hair: Vector2 = hair_top(sprite)
	var head: Vector2 = ScreenView.world_to_screen(t, hair)
	var guarding: bool = t.player.is_posed() and sprite.frame_coords.x in [0, 1]
	t.log_p("posed %s on %s, frame %s; the top of the hair on screen %s" % [t.player.is_posed(), sprite.texture.resource_path.get_file(), sprite.frame_coords, head])
	if up.size() == 1:
		var rect := rect_of(up[0])
		t.log_p("TIRED! at %s" % rect)
		# Its gap and its rise over the head texel, which is a few texels over the hair, at the brawl's zoom.
		var over: float = head.y - rect.end.y
		var least: float = DefenseHypeArtLayout.POPUP_GAP + DefenseHypeArtLayout.POPUP_RISE
		t.check(guarding and over >= least and over <= least + 40.0 and absf(rect.get_center().x - head.x) <= 12.0,
			"over the top of their hair as the brawl draws them in their guard, centred on it (%.1f px over it)" % over)
		t.check(clear_of_hud(t, rect), "clear of the HUD and whole on the screen")
	else:
		t.check(false, "TIRED! up in the brawl (%d words)" % up.size())
	brawl_tests.leave(t)


# The top of the opaque part of the frame the sprite shows, at its middle column, where the sprite draws it: read off
# the sheet itself, so it checks the brawl's `head` texel rather than repeating it.
static func hair_top(sprite: Sprite2D) -> Vector2:
	var image: Image = sprite.texture.get_image()
	var cell := Vector2i(image.get_width() / sprite.hframes, image.get_height() / sprite.vframes)
	var origin := Vector2i(sprite.frame_coords.x * cell.x, sprite.frame_coords.y * cell.y)
	for y in cell.y:
		for x in cell.x:
			if image.get_pixel(origin.x + x, origin.y + y).a > 0.0:
				var columns := []
				for x2 in cell.x:
					if image.get_pixel(origin.x + x2, origin.y + y).a > 0.0:
						columns.append(x2)
				var middle: float = (columns.min() + columns.max() + 1) / 2.0
				return sprite.to_global(Vector2(middle, y) - Vector2(cell) / 2.0 + sprite.offset)
	return sprite.global_position
