extends Node2D
var world
func _ready():
	get_window().size = Vector2i(1280, 720)
	get_window().content_scale_size = Vector2i(640, 360)
	get_window().content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	world = load("res://scripts/game/world.gd").new()
	world.fresh()
	world.s.buildings.clear()
	world.add_building("residence", 20, 14, true)
	world.add_building("well", 24, 14, true)
	world.add_building("garden", 27, 17, true)
	world.add_building("campfire", 23, 18, true)
	var view = load("res://scripts/game/map_view.gd").new()
	view.world = world
	for id in ["grass", "family_home", "village_well", "crop_plot", "campfire", "oak_tree", "founder", "companion", "thornling", "storage_chest"]:
		view.art[id] = load("res://assets/demo/" + id + ".png")
	view.position = Vector2(90, 54)
	view.camera = Vector2(550, 396)
	add_child(view)
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("F:/my-loop-game/art-source/demo-v1/previews/benchmark.png")
	print("BENCHMARK_CAPTURED")
