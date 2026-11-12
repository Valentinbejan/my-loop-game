extends SceneTree
func _initialize():
	var world = load("res://scripts/game/world.gd").new()
	world.fresh()
	assert(world.s.people.size() == 1)
	assert(world.s.mode == "town")
	world.tick(1000)
	assert(world.s.day == 0)
	print("MODEL_SMOKE_OK")
	quit()
