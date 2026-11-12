class_name KingdomMapView
extends Node2D

var world
var art: Dictionary = {}
var clock := 0.0
var camera := Vector2(544, 396)
var build_kind := ""
var relocate_id := ""
var hover_cell := Vector2i(-1, -1)
var selected_card := ""
var build_mode := false
var moving := false
var direction := "front"
var font: Font
var reduced_flashes := false

func _process(delta: float) -> void:
	clock += delta
	queue_redraw()

func sprite(id: String, at: Vector2, scale_value: float = 1.0, tint: Color = Color.WHITE, flip: bool = false) -> void:
	if not art.has(id):
		return
	var rect = Rect2(at.floor(), Vector2(64, 64) * scale_value)
	if flip:
		rect.position.x += rect.size.x
		rect.size.x = -rect.size.x
	draw_texture_rect(art[id], rect, false, tint)

func tiled(id: String, origin: Vector2 = Vector2.ZERO, tint: Color = Color.WHITE) -> void:
	for y in range(-1, 6):
		for x in range(-1, 9):
			sprite(id, Vector2(x * 64, y * 64) - Vector2(fmod(origin.x, 64), fmod(origin.y, 64)), 1, tint)

func small_text(message: String, p: Vector2, color: Color = Color("f8edcb"), size: int = 9) -> void:
	if font != null:
		draw_string(font, p.floor(), message, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func actor(p: Dictionary, at: Vector2, walking: bool = false, facing: String = "front", scale_value: float = 1.0) -> void:
	var role = str(world.data.roles[p.role].art)
	var age = world.age_of(p)
	var key = role
	if art.has(role + "_" + facing): key = role + "_" + facing
	var frame = int(clock * 7) % 4 if walking else int(clock * 2) % 2
	if art.has(key + "_%d" % frame): key += "_%d" % frame
	var base_key = role + "_front"
	if p.incapacitated and art.has(base_key + "_defeat"):
		key = base_key + "_defeat"
	elif world.s.mode == "combat" and not world.s.combat.is_empty() and world.s.combat.get("impact", "") == p.id:
		var state_key = base_key + "_" + world.s.combat.get("impact_kind", "attack")
		if art.has(state_key) and (not reduced_flashes or not state_key.ends_with("hurt")): key = state_key
	var bounce = (1 if frame % 2 == 1 else 0) if walking else 0
	var tint = Color.WHITE
	if not p.alive or p.incapacitated: tint = Color(0.5, 0.45, 0.5)
	if age < 18: scale_value *= 0.75 if age >= 8 else 0.5
	foot_shadow(at + Vector2(32, 57) * scale_value, Vector2(8, 2) * scale_value, Color(0.1, 0.18, 0.13, 0.25))
	sprite(key, at - Vector2(0, bounce), scale_value, tint, facing == "left" and not art.has(role + "_left"))

func foot_shadow(center: Vector2, radius: Vector2, color: Color) -> void:
	var points = PackedVector2Array()
	for i in range(16):
		points.append(center + Vector2(cos(i * TAU / 16), sin(i * TAU / 16)) * radius)
	draw_colored_polygon(points, color)

func _draw() -> void:
	if world == null or world.s.is_empty(): return
	match world.s.mode:
		"town", "map": draw_town()
		"home": draw_home()
		"expedition": draw_route()
		"combat": draw_combat()
		"victory": draw_town()

func draw_town() -> void:
	tiled("grass", camera)
	var s = world.s
	# Quiet vegetation at the edges leaves a clear buildable central clearing.
	for y in range(0, 17):
		for x in range(0, 25):
			var pos = Vector2(x * 64, y * 64)
			if (x < 6 or x > 18 or y < 4 or y > 12) and (x * 17 + y * 13) % 4 != 0:
				if Rect2(camera - Vector2(64, 64), Vector2(576, 376)).has_point(pos):
					sprite("oak_tree", pos - camera)
	for road in s.roads:
		var pos = Vector2(float(road[0]) * 32, float(road[1]) * 32) - camera
		if art.has("path"):
			draw_texture_rect_region(art.path, Rect2(pos.floor(), Vector2(32, 32)), Rect2(0, 0, 32, 32))
		else:
			draw_rect(Rect2(pos.floor(), Vector2(32, 32)), Color("bda474"))
	var objects = []
	for b in s.buildings:
		var pos = Vector2(float(b.x) * 32, float(b.y) * 32)
		objects.append({"type": "building", "pos": pos, "b": b})
	var leader = world.person(s.leader)
	var player = Vector2(float(s.player[0]), float(s.player[1]))
	objects.append({"type": "actor", "pos": player - Vector2(32, 56), "p": leader, "walking": moving})
	var index = 0
	for p in world.living():
		if p.id == s.leader or p.mission != "": continue
		var center = Vector2(650 + (index % 5) * 62, 520 + int(index / 5.0) * 58)
		var offset = Vector2(sin(clock * 0.27 + index * 2.3) * 18, cos(clock * 0.2 + index) * 12)
		objects.append({"type": "actor", "pos": center + offset - Vector2(32, 56), "p": p, "walking": true})
		index += 1
	objects.sort_custom(func(a, b): return a.pos.y < b.pos.y)
	for obj in objects:
		var at = obj.pos - camera
		if not Rect2(-64, -64, 576, 376).has_point(at): continue
		if obj.type == "building":
			var b = obj.b
			var id = str(world.definition("buildings", b.kind).art)
			if b.kind == "residence" and art.has("residence_%d" % int(s.rank)): id = "residence_%d" % int(s.rank)
			var obscures = player.y < obj.pos.y + 60 and player.y > obj.pos.y + 14 and absf(player.x - (obj.pos.x + 32)) < 28
			var tint = Color(1, 1, 1, 0.55 if obscures else 1.0)
			if float(b.remaining) > 0: tint = Color(0.7, 0.8, 0.85, 0.6)
			sprite(id, at, 1, tint)
			if float(b.remaining) > 0:
				small_text("%.0fd" % float(b.remaining), at + Vector2(23, 29), Color("fff2b8"))
			elif b.kind == "campfire":
				if art.has("campfire_%d" % (int(clock * 5) % 3)): sprite("campfire_%d" % (int(clock * 5) % 3), at)
		else:
			actor(obj.p, at, obj.walking, direction if obj.p.id == s.leader else "front")
			if obj.p.id == s.leader:
				draw_line(at + Vector2(26, 63), at + Vector2(38, 63), Color("f6da89"), 1)
	if build_mode:
		for x in range(0, 16):
			var gx = x * 32 - fmod(camera.x, 32)
			draw_line(Vector2(gx, 0), Vector2(gx, 248), Color(0.9, 1, 0.8, 0.13))
		for y in range(0, 10):
			var gy = y * 32 - fmod(camera.y, 32)
			draw_line(Vector2(0, gy), Vector2(448, gy), Color(0.9, 1, 0.8, 0.13))
		if hover_cell.x >= 0 and not build_kind.is_empty():
			var cellpos = Vector2(hover_cell) * 32 - camera
			if build_kind == "road":
				draw_rect(Rect2(cellpos, Vector2(32, 32)), Color(0.8, 0.7, 0.4, 0.6))
			else:
				var d = world.definition("buildings", build_kind)
				var valid = world.valid_plot(build_kind, hover_cell.x, hover_cell.y, relocate_id)
				draw_rect(Rect2(cellpos, Vector2(d.footprint[0], d.footprint[1]) * 32), Color(0.2, 0.7, 0.4, 0.4) if valid else Color(0.9, 0.2, 0.2, 0.4))
				sprite(d.art, cellpos, 1, Color(1, 1, 1, 0.65))
				small_text("Entrance", cellpos + Vector2(9, 76), Color("fff2b8"), 8)

func draw_home() -> void:
	tiled("floor" if art.has("floor") else "grass")
	draw_rect(Rect2(16, 16, 416, 24), Color("513a33"))
	draw_rect(Rect2(16, 16, 16, 216), Color("513a33"))
	draw_rect(Rect2(416, 16, 16, 216), Color("513a33"))
	for x in [40, 320]:
		sprite("bed" if art.has("bed") else "shelter", Vector2(x, 44))
	sprite("table" if art.has("table") else "storage_chest", Vector2(190, 104))
	sprite("campfire", Vector2(352, 132))
	sprite("storage_chest", Vector2(42, 150))
	var index = 0
	for p in world.living():
		if p.dynasty or p.spouse:
			actor(p, Vector2(92 + (index % 5) * 55, 104 + int(index / 5.0) * 42))
			index += 1
	small_text("HOME / THE CALENDAR IS PAUSED", Vector2(94, 29), Color("f5deaf"), 10)
	draw_rect(Rect2(197, 222, 54, 26), Color("98774e"))
	small_text("Outside", Vector2(203, 239), Color("fff3d3"), 9)

func draw_route() -> void:
	var e = world.s.expedition
	if e.is_empty(): return
	var region = world.data.regions[int(e.region)]
	tiled(region.terrain if art.has(region.terrain) else "grass")
	for y in range(8):
		for x in range(14):
			if (x * 7 + y * 13) % 17 == 0:
				sprite("rock" if int(e.region) >= 2 else "oak_tree", Vector2(x * 32, y * 32 - 20), 0.5, Color(1, 1, 1, 0.7))
	for index in range(e.route.size()):
		var cell = e.route[index]
		var pos = Vector2(float(cell[0]) * 32, float(cell[1]) * 32)
		if art.has("path"):
			draw_texture_rect_region(art.path, Rect2(pos, Vector2(32, 32)), Rect2(0, 0, 32, 32))
		else: draw_rect(Rect2(pos, Vector2(32, 32)), Color("bda474"))
		if index == 0: sprite("campfire", pos - Vector2(0, 12), 0.5)
		if e.cards.has(str(index)):
			var card = world.definition("cards", e.cards[str(index)])
			sprite(card.art, pos - Vector2(0, 10), 0.5)
		if not selected_card.is_empty():
			draw_rect(Rect2(pos, Vector2(32, 32)), Color(0.8, 0.9, 0.6, 0.25), false, 1)
	var current = e.route[int(e.position)]
	var at = Vector2(float(current[0]) * 32 - 16, float(current[1]) * 32 - 30)
	actor(world.person(world.s.leader), at, not world.s.paused)
	small_text(region.name.to_upper(), Vector2(16, 18), Color("fff0cb"), 11)
	small_text("CIRCUIT %d" % int(e.circuit), Vector2(16, 34), Color("f5dda5"))
	if world.s.paused:
		draw_rect(Rect2(167, 108, 114, 25), Color(0.09, 0.16, 0.16, 0.9))
		small_text("PAUSED / SPACE", Vector2(181, 125), Color("ffdfa2"), 11)

func draw_combat() -> void:
	if world.s.combat.is_empty(): return
	var e = world.s.expedition
	var c = world.s.combat
	var region = world.data.regions[int(e.region)]
	tiled(region.terrain if art.has(region.terrain) else "grass", Vector2.ZERO, Color("b6bd9a"))
	for x in range(7):
		sprite("oak_tree" if int(e.region) < 2 else "rock", Vector2(x * 70 - 20, -28))
	small_text("GUARDIAN ENCOUNTER" if c.boss else "PARTY COMBAT", Vector2(130, 18), Color("fff3d0"), 11)
	for i in range(world.s.party.size()):
		var p = world.person(world.s.party[i])
		var pos = Vector2(22 + int(i / 5.0) * 68, 12 + (i % 5) * 41)
		var acting = c.get("impact", "") == p.id and not reduced_flashes
		actor(p, pos + Vector2(2 if acting and int(clock * 8) % 2 else 0, 0))
		draw_rect(Rect2(pos + Vector2(17, 62), Vector2(31, 3)), Color("503c36"))
		draw_rect(Rect2(pos + Vector2(17, 62), Vector2(maxf(0, p.hp / world.stats(p).hp) * 31, 3)), Color("75b979"))
	for i in range(c.enemies.size()):
		var foe = c.enemies[i]
		var pos = Vector2(282 + (i % 2) * 66, 52 + int(i / 2.0) * 88)
		if c.boss: pos = Vector2(286, 86)
		var tint = Color.WHITE if foe.hp > 0 else Color(0.3, 0.3, 0.3, 0.45)
		var key = foe.id
		var frame = int(clock * 3) % 2
		if art.has(key + "_%d" % frame): key += "_%d" % frame
		sprite(key, pos + Vector2(0, frame), 1, tint)
		draw_rect(Rect2(pos + Vector2(4, 65), Vector2(56, 4)), Color("503c36"))
		draw_rect(Rect2(pos + Vector2(4, 65), Vector2(56 * maxf(0, foe.hp / foe.max_hp), 4)), Color("cb7060"))
		small_text(foe.name, pos + Vector2(-2, 82), Color("fff0c6"), 9)
	if world.s.paused:
		draw_rect(Rect2(159, 114, 116, 26), Color(0.09, 0.16, 0.16, 0.92))
		small_text("PAUSED / SPACE", Vector2(172, 131), Color("ffdda2"), 11)

func walkable(at: Vector2) -> bool:
	if at.x < 160 or at.y < 128 or at.x > 1376 or at.y > 920: return false
	for b in world.s.buildings:
		var fp = world.definition("buildings", b.kind).footprint
		var rect = Rect2(float(b.x) * 32 + 4, float(b.y) * 32 + 30, float(fp[0]) * 32 - 8, float(fp[1]) * 32 - 34)
		if rect.grow(4).has_point(at): return false
	return true

