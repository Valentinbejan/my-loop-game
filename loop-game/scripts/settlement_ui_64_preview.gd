extends Node2D

const ROOT := "res://assets/settlement-ui-64-v1/"
const ITEMS := [
	{"id": "family_home", "title": "Family cottage", "description": "The household's home.\nThe only enterable building."},
	{"id": "oak_tree", "title": "Oak tree", "description": "A landmark for the\nsettlement's gardens."},
	{"id": "village_well", "title": "Village well", "description": "Water for gardens\nand everyday village life."},
	{"id": "storage_chest", "title": "Storage chest", "description": "A place for supplies\nbrought back from adventures."},
	{"id": "campfire", "title": "Starter campfire", "description": "The first gathering place\nwhen founding a settlement."},
	{"id": "crop_plot", "title": "Vegetable garden", "description": "Food for the household\nand the next expedition."},
]
var textures: Dictionary = {}
var selection_title: Label
var selection_description: Label
var selection_picture: Sprite2D
var status: Label
var action: Button
var selected := 0
var placing := false
var ghost: Sprite2D
var placed_objects: Array[Sprite2D] = []
var asset_buttons: Array[Button] = []
var pixel_font := SystemFont.new()

func _ready() -> void:
	get_window().title = "Kingdom Loop - environment and pixel UI"
	get_window().size = Vector2i(1280, 800)
	get_window().content_scale_size = Vector2i(640, 400)
	get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	RenderingServer.set_default_clear_color(Color("172b2a"))
	pixel_font.font_names = PackedStringArray(["Consolas", "Courier New"])
	pixel_font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	pixel_font.hinting = TextServer.HINTING_NORMAL
	for id in ["family_home", "oak_tree", "village_well", "storage_chest", "campfire", "crop_plot", "ui_panel", "ui_button", "icon_wood", "icon_food"]:
		var tex := load(ROOT + id + ".png") as Texture2D
		assert(tex != null and tex.get_size() == Vector2(64, 64), "Expected 64x64 asset: " + id)
		textures[id] = tex
		print("ASSET_OK ", id, " ", tex.get_size())
	panel(Rect2(8, 8, 624, 42))
	caption("KINGDOM LOOP", Vector2(20, 21), 15)
	picture("icon_wood", Rect2(206, 12, 32, 32))
	caption("120", Vector2(239, 22), 13)
	picture("icon_food", Rect2(286, 12, 32, 32))
	caption("90", Vector2(319, 22), 13)
	caption("Day 1 / PAUSED", Vector2(448, 22), 12)
	panel(Rect2(8, 58, 400, 246))
	caption("SETTLEMENT", Vector2(24, 70), 14)
	for index in range(ITEMS.size()):
		var p := Vector2(38 + (index % 3) * 125, 95 + int(index / 3.0) * 102)
		var item: Dictionary = ITEMS[index]
		var selector := TextureButton.new()
		selector.position = p
		selector.size = Vector2(64, 64)
		selector.texture_normal = textures[item.id]
		selector.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		selector.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		selector.pressed.connect(select_item.bind(index))
		add_child(selector)
		caption(item.title, p + Vector2(-12, 66), 10)
	panel(Rect2(416, 58, 216, 246))
	selection_title = caption("", Vector2(432, 75), 14)
	selection_picture = picture("family_home", Rect2(489, 101, 64, 64))
	selection_description = caption("", Vector2(432, 174), 11)
	status = caption("64 x 64 / Pixel art", Vector2(432, 214), 11)
	action = button("Place preview", Rect2(432, 245, 184, 40), toggle_placement)
	panel(Rect2(8, 312, 624, 80))
	for index in range(ITEMS.size()):
		var item: Dictionary = ITEMS[index]
		var slot := button("", Rect2(18 + index * 70, 319, 64, 64), select_item.bind(index))
		asset_buttons.append(slot)
		var icon := TextureRect.new()
		icon.texture = textures[item.id]
		icon.size = Vector2(64, 64)
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(icon)
	caption("Choose an asset.\nEsc: cancel\nRight click: clear", Vector2(450, 331), 11)
	ghost = Sprite2D.new()
	ghost.centered = false
	ghost.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	ghost.modulate = Color(1, 1, 1, 0.6)
	ghost.visible = false
	ghost.z_index = 10
	add_child(ghost)
	select_item(0)
	if "--verify-ui" in OS.get_cmdline_user_args():
		verify_controls()
		get_tree().quit()
		return
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path := ProjectSettings.globalize_path("res://../art-source/settlement-ui-64-v1/previews/godot-preview.png")
	print("PREVIEW_CAPTURE ", get_viewport().get_texture().get_image().save_png(path), " ", path)

func panel(rect: Rect2) -> void:
	var p := NinePatchRect.new()
	p.position = rect.position
	p.size = rect.size
	p.texture = textures.ui_panel
	p.patch_margin_left = 12
	p.patch_margin_top = 12
	p.patch_margin_right = 12
	p.patch_margin_bottom = 12
	p.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(p)

func caption(value: String, p: Vector2, font_size: int) -> Label:
	var l := Label.new()
	l.text = value
	l.position = p
	l.add_theme_font_override("font", pixel_font)
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", Color("422d24"))
	l.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l

func picture(id: String, rect: Rect2) -> Sprite2D:
	var p := Sprite2D.new()
	p.texture = textures[id]
	p.centered = false
	p.position = rect.position
	p.scale = rect.size / 64.0
	p.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(p)
	return p

func button(value: String, rect: Rect2, callback: Callable) -> Button:
	var b := Button.new()
	b.position = rect.position
	b.size = rect.size
	b.text = value
	b.add_theme_font_override("font", pixel_font)
	b.add_theme_font_size_override("font_size", 12)
	b.add_theme_color_override("font_color", Color("fff0c8"))
	b.add_theme_color_override("font_hover_color", Color("fff0c8"))
	b.add_theme_color_override("font_pressed_color", Color("fff0c8"))
	for state in ["normal", "hover", "pressed", "focus"]:
		var skin := StyleBoxTexture.new()
		skin.texture = textures.ui_button
		for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
			skin.set_texture_margin(side, 12)
		if state == "hover":
			skin.modulate_color = Color(1.15, 1.15, 1.15)
		elif state == "pressed":
			skin.modulate_color = Color(0.8, 0.8, 0.8)
		b.add_theme_stylebox_override(state, skin)
	b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.pressed.connect(callback)
	add_child(b)
	return b

func select_item(index: int) -> void:
	selected = index
	placing = false
	selection_title.text = ITEMS[index].title
	selection_description.text = ITEMS[index].description
	selection_picture.texture = textures[ITEMS[index].id]
	status.text = "64 x 64 / Pixel art"
	action.text = "Place preview"
	if ghost != null:
		ghost.visible = false

func toggle_placement() -> void:
	placing = not placing
	ghost.texture = textures[ITEMS[selected].id]
	action.text = "Cancel placement" if placing else "Place preview"
	status.text = "Click inside the town" if placing else "64 x 64 / Pixel art"

func _process(_delta: float) -> void:
	if ghost != null:
		var mouse := get_global_mouse_position()
		ghost.visible = placing and Rect2(24, 91, 368, 192).has_point(mouse)
		ghost.position = (mouse - Vector2(32, 48)).snapped(Vector2(8, 8)).clamp(Vector2(24, 96), Vector2(328, 216))

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		placing = false
		if action != null:
			action.text = "Place preview"
			status.text = "64 x 64 / Pixel art"
	if event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			for placed in placed_objects:
				placed.queue_free()
			placed_objects.clear()
		elif event.button_index == MOUSE_BUTTON_LEFT and placing and ghost.visible and Rect2(24, 91, 368, 192).has_point(event.position):
			var placed := Sprite2D.new()
			placed.texture = ghost.texture
			placed.centered = false
			placed.position = ghost.position
			placed.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			placed.z_index = 5
			add_child(placed)
			placed_objects.append(placed)
			get_viewport().set_input_as_handled()

func verify_controls() -> void:
	asset_buttons[5].pressed.emit()
	assert(selected == 5 and selection_title.text == "Vegetable garden")
	assert(selection_picture.texture == textures.crop_plot)
	action.pressed.emit()
	assert(placing and ghost.texture == textures.crop_plot)
	ghost.visible = true
	ghost.position = Vector2(96, 120)
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = Vector2(128, 168)
	_input(click)
	assert(placed_objects.size() == 1)
	assert(placed_objects[0].position == Vector2(96, 120))
	assert(placed_objects[0].texture == textures.crop_plot)
	click.button_index = MOUSE_BUTTON_RIGHT
	_input(click)
	assert(placed_objects.is_empty())
	var escape := InputEventKey.new()
	escape.pressed = true
	escape.keycode = KEY_ESCAPE
	_input(escape)
	assert(not placing and action.text == "Place preview")
	asset_buttons[2].pressed.emit()
	assert(selected == 2 and not placing and not ghost.visible)
	var report := {"asset_selection": true, "placement_button": true, "placement_click": true,
		"clear_placements": true, "cancel_placement": true, "source_canvas": "64x64", "characters": "excluded"}
	var path := ProjectSettings.globalize_path("res://../art-source/settlement-ui-64-v1/ui-verification.json")
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	print("UI_CHECKS_OK ", JSON.stringify(report))
