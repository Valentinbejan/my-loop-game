class_name KingdomWorld
extends RefCounted

signal changed
signal notice(message: String)
signal combat_started
signal combat_ended

var data: Dictionary = {}
var s: Dictionary = {}
var rng := RandomNumberGenerator.new()
var save_root := "user://kingdom-loop"
var real_accumulator := 0.0
var combat_accumulator := 0.0
var move_accumulator := 0.0

func _init() -> void:
	data = JSON.parse_string(FileAccess.get_file_as_string("res://data/demo.json"))

func fresh(seed_value: int = 9137) -> void:
	rng.seed = seed_value
	s = {"version": 1, "seed": seed_value, "rng_state": rng.state, "day": 0.0, "mode": "town", "paused": false,
		"rank": 0, "resources": {"wood": 180.0, "stone": 100.0, "food": 180.0, "herbs": 25.0, "ore": 20.0, "gold": 80.0, "potions": 8.0, "meals": 15.0, "cloth": 20.0},
		"people": [], "buildings": [], "roads": [], "party": ["founder"], "leader": "founder", "heir": "", "inventory": ["blade", "armor", "charm"],
		"expedition": {}, "combat": {}, "crafts": [], "missions": [], "events": [], "journal": [], "history": [],
		"bosses": [], "rescues": [], "relationships": {}, "pregnancies": [], "next_id": 1, "next_migration": 120.0,
		"next_raid": 730.0, "raid_warning": false, "outpost": false, "outpost_policy": "supplies", "outpost_next": 0.0, "outpost_governor": "",
		"supply_health": 0.4, "meal_health": 0.7, "auto_pause": true, "tutorial": 0, "tutorial_skipped": false,
		"player": [768.0, 544.0], "victory": false, "defeats": 0, "runs": 0, "game_over": false, "revision": 0}
	var founder = make_person("Rowan", "defender", 24, true, "founder")
	founder.job = "leader"
	s.people.append(founder)
	add_building("campfire", 23, 17, true)
	add_building("shelter", 20, 14, true)
	add_building("storage", 26, 14, true)
	for x in range(20, 29):
		s.roads.append([x, 17])
	log_event("Founding", "Rowan reaches a quiet clearing. Rescue residents on the frontier to build a home.")
	changed.emit()

func make_person(label: String, role: String, age: int, dynasty: bool = false, fixed_id: String = "") -> Dictionary:
	var ident = fixed_id
	if ident.is_empty():
		ident = "person_%d" % int(s.next_id)
		s.next_id += 1
	var base_stats = data.roles[role]
	return {"id": ident, "name": label, "role": role, "birth": float(s.day) - age * 365.0, "dynasty": dynasty,
		"alive": true, "hp": float(base_stats.hp), "level": 1, "xp": 0, "job": "idle", "equipment": {}, "injury_until": 0.0,
		"spouse": false, "parent_ids": [], "education": "ranger", "history": ["Joined the settlement"], "morale": 80.0,
		"last_age": age, "old_warned": false, "mission": "", "incapacitated": false, "poison": 0,
		"formation": "front" if role in ["defender", "melee"] else "rear" if role in ["healer", "ranger"] else "middle"}

func person(ident: String) -> Dictionary:
	for p in s.people:
		if p.id == ident:
			return p
	return {}

func living() -> Array:
	return s.people.filter(func(p): return p.alive)

func age_of(p: Dictionary) -> int:
	return int(maxf(0.0, (float(s.day) - float(p.birth)) / 365.0))

func definition(group: String, ident: String) -> Dictionary:
	for entry in data[group]:
		if entry.id == ident:
			return entry
	return {}

func stats(p: Dictionary) -> Dictionary:
	var base = data.roles[p.role]
	var level = int(p.level)
	var result = {"hp": float(base.hp) + (level - 1) * 10, "attack": float(base.attack) + (level - 1) * 2, "defense": float(base.defense) + (level - 1)}
	for item in p.equipment.values():
		var d = definition("items", item)
		if not d.is_empty():
			for stat in ["hp", "attack", "defense"]:
				result[stat] += d[stat]
	if float(p.injury_until) > float(s.day):
		result.attack *= 0.7
	return result

func amount(resource: String) -> float:
	return float(s.resources.get(resource, 0))

func can_pay(cost: Dictionary) -> bool:
	for key in cost:
		if amount(key) < float(cost[key]):
			return false
	return true

func pay(cost: Dictionary) -> bool:
	if not can_pay(cost):
		return false
	for key in cost:
		s.resources[key] = amount(key) - float(cost[key])
	return true

func grant(rewards: Dictionary) -> void:
	for key in rewards:
		s.resources[key] = minf(capacity(), amount(key) + float(rewards[key]))

func capacity() -> float:
	return 1200.0 + count_building("storage") * 1200.0

func count_building(kind: String) -> int:
	return s.buildings.filter(func(b): return b.kind == kind and float(b.remaining) <= 0).size()

func housing() -> int:
	return 2 + count_building("shelter") * 3 + count_building("residence") * (8 + int(s.rank) * 4)

func defense() -> float:
	var guards = living().filter(func(p): return p.job == "guard" and not s.party.has(p.id)).size()
	return count_building("tower") * 15.0 + count_building("wall") * 5.0 + guards * 8.0 + s.bosses.size() * 5.0

func party_limit() -> int:
	return mini(10, 1 + s.rescues.size() + s.bosses.size() * 2 + int(s.rank))

func log_event(title: String, detail: String) -> void:
	var record = {"day": float(s.day), "title": title, "text": detail}
	s.events.push_front(record)
	s.history.push_front(record.duplicate(true))
	if s.events.size() > 30:
		s.events.resize(30)
	if s.history.size() > 250:
		s.history.resize(250)
	notice.emit(title + ": " + detail)

func failure(message: String) -> bool:
	notice.emit(message)
	return false

func add_building(kind: String, x: int, y: int, immediate: bool = false) -> void:
	var d = definition("buildings", kind)
	var id = "building_%d" % int(s.next_id)
	s.next_id += 1
	s.buildings.append({"id": id, "kind": kind, "x": x, "y": y, "remaining": 0.0 if immediate else float(d.days), "level": 1})

func valid_plot(kind: String, x: int, y: int, ignore: String = "") -> bool:
	var d = definition("buildings", kind)
	var fp = d.footprint
	if x < 3 or y < 3 or x + int(fp[0]) > 45 or y + int(fp[1]) > 28:
		return false
	var target = Rect2i(x, y, int(fp[0]), int(fp[1]))
	for b in s.buildings:
		if b.id == ignore:
			continue
		var other = definition("buildings", b.kind).footprint
		# Preserve one cell of approach space beneath every building.
		var footprint = Rect2i(int(b.x), int(b.y), int(other[0]), int(other[1]) + 1)
		if target.intersects(footprint) or Rect2i(x, y, int(fp[0]), int(fp[1]) + 1).intersects(Rect2i(int(b.x), int(b.y), int(other[0]), int(other[1]))):
			return false
	return true

func build(kind: String, x: int, y: int) -> bool:
	var d = definition("buildings", kind)
	if s.mode != "town":
		return failure("Construction is planned at home.")
	if int(d.rank) > int(s.rank):
		return failure("Requires settlement rank: " + data.ranks[int(d.rank)])
	if not valid_plot(kind, x, y):
		return failure("Choose clear ground with space for the entrance.")
	if not pay(d.cost):
		return failure("Not enough building materials.")
	add_building(kind, x, y, kind in ["campfire", "shelter"])
	if kind not in ["campfire", "shelter"]:
		for p in living():
			if p.job == "idle" and age_of(p) >= 18 and not s.party.has(p.id) and p.mission == "":
				p.job = "builder"
				break
	log_event("Construction planned", d.name + " will progress during adventures when a builder is available.")
	update_rank()
	changed.emit()
	return true

func relocate(id: String, x: int, y: int) -> bool:
	for b in s.buildings:
		if b.id == id:
			if not valid_plot(b.kind, x, y, id):
				return failure("That plot blocks a building or its entrance.")
			if not pay({"wood": 5, "gold": 5}):
				return failure("Relocation costs 5 timber and 5 gold.")
			b.x = x
			b.y = y
			changed.emit()
			return true
	return false

func road(x: int, y: int) -> bool:
	if x < 2 or y < 2 or x > 45 or y > 29:
		return false
	for r in s.roads:
		if int(r[0]) == x and int(r[1]) == y:
			return false
	if not pay({"stone": 1}):
		return failure("A road cell costs 1 stone.")
	s.roads.append([x, y])
	changed.emit()
	return true

func assign(id: String, job: String) -> bool:
	var p = person(id)
	if p.is_empty() or not p.alive or age_of(p) < 18 or p.mission != "" or id == s.leader:
		return failure("This resident is not available for that job.")
	if s.party.has(id):
		s.party.erase(id)
	p.job = job
	changed.emit()
	return true

func toggle_party(id: String) -> bool:
	var p = person(id)
	if s.mode not in ["town", "home"]:
		return failure("Change companions at home.")
	if id == s.leader:
		return failure("The expedition leader must remain in the party.")
	if s.party.has(id):
		s.party.erase(id)
		changed.emit()
		return true
	if p.is_empty() or not p.alive or age_of(p) < 18 or p.mission != "":
		return failure("Only available adults can join an expedition.")
	if s.party.size() >= party_limit():
		return failure("Party capacity is %d. Progress the settlement to expand it." % party_limit())
	s.party.append(id)
	p.job = "adventurer"
	changed.emit()
	return true

func equip(id: String, item_id: String) -> bool:
	var p = person(id)
	var d = definition("items", item_id)
	if p.is_empty() or d.is_empty() or not s.inventory.has(item_id):
		return failure("That equipment is no longer available.")
	if s.mode == "combat":
		return failure("Change equipment outside combat.")
	if p.equipment.has(d.slot):
		s.inventory.append(p.equipment[d.slot])
	p.equipment[d.slot] = item_id
	s.inventory.erase(item_id)
	p.hp = minf(p.hp, stats(p).hp)
	changed.emit()
	return true

func craft(recipe_id: String) -> bool:
	var d = definition("recipes", recipe_id)
	var item = false
	if d.is_empty():
		d = definition("items", recipe_id)
		item = true
	if d.is_empty():
		return false
	var building = "smithy" if item else str(d.building)
	if count_building(building) == 0:
		return failure("Build a " + definition("buildings", building).name + " first.")
	if not pay(d.cost):
		return failure("Not enough crafting materials.")
	s.crafts.append({"id": recipe_id, "item": item, "remaining": 5.0 if item else float(d.days), "building": building})
	changed.emit()
	return true

func worker_count(job: String) -> int:
	return living().filter(func(p): return p.job == job and age_of(p) >= 18 and not s.party.has(p.id) and p.mission == "").size()

func forecast(days: float) -> Dictionary:
	var farmers = worker_count("farmer")
	var plots = count_building("garden") + count_building("field") + count_building("pen")
	var production = mini(farmers, plots) * (5.0 + minf(2.0, count_building("well")))
	var need = living().size() * 0.2
	return {"food_per_day": production - need, "food_after": maxf(0.0, amount("food") + (production - need) * days), "days": days, "builders": worker_count("builder")}

func tick(delta: float) -> void:
	if s.is_empty() or s.paused or s.game_over or s.mode not in ["expedition", "combat"]:
		return
	var region = data.regions[int(s.expedition.region)]
	if float(s.expedition.get("travel_remaining", 0)) > 0:
		var travel_step = minf(float(s.expedition.travel_remaining), delta * 30)
		s.expedition.travel_remaining -= travel_step
		advance_days(travel_step)
		return
	advance_days(delta * float(region.days_per_second))
	if s.paused or s.game_over: return
	if s.mode == "combat":
		combat_accumulator += delta
		if combat_accumulator >= 1.0:
			combat_accumulator -= 1.0
			combat_round()
	elif s.mode == "expedition":
		move_accumulator += delta
		if move_accumulator >= 2.4:
			move_accumulator -= 2.4
			step_route()
	s.rng_state = str(rng.state)

func advance_days(days: float) -> void:
	# All callers represent elapsed adventure or disclosed expedition travel.
	var left = days
	while left > 0.0001:
		var step = minf(left, 1.0)
		s.day += step
		left -= step
		simulate_day(step)
		if s.paused or s.game_over:
			if not s.expedition.is_empty(): s.expedition.travel_remaining = float(s.expedition.get("travel_remaining", 0)) + left
			break
	update_rank()

func simulate_day(dt: float) -> void:
	var f = forecast(dt)
	s.resources.food = clampf(amount("food") + float(f.food_per_day) * dt, 0.0, capacity())
	var builders = worker_count("builder")
	for b in s.buildings:
		if float(b.remaining) > 0 and builders > 0:
			b.remaining = maxf(0.0, float(b.remaining) - dt * builders)
			if b.remaining <= 0:
				log_event("Building complete", definition("buildings", b.kind).name + " is ready for use.")
	var gatherers = worker_count("gatherer")
	grant({"wood": gatherers * 1.2 * dt, "stone": gatherers * 0.7 * dt, "herbs": mini(worker_count("herbalist"), count_building("herbalist")) * 0.8 * dt})
	for c in s.crafts.duplicate():
		var job = "smith" if c.item else {"kitchen": "cook", "herbalist": "herbalist", "tailor": "tailor"}.get(c.building, "smith")
		if worker_count(job) <= 0:
			continue
		c.remaining -= dt * worker_count(job)
		if c.remaining <= 0:
			if c.item:
				s.inventory.append(c.id)
			else:
				grant(definition("recipes", c.id).reward)
			s.crafts.erase(c)
			log_event("Crafting complete", (definition("items", c.id) if c.item else definition("recipes", c.id)).name)
	for p in living():
		var age = age_of(p)
		if age >= 18 and int(p.last_age) < 18:
			p.role = p.education
			p.hp = stats(p).hp
			p.history.append("Came of age")
			log_event("Coming of age", p.name + " can now train, work, and join expeditions.")
		p.last_age = age
		p.morale = clampf(float(p.morale) + (0.04 if amount("food") > 0 else -0.15) * dt, 10.0, 100.0)
		if living().size() > housing():
			p.morale = maxf(10.0, p.morale - dt * 0.06)
		if not s.party.has(p.id) and p.mission == "":
			p.hp = minf(stats(p).hp, float(p.hp) + dt * (0.8 + mini(count_building("infirmary"), worker_count("doctor")) * 2.0))
			if count_building("school") > 0 and age < 18 and worker_count("teacher") > 0:
				p.xp += dt * 0.01
			if count_building("training") > 0 and p.job == "trainee":
				p.xp += dt * 0.07
		if p.xp >= int(p.level) * 20 and int(p.level) < 12:
			p.xp = 0
			p.level += 1
		if age >= 65 and not p.old_warned:
			p.old_warned = true
			log_event("Plan for succession", p.name + " is entering old age. Choose an adult dynasty heir.")
		if age >= 78:
			p.alive = false
			p.history.append("Died of old age")
			s.party.erase(p.id)
			log_event("A life remembered", p.name + " has died of old age.")
			if p.id == s.leader:
				succeed()
	for pregnancy in s.pregnancies.duplicate():
		if float(s.day) >= float(pregnancy.due):
			var mother = person(pregnancy.mother)
			if mother.alive:
				var names = ["Elian", "Aster", "Wren", "Liora", "Finn", "Iris", "Theo", "Nell"]
				var child = make_person(names[int(s.next_id) % names.size()], "ranger", 0, true)
				child.parent_ids = [pregnancy.father, pregnancy.mother]
				child.job = "child"
				s.people.append(child)
				log_event("A new family member", mother.name + " welcomes " + child.name + ". The child inherits resurrection.")
			s.pregnancies.erase(pregnancy)
	for m in s.missions.duplicate():
		if float(s.day) >= float(m.due):
			resolve_mission(m)
	if s.outpost and float(s.day) >= float(s.outpost_next) and not person(s.outpost_governor).is_empty() and person(s.outpost_governor).alive:
		s.outpost_next = float(s.day) + 90
		grant({"ore": 35, "gold": 25} if s.outpost_policy == "materials" else {"food": 90, "wood": 45})
		log_event("Outpost delivery", "The secured road brings supplies to the capital.")
	if float(s.day) >= float(s.next_migration):
		s.next_migration = float(s.day) + 180
		if housing() > living().size() and amount("food") > 30 and living().size() < 24 and s.rescues.size() > 0:
			recruit_resident()
	if int(s.rank) >= 2 and float(s.day) >= float(s.next_raid) - 60 and not s.raid_warning:
		s.raid_warning = true
		log_event("Raid warning", "Monster pressure is rising. The settlement needs at least %d defense." % (15 + int(s.rank) * 8))
		if s.auto_pause:
			s.paused = true
	if float(s.day) >= float(s.next_raid):
		s.next_raid = float(s.day) + 730
		s.raid_warning = false
		if int(s.rank) >= 2:
			var defended = defense() >= 15 + int(s.rank) * 8
			if not defended:
				s.resources.wood = amount("wood") * 0.85
				s.resources.food = amount("food") * 0.85
			log_event("Raid repelled" if defended else "Raid damage", "The guards protected the settlement." if defended else "Poor defenses cost 15% of stored timber and food. No residents were lost.")

func recruit_resident() -> void:
	var names = ["Tovin", "Bran", "Nessa", "Corin", "Faye", "Oren", "Tess", "Ari", "Galen", "Petra", "Lark", "Reed"]
	var roles = ["melee", "ranger", "healer", "mage", "defender"]
	var p = make_person(names[int(s.next_id) % names.size()], roles[int(s.next_id) % roles.size()], rng.randi_range(20, 32))
	p.job = "farmer" if worker_count("farmer") == 0 else "gatherer"
	s.people.append(p)
	log_event("A new resident", p.name + " joins the settlement, drawn by shelter and food.")

func update_rank() -> void:
	var count = s.buildings.filter(func(b): return b.remaining <= 0).size()
	var next = 0
	if count >= 4 and living().size() >= 2:
		next = 1
	if count >= 7 and living().size() >= 4 and s.bosses.size() >= 1:
		next = 2
	if count >= 10 and living().size() >= 7 and s.bosses.size() >= 2:
		next = 3
	if count >= 12 and living().size() >= 10 and s.outpost and defense() >= 30:
		next = 4
	if next > int(s.rank):
		s.rank = next
		log_event("Settlement grows", "Your settlement is now a " + data.ranks[next] + ".")

func talk(id: String) -> bool:
	var p = person(id)
	if p.is_empty() or not p.alive:
		return false
	if id not in ["mira", "sera"]:
		return failure(p.name + ": " + ("I look forward to our next journey." if s.party.has(id) else "A safe home and steady meals make all the difference."))
	var rel = s.relationships.get(id, {"bond": 0, "last_run": -1, "last_birth": -1000.0})
	if int(rel.last_run) == int(s.runs):
		return failure("You have shared today's conversation. Return from another expedition for a new event.")
	rel.last_run = s.runs
	rel.bond = mini(5, int(rel.bond) + 1)
	s.relationships[id] = rel
	var lines = ["Thank you for making a place for me here.", "I believe in the home we are building together.", "After all we have faced, I would gladly share a life with you.", "Our family gives these journeys meaning.", "Whatever comes next, we will face it together."]
	log_event("A conversation with " + p.name, lines[int(rel.bond) - 1])
	changed.emit()
	return true

func marry(id: String) -> bool:
	var p = person(id)
	var rel = s.relationships.get(id, {})
	if p.is_empty() or p.spouse or int(rel.get("bond", 0)) < 3 or age_of(p) < 18 or not p.alive:
		return failure("Marriage requires three shared relationship events and a willing adult partner.")
	if count_building("residence") == 0:
		return failure("Build the family residence before making this commitment.")
	p.spouse = true
	p.history.append("Married " + person(s.leader).name)
	log_event("A shared future", p.name + " freely chooses to join your household in marriage.")
	changed.emit()
	return true

func start_family(id: String) -> bool:
	var p = person(id)
	if p.is_empty() or not p.spouse or not p.alive or age_of(p) >= 45:
		return failure("This partner is not currently eligible to begin a pregnancy.")
	if s.pregnancies.any(func(v): return v.mother == id):
		return failure("This household is already expecting a child.")
	var rel = s.relationships[id]
	if float(s.day) - float(rel.last_birth) < 500:
		return failure("Allow time for the household to recover before another pregnancy.")
	if housing() <= living().size() + s.pregnancies.size() or amount("food") < 80:
		return failure("The household needs room and at least 80 food in reserve.")
	rel.last_birth = float(s.day)
	s.pregnancies.append({"mother": id, "father": s.leader, "due": float(s.day) + 280})
	log_event("Expecting a child", p.name + " is expecting. Birth follows the shared adventure calendar.")
	changed.emit()
	return true

func choose_heir(id: String) -> bool:
	var p = person(id)
	if p.is_empty() or not p.alive or not p.dynasty or age_of(p) < 18 or id == s.leader:
		return failure("Choose a living adult dynasty member.")
	s.heir = id
	log_event("Succession secured", p.name + " is the chosen heir.")
	return true

func succeed() -> void:
	var heir = person(s.heir)
	if heir.is_empty() or not heir.alive or age_of(heir) < 18:
		s.game_over = true
		s.paused = true
		log_event("The dynasty ends", "There is no eligible chosen heir. Load an earlier save to change the outcome.")
		return
	s.leader = heir.id
	heir.job = "leader"
	heir.mission = ""
	s.missions = s.missions.filter(func(m): return m.person != heir.id)
	s.heir = ""
	if not s.party.has(heir.id):
		s.party.push_front(heir.id)
	log_event("A new ruler", heir.name + " inherits the kingdom and the family legacy.")

func dispatch(mission_id: String, person_id: String, cautious: bool = true) -> bool:
	var d = definition("missions", mission_id)
	var p = person(person_id)
	if count_building("lodge") == 0:
		return failure("Build the expedition lodge first.")
	if p.is_empty() or not p.alive or age_of(p) < 18 or s.party.has(person_id) or p.mission != "":
		return failure("Choose an available adult outside the active party.")
	if not pay({"food": d.cost}):
		return failure("Not enough food for the mission.")
	p.mission = mission_id
	s.missions.append({"id": mission_id, "person": person_id, "due": float(s.day) + float(d.days), "cautious": cautious})
	changed.emit()
	return true

func resolve_mission(m: Dictionary) -> void:
	var p = person(m.person)
	var d = definition("missions", m.id)
	var risk = maxf(0.01, float(d.risk) - float(p.level) * 0.01 - stats(p).defense * 0.003)
	if m.cautious:
		risk *= 0.4
	var failed = rng.randf() < risk
	p.mission = ""
	if failed:
		p.injury_until = float(s.day) + 90
		log_event("Mission retreat", p.name + " returned injured after an unsafe encounter. The retreat policy saved the party.")
	else:
		grant(d.reward)
		p.xp += 12
		if m.id == "rescue" and housing() > living().size():
			recruit_resident()
		log_event("Mission complete", p.name + " returned with supplies and experience.")
	s.missions.erase(m)

func found_outpost() -> bool:
	if s.outpost:
		return failure("The outpost is already established.")
	if not s.bosses.has(2):
		return failure("Secure the highland pass first.")
	var governors = living().filter(func(p): return age_of(p) >= 18 and not s.party.has(p.id) and p.mission == "")
	if governors.is_empty():
		return failure("An available adult outside the party must govern the outpost.")
	if not pay({"wood": 150, "stone": 100, "food": 80}):
		return failure("Outpost: 150 timber, 100 stone, 80 food.")
	s.outpost = true
	s.outpost_governor = governors[0].id
	governors[0].job = "governor"
	s.outpost_next = float(s.day) + 90
	log_event("A road to the kingdom", "The highland outpost and its supply road are established.")
	update_rank()
	changed.emit()
	return true

func depart(region_index: int, recovery: bool = false) -> bool:
	if s.mode not in ["town", "home", "map"] or s.game_over:
		return failure("Return home before starting a new expedition.")
	if region_index > 0 and not s.bosses.has(region_index - 1):
		return failure("Defeat the previous region's guardian first.")
	if region_index == 3 and int(s.rank) < 3:
		return failure("The final campaign requires a city and a prepared party.")
	var required = 18 + s.party.size() * 8
	if not recovery and amount("food") < required + living().size() * 3:
		return failure("Reserve food for residents or take a short recovery expedition.")
	var supplied = minf(amount("food"), 55 + s.party.size() * 15)
	s.resources.food -= supplied
	var potions = minf(amount("potions"), 3 + s.party.size())
	s.resources.potions -= potions
	var meals = minf(amount("meals"), 4 + s.party.size())
	s.resources.meals -= meals
	var route = []
	var top = rng.randi_range(1, 2)
	for x in range(2, 12): route.append([x, top])
	for y in range(top + 1, 7): route.append([11, y])
	for x in range(10, 1, -1): route.append([x, 6])
	for y in range(5, top, -1): route.append([2, y])
	var hand = ["grove", "garden", "shelter", "bramble_den", "outcrop"]
	for c in range(mini(region_index + 2, 7)): hand.append(data.cards[rng.randi_range(0, data.cards.size() - 1)].id)
	s.expedition = {"region": region_index, "route": route, "position": 0, "circuit": 1, "threat": 0.0, "cards": {}, "hand": hand,
		"food": supplied, "potions": potions, "meals": meals, "cargo": {}, "loot": [], "rescued": [], "start_day": float(s.day),
		"kills": 0, "boss_won": false, "recovery": recovery, "travel_remaining": 0.0}
	for id in s.party:
		var p = person(id)
		p.incapacitated = false
		p.hp = maxf(float(p.hp), stats(p).hp * 0.65)
	s.mode = "expedition"
	s.paused = false
	move_accumulator = 0
	combat_accumulator = 0
	advance_days(1.0 if recovery else float(data.regions[region_index].travel_days))
	autosave()
	changed.emit()
	return true

func cargo(reward: Dictionary) -> void:
	var used = 0.0
	for v in s.expedition.cargo.values(): used += float(v)
	var cap = 150 + s.party.size() * 60
	for key in reward:
		var accepted = minf(float(reward[key]), maxf(0, cap - used))
		s.expedition.cargo[key] = float(s.expedition.cargo.get(key, 0)) + accepted
		used += accepted

func place_card(card_id: String, index: int) -> bool:
	if s.mode not in ["expedition", "combat"] or not s.expedition.hand.has(card_id):
		return false
	if index <= 0 or index >= s.expedition.route.size():
		return failure("The departure camp cannot be replaced.")
	var key = str(index)
	var d = definition("cards", card_id)
	if d.effect == "remove":
		if not s.expedition.cards.has(key): return failure("Choose an occupied card tile.")
		s.expedition.cards.erase(key)
		cargo({"wood": 8})
	else:
		if s.expedition.cards.has(key): return failure("That tile already has a card.")
		s.expedition.cards[key] = card_id
		s.expedition.threat = minf(100, float(s.expedition.threat) + 9)
	s.expedition.hand.erase(card_id)
	for neighbor in [str(index - 1), str(index + 1)]:
		if s.expedition.cards.has(neighbor):
			var pair = [card_id, s.expedition.cards[neighbor]]
			var combo = ""
			if pair.has("grove") and pair.has("garden"): combo = "Fertile grove"
			if pair.has("garden") and pair.has("spring"): combo = "Irrigated garden"
			if pair.has("herbs") and pair.has("spring"): combo = "Restorative bank"
			if not combo.is_empty():
				cargo({"food": 15, "herbs": 6})
				if not s.journal.has(combo):
					s.journal.append(combo)
					log_event("Combination discovered", combo + " improves gathering on this route.")
	changed.emit()
	return true

func step_route() -> void:
	var e = s.expedition
	e.position = (int(e.position) + 1) % e.route.size()
	if int(e.position) == 0:
		e.circuit += 1
		e.threat = minf(100, float(e.threat) + 20)
		for id in s.party:
			var p = person(id)
			if p.alive and not p.incapacitated: p.hp = minf(stats(p).hp, float(p.hp) + stats(p).hp * 0.12)
		log_event("Circuit %d" % int(e.circuit), "Enemies grow stronger. The camp is a safe place to return.")
		if e.recovery and int(e.circuit) > 1:
			return_home(false)
			return
	e.food = maxf(0.0, float(e.food) - 0.35 * s.party.size())
	if e.food <= 0:
		for id in s.party:
			var p = person(id)
			p.hp = maxf(1, float(p.hp) - 2)
	var index = int(e.position)
	var card = definition("cards", str(e.cards.get(str(index), "")))
	if not card.is_empty():
		match card.effect:
			"wood": cargo({"wood": 12})
			"stone": cargo({"stone": 10, "ore": 4})
			"food": cargo({"food": 18})
			"herbs": cargo({"herbs": 12})
			"heal", "spring":
				for id in s.party:
					var p = person(id)
					if not p.incapacitated: p.hp = minf(stats(p).hp, float(p.hp) + stats(p).hp * 0.2)
			"beacon": e.threat = maxf(0, float(e.threat) - 4)
			"ore": cargo({"ore": 16})
	if index == 4 and int(e.circuit) == 1:
		var region = int(e.region)
		if region < 2 and not s.rescues.has(region):
			e.rescued.append(region)
			log_event("Survivor found", "A traveler needs a safe home. Return to bring them into the settlement.")
	if index % 4 == 0 and index > 0:
		cargo({"wood": 5, "stone": 4, "food": 4, "gold": 3})
		if e.hand.size() < 10: e.hand.append(data.cards[rng.randi_range(0, data.cards.size() - 1)].id)
	if index > 0 and (index % 5 == 0 or card.get("effect", "") in ["den", "treasure", "ore"]):
		start_combat(false, card.get("effect", "") == "treasure")
	changed.emit()

func challenge_boss() -> bool:
	if s.mode != "expedition" or s.expedition.threat < 100:
		return failure("Place cards and complete encounters to fill the threat meter.")
	if s.expedition.boss_won:
		return failure("This expedition has already defeated its guardian.")
	if int(s.expedition.region) == 3 and int(s.rank) < 4:
		return failure("Establish a defended kingdom and its outpost before challenging the Hollow King.")
	start_combat(true)
	return true

func start_combat(boss: bool, elite: bool = false) -> void:
	var e = s.expedition
	var r = data.regions[int(e.region)]
	var enemies = []
	var count = 1 if boss else mini(4, 1 + int(int(e.region) / 2.0) + int((int(e.circuit) - 1) / 2.0))
	for i in range(count):
		var id = r.boss if boss else r.enemy[rng.randi_range(0, 1)]
		var d = {"hp": r.boss_hp, "attack": r.attack, "name": r.boss_name} if boss else data.enemies[id]
		var mult = 1.0 + (int(e.circuit) - 1) * 0.2 + (0.4 if elite else 0.0)
		var hp = float(d.hp) * mult
		enemies.append({"id": id, "name": d.name, "hp": hp, "max_hp": hp, "attack": float(d.attack) * mult, "flash": 0.0})
	s.combat = {"enemies": enemies, "boss": boss, "round": 0, "log": ["The party takes its formation."], "impact": "", "impact_kind": "attack"}
	s.mode = "combat"
	combat_accumulator = 0
	s.paused = false
	combat_started.emit()
	changed.emit()

func battle_log(line: String) -> void:
	s.combat.log.push_front(line)
	if s.combat.log.size() > 8: s.combat.log.resize(8)

func active_party() -> Array:
	var members = []
	for id in s.party:
		var p = person(id)
		if not p.is_empty() and p.alive and not p.incapacitated and float(p.hp) > 0: members.append(p)
	return members

func combat_round() -> void:
	if s.mode != "combat": return
	var c = s.combat
	c.round += 1
	var party = active_party()
	for p in party:
		if int(p.get("poison", 0)) > 0:
			p.hp = maxf(1, float(p.hp) - 2)
			p.poison -= 1
		var targets = c.enemies.filter(func(e): return float(e.hp) > 0)
		if targets.is_empty():
			win_combat()
			return
		if p.role == "healer" and int(c.round) % 3 == 0:
			var injured = party.duplicate()
			injured.sort_custom(func(a, b): return a.hp / stats(a).hp < b.hp / stats(b).hp)
			var target = injured[0]
			target.hp = minf(stats(target).hp, float(target.hp) + 18 + int(p.level) * 3)
			battle_log(p.name + " restores " + target.name + ".")
		else:
			var victim = targets[0]
			if p.role == "ranger":
				targets.sort_custom(func(a, b): return a.hp < b.hp)
				victim = targets[0]
			var damage = stats(p).attack * rng.randf_range(0.85, 1.15)
			if victim.id in ["golem", "sentinel"]: damage *= 0.8
			victim.hp = maxf(0, float(victim.hp) - damage)
			if (p.role == "mage" and int(c.round) % 3 == 0) or (p.role == "melee" and int(c.round) % 4 == 0):
				for other in targets:
					if other != victim: other.hp = maxf(0, float(other.hp) - damage * 0.45)
			c.impact = p.id
			c.impact_kind = "attack"
			battle_log(p.name + " hits " + victim.name + " for %d." % int(damage))
		if float(p.hp) < stats(p).hp * float(s.supply_health) and s.expedition.potions >= 1:
			s.expedition.potions -= 1
			p.hp = minf(stats(p).hp, float(p.hp) + stats(p).hp * 0.55)
			battle_log(p.name + " uses a healing mixture.")
	if c.enemies.all(func(e): return e.hp <= 0):
		win_combat()
		return
	if int(c.round) % 2 == 0:
		for foe in c.enemies:
			if foe.hp <= 0: continue
			party = active_party()
			if party.is_empty(): break
			var front = party.filter(func(p): return p.get("formation", "middle") == "front")
			var target = front[rng.randi_range(0, front.size() - 1)] if not front.is_empty() else party[0]
			if foe.id in ["harpy", "moth"]:
				var rear = party.filter(func(p): return p.get("formation", "middle") == "rear")
				if not rear.is_empty(): target = rear[rng.randi_range(0, rear.size() - 1)]
			var guard = false
			for key in s.expedition.cards:
				if s.expedition.cards[key] == "watch" and absi(int(key) - int(s.expedition.position)) <= 1: guard = true
			var damage = maxf(2, float(foe.attack) - stats(target).defense) * (0.8 if guard else 1.0)
			if foe.id in ["boar", "iron_hart"] and int(c.round) % 6 == 0: damage *= 1.7
			if foe.id == "moth": target.poison = 3
			if foe.id in ["slime", "marsh_matron"] and int(c.round) % 6 == 0: foe.hp = minf(foe.max_hp, foe.hp + foe.max_hp * 0.07)
			if foe.id == "wraith": foe.hp = minf(foe.max_hp, foe.hp + damage * 0.4)
			if foe.id == "hollow_king" and int(c.round) % 6 == 0:
				for ally in party:
					ally.hp = maxf(1, float(ally.hp) - maxf(3, 17 - stats(ally).defense))
				battle_log("The Hollow King's shockwave strikes the formation.")
			target.hp = maxf(0, float(target.hp) - damage)
			c.impact = target.id
			c.impact_kind = "hurt"
			battle_log(foe.name + " hits " + target.name + " for %d." % int(damage))
			if target.hp <= 0:
				target.incapacitated = true
				log_event("Fighter incapacitated", target.name + " has fallen. Retreat now to bring them home safely.")
				if s.auto_pause: s.paused = true
	if active_party().is_empty():
		return_home(true)
	elif active_party().any(func(p): return p.hp < stats(p).hp * 0.15) and s.auto_pause:
		s.paused = true
	changed.emit()

func win_combat() -> void:
	var e = s.expedition
	e.kills += 1
	e.threat = minf(100, float(e.threat) + 16)
	cargo({"wood": 8, "stone": 6, "gold": 8 + int(e.region) * 4, "ore": 3 + int(e.region) * 3})
	for p in active_party():
		p.xp += 7
		if p.hp < stats(p).hp * float(s.meal_health) and e.meals >= 1:
			e.meals -= 1
			p.hp = minf(stats(p).hp, p.hp + stats(p).hp * 0.25)
	if rng.randf() < 0.35:
		e.loot.append(data.items[rng.randi_range(0, mini(5, int(e.region) * 2 + 1))].id)
	if s.combat.boss:
		e.boss_won = true
		if not s.bosses.has(int(e.region)):
			s.bosses.append(int(e.region))
			grant(data.regions[int(e.region)].reward)
		log_event("Guardian defeated", data.regions[int(e.region)].boss_name + " falls. The region is secured.")
		if int(e.region) == 3:
			s.victory = true
			return_home(false)
			s.mode = "victory"
			return
	s.mode = "expedition"
	s.combat = {}
	combat_ended.emit()
	changed.emit()

func return_home(defeated: bool = false) -> void:
	if s.expedition.is_empty(): return
	var e = s.expedition
	var safe = int(e.position) == 0 or e.boss_won or e.recovery
	var keep = 0.5 if defeated else (1.0 if safe else 0.75)
	var retained = {}
	for key in e.cargo: retained[key] = floorf(float(e.cargo[key]) * keep)
	grant(retained)
	grant({"food": e.food, "potions": e.potions, "meals": e.meals})
	for item in e.loot:
		if not defeated or rng.randf() < 0.5: s.inventory.append(item)
	for index in e.rescued:
		if not s.rescues.has(int(index)) and not defeated:
			var d = data.romances[int(index)]
			var p = make_person(d.name, d.role, int(d.age), false, d.id)
			p.job = "builder"
			s.people.append(p)
			s.rescues.append(int(index))
			log_event("Welcome home", p.name + " joins the settlement and can work or accompany you.")
	for id in s.party.duplicate():
		var p = person(id)
		if p.incapacitated:
			if defeated and not p.dynasty:
				p.alive = false
				s.party.erase(id)
				p.history.append("Lost during a defeated expedition")
				log_event("A companion remembered", p.name + " could not be rescued after the party fell.")
			else:
				p.injury_until = float(s.day) + 90
				p.hp = stats(p).hp * 0.5
				p.incapacitated = false
				log_event("Resurrection" if p.dynasty else "Recovery", p.name + " returns with personal equipment and needs time to recover.")
	if defeated: s.defeats += 1
	s.runs += 1
	s.mode = "town"
	s.paused = false
	s.expedition = {}
	s.combat = {}
	log_event("Expedition report", "Returned with %d%% of cargo after %.0f days. %d encounters completed." % [int(keep * 100), float(s.day) - float(e.start_day), int(e.kills)])
	update_rank()
	autosave()
	changed.emit()

func objectives() -> Array:
	var result = []
	if s.rescues.is_empty(): result.append("Explore the frontier and bring a survivor home.")
	if count_building("residence") == 0: result.append("Build a family residence; assign a builder.")
	if count_building("garden") == 0: result.append("Build a garden and assign a farmer.")
	if s.bosses.is_empty(): result.append("Equip a companion and defeat the Briar Warden.")
	if s.bosses.size() == 1: result.append("Explore Amber Marsh; establish meals and medicine.")
	if count_building("residence") > 0 and not living().any(func(p): return p.spouse): result.append("Share relationship events after returning from adventures.")
	if s.bosses.size() >= 2 and not s.outpost: result.append("Secure the highland pass and found an outpost.")
	if s.bosses.size() == 3 and not s.victory: result.append("Build a city, prepare a large party, defeat the Hollow King.")
	if s.victory: result.append("The kingdom is safe. Continue building your family's future.")
	result.append("Next rank: %s | homes %d/%d | defense %d" % [data.ranks[mini(4, int(s.rank) + 1)], living().size(), housing(), int(defense())])
	return result

func save_game(slot: String) -> bool:
	DirAccess.make_dir_recursive_absolute(save_root)
	s.rng_state = str(rng.state)
	s.revision += 1
	var path = save_root.path_join(slot + ".json")
	var temp = path + ".tmp"
	var file = FileAccess.open(temp, FileAccess.WRITE)
	if file == null: return failure("Save could not be written. Check folder access.")
	file.store_string(JSON.stringify(s))
	file.close()
	if FileAccess.file_exists(path):
		DirAccess.copy_absolute(path, path + ".bak")
	var err = DirAccess.rename_absolute(temp, path)
	return err == OK

func load_game(slot: String) -> bool:
	var path = save_root.path_join(slot + ".json")
	var loaded = read_save(path)
	if loaded.is_empty(): loaded = read_save(path + ".bak")
	if loaded.is_empty(): return failure("That save is unavailable or damaged; choose another slot.")
	s = loaded
	rng.seed = int(s.seed)
	rng.state = int(s.rng_state)
	s.paused = s.mode in ["expedition", "combat"]
	move_accumulator = 0
	combat_accumulator = 0
	changed.emit()
	return true

func read_save(path: String) -> Dictionary:
	if not FileAccess.file_exists(path): return {}
	var parser = JSON.new()
	if parser.parse(FileAccess.get_file_as_string(path)) != OK: return {}
	var d = parser.data
	if not d is Dictionary or int(d.get("version", 0)) != 1: return {}
	for key in ["people", "buildings", "resources", "mode", "party", "day", "expedition", "rng_state"]:
		if not d.has(key): return {}
	return d

func autosave() -> void:
	var slot = "auto_%d" % (int(s.runs) % 3)
	save_game(slot)
	save_game("continue")

