extends Node2D

const World = preload("res://scripts/game/world.gd")
const MapView = preload("res://scripts/game/map_view.gd")
var world = World.new()
var art: Dictionary = {}
var ui: Control
var map_view
var viewport: SubViewport
var font: Font
var overlay := "title"
var page := 0
var selected_person := "founder"
var selected_building := ""
var job_index := 0
var mission_person := ""
var cautious := true
var needs_refresh := true
var previous_mode := "town"
var resume_after_menu := false
var toast := ""
var toast_time := 0.0
var refresh_time := 0.0
var speed := 1.0
var ui_scale := 2
var rebind_action := ""
var config := ConfigFile.new()
var jobs := ["idle", "builder", "farmer", "gatherer", "cook", "herbalist", "smith", "tailor", "guard", "trainee", "teacher", "doctor"]
var theme_resource := Theme.new()
var capturing := false

func _ready() -> void:
	get_window().title = "Kingdom Loop / A Dynasty Begins"
	get_window().size = Vector2i(1280, 720)
	get_window().content_scale_size = Vector2i(640, 360)
	get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	RenderingServer.set_default_clear_color(Color("152c2b"))
	load_art()
	font = load("res://assets/fonts/Silkscreen-Regular.ttf")
	if font is FontFile:
		font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		font.generate_mipmaps = false
	theme_resource.default_font = font
	theme_resource.default_font_size = 8
	setup_input()
	world.fresh()
	world.changed.connect(func(): needs_refresh = true)
	world.notice.connect(func(message): toast = message; toast_time = 7; needs_refresh = true)
	world.combat_started.connect(func(): needs_refresh = true)
	viewport = SubViewport.new()
	viewport.size = Vector2i(448, 248)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	add_child(viewport)
	map_view = MapView.new()
	map_view.world = world
	map_view.art = art
	map_view.font = font
	viewport.add_child(map_view)
	ui = Control.new()
	ui.size = Vector2(640, 360)
	ui.theme = theme_resource
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(ui)
	config.load("user://kingdom-loop-settings.cfg")
	map_view.reduced_flashes = config.get_value("display", "reduced_flashes", false)
	if "--review" in OS.get_cmdline_user_args():
		setup_review()
	rebuild()
	if "--capture" in OS.get_cmdline_user_args():
		await capture("current")

func load_art() -> void:
	for file in DirAccess.get_files_at("res://assets/demo"):
		if file.ends_with(".png"):
			var tex = load("res://assets/demo/" + file)
			if tex != null:
				assert(tex.get_width() == 64 and tex.get_height() == 64, file + " must be 64x64")
				art[file.trim_suffix(".png")] = tex

func setup_input() -> void:
	var bindings = {"walk_up": KEY_W, "walk_down": KEY_S, "walk_left": KEY_A, "walk_right": KEY_D, "interact": KEY_E, "pause_adventure": KEY_SPACE}
	config.load("user://kingdom-loop-settings.cfg")
	for action in bindings:
		if not InputMap.has_action(action): InputMap.add_action(action)
		InputMap.action_erase_events(action)
		var event = InputEventKey.new()
		event.physical_keycode = int(config.get_value("keys", action, bindings[action]))
		InputMap.action_add_event(action, event)
	for pair in [["walk_up", KEY_UP], ["walk_down", KEY_DOWN], ["walk_left", KEY_LEFT], ["walk_right", KEY_RIGHT]]:
		var event = InputEventKey.new()
		event.physical_keycode = pair[1]
		InputMap.action_add_event(pair[0], event)

func _process(delta: float) -> void:
	if ui == null: return
	toast_time = maxf(0, toast_time - delta)
	refresh_time += delta
	if overlay.is_empty():
		world.tick(minf(delta, 0.1) * speed)
		if world.s.mode == "town":
			var axis = Input.get_vector("walk_left", "walk_right", "walk_up", "walk_down")
			map_view.moving = axis.length() > 0
			if map_view.build_mode:
				map_view.camera = (map_view.camera + axis * delta * 190).clamp(Vector2.ZERO, Vector2(1088, 776))
			else:
				var p = Vector2(world.s.player[0], world.s.player[1])
				var dx = p + Vector2(axis.x * delta * 92, 0)
				if map_view.walkable(dx): p = dx
				var dy = p + Vector2(0, axis.y * delta * 92)
				if map_view.walkable(dy): p = dy
				world.s.player = [p.x, p.y]
				map_view.camera = (p - Vector2(224, 144)).floor().clamp(Vector2.ZERO, Vector2(1088, 776))
				if axis.x > 0: map_view.direction = "right"
				elif axis.x < 0: map_view.direction = "left"
				elif axis.y < 0: map_view.direction = "back"
				elif axis.y > 0: map_view.direction = "front"
		elif world.s.mode == "victory":
			open_menu("victory")
		if world.s.game_over:
			open_menu("game_over")
		check_tutorial()
	map_view.hover_cell = Vector2i(floor((get_global_mouse_position().x - 8 + map_view.camera.x) / 32), floor((get_global_mouse_position().y - 44 + map_view.camera.y) / 32))
	if world.s.mode != previous_mode:
		previous_mode = world.s.mode
		needs_refresh = true
	if refresh_time > 0.5:
		refresh_time = 0
		if overlay.is_empty(): needs_refresh = true
	if needs_refresh:
		needs_refresh = false
		rebuild()

func _input(event: InputEvent) -> void:
	if not rebind_action.is_empty() and event is InputEventKey and event.pressed:
		if event.keycode != KEY_ESCAPE:
			config.set_value("keys", rebind_action, event.physical_keycode)
			config.save("user://kingdom-loop-settings.cfg")
			setup_input()
		rebind_action = ""
		needs_refresh = true
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_F12:
			capture("manual")
		elif event.keycode == KEY_ESCAPE:
			if not overlay.is_empty() and overlay != "title": close_menu()
			elif map_view.build_mode:
				map_view.build_mode = false
				map_view.build_kind = ""
				map_view.relocate_id = ""
			elif not map_view.selected_card.is_empty(): map_view.selected_card = ""
			elif overlay.is_empty(): open_menu("pause")
		elif event.is_action_pressed("pause_adventure") and overlay.is_empty(): pause_toggle()
		elif event.is_action_pressed("interact") and overlay.is_empty(): interact_nearby()
		elif event.keycode == KEY_B and overlay.is_empty() and world.s.mode == "town": open_menu("build")
		elif event.keycode == KEY_I and overlay.is_empty(): open_menu("inventory")
		elif event.keycode == KEY_M and overlay.is_empty(): open_menu("map")
		elif event.keycode == KEY_P and overlay.is_empty(): open_menu("people")
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT and overlay.is_empty():
		var local = event.position - Vector2(8, 44)
		if Rect2(0, 0, 448, 248).has_point(local):
			map_click(local)
			get_viewport().set_input_as_handled()

func clear_ui() -> void:
	for child in ui.get_children():
		ui.remove_child(child)
		child.queue_free()

func panel(rect: Rect2, parent: Node = null) -> Control:
	var n = NinePatchRect.new()
	n.texture = art.ui_panel
	n.position = rect.position
	n.size = rect.size
	n.patch_margin_left = 12
	n.patch_margin_right = 12
	n.patch_margin_top = 12
	n.patch_margin_bottom = 12
	n.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	n.mouse_filter = Control.MOUSE_FILTER_IGNORE
	(parent if parent != null else ui).add_child(n)
	return n

func label(value: String, rect: Rect2, size_value: int = 8, color: Color = Color("48362d")) -> Label:
	var l = Label.new()
	l.text = value
	l.position = rect.position
	l.size = rect.size
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.add_theme_font_size_override("font_size", size_value)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(l)
	return l

func button(value: String, rect: Rect2, callback: Callable, disabled: bool = false, help: String = "") -> Button:
	var b = Button.new()
	b.text = value
	b.position = rect.position
	b.size = rect.size
	b.disabled = disabled
	b.tooltip_text = help
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.add_theme_font_size_override("font_size", 8)
	b.add_theme_color_override("font_color", Color("fff0c5"))
	b.add_theme_color_override("font_hover_color", Color("ffffff"))
	b.add_theme_color_override("font_pressed_color", Color("fadd9d"))
	b.add_theme_color_override("font_disabled_color", Color("aea991"))
	for state in ["normal", "hover", "pressed", "disabled", "focus"]:
		var skin = StyleBoxTexture.new()
		skin.texture = art.ui_button
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]: skin.set_texture_margin(side, 10)
		skin.content_margin_left = 6
		skin.content_margin_right = 6
		skin.content_margin_top = 3
		skin.content_margin_bottom = 3
		if state == "hover" or state == "focus": skin.modulate_color = Color(1.2, 1.2, 1.1)
		elif state == "pressed": skin.modulate_color = Color(0.8, 0.85, 0.8)
		elif state == "disabled": skin.modulate_color = Color(0.55, 0.6, 0.6)
		b.add_theme_stylebox_override(state, skin)
	b.pressed.connect(callback)
	ui.add_child(b)
	return b

func icon(id: String, rect: Rect2, tint: Color = Color.WHITE) -> void:
	if not art.has(id): return
	var p = Sprite2D.new()
	p.texture = art[id]
	p.centered = false
	p.position = rect.position
	p.scale = rect.size / 64.0
	p.modulate = tint
	p.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ui.add_child(p)

func bar(value: float, maximum: float, rect: Rect2, color: Color) -> void:
	var back = ColorRect.new()
	back.position = rect.position
	back.size = rect.size
	back.color = Color("493d36")
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(back)
	var fill = ColorRect.new()
	fill.position = rect.position + Vector2.ONE
	fill.size = Vector2(maxf(0, (rect.size.x - 2) * clampf(value / maxf(1, maximum), 0, 1)), rect.size.y - 2)
	fill.color = color
	fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(fill)

func rebuild() -> void:
	clear_ui()
	if overlay == "title":
		title_screen()
		return
	panel(Rect2(4, 3, 632, 37))
	label("KINGDOM LOOP", Rect2(14, 12, 119, 18), 10)
	icon("icon_wood", Rect2(132, 4, 32, 32))
	label(str(int(world.amount("wood"))), Rect2(162, 14, 48, 15))
	icon("icon_food", Rect2(207, 4, 32, 32))
	label(str(int(world.amount("food"))), Rect2(238, 14, 49, 15))
	label("STONE %d  GOLD %d" % [int(world.amount("stone")), int(world.amount("gold"))], Rect2(295, 14, 170, 15))
	label("Y%d / DAY %d" % [1 + int(float(world.s.day) / 365), int(world.s.day) % 365 + 1], Rect2(482, 13, 143, 16), 9)
	var image = TextureRect.new()
	image.texture = viewport.get_texture()
	image.position = Vector2(8, 44)
	image.size = Vector2(448, 248)
	image.mouse_filter = Control.MOUSE_FILTER_IGNORE
	image.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ui.add_child(image)
	panel(Rect2(464, 42, 172, 252))
	if world.s.mode in ["town", "home", "map", "victory"]: town_sidebar()
	else: expedition_sidebar()
	panel(Rect2(4, 299, 632, 57))
	var nav = [["BUILD", "build"], ["PEOPLE", "people"], ["SUPPLIES", "inventory"], ["REGIONS", "map"], ["JOURNAL", "journal"], ["MENU", "pause"]]
	for i in range(nav.size()):
		var disabled = i == 0 and world.s.mode != "town"
		button(nav[i][0], Rect2(12 + i * 103, 307, 99, 22), open_menu.bind(nav[i][1]), disabled, "Construction is available in town." if disabled else "")
	var hint = "WASD: walk / E: interact / B: build / P: people / F12: screenshot"
	if map_view.build_mode: hint = "WASD: pan / click: place / Esc: leave build mode"
	elif world.s.mode == "expedition": hint = "SPACE: pause / Cards: shape the route / Return: preserve your cargo"
	elif world.s.mode == "combat": hint = "Automatic attacks and skills / SPACE: pause / Retreat to rescue fallen allies"
	if toast_time > 0: hint = toast
	label(hint, Rect2(15, 333, 610, 17), 8)
	if not overlay.is_empty(): modal()

func town_sidebar() -> void:
	label(str(world.data.ranks[int(world.s.rank)]).to_upper(), Rect2(476, 54, 145, 20), 12)
	label("Calendar paused", Rect2(476, 76, 144, 14), 8, Color("426650"))
	label("Residents %d / Homes %d\nDefense %d / Party %d/%d" % [world.living().size(), world.housing(), int(world.defense()), world.s.party.size(), world.party_limit()], Rect2(476, 98, 147, 33))
	label("NEXT STEPS", Rect2(476, 140, 143, 14), 9)
	var tasks = world.objectives()
	label("\n\n".join(tasks.slice(0, mini(2, tasks.size()))), Rect2(476, 158, 145, 68))
	button("EXPEDITION", Rect2(476, 231, 145, 24), open_menu.bind("map"))
	button("LEAVE HOME" if world.s.mode == "home" else "HOUSEHOLD", Rect2(476, 259, 145, 23), enter_home if world.s.mode == "home" else open_menu.bind("family"))

func expedition_sidebar() -> void:
	var e = world.s.expedition
	if e.is_empty(): return
	label("BATTLE" if world.s.mode == "combat" else "EXPEDITION", Rect2(476, 54, 145, 18), 11)
	label("Threat %d / 100" % int(e.threat), Rect2(476, 77, 145, 15))
	bar(e.threat, 100, Rect2(476, 94, 145, 6), Color("c4815a"))
	var party = world.s.party
	for i in range(mini(10, party.size())):
		var p = world.person(party[i])
		var y = 106 + i * 8
		label(p.name.left(9), Rect2(476, y, 75, 10), 7)
		bar(p.hp, world.stats(p).hp, Rect2(549, y + 2, 70, 5), Color("73aa72"))
	label("Food %d / Mix %d" % [int(e.food), int(e.potions)], Rect2(476, 190, 145, 12), 8)
	button("RESUME" if world.s.paused else "PAUSE", Rect2(476, 205, 70, 22), pause_toggle)
	button("RETREAT", Rect2(549, 205, 72, 22), open_menu.bind("retreat"))
	button("CARDS (%d)" % e.hand.size(), Rect2(476, 232, 145, 22), open_menu.bind("cards"), world.s.mode == "combat", "Place cards between battles.")
	button("CHALLENGE GUARDIAN", Rect2(476, 258, 145, 23), challenge, e.threat < 100 or world.s.mode == "combat" or e.boss_won, "Fill the threat meter to challenge this region's guardian.")
	if world.s.mode == "combat" and not world.s.combat.is_empty():
		var lines = world.s.combat.log.slice(0, 2)
		label("\n".join(lines), Rect2(18, 269, 432, 24), 7, Color("fff2ce"))

func title_screen() -> void:
	for y in range(6):
		for x in range(10): icon("grass", Rect2(x * 64, y * 64, 64, 64))
	for x in [4, 68, 126, 494, 558]: icon("oak_tree", Rect2(x, 250, 64, 64))
	icon("family_home", Rect2(92, 172, 128, 128))
	icon("founder", Rect2(177, 230, 64, 64))
	panel(Rect2(40, 34, 560, 108))
	label("KINGDOM LOOP", Rect2(82, 54, 489, 33), 24)
	label("A DYNASTY BEGINS", Rect2(188, 103, 295, 21), 12)
	panel(Rect2(306, 159, 264, 171))
	button("NEW JOURNEY", Rect2(327, 180, 222, 28), new_game)
	button("CONTINUE", Rect2(327, 214, 222, 28), continue_game, not FileAccess.file_exists(world.save_root.path_join("continue.json")))
	button("LOAD / SETTINGS", Rect2(327, 248, 222, 28), open_menu.bind("pause"))
	button("QUIT", Rect2(327, 282, 222, 25), func(): get_tree().quit())
	label("A complete systems demo / Temporary character art", Rect2(57, 339, 555, 14), 8, Color("f4e7bc"))

func new_game() -> void:
	world.fresh(randi_range(1000, 999999))
	selected_person = "founder"
	overlay = "tutorial"
	page = 0
	needs_refresh = true

func continue_game() -> void:
	if world.load_game("continue"):
		overlay = ""
		selected_person = world.s.leader
		needs_refresh = true

func open_menu(name: String) -> void:
	if overlay.is_empty():
		resume_after_menu = not world.s.paused and world.s.mode in ["expedition", "combat"]
		if world.s.mode in ["expedition", "combat"]: world.s.paused = true
	overlay = name
	page = 0
	needs_refresh = true

func close_menu() -> void:
	overlay = ""
	if resume_after_menu and world.s.mode in ["expedition", "combat"]: world.s.paused = false
	resume_after_menu = false
	needs_refresh = true

func pause_toggle() -> void:
	if world.s.mode in ["expedition", "combat"]:
		world.s.paused = not world.s.paused
		needs_refresh = true

func modal() -> void:
	var shade = ColorRect.new()
	shade.size = Vector2(640, 360)
	shade.color = Color(0.04, 0.1, 0.1, 0.73)
	ui.add_child(shade)
	panel(Rect2(16, 19, 608, 320))
	label(overlay.replace("_", " ").to_upper(), Rect2(34, 32, 460, 23), 14)
	button("CLOSE", Rect2(543, 29, 62, 24), close_menu, overlay in ["victory", "game_over"])
	match overlay:
		"build": build_menu()
		"people": people_menu()
		"person": person_menu()
		"family": family_menu()
		"inventory": inventory_menu()
		"craft": craft_menu()
		"stockpile": stockpile_menu()
		"map": map_menu()
		"missions": mission_menu()
		"outpost": outpost_menu()
		"cards": cards_menu()
		"journal": journal_menu()
		"building": building_menu()
		"retreat": retreat_menu()
		"pause": pause_menu()
		"settings": settings_menu()
		"tutorial": tutorial_menu()
		"victory": victory_menu()
		"game_over":
			label("The ruling dynasty has no eligible chosen heir.\nYour earlier saves can restore a different future.", Rect2(56, 99, 530, 75), 12)
			button("LOAD A SAVE", Rect2(200, 220, 240, 32), open_menu.bind("pause"))

func paging(total: int, per_page: int) -> void:
	page = clampi(page, 0, maxi(0, int(ceil(total / float(per_page))) - 1))
	button("PREV", Rect2(34, 301, 64, 23), func(): page = maxi(0, page - 1); needs_refresh = true, page == 0)
	label("%d / %d" % [page + 1, maxi(1, int(ceil(total / float(per_page))))], Rect2(110, 307, 130, 13))
	button("NEXT", Rect2(253, 301, 64, 23), func(): page += 1; needs_refresh = true, (page + 1) * per_page >= total)

func cost_text(cost: Dictionary) -> String:
	var parts = []
	for key in cost: parts.append("%d %s" % [int(cost[key]), "timber" if key == "wood" else key])
	return ", ".join(parts)

func build_menu() -> void:
	var list = world.data.buildings
	paging(list.size(), 6)
	for i in range(page * 6, mini(list.size(), page * 6 + 6)):
		var d = list[i]
		var n = i - page * 6
		var x = 32 + (n % 3) * 194
		var y = 67 + int(n / 3.0) * 112
		panel(Rect2(x, y, 188, 106))
		icon(d.art, Rect2(x + 3, y + 17, 64, 64))
		label(d.name, Rect2(x + 69, y + 10, 110, 27), 9)
		label(cost_text(d.cost), Rect2(x + 69, y + 40, 109, 26), 8)
		button("PLACE" if int(d.rank) <= int(world.s.rank) else str(world.data.ranks[int(d.rank)]), Rect2(x + 69, y + 74, 108, 23), select_build.bind(d.id), int(d.rank) > int(world.s.rank) or not world.can_pay(d.cost))
	button("ROAD / 1 STONE", Rect2(349, 301, 160, 23), select_build.bind("road"))
	button("JOBS", Rect2(520, 301, 82, 23), open_menu.bind("people"))

func select_build(id: String) -> void:
	close_menu()
	map_view.build_mode = true
	map_view.build_kind = id
	map_view.relocate_id = ""
	toast = "Choose an open plot. Keep the front entrance clear."
	toast_time = 6

func people_menu() -> void:
	var list = world.living()
	paging(list.size(), 6)
	for i in range(page * 6, mini(list.size(), page * 6 + 6)):
		var p = list[i]
		var y = 65 + (i - page * 6) * 37
		icon(world.data.roles[p.role].art, Rect2(38, y - 16, 48, 48))
		label(p.name + " / " + str(world.age_of(p)), Rect2(90, y + 2, 138, 16), 10)
		label(str(world.data.roles[p.role].name) + " / " + p.job, Rect2(230, y + 4, 213, 22), 8)
		button("DETAILS", Rect2(453, y, 71, 26), show_person.bind(p.id))
		button("IN PARTY" if world.s.party.has(p.id) else "RECRUIT", Rect2(528, y, 76, 26), func(): world.toggle_party(p.id); needs_refresh = true, world.age_of(p) < 18 or p.id == world.s.leader)
	button("MISSIONS", Rect2(353, 301, 117, 23), open_menu.bind("missions"))
	button("FAMILY", Rect2(486, 301, 117, 23), open_menu.bind("family"))

func show_person(id: String) -> void:
	selected_person = id
	open_menu("person")
	var p = world.person(id)
	job_index = maxi(0, jobs.find(p.get("job", "idle")))

func person_menu() -> void:
	var p = world.person(selected_person)
	if p.is_empty(): return
	var stats = world.stats(p)
	icon(world.data.roles[p.role].art, Rect2(47, 53, 96, 96))
	label(p.name + " / AGE " + str(world.age_of(p)), Rect2(151, 72, 400, 21), 13)
	label("%s / LEVEL %d / %s" % [world.data.roles[p.role].name, int(p.level), "DYNASTY" if p.dynasty else "MORTAL"], Rect2(151, 101, 410, 20), 9)
	label("HP %d/%d   ATK %d   DEF %d" % [int(p.hp), int(stats.hp), int(stats.attack), int(stats.defense)], Rect2(151, 128, 402, 18), 9)
	bar(p.hp, stats.hp, Rect2(151, 149, 410, 8), Color("729864"))
	label("Work: " + p.job + " / morale %d" % int(p.morale), Rect2(40, 173, 284, 18), 9)
	button("<", Rect2(37, 197, 26, 23), func(): job_index = posmod(job_index - 1, jobs.size()); needs_refresh = true)
	label(jobs[job_index].to_upper(), Rect2(72, 203, 128, 14), 9)
	button(">", Rect2(199, 197, 26, 23), func(): job_index = (job_index + 1) % jobs.size(); needs_refresh = true)
	button("ASSIGN", Rect2(232, 197, 79, 23), func(): world.assign(p.id, jobs[job_index]); needs_refresh = true)
	button("EQUIPMENT", Rect2(329, 170, 115, 24), open_menu.bind("inventory"))
	button("LEAVE PARTY" if world.s.party.has(p.id) else "JOIN PARTY", Rect2(452, 170, 151, 24), func(): world.toggle_party(p.id); needs_refresh = true, p.id == world.s.leader or world.age_of(p) < 18)
	button("CONVERSE", Rect2(329, 200, 115, 24), func(): world.talk(p.id); needs_refresh = true)
	button("MARRY" if not p.spouse else "PLAN CHILD", Rect2(452, 200, 151, 24), func():
		if p.spouse: world.start_family(p.id)
		else: world.marry(p.id)
		needs_refresh = true, p.id not in ["mira", "sera"])
	if world.age_of(p) < 18:
		button("EDUCATION: " + p.education, Rect2(37, 232, 274, 25), func():
			var roles = world.data.roles.keys()
			p.education = roles[(roles.find(p.education) + 1) % roles.size()]
			needs_refresh = true)
	else:
		button("CHOOSE HEIR", Rect2(37, 232, 274, 25), func(): world.choose_heir(p.id); needs_refresh = true, not p.dynasty or p.id == world.s.leader)
	label("\n".join(p.history.slice(maxi(0, p.history.size() - 2))), Rect2(333, 237, 269, 47), 8)
	button("FORMATION: " + p.get("formation", "middle"), Rect2(37, 264, 274, 23), func():
		var choices = ["front", "middle", "rear"]
		p.formation = choices[(choices.find(p.get("formation", "middle")) + 1) % 3]
		needs_refresh = true)
	button("ALL RESIDENTS", Rect2(37, 297, 172, 26), open_menu.bind("people"))
	label("Recovery: %.0f days" % maxf(0, float(p.injury_until) - float(world.s.day)), Rect2(338, 303, 264, 20), 9)

func family_menu() -> void:
	var family = world.s.people.filter(func(p): return p.dynasty or p.spouse)
	paging(family.size(), 5)
	label("Chosen heir: " + (world.person(world.s.heir).get("name", "None")), Rect2(37, 63, 389, 18), 9)
	for i in range(page * 5, mini(family.size(), page * 5 + 5)):
		var p = family[i]
		var y = 92 + (i - page * 5) * 37
		var parents = []
		for id in p.parent_ids: parents.append(world.person(id).get("name", "Unknown"))
		label(p.name + " / " + str(world.age_of(p)) + (" / deceased" if not p.alive else ""), Rect2(40, y, 219, 19), 9)
		label("Child of " + " & ".join(parents) if not parents.is_empty() else ("Spouse" if p.spouse else "Founder / ruler"), Rect2(265, y, 252, 29), 8)
		button("VIEW", Rect2(529, y - 2, 73, 26), show_person.bind(p.id))
	button("ENTER HOME", Rect2(345, 301, 125, 23), enter_home, world.count_building("residence") == 0)
	button("RESIDENTS", Rect2(483, 301, 120, 23), open_menu.bind("people"))
	if not world.s.pregnancies.is_empty():
		label("Expecting: " + str(world.s.pregnancies.size()) + " / next birth in %.0f days" % maxf(0, world.s.pregnancies[0].due - world.s.day), Rect2(37, 278, 565, 17), 8)

func inventory_menu() -> void:
	var p = world.person(selected_person)
	if p.is_empty(): selected_person = world.s.leader; p = world.person(selected_person)
	button("FIGHTER: " + p.name, Rect2(35, 62, 251, 24), func():
		var members = world.living().filter(func(v): return world.age_of(v) >= 18)
		var index = members.find(p)
		selected_person = members[(index + 1) % members.size()].id
		needs_refresh = true)
	button("CRAFT", Rect2(298, 62, 137, 24), open_menu.bind("craft"))
	button("STOCKPILE", Rect2(447, 62, 156, 24), open_menu.bind("stockpile"))
	var list = world.s.inventory
	paging(list.size(), 6)
	for i in range(page * 6, mini(list.size(), page * 6 + 6)):
		var d = world.definition("items", list[i])
		var y = 97 + (i - page * 6) * 31
		label(d.name, Rect2(41, y + 3, 167, 17), 9)
		var current = world.definition("items", p.equipment.get(d.slot, ""))
		label("%s / ATK %+d DEF %+d HP %+d" % [d.slot, int(d.attack) - int(current.get("attack", 0)), int(d.defense) - int(current.get("defense", 0)), int(d.hp) - int(current.get("hp", 0))], Rect2(211, y + 4, 300, 19), 8)
		button("EQUIP", Rect2(527, y, 76, 24), func(): world.equip(p.id, d.id); needs_refresh = true, world.s.mode == "combat")
	label("Equipped: " + ", ".join(p.equipment.values()), Rect2(334, 302, 269, 24), 8)

func craft_menu() -> void:
	var list = world.data.recipes + world.data.items
	paging(list.size(), 7)
	for i in range(page * 7, mini(list.size(), page * 7 + 7)):
		var d = list[i]
		var y = 65 + (i - page * 7) * 32
		label(d.name, Rect2(39, y + 3, 178, 17), 9)
		label(cost_text(d.cost), Rect2(222, y + 4, 290, 20), 8)
		button("QUEUE", Rect2(529, y, 74, 25), func(): world.craft(d.id); needs_refresh = true, not world.can_pay(d.cost))
	button("JOBS", Rect2(349, 301, 113, 23), open_menu.bind("people"))
	label("Queued: " + str(world.s.crafts.size()), Rect2(479, 304, 124, 17), 9)

func stockpile_menu() -> void:
	var keys = world.s.resources.keys()
	for i in range(keys.size()):
		var x = 42 + int(i / 5.0) * 280
		var y = 74 + (i % 5) * 32
		label(keys[i].to_upper(), Rect2(x, y, 161, 21), 10)
		label(str(int(world.amount(keys[i]))), Rect2(x + 174, y, 84, 21), 10)
	var f = world.forecast(90)
	label("Food balance: %+.1f / day   90-day stock forecast: %d" % [f.food_per_day, int(f.food_after)], Rect2(43, 245, 548, 24), 9)
	button("POTION BELOW %d%%" % int(world.s.supply_health * 100), Rect2(38, 283, 272, 30), func(): world.s.supply_health = 0.25 if world.s.supply_health >= 0.7 else world.s.supply_health + 0.15; needs_refresh = true)
	button("MEAL BELOW %d%%" % int(world.s.meal_health * 100), Rect2(326, 283, 275, 30), func(): world.s.meal_health = 0.4 if world.s.meal_health >= 0.85 else world.s.meal_health + 0.15; needs_refresh = true)

func map_menu() -> void:
	for i in range(4):
		var r = world.data.regions[i]
		var x = 31 + i * 148
		panel(Rect2(x, 66, 143, 221))
		label(r.name, Rect2(x + 9, 77, 124, 28), 10)
		icon(r.boss, Rect2(x + 39, 105, 64, 64))
		label("SECURED" if world.s.bosses.has(i) else r.subtitle, Rect2(x + 10, 168, 123, 27), 8)
		var duration = float(r.travel_days) + float(r.days_per_second) * 180
		label("Est. %.0f days\nFood after: %d" % [duration, int(world.forecast(duration).food_after)], Rect2(x + 10, 202, 123, 30), 8)
		var locked = i > 0 and not world.s.bosses.has(i - 1)
		button("LOCKED" if locked else "DEPART", Rect2(x + 10, 253, 123, 24), depart.bind(i, false), locked or world.s.mode not in ["town", "home", "map"])
	button("RECOVERY TRIP", Rect2(35, 299, 173, 25), depart.bind(0, true), world.s.mode not in ["town", "home", "map"])
	button("OUTPOST", Rect2(217, 299, 121, 25), open_menu.bind("outpost"))
	button("MISSIONS", Rect2(347, 299, 121, 25), open_menu.bind("missions"))
	button("PARTY", Rect2(478, 299, 125, 25), open_menu.bind("people"))

func depart(region: int, recovery: bool) -> void:
	if world.depart(region, recovery):
		overlay = ""
		resume_after_menu = false
		map_view.build_mode = false
		needs_refresh = true

func mission_menu() -> void:
	var available = world.living().filter(func(p): return world.age_of(p) >= 18 and not world.s.party.has(p.id) and p.mission == "")
	if not available.any(func(p): return p.id == mission_person): mission_person = "" if available.is_empty() else available[0].id
	button("FIGHTER: " + world.person(mission_person).get("name", "None available"), Rect2(36, 65, 291, 28), func():
		if not available.is_empty():
			var index = available.find(world.person(mission_person))
			mission_person = available[(index + 1) % available.size()].id
			needs_refresh = true)
	button("CAUTIOUS" if cautious else "STANDARD", Rect2(340, 65, 261, 28), func(): cautious = not cautious; needs_refresh = true)
	for i in range(3):
		var d = world.data.missions[i]
		var y = 112 + i * 46
		label(d.name, Rect2(40, y, 222, 20), 10)
		label("%dd / %d food / retreat at danger" % [int(d.days), int(d.cost)], Rect2(40, y + 19, 432, 20), 8)
		button("DISPATCH", Rect2(476, y, 125, 31), func(): world.dispatch(d.id, mission_person, cautious); needs_refresh = true, mission_person.is_empty())
	label("Active missions: " + str(world.s.missions.size()) + " / progress only during your adventures", Rect2(40, 267, 562, 36), 9)

func outpost_menu() -> void:
	icon("lodge", Rect2(55, 86, 128, 128))
	label("THE HIGHLAND ROAD", Rect2(209, 80, 370, 24), 13)
	label("Secure the highland guardian to establish a governed outpost. Deliveries follow the same adventure calendar as your capital.", Rect2(211, 117, 369, 63), 10)
	if world.s.outpost:
		label("Governor: %s\nNext: %.0fd / %s" % [world.person(world.s.outpost_governor).get("name", "Vacant"), maxf(0, world.s.outpost_next - world.s.day), world.s.outpost_policy], Rect2(211, 193, 364, 42), 10)
		button("CHANGE DELIVERY POLICY", Rect2(210, 252, 365, 33), func(): world.s.outpost_policy = "materials" if world.s.outpost_policy == "supplies" else "supplies"; needs_refresh = true)
	else:
		label("150 timber / 100 stone / 80 food", Rect2(211, 197, 370, 29), 10)
		button("ESTABLISH OUTPOST", Rect2(210, 252, 365, 33), func(): world.found_outpost(); needs_refresh = true)

func cards_menu() -> void:
	if world.s.expedition.is_empty(): return
	var hand = world.s.expedition.hand
	paging(hand.size(), 4)
	for i in range(page * 4, mini(hand.size(), page * 4 + 4)):
		var d = world.definition("cards", hand[i])
		var x = 31 + (i - page * 4) * 148
		panel(Rect2(x, 67, 143, 223))
		label(d.name, Rect2(x + 10, 77, 123, 29), 10)
		icon(d.art, Rect2(x + 38, 105, 64, 64))
		label(d.text, Rect2(x + 11, 176, 121, 65), 8)
		button("PLACE", Rect2(x + 10, 253, 123, 25), func():
			map_view.selected_card = d.id
			close_menu()
			world.s.paused = true
			toast = "Click a highlighted route tile. Space resumes travel."
			toast_time = 6)

func journal_menu() -> void:
	var entries = world.s.history
	paging(entries.size(), 5)
	for i in range(page * 5, mini(entries.size(), page * 5 + 5)):
		var e = entries[i]
		var y = 66 + (i - page * 5) * 45
		label("DAY %d / %s" % [int(e.day), e.title], Rect2(39, y, 558, 18), 9)
		label(e.text, Rect2(39, y + 19, 558, 25), 8)
	label("Combinations: " + str(world.s.journal.size()) + " / 3", Rect2(352, 306, 245, 17), 9)

func building_menu() -> void:
	var match_list = world.s.buildings.filter(func(b): return b.id == selected_building)
	if match_list.is_empty(): close_menu(); return
	var b = match_list[0]
	var d = world.definition("buildings", b.kind)
	icon(d.art, Rect2(47, 73, 128, 128))
	label(d.name, Rect2(205, 76, 366, 23), 14)
	label("Ready" if b.remaining <= 0 else "Construction: %.1f days remaining" % b.remaining, Rect2(205, 113, 365, 28), 10)
	label("Role: " + str(d.effect) + "\nFootprint: %d x %d / entrance faces south\nWork progresses during adventures." % [int(d.footprint[0]), int(d.footprint[1])], Rect2(205, 154, 369, 65), 9)
	button("ASSIGN WORKERS", Rect2(40, 249, 177, 32), open_menu.bind("people"))
	button("MOVE / 5 WOOD + 5 GOLD", Rect2(229, 249, 230, 32), func():
		close_menu()
		map_view.build_mode = true
		map_view.build_kind = b.kind
		map_view.relocate_id = b.id)
	button("ENTER" if b.kind == "residence" else "CRAFT", Rect2(471, 249, 129, 32), enter_home if b.kind == "residence" else open_menu.bind("craft"), b.remaining > 0)
	label("Only the family residence can be entered.", Rect2(40, 299, 555, 17), 9)

func retreat_menu() -> void:
	if world.s.expedition.is_empty(): return
	var e = world.s.expedition
	var safe = int(e.position) == 0 or e.boss_won or e.recovery
	label("RETURN TO YOUR SETTLEMENT", Rect2(49, 86, 540, 30), 14)
	label("You retain %d%% of unsecured cargo. Equipped gear is kept. Retreat rescues incapacitated allies; a complete defeat can kill mortal companions." % (100 if safe else 75), Rect2(51, 132, 529, 69), 11)
	label("Cargo: " + cost_text(e.cargo), Rect2(51, 210, 529, 35), 9)
	button("RETURN HOME", Rect2(65, 267, 243, 34), func(): world.return_home(false); overlay = "journal"; page = 0; resume_after_menu = false; needs_refresh = true)
	button("KEEP ADVENTURING", Rect2(327, 267, 243, 34), close_menu)

func pause_menu() -> void:
	for i in range(3):
		var y = 76 + i * 44
		label("SLOT " + str(i + 1), Rect2(41, y + 6, 144, 20), 11)
		button("SAVE", Rect2(190, y, 115, 30), func(): world.save_game("slot_%d" % (i + 1)); toast = "Game saved"; toast_time = 5; needs_refresh = true)
		button("LOAD", Rect2(321, y, 115, 30), func():
			if world.load_game("slot_%d" % (i + 1)): overlay = ""; selected_person = world.s.leader; needs_refresh = true, not FileAccess.file_exists(world.save_root.path_join("slot_%d.json" % (i + 1))))
		button("AUTO " + str(i + 1), Rect2(451, y, 145, 30), func():
			if world.load_game("auto_%d" % i): overlay = ""; selected_person = world.s.leader; needs_refresh = true, not FileAccess.file_exists(world.save_root.path_join("auto_%d.json" % i)))
	button("SETTINGS", Rect2(39, 226, 171, 30), open_menu.bind("settings"))
	button("HOW TO PLAY", Rect2(230, 226, 173, 30), open_menu.bind("tutorial"))
	button("RESUME", Rect2(423, 226, 176, 30), close_menu)
	button("TITLE SCREEN", Rect2(39, 276, 264, 31), func(): world.save_game("continue"); overlay = "title"; needs_refresh = true)
	button("SAVE AND QUIT", Rect2(326, 276, 273, 31), func(): world.save_game("continue"); get_tree().quit())

func settings_menu() -> void:
	button("FULLSCREEN / WINDOW", Rect2(37, 72, 271, 28), func():
		get_window().mode = Window.MODE_WINDOWED if get_window().mode == Window.MODE_FULLSCREEN else Window.MODE_FULLSCREEN)
	button("LARGE WINDOW" if ui_scale == 2 else "NORMAL WINDOW", Rect2(325, 72, 277, 28), func():
		ui_scale = 3 if ui_scale == 2 else 2
		get_window().size = Vector2i(640, 360) * ui_scale
		needs_refresh = true)
	button("AUTO PAUSE: " + ("ON" if world.s.auto_pause else "OFF"), Rect2(37, 112, 271, 28), func(): world.s.auto_pause = not world.s.auto_pause; needs_refresh = true)
	button("REDUCED FLASH: " + ("ON" if map_view.reduced_flashes else "OFF"), Rect2(325, 112, 277, 28), func():
		map_view.reduced_flashes = not map_view.reduced_flashes
		config.set_value("display", "reduced_flashes", map_view.reduced_flashes)
		config.save("user://kingdom-loop-settings.cfg")
		needs_refresh = true)
	var actions = ["walk_up", "walk_down", "walk_left", "walk_right", "interact", "pause_adventure"]
	for i in range(actions.size()):
		var action = actions[i]
		var x = 37 + (i % 2) * 288
		var y = 156 + int(i / 2.0) * 37
		var key = InputMap.action_get_events(action)[0]
		button(action.replace("_", " ") + ": " + OS.get_keycode_string(key.physical_keycode), Rect2(x, y, 271, 28), func(): rebind_action = action; needs_refresh = true)
	label("Press a new key. Escape cancels." if not rebind_action.is_empty() else "No audio / All strategic time stops in menus and town.", Rect2(38, 287, 564, 26), 9)

func tutorial_menu() -> void:
	label("BUILD A HOME. SHAPE THE ROAD.", Rect2(40, 76, 557, 30), 14)
	var step = int(world.s.tutorial)
	var text = [
		"Walk with WASD and interact with E. Open Supplies to equip your starting gear. Then choose Regions and depart for the Green Frontier. Your first goal is to rescue a resident and return home.",
		"Heroes travel and fight automatically. Space pauses safely. Open Cards, choose a card, and click a route tile. Gather supplies and return with the survivor. Fill the threat meter when ready to challenge the guardian.",
		"Build a residence and garden. A builder completes projects while you adventure; a farmer produces food. People lets you assign jobs or recruit companions. A worker taken on an expedition stops working at home.",
		"Share a new conversation after each expedition. Willing adult partners can marry after three relationship events and a completed family home. A household with space and food can plan children.",
		"Later expeditions span months and years. Everyone shares the same calendar. Train adult heirs, choose a successor, equip your party, staff defenses, and establish a highland outpost.",
		"Prepare a city and a large party for the Hollow Crown. Meals, medicine, equipment and formations matter. You can retreat to save incapacitated allies. Victory lets you continue building the kingdom."
	]
	label(text[mini(step, 5)], Rect2(45, 124, 545, 130), 12)
	button("GOT IT", Rect2(50, 276, 247, 33), func(): world.s.tutorial = mini(6, step + 1); close_menu())
	button("SKIP TUTORIAL", Rect2(322, 276, 267, 33), func(): world.s.tutorial_skipped = true; close_menu())

func check_tutorial() -> void:
	if world.s.tutorial_skipped or not overlay.is_empty(): return
	var step = int(world.s.tutorial)
	if (step == 1 and world.s.mode == "expedition") or (step == 2 and world.s.runs >= 1) or (step == 3 and world.count_building("residence") > 0) or (step == 4 and world.s.bosses.size() >= 2) or (step == 5 and world.s.bosses.size() >= 3):
		open_menu("tutorial")

func victory_menu() -> void:
	label("THE KINGDOM ENDURES", Rect2(74, 79, 510, 37), 20)
	icon("residence_4" if art.has("residence_4") else "family_home", Rect2(52, 134, 128, 128))
	label("The Hollow King has fallen. Your settlement, companions, and family made this victory possible.", Rect2(211, 129, 365, 66), 12)
	label("%d residents / %d expeditions / %d years\nYour family's history remains in the journal." % [world.living().size(), int(world.s.runs), int(world.s.day / 365)], Rect2(212, 209, 366, 47), 10)
	button("CONTINUE YOUR KINGDOM", Rect2(210, 273, 368, 34), func(): world.s.mode = "town"; close_menu(); world.autosave())

func enter_home() -> void:
	if world.s.mode == "home": world.s.mode = "town"
	elif world.count_building("residence") > 0 and world.s.mode == "town": world.s.mode = "home"
	else: toast = "The completed family residence can be entered from town."; toast_time = 5; return
	close_menu()
	needs_refresh = true

func challenge() -> void:
	world.challenge_boss()
	needs_refresh = true

func map_click(local: Vector2) -> void:
	if world.s.mode == "town":
		var wp = local + map_view.camera
		if map_view.build_mode and not map_view.build_kind.is_empty():
			var cell = Vector2i(floor(wp.x / 32), floor(wp.y / 32))
			if not map_view.relocate_id.is_empty():
				if world.relocate(map_view.relocate_id, cell.x, cell.y): map_view.relocate_id = ""; map_view.build_mode = false
			elif map_view.build_kind == "road": world.road(cell.x, cell.y)
			else: world.build(map_view.build_kind, cell.x, cell.y)
			needs_refresh = true
			return
		for b in world.s.buildings:
			if Rect2(float(b.x) * 32, float(b.y) * 32, 64, 64).has_point(wp):
				selected_building = b.id
				open_menu("building")
				return
	elif world.s.mode == "expedition" and not map_view.selected_card.is_empty():
		var cell = Vector2i(floor(local.x / 32), floor(local.y / 32))
		for i in range(world.s.expedition.route.size()):
			var route = world.s.expedition.route[i]
			if int(route[0]) == cell.x and int(route[1]) == cell.y:
				if world.place_card(map_view.selected_card, i): map_view.selected_card = ""
				needs_refresh = true
				return
	elif world.s.mode == "home" and local.y > 210: enter_home()

func interact_nearby() -> void:
	if world.s.mode == "home": enter_home(); return
	if world.s.mode != "town": return
	var p = Vector2(world.s.player[0], world.s.player[1])
	var closest = {}
	var distance = 94.0
	for b in world.s.buildings:
		var d = p.distance_to(Vector2(float(b.x) * 32 + 32, float(b.y) * 32 + 64))
		if d < distance: distance = d; closest = b
	if not closest.is_empty():
		selected_building = closest.id
		open_menu("building")
	else:
		toast = "Approach a building entrance, or open People to talk to residents."
		toast_time = 5

func capture(name: String) -> void:
	if capturing: return
	capturing = true
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var directory = ProjectSettings.globalize_path("res://../art-source/demo-v1/previews") if OS.has_feature("editor") else "user://screenshots"
	DirAccess.make_dir_recursive_absolute(directory)
	var path = directory.path_join(name + ".png")
	var result = get_viewport().get_texture().get_image().save_png(path)
	print("CAPTURE ", result, " ", path)
	capturing = false

func setup_review() -> void:
	world.s.buildings.clear()
	for placement in [["residence", 20, 13], ["well", 24, 13], ["garden", 27, 16], ["campfire", 23, 17], ["storage", 19, 17], ["herbalist", 27, 12]]:
		world.add_building(placement[0], placement[1], placement[2], true)
	world.s.people.append(world.make_person("Mira", "healer", 25, false, "mira"))
	world.s.people.append(world.make_person("Tovin", "melee", 26))
	world.s.rescues = [0]
	world.s.rank = 1
	world.s.tutorial_skipped = true
	world.s.player = [768.0, 564.0]
	overlay = ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--screen="):
			var screen = arg.trim_prefix("--screen=")
			if screen == "town": continue
			if screen == "combat":
				world.depart(0)
				world.start_combat(false)
				world.s.paused = true
			elif screen == "expedition":
				world.depart(0)
				world.place_card("grove", 3)
				world.place_card("garden", 4)
				world.s.paused = true
			elif screen == "home": world.s.mode = "home"
			else: overlay = screen
