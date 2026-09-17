extends RefCounted

# One attack reaching the player, resolved by player.receive_hit(). It carries the attack's catalog
# entry (AttackCatalog), what is hitting (the source: absorbing and perfect dodges are tracked per
# source), where the attack comes from (the origin: a block needs to face it) and, for attacks a parry
# can stagger, the boss.
# Hitboxes in the "enemy projectile" group carry their id as node metadata, set in their own _ready.
# Mustn't preload PlayerScript.gd, which preloads this: that would be an import cycle.

const AttackCatalog := preload("res://Scripts/AttackCatalog.gd")

enum Result { IGNORED, HIT, BLOCKED, PARRIED, DODGED }

const META_ATTACK := &"attack_id"
# A Vector2 to block against instead of the area's own position.
const META_ORIGIN := &"attack_origin"
const META_BOSS := &"attack_boss"

var attack_id := &""
var source: Object
var origin := Vector2.ZERO
var boss: Node

var damage := 1
var blockable := false
var parryable := false
var weight := AttackCatalog.Weight.NONE
var tell := false
var parry_stagger := false
var from_above := false
var dash_through := false
var grab := false
var bypass_invincibility := false
var hype_loss := true

static var warned_areas := {}


static func make(id: StringName, from: Object, at: Vector2, by: Node = null) -> RefCounted:
	var hit = new()
	hit.attack_id = id
	hit.source = from
	hit.origin = at
	hit.boss = by
	var attack := AttackCatalog.get_attack(id)
	for property in attack:
		hit.set(property, attack[property])
	return hit


static func from_area(area: Area2D) -> RefCounted:
	var id: StringName = area.get_meta(META_ATTACK, &"")
	if id.is_empty():
		var path := str(area.get_path())
		if not warned_areas.has(path):
			warned_areas[path] = true
			push_warning("HitInfo: '%s' has no attack id, treated as untagged" % path)
		id = &"untagged"
	var by: Node = area.get_meta(META_BOSS) if area.has_meta(META_BOSS) else null
	return make(id, area, area.get_meta(META_ORIGIN, area.global_position), by)
