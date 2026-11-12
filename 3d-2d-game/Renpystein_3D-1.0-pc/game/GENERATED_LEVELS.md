# Generated building floors

Starting a new game builds three full building floors once. Enclosed elevators
join floor 1 to 2 and floor 2 to 3, with return trips on the same shafts. Enter a
cabin and press F (or Use Lift on touch); ECHO boards, the doors close, and the
next floor opens after the ride. Only floor 3 has the final exit beacon.
Elevators have no collection or kill-all lock. New runs select one final boss
and a seeded extraction-room cover arrangement. New version 7 runs place an
animated gold boss key on floor 3's MAIN DECK, in a clear reachable room away
from the arena. Placement favors the far side by walking distance. Every arena
entrance is visibly sealed until the key is picked up; collecting it opens all
entrances. The final exit requires both the key and defeating the boss.
Defeating all ordinary enemies and collecting everything remains optional.
An optional 100% clear counts every room, enemy, data pickup and weapon pickup;
unused medicine and decorations do not count. The sector badge shows the level,
current sector name/color, explored rooms, data, gear and overall clear percentage.
The existing bottom HUD shows health, kills and remaining hostiles, including
the inactive local deck. Freight lifts now connect a main deck to UPPER WORKS:
three playable rooms directly above existing rooms at the same XY coordinates.
They remain within the same mission floor. Ride back down on the same lift.
The top-right minimap gradually reveals nearby visible portions of the active
deck in sector colors. Its six-tile survey radius stops at walls and solid
diagonal corners; unseen rooms and lift/exit/ECHO markers stay hidden. Explored
areas remain visible after leaving them. Its header gives the
building floor number and deck name. It switches with the active area and also
works in existing saves and the two original maps. Touch FX/CRT buttons sit below
the map; tapping the map does not attack. Cached map surfaces are excluded from
saves and rebuilt after loading; turning does not rebuild the static layout.
Each combat session saves its own `explored_cells` set, so main/upper decks and
building floors retain independent discovery through save/load and return trips.
Retry clears the occupied deck's discovery along with its exploration checkpoint.
Older saves without survey data start revealing around the current location.

## Layout rules

| Floor | Grid limit | Rooms | Hostiles |
| --- | --- | --- | --- |
| 1 | 56 x 56 | 12 + 3 upper | 20 + 3 upper |
| 2 | 64 x 64 | 15 + 3 upper | 28 + 3 upper |
| 3 | 72 x 72 | 18 + 3 upper | 36 + 3 upper |

Generator version 7 adds boss-key placement and validates reachability with all
arena entrances closed, at both lift stops. Normal unlocked-world validation
still checks the complete level and return routes. Seeded rotations/reflections
transform the key and every gate with the map. Key ownership survives real saves
and building/local-deck travel. Retry restores ownership from the occupied
deck's entry checkpoint. Existing saved definitions without key metadata keep
their original completion rules; start a new run to play the key objective.

Generator version 4 adds aligned upper rooms to each floor and replaces the
gallery platform shortcut with a full-storey freight lift. Existing version 1/2/3
saves keep their saved maps and progression; choose New Game for stacked areas.

- Four sectors have offset randomized boundaries, four different palettes chosen
  from cyan, blue, green, amber, red, violet, white and pink, and a winding order:
  ARRIVAL, REACTOR, LABORATORY, EXTRACTION. Walls, floors, ceilings and props use
  the same explicit sector identity. Corridor mouths use their own sector's color.
- Rooms vary in size, offset and connection, generally 7-11 cells per side.
  Adaptive subdivision supports more than four rooms in a sector. Corridors are at least two cells
  wide. Within-sector loop routes and side rooms allow exploration. Inter-sector
  connections form a progression. The starting room and elevator lobbies stay
  safe; other rooms in the first sector can now contain encounters too.
- One middle sector contains a 16 x 16 vertical module, randomly rotated and
  mirrored: gallery at +0.75, ground circulation, service bay at -0.5, broad
  stairs in 0.125 increments, and a 2 x 2 freight lift. Main ceiling height is 2;
  the shaft reaches 5. Upper rooms have floor 3 and ceiling 5, above the original
  ceiling. More than 40 playable upper cells overlap main-deck playable cells.
  The enclosed shaft has matching XY bounds on both decks. Three upper rooms,
  a two-wide circulation loop, three enemies, three data pickups, healing and
  two weapon/ammo pickups make the destination usable exploration space.
- Gallery and service-bay height changes still have reversible stairs. The upper
  works use the freight lift in both directions. ECHO boards before the gate
  closes; disabled ECHO cannot block travel. The platform actually animates from
  0 to 3 or 3 to 0. At arrival the active deck changes behind the closed gate.
  Only the active deck is rendered; upper/lower rooms cannot be seen through one
  another or fought across storeys. This retains the four-texture GPU limit.
- Each session retains data-only snapshots for inactive local decks: defeated
  enemies, removed pickups, exploration and local state. Health, weapons, ammo
  and ECHO travel with the player. Snapshots also survive building-floor travel.
  Pause freezes the ride; saves preserve the gate phase, elevation and progress.
  Retrying the occupied deck resets that deck while retaining other deck states.
- Two-person elevator cabins have three enclosing walls, a clear two-cell
  entrance, protected boarding/lobby space, blinking signs and a floor-number
  prompt. The middle floor has a return cabin and a separate onward cabin.
- Spawn, exit, stair approaches, shaft perimeter and marked lift landings have
  protected placement space. Props use validated cell centres. Only accepted
  prop designs 0-7 are used; archived expansion designs are excluded.

## Combat and supplies

- Mission one uses sentries, drones and crawlers; heavy robots and turrets begin
  on mission two. Encounters have at most three initial enemies. The entire open
  vertical module shares one three-enemy encounter budget rather than treating
  its three connected rooms as separate fights. Enemies can pursue the player.
- There is no hostile firing line into spawn. All enemies have a reachable
  fighting position after blocking props are placed.
- A rifle and pistol are accessible in the safe starting room. Two other existing
  weapons are placed in optional rooms, plus a pistol refill near extraction.
  Floors 1/2/3 also have 3/5/7 ammunition caches using existing animated gun
  pickups and 4/5/6 additional healing pickups spread through exploration rooms.
  Collected equipment/ammo carries between floors; no incoming ammo is assumed
  when the generator validates a mission's independent supply budget.
- Every sector has one healing pickup; every room has data. The conservative
  ammo budget counts two magazines per gun pickup and must cover at least 1.5
  times total enemy HP, excluding initial ammunition, ECHO damage, melee attacks,
  scattergun pellet multiplication and launcher splash damage.
- Enemy/pickup casings and exit markers use contrasting existing colors; their
  lights and functional markings retain their established readable accents.
  The eight original prop slots now use Krea 2 Turbo masters finished as 64x64
  Aseprite art, with four animation frames and 32 existing sector colorways each.
  Medical markings and functional lights keep their distinct colors. Health/data
  pickups retain compact world scales; lamp mounts follow the local ceiling.

## API and validation

`retro_generation.py` is pure Python; it has no Ren'Py, pygame, asset-loading,
global RNG or rendering dependency.

```python
from retro_generation import generate_run, validate_level, fresh_run
run = generate_run(20261015, rules=None)
report = validate_level(run.levels[0])
assert report['valid'], report['errors']
```

`generate_run(seed, rules)` returns a `GeneratedRun` containing `seed`, `version`,
three `levels`, `results` and inactive `floor_states`. `rules` may override `sizes`, `rooms`, `enemies`
(three entries each), `ammo_caches`, `bonus_healing`, and `attempts`.
Defaults are the table above, the supply counts above, and 12 attempts.
Each `LevelDefinition` contains complete world/floor/ceiling grids, room and
sector grids/identities, themes, spawn/facing, exits, props, encounters, enemies,
weapon pickups, protected cells, optional-room identities, lift rectangle/stops
and marked landing positions. `building_elevators` additionally records cabin
rectangles, enclosing walls, lobby/boarding cells, door direction, shaft identity
and destination floor. All grids are column-major: `grid[x][y]`.
`stacked_areas` contains the complete upper `LevelDefinition`. Each deck has
`area_id` and `area_name`; linked freight-lift specs add `target_area`, `parked`,
and a shared shaft rectangle/normal. Upper decks have no mission exit or building
cabin. The active session's `floor_definition` and `area_states` let
`level_progress()` include both decks even before the upper works are visited.
`build_heights()` clones mutable heights so moving a lift cannot alter its blueprint.

Validation runs after all placements. At both parked lift heights it checks
real player/ECHO radius clearance, headroom, reversible upward-step limits,
all open playable cells and rooms, exits and collectibles, fighting positions,
landings/call distance, colors, encounter limits, safe spawn and supplies.
It also checks building cabin dimensions, reachability, clear lobbies, enclosure
and reciprocal adjacent-floor link identities.
The symmetric connected graph proves return routes even though the player can
also take larger one-way drops. Since props are cell-centred and radii are below
half a cell, validated adjacent cell-centre routes have continuous clearance.
Independent movement tests exercise these routes using actual player steering.
Invalid definitions return `valid=False` plus specific `errors` and check data.

After 12 rejected attempts, generation searches a bounded bank of 256 asymmetric
fallback candidates, removes optional blocking props and validates the result.
The requested seed rotates/reflects this safe layout; the transformed result is
validated again. Unsupported/impossible rules raise a descriptive error.
`fresh_run(seed, previous_fingerprint)` also rejects an immediate structural
repeat of any preceding mission, including the fallback path. Structural hashes
include geometry, heights, spawn/exit and stacked-area hashes, so palette changes alone do not qualify.

## Saves, retries and compatibility

Generation happens at run start, never during rendering. Ren'Py saves retain the
seed, generator version, complete definitions, current arena/player/lift/ECHO,
visited rooms, remaining pickups, enemies, inventory and completed summaries.
`BuildingSession` owns the active arena. Leaving a floor stores its combat,
pickup, height/lift and exploration data without retaining its renderer or GPU
textures. Returning restores that data; defeated enemies and collected loot
stay cleared. Player health, weapon ownership/ammunition/reload clocks and
ECHO's health/repair timers travel between floors. Only one ECHO is active.
The elevator waits for a healthy ECHO to board, freezes movement/combat while
doors close and travel, and resumes the saved ride after loading. Pause freezes
the ride. Saves can include the active floor and all visited inactive floors.
P or the MENU button pauses and exposes Save/Load on desktop and touch screens.
F5 quicksaves; F9 quickloads. Loading uses saved definitions instead of regenerating from a seed. Retry uses
the same definition, restores deck-entry equipment and pickups, clears the
occupied deck's exploration, and returns its lift/player to their starting state.
Other visited decks and floors remain unchanged. Entry equipment is refreshed on arrival.
The persistent last-run structural fingerprint prevents an immediate repeat.

The two original maps and `Renpystein.for_level()` remain regression fixtures.
Existing saves without a generated run continue through those original maps.
Generated arenas use explicit metadata, never the demo gallery/lift coordinates.
Existing controls, F6 effects, flat F7 CRT, soft distant textures, native pixel
assets and touch controls are preserved.

Version 6 adds three final boss types and boss-room metadata (`boss` with kind,
room, rectangle, spawn, layout, arena name and exit). Accepted energy drums now
explode when shot, chain to nearby drums, respect cover and damage enemies only.
Each main deck and upper works contains route-safe drums. Final boss rooms add
cover, drums, healing and independent weapon/ammunition supplies. Native boss
art and generation records are retained in the sibling `krea3/bosses-v40`.

For embedding, call `retro_minigame`; its structured return includes status,
seed and full-building progress. The v41 entry point saves an explicit
`retro_active_controller` and uses `renpy.retain_after_load()` to preserve actual
interaction progress in real Ren'Py slots. It restores the caller's story
variables, quick menu, skip and dialogue-window state when returning. Loading
clears held movement/fire input. The copy bundle and independent 1280x720 host
test are in `retro-readiness-v41`; see its `INTEGRATION.md` for installation.

CPU surfaces/walls/props and GPU rendering receive the same theme grid. The GPU
lookup map stores `palette * 16 + lift_edge_flags` in its blue byte; the high and
low nibbles are decoded independently. The color shader still uses four samplers,
and the geometry-only depth shader uses one. This retains GLES 1.00-compatible
shader source; Android device performance still requires testing on a device.

## Validation artifacts

The sibling `retro-stacked-areas-v31` folder contains the 3,000-floor stacked-layout
seed audit, deck/lift/save/progress checks, aligned overlap preview, actual ride
screenshots and desktop GL2 timing data. `retro-building-v30` retains the building
elevator/traveler/AI regressions. Earlier generation and movement
fixtures remain in `retro-procedural-v26` and `retro-larger-levels-v27`.
Pacing requires human playtesting; elevators do not wait for combat or collection
completion. Distant unalerted rooms skip sight rays and clear direct chases skip
discarded path searches to limit the cost of the denser population.
