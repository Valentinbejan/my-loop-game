extends SceneTree
const World = preload("res://scripts/game/world.gd")
var passed: Array = []

func check(value: bool, title: String) -> void:
	if not value:
		push_error("FAILED: " + title)
		quit(1)
		assert(value, title)
	passed.append(title)
	print("PASS ", title)

func make_world():
	var w = World.new()
	w.fresh(51421)
	w.save_root = "res://../art-source/demo-v1/test-saves"
	w.s.auto_pause = false
	return w

func _initialize() -> void:
	var w = make_world()
	w.tick(100)
	check(w.s.day == 0, "Town never advances strategic time")
	w.equip("founder", "blade")
	w.equip("founder", "armor")
	check(w.stats(w.person("founder")).attack > 13, "Equipment modifies actual combat statistics")
	check(w.depart(0), "Prepared party can depart")
	var day = float(w.s.day)
	w.s.paused = true
	w.tick(100)
	check(w.s.day == day, "Paused adventure freezes all simulation")
	w.s.paused = false
	w.tick(1)
	check(w.s.day > day, "Unpaused adventure advances strategic time")
	check(w.place_card("grove", 3) and w.place_card("garden", 4), "Terrain cards can be placed on legal route cells")
	check(w.s.journal.has("Fertile grove"), "Adjacent cards discover a permanent combination")
	var cargo_before = w.s.expedition.cargo.duplicate(true)
	check(not w.place_card("garden", 4) and w.s.expedition.cargo == cargo_before, "Consumed cards cannot duplicate rewards")
	w.start_combat(true)
	var rounds = 0
	while w.s.mode == "combat" and rounds < 200:
		w.combat_round()
		rounds += 1
	check(w.s.bosses.has(0), "Equipped founder can defeat the first guardian")
	w.return_home(false)
	check(w.s.mode == "town" and w.s.expedition.is_empty(), "Returning clears temporary expedition state")
	check(w.save_game("regression"), "Save writes successfully")
	var original_day = w.s.day
	w.s.day += 3
	check(w.save_game("regression"), "Atomic replacement of an existing save succeeds")
	check(w.load_game("regression") and w.s.day == original_day + 3, "Save restores calendar without offline progression")
	var file = FileAccess.open(w.save_root.path_join("regression.json"), FileAccess.WRITE)
	file.store_string("broken")
	file.close()
	check(w.load_game("regression") and w.s.day == original_day, "Corrupt primary save recovers the previous backup")
	w = make_world()
	var worker = w.make_person("Worker", "melee", 23, false, "worker")
	w.s.people.append(worker)
	w.add_building("garden", 10, 10, true)
	w.add_building("well", 13, 10, true)
	var food = w.amount("food")
	w.advance_days(3)
	check(w.amount("food") < food, "Unstaffed facilities produce no resources")
	w.assign("worker", "farmer")
	food = w.amount("food")
	w.advance_days(3)
	check(w.amount("food") > food, "Staffed garden feeds the settlement during adventure time")
	w.assign("worker", "builder")
	check(w.build("residence", 10, 14), "Construction reserves materials and accepts a clear plot")
	check(not w.build("residence", 10, 14), "Overlapping construction is rejected")
	w.advance_days(4)
	check(w.count_building("residence") == 1, "Staffed construction completes through the shared calendar")
	w = make_world()
	var mira = w.make_person("Mira", "healer", 25, false, "mira")
	w.s.people.append(mira)
	w.add_building("residence", 10, 10, true)
	for n in range(3):
		w.s.runs = n
		check(w.talk("mira"), "Relationship event %d unlocks after a distinct run" % n)
	check(not w.talk("mira"), "Conversation cannot be farmed by reopening a menu")
	check(w.marry("mira"), "Eligible adults can marry after relationship progression")
	check(w.start_family("mira"), "A supported household can begin pregnancy")
	w.advance_days(281)
	var children = w.s.people.filter(func(p): return not p.parent_ids.is_empty())
	check(children.size() == 1 and children[0].dynasty, "Birth creates a child inheriting resurrection")
	var child = children[0]
	check(not w.toggle_party(child.id), "Children cannot join combat parties")
	w.advance_days(18 * 365 + 1)
	check(w.age_of(child) >= 18, "Child adulthood follows the common calendar")
	check(w.choose_heir(child.id), "An adult dynasty member can be selected as heir")
	w.person("founder").birth = float(w.s.day) - 78 * 365
	w.advance_days(1)
	check(w.s.leader == child.id and not w.s.game_over, "Old age transfers control to the chosen adult heir")
	w = make_world()
	var mortal = w.make_person("Mortal", "melee", 25, false, "mortal")
	w.s.people.append(mortal)
	w.s.party.append("mortal")
	w.equip("founder", "armor")
	w.depart(0)
	w.person("founder").hp = 0
	w.person("founder").incapacitated = true
	mortal.hp = 0
	mortal.incapacitated = true
	w.return_home(true)
	check(w.person("founder").alive and w.person("founder").equipment.get("armor") == "armor", "Resurrection preserves personal equipment")
	check(not mortal.alive, "Mortal allies can be permanently lost after complete defeat")
	check(w.depart(0, true), "A recovering founder can take a recovery expedition")
	w = make_world()
	w.s.resources.wood = 500
	w.s.resources.stone = 500
	w.s.resources.food = 500
	w.s.bosses = [0, 1, 2]
	w.s.people.append(w.make_person("Governor", "ranger", 28, false, "governor"))
	check(w.found_outpost(), "Secured territory can become a governed outpost")
	w.s.outpost_policy = "materials"
	var ore = w.amount("ore")
	w.advance_days(91)
	check(w.amount("ore") > ore and w.person("governor").job == "governor", "Governed outpost deliveries use adventure time")
	w.add_building("lodge", 10, 10, true)
	var scout = w.make_person("Scout", "ranger", 28, false, "scout")
	w.s.people.append(scout)
	check(w.dispatch("gather", "scout", true), "An available adult can be dispatched with supplies")
	w.advance_days(91)
	check(w.s.missions.is_empty() and scout.mission == "", "Autonomous mission resolves and releases its fighter")
	w = make_world()
	w.s.rank = 2
	w.s.auto_pause = true
	w.s.next_raid = 100
	w.depart(0)
	w.advance_days(100)
	check(w.s.paused and w.s.day < 100 and w.s.expedition.travel_remaining > 0, "Critical warnings stop large calendar advances without discarding remaining travel")
	var report = {"passed": passed.size(), "checks": passed, "status": "passed"}
	file = FileAccess.open("res://../art-source/demo-v1/systems-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SYSTEMS_OK ", passed.size())
	quit()
