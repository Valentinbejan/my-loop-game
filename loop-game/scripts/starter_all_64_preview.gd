extends Node2D

const ASSETS := [
	{"id": "founder", "title": "Founder", "pixels": 64},
	{"id": "companion", "title": "Healer companion", "pixels": 64},
	{"id": "family_home", "title": "Front-facing cottage", "pixels": 64},
	{"id": "oak_tree", "title": "Oak tree", "pixels": 64},
]

func _ready() -> void:
	get_window().title = "Kingdom Loop - 64 pixel assets"
	get_window().size = Vector2i(1120, 540)
	get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_DISABLED
	RenderingServer.set_default_clear_color(Color("172126"))
	add_label("Kingdom Loop / Compact sprites", Vector2(32, 24), 28, Color("f1e5c7"))
	add_label("All sprites 64 x 64 / Front-only cottage", Vector2(32, 68), 17, Color("b1c4b5"))
	for index in range(ASSETS.size()):
		var asset: Dictionary = ASSETS[index]
		var origin := Vector2(32 + index * 270, 116)
		var path: String = "res://assets/starter-all-64-v1/%s.png" % asset.id
		var texture := load(path) as Texture2D
		assert(texture != null, "Missing asset: " + path)
		assert(texture.get_width() == asset.pixels and texture.get_height() == asset.pixels,
			"Incorrect asset dimensions: " + asset.id)
		var sprite := Sprite2D.new()
		sprite.name = asset.id
		sprite.texture = texture
		sprite.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		var enlargement := 256.0 / float(asset.pixels)
		sprite.scale = Vector2(enlargement, enlargement)
		sprite.position = origin + Vector2(128, 128)
		add_child(sprite)
		add_label(asset.title, origin + Vector2(0, 276), 21, Color("f1e5c7"))
		add_label("%d x %d / %dx preview" % [asset.pixels, asset.pixels, int(enlargement)],
			origin + Vector2(0, 309), 16, Color("b1c4b5"))
		print("ASSET_OK ", asset.id, " ", texture.get_size())
	add_label("Source files remain editable in Aseprite. These are static starter assets.",
		Vector2(32, 485), 16, Color("b1c4b5"))
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var capture := get_viewport().get_texture().get_image()
	var capture_path := ProjectSettings.globalize_path("res://../art-source/starter-all-64-v1/previews/godot-preview.png")
	var result := capture.save_png(capture_path)
	print("PREVIEW_CAPTURE ", result, " ", capture_path)

func add_label(caption: String, location: Vector2, font_size: int, color: Color) -> void:
	var label := Label.new()
	label.text = caption
	label.position = location
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	add_child(label)

func _draw() -> void:
	for index in range(ASSETS.size()):
		var origin := Vector2(32 + index * 270, 116)
		for y in range(16):
			for x in range(16):
				var color := Color("35423c") if (x + y) % 2 == 0 else Color("2a3733")
				draw_rect(Rect2(origin + Vector2(x * 16, y * 16), Vector2(16, 16)), color)

