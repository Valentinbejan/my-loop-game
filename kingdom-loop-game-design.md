**Kingdom Loop — Gameplay and Art Direction**

Working project label, not a final game title. Design baseline v0.1 · 28 September 2026.

A lone adventurer builds a camp into a kingdom, raises a family of heroes, and prepares a large expedition to defeat the monsters threatening the world. Adventures use automatic movement and combat, terrain cards, equipment choices, and escalating risk. The permanent settlement houses people, produces supplies, trains fighters, and visibly grows through the campaign.

This document consolidates the creator's decisions and the recommended defaults they authorized. Added rules below are the initial design baseline; balance values and example content remain provisional. It specifies the intended game, not an implemented product or a claim about Loop Hero's exact mechanics.

**1. The experience the game should deliver**

The player should remember the first campfire, the first resident, the first harvest, and the first child who eventually accompanies the founder into battle. The final expedition should feel like the result of building a community over decades.

The game has two main playable modes: expeditions and settlement life. A regional map connects them. Family, production, and territorial growth operate through these modes rather than becoming unrelated minigames.

| Pillar | Design requirement |
| --- | --- |
| Shape the adventure | Players place cards, select equipment, configure supplies, and assemble parties while heroes move and fight automatically. |
| Build a visible home | Houses, farms, gardens, animal enclosures, roads, workshops, and defenses occupy physical space. |
| Make preparation matter | Food, potions, equipment, training, and protection change expedition outcomes. |
| Know the people | Named residents have occupations, skills, relationships, and personal histories. |
| Develop a heroic family | Adult children inherit resurrection and can become expedition companions. |
| Grow into rulership | The founder becomes king of a capital and supporting settlements. |

**2. A typical session**

Return home, review expedition losses and gains, meet family members, inspect newly completed buildings, and decide what the settlement needs next. Place construction projects, assign workers, queue crafting, and reserve supplies. Visit the family home, select a destination, assemble a party, and depart.

During the adventure, place terrain cards, develop combinations, compare equipment, and manage risk. Choose whether to complete another circuit or return. Time spent adventuring advances the settlement, independent missions, relationships that depend on elapsed time, and everyone's age. On return, the town presents the consequences clearly.

The repeating relationship is: exploration supplies the town; the town prepares stronger expeditions; stronger expeditions secure territory and bring new people and possibilities home.

**3. Time advances through adventures**

The world calendar advances only while the currently controlled protagonist is actively adventuring. Town exploration, construction planning, inventory screens, conversations, the family interior, and menus do not advance it. Pausing an expedition also pauses all simulation.

Town residents may walk, work, and play ambient animations while the player is home, but these animations do not generate resources, consume supplies, progress pregnancies, age anyone, or complete tasks. There is no offline progression.

| Activity | While the protagonist is home | While the protagonist adventures |
| --- | --- | --- |
| Farming and animal husbandry | Assign workers and inspect fields | Growth, production, and feed consumption advance |
| Crafting and construction | Queue work and reserve materials | Staffed work progresses |
| Independent expeditions | Dispatch, equip, and set instructions | Travel, encounters, and return progress |
| Aging and childhood | Inspect ages and milestones | Everyone advances on the same calendar |
| Injury and resurrection recovery | Choose care and reserve supplies | Recovery progresses |
| Relationships | Hold available conversations and make choices | Elapsed-time requirements advance |

The expedition has three distinct measures: combat time, strategic days, and completed route circuits. Combat runs in seconds. Movement and encounters accumulate strategic time. Completing the route increments its difficulty. Calendar days and circuits are never treated as interchangeable labels.

Regional travel carries a disclosed calendar cost; remote expeditions can take substantially longer in the world than nearby ones. Any accelerated travel advances every affected system consistently. Before departure, show expected duration, food coverage, and approaching family milestones. Exact conversion rates require a pacing prototype capable of supporting decades without hundreds of repetitive missions.

Players cannot repeatedly collect production or relationship rewards by opening menus or reloading the town. Important conversations are unlocked by distinct events, relationship progress, or new calendar periods.

**4. Expedition movement, cards, and encounters**

The protagonist follows a generated circuit automatically. The party travels as one group. Players can pause freely, inspect encounters, place cards, change eligible equipment, and configure consumable use. Combat uses automatic attacks and skills; there are no reflex-based attack or dodge controls.

Each region supplies its own terrain, monsters, rewards, and hazards. Before departure, choose a limited card loadout from unlocked options. Rewards during the expedition provide cards drawn from that selection. Cards can create enemy habitats, safe locations, landscape bonuses, gathering sites, or special rules.

| Card purpose | Example concept | Strategic decision |
| --- | --- | --- |
| Create encounters | Monster den | Add danger to obtain needed rewards |
| Support survival | Wayside shelter | Place recovery before a difficult segment |
| Generate materials | Mineral outcrop | Trade space and encounter risk for crafting inputs |
| Affect an area | Watch post | Cover several useful route tiles |
| Modify the landscape | Flowering grove | Support a combination or party bonus |
| Remove or transform | Reclamation card | Spend a limited opportunity to correct the route |

These names are examples for original content. Final cards need distinct art, fiction, and rules. The game should establish its own combinations rather than reproduce Loop Hero's card catalogue.

A placement preview displays affected tiles, known transformations, and immediate consequences. Newly discovered combinations enter a permanent journal. Discoveries can surprise the player; previously learned rules remain easy to inspect.

Repeated circuits escalate enemy strength and exposure. Visible threat progress eventually enables or summons the regional boss according to that region's rules. The player can see the threshold and choose when to approach it. Boss pacing, card weights, spawn rates, and scaling curves remain balance work.

**5. Party combat and supplies**

Begin alone. Early milestones unlock a small accompanying party, followed by larger groups as leadership, facilities, and objectives develop. The final campaign supports approximately ten fighters. Ordinary expeditions can remain smaller to preserve readability and reduce equipment administration.

Each fighter has individual equipment, skills, traits, health, and a role. Formations group fighters into front, middle, and rear positions. Targeting rules and ability descriptions explain who can protect, heal, or attack whom. Distinct roles include defender, physical attacker, ranged attacker, healer, and magical support; these are initial roles, not a final class roster.

Food and potions primarily follow configurable automatic rules. Examples include eating between encounters below a health threshold, reserving an antidote for poison, or retaining emergency healing for the boss. Players can override a rule while paused. Shared inventory and simple per-character permissions avoid requiring ten separate consumable bars.

| Supply | Primary role |
| --- | --- |
| Rations | Sustain travel and prevent exhaustion |
| Prepared meals | Heal between encounters or grant a lasting expedition bonus |
| Potions | Address combat emergencies and specific conditions |
| Equipment | Provide persistent character strength and specialization |
| Enhancements | Prepare gear for particular environments or enemies |
| Field tools | Enable gathering, salvage, or expedition objectives |

Equipment found in the field can be used immediately when eligible. Replaced equipment remains cargo until sold, salvaged, stored, or deliberately discarded. Carrying limits make loot choices meaningful without automatically destroying a treasured item.

**6. The permanent world and temporary expedition**

The regional map stores discovered territories, settlements, roads, resource opportunities, cleared objectives, and persistent threats. Each active expedition creates a temporary route within a selected region. Terrain cards shape that route but ordinarily do not rebuild the regional map.

| Result | Persistence |
| --- | --- |
| Routine placed terrain and local enemy populations | Reset with the expedition |
| Surviving characters and retained cargo | Return home |
| Recipes, knowledge, discovered combinations | Remain unlocked |
| Rescued residents and recruited companions | Join the persistent population |
| Discovered mine or secured pass | Becomes a regional opportunity or completed objective |
| Outpost founded through a settlement objective | Remains on the regional map |

Securing territory requires a named objective and appropriate supplies. Drawing a profitable card alone does not permanently claim land. Regions can be revisited for gathering and unresolved challenges after their main boss is defeated.

**7. Walking around and building the settlement**

The protagonist can walk around town, meet residents, interact with exterior workstations, inspect farms and animals, and enter his current family residence. A freely moving construction camera handles placement, roads, worker assignment, and settlement overlays.

The family residence is the only enterable building. Every other structure operates through its exterior, yard, contextual panel, and visible workers. The same restriction applies as the town becomes a city and other settlements are founded.

Buildings occupy explicit grid footprints. Placement shows the foundation, required entrance access, work yard, and any reserved expansion space. Roads connect entrances and support hauling. Farms require workable ground and access to irrigation infrastructure; animal enclosures require usable pen space, feed, and workers.

Use footprint differences that players can understand. A small home, crop plot, forge with a yard, and livestock enclosure should create visibly different land-use choices. Dimensions are provisional until an art and placement prototype establishes a common tile scale.

Existing buildings can be relocated at a disclosed cost. New projects reserve materials when confirmed and complete as adventure time advances. Emergency starter shelter and a basic campfire are immediate founding actions so the lone protagonist can begin play without workers or a construction queue.

**8. Population, jobs, and ordinary life**

Residents need housing, food, health care, safety, and reasonable living conditions. Jobs include farming, animal care, cooking, hauling, construction, smithing, tailoring, alchemy, teaching, medicine, guarding, and adventuring. One person can change occupation, but taking a trained worker on a mission reduces their contribution at home.

The early camp receives direct assignments. Larger settlements use staffing priorities and district summaries, with individual overrides. Residents retain names, relationships, and histories; city-scale management does not require selecting every person every day.

| Condition | Gameplay consequence |
| --- | --- |
| Insufficient housing | Crowding and reduced willingness to settle |
| Food shortages | Reduced health, morale, and readiness; escalating consequences are forecast |
| Poor health care | Longer recovery and greater danger to mortal residents |
| Weak defenses | Greater raid risk and damage to production |
| Low happiness | Lower productivity and possible departure |
| Strong services and safety | Better recruitment and stable growth |

Residents arrive through rescue, recruitment, migration, and family growth. Each arrival should have a visible reason. Named specialists can unlock recipes, training, or production methods. Mortal recruits remain competitively useful through skills and experience even when the dynasty grows.

**9. Production equips the adventurers**

Materials move through understandable chains. Farms produce ingredients, cooks make meals, storage reserves a share for residents, and expedition preparation draws from the remaining stock. Ore, fuel, and a trained smith become weapons and armor. Medicinal plants and an alchemist become potions.

| Facility | Main expedition contribution |
| --- | --- |
| Gardens, fields, orchards | Food ingredients and medicinal plants |
| Animal enclosures | Eggs, milk, wool, hides, and other husbandry products |
| Kitchen and bakery | Meals and rations |
| Herbalist and alchemy workshop | Medicine, healing mixtures, antidotes, resistance potions |
| Smithy | Weapons, armor, repairs, improvements |
| Tailor and leatherworker | Clothing, light armor, bags, travel gear |
| Enchanting workshop | Specialized equipment enhancements |
| Training grounds and school | Combat skills and development of future specialists |
| Infirmary | Treatment and resurrection recovery |
| Warehouse and expedition lodge | Stock management and party preparation |

Reserve food for residents and supplies for assigned missions before allowing crafting or new departures to consume them. Show projected stock over the intended adventure duration, including consumption by animals and independent teams.

At the beginning, the protagonist gathers and salvages basic necessities himself during expeditions. Starting provisions make the first departures possible. Unstaffed town facilities do not produce resources. Short gathering expeditions provide a recovery path when the town is poorly supplied.

An example progression: discover a marsh, bring back medicinal plants, grow them at home, recruit or train an alchemist, manufacture antidotes, then explore the marsh more effectively. The discovery changes the settlement and the settlement changes the adventure.

**10. Independent expeditions and settlement protection**

Recruitable adults can accompany the protagonist or undertake autonomous missions. Before sending them, select an objective, party, equipment, supply allowance, and retreat policy. Their missions progress only while the controlled protagonist is adventuring.

Autonomous missions use the same broad combat statistics, environmental requirements, and supply rules as player-led expeditions. They resolve as an event sequence with a readable report rather than requiring simultaneous manual card placement on several maps. Players are not required to switch attention between multiple live battles.

Policies include avoiding elite encounters, returning at a supply threshold, and abandoning an objective when a companion is incapacitated. Forecasts show uncertainty and notable risks; they do not promise safety when survival is probabilistic.

Mortal companions can be permanently killed. Important consequences identify the encounter, preparation weakness, and failed retreat opportunity. Injuries and failed missions should be more common than arbitrary, unexplained deaths on routine assignments.

Monster pressure threatens the settlement while adventure time advances. Guards, walls, watchtowers, secure routes, and regional victories reduce that pressure. Raids are resolved through defenses and assigned forces, supported by a visible warning system. Critical home events can automatically pause the active expedition and offer a return decision. A new siege-control mode is outside the initial design.

**11. Family, marriage, and the home interior**

The protagonist can develop relationships with adult women, marry multiple willing partners, and have children. Marriage is represented through conversations, shared events, commitments, and household development. Spouses retain personalities, occupations, preferences, and goals. They can contribute as specialists, companions, or community leaders according to their abilities.

All spouses and dependent children belong to the protagonist's expanding household. The home progresses from a modest shelter to a larger family residence and eventually a royal residence. It remains the sole enterable building, with growing room capacity, shared spaces, furniture, family keepsakes, and domestic scenes. If the protagonist changes residence, only the current family home is enterable.

Pregnancy, birth, and childhood follow the adventure calendar. Family events are queued for presentation on return or at an appropriate pause; walking around town cannot accelerate them. Adult children can establish households of their own, although those houses remain exterior-only under the interior rule.

Children develop interests and aptitudes through education, mentors, household conditions, and later training. Only adults join combat expeditions. Every child inherits the resurrection ability, but combat proficiency still requires equipment, experience, and instruction. Descendants can choose civilian roles while retaining the ability.

The design should reward caring for the household and building a strong community. A larger family requires housing, food, education, and equipment; additional births do not instantly create a stronger fighting party.

**12. Resurrection, defeat, aging, and succession**

The founder cannot be permanently killed by violence, monsters, poison, disease, or other causes except natural old age. His children inherit this property. As a baseline extension, the ability passes through subsequent biological descendants regardless of sex. Spouses and unrelated recruits do not gain it through marriage or service.

Defeated dynasty members return to the settlement's designated revival sanctuary, beginning with a simple site at the camp. Resurrection does not reverse age. It creates a recovery condition and a return delay; recovered heroes require elapsed adventure time and care before they regain full readiness.

Equipped personal gear returns with the resurrected character to avoid repeatedly stripping away their identity and build. Unsecured expedition cargo and unused field supplies can be lost or left for recovery. Mortal allies do not automatically return with them. A party may rescue an incapacitated mortal ally before death; confirmed death is permanent.

The player must never become trapped because the active protagonist needs adventure time to recover. He can undertake low-risk recovery expeditions with penalties, or temporarily let an eligible adult heir lead while he rests. The expedition clock follows whichever protagonist the player currently controls.

Old age is forecast through life stages and clear warnings, with a succession plan available before it becomes urgent. The intended campaign gives the founder a generous opportunity to face the final boss alongside his grown children. If he dies of old age first, control passes to a chosen adult descendant and the kingdom continues. Lack of an eligible heir is a campaign-loss condition with advance warning and access to prior saves.

Exact life expectancy, adulthood timing, inheritance presentation, and recovery duration require testing. They must support family attachment and a founder-led ending without punishing time spent in menus or town exploration.

**13. From camp to nation**

Settlement ranks depend on services, population stability, security, and progression objectives. A stockpile of money alone cannot promote a camp into a city.

| Stage | Visible development | New responsibility |
| --- | --- | --- |
| Camp | Fire, shelter, storage, starter plots | Survive and attract the first residents |
| Village | Houses, gardens, livestock, basic workshops | Feed the community and establish reliable production |
| Town | Streets, specialists, defenses, training | Support several expedition teams |
| City | Districts, advanced workshops, civic spaces, royal residence | Coordinate larger production and services |
| Kingdom / nation | Capital, governed outposts, satellite settlements, trade routes | Reclaim territory and supply the final campaign |

The protagonist's coronation is a story and progression milestone tied to a functioning, protected realm. The main late-game conflict concerns monster-held territory. Extensive diplomacy, rival human empires, and separately controlled battlefield armies are deferred so the game keeps its two-part identity.

Governors manage satellite settlements through staffing priorities and production orders. A regional overview handles trade and security; the capital remains the most detailed place to walk around and build. Beyond nation scale, further expansion is optional postgame territory, not an unbounded requirement for the first release.

**14. The final campaign**

Regional victories reveal the central monster threat and provide materials, knowledge, and routes needed for the final expedition. The climax is designed around approximately ten well-prepared adult fighters. The intended emotional outcome is a founder leading a party made largely of his grown children, supported by the kingdom he created.

The encounter requires complementary roles, survival preparation, and coordinated automatic abilities. It should not become a reflex-action boss. Players retain pause, inspection, formation planning, and supply control. Mortal recruits remain valid party members; a specific number of biological children is not a hard entry requirement.

Defeated resurrecting characters return home after the failed attempt rather than rejoining the same boss battle endlessly. Withdrawal or a party wipe resets the encounter. Failures therefore cost time, cargo, preparation, and potentially mortal companions while allowing the dynasty to learn and try again.

Victory completes the main story. An optional continuation allows rebuilding, further family life, and unfinished exploration. Exact boss fiction and phases remain original-content work.

**15. Art direction: colorful pixel art with visible depth**

Current production rules are recorded in [kingdom-loop-art-rules.md](F:/my-loop-game/kingdom-loop-art-rules.md): all individual assets and UI graphics use 64×64 canvases, buildings show only their fronts, and characters will be authored by the user. These rules supersede the provisional sizes and building-perspective assumptions below.

Use an elevated, three-quarter top-down view in the spirit of Stardew Valley's spatial readability. Houses have visible fronts, roofs, height, and grounding shadows. Farms, yards, animal pens, trees, and streets clearly occupy the map. The production baseline is 2D pixel art with layered sprites and depth sorting, providing the desired dimensional appearance without requiring a fully 3D world.

There is no 16-color palette limit or attempt to reproduce old-console hardware restrictions. Use rich regional palettes, expressive characters, detailed architecture, and restrained lighting effects that respect the pixel grid. Color abundance should still preserve contrast between characters, terrain, hazards, and interaction prompts.

| Visual element | Direction |
| --- | --- |
| Overall mood | Warm, lively settlements within an adventurous fantasy world; danger becomes more pronounced in monster regions |
| Characters | Moderately detailed, stylized figures with readable silhouettes and visible equipment accents |
| Portraits | More expressive detail for family, companions, and significant residents |
| Buildings | Consistent cultural foundations that grow from improvised wood and cloth into timber, masonry, and civic architecture |
| Farms and gardens | Clear growth stages, varied crops, irrigation details, fences, tools, and harvested states |
| Animals | Recognizable silhouettes and small idle, feeding, and movement animations |
| Seasons | Distinct foliage, ground, weather, crop availability, and travel conditions |
| Monsters | Distinct forms and attack cues; colorful does not mean harmless |
| Interface | Clean readable panels, optional crisp text, restrained ornamental borders |

Set one consistent world pixel scale during the first art test. A provisional starting point is a 32-pixel ground tile with characters roughly one tile wide and taller than one tile; this is an art-test assumption, not a locked requirement. Scale sprites together, use stable pixel alignment, and prevent inconsistent resolutions between assets.

Roofs and foreground objects fade or cut away when they obscure characters. Placement mode shows exact occupied cells, entrances, work zones, and expansion reservations. Crop and animal states need distinct silhouettes and icons as well as color differences.

**16. How growth looks and sounds**

Upgrades should change the settlement's appearance: tents become cottages, cottages gain extensions, paths gain paving, workshops acquire visible equipment, and civic structures distinguish the capital. Preserve some early landmarks so the player can recognize where the kingdom began.

Town movement shows hauling, tending crops, gathering around shared spaces, training, and family activity. When the calendar is paused at home, these remain ambient displays of the current state. Completed buildings, new age stages, and harvested resources reflect the last elapsed adventure time.

Expeditions use a readable board with terrain cards and a separate combat presentation. The board shares the settlement's color language and materials. Combat uses larger, expressive sprites, restrained effects, and clear formation positions. In a ten-person fight, effects must not conceal who is injured, targeted, or acting.

Sound supports both modes: quiet domestic activity and production at home, distinct encounter cues during adventures, and recognizable alerts for supplies, injuries, transformation discoveries, and retreat. Family and kingdom themes can develop as the settlement grows. Precise music instrumentation remains an audio-direction task.

**17. Information the player needs**

The town overview shows population, available housing, food coverage, workers, queued construction, production bottlenecks, active missions, and threat. The expedition screen shows party condition, consumables, cargo capacity, elapsed strategic time, current circuit, and boss progress.

Hover or selection explains where a bonus came from and what a statistic changes. Supply forecasts account for both residents and outgoing teams. Combat reports distinguish damage, healing, protection, and the cause of incapacitation. A family tree records relationships, ages, inherited resurrection, occupations, and memorable events.

Support scalable text, color-independent status icons, reduced flashes, optional automatic pause at critical health or major events, and clear autosaves before expeditions and irreversible milestones. No multiplayer or monetization systems are part of this baseline.

**18. The first playable slice and unresolved tuning**

Build one complete connection between expedition and settlement before expanding content. The first slice begins alone, lets the player rescue a resident, construct a home and garden, produce useful food, equip a companion, and defeat one regional boss. It includes town walking and a small enterable family residence shell, but not the whole dynasty campaign.

| Milestone | What it must prove |
| --- | --- |
| Expedition prototype | Automatic combat and card placement create meaningful choices |
| Settlement prototype | Footprints, roads, staffing, and production are understandable |
| Connected slice | An expedition discovery changes town production and the next adventure |
| Time and family prototype | Adventure-driven years support childhood, adulthood, recovery, and succession |
| Party expansion | Larger groups remain readable and manageable |
| Campaign expansion | Town growth, regional objectives, and family development support the final battle |

Provisional slice quantities: one region, one protagonist, two companion roles, four enemy types, eight to twelve cards, several interactions, and one boss. These are production limits for testing, not the final game's content ceiling.

Remaining tuning includes calendar conversion, campaign duration, life stages, population thresholds, footprints, card frequencies, equipment statistics, resource ratios, party unlocks, raid frequency, recovery times, and boss difficulty. Engine choice, final title, original character designs, and the specific supernatural explanation for resurrection also remain undecided. These do not prevent prototyping the agreed gameplay.

**19. Reference boundaries**

Loop Hero supplies the reference for automatic expeditions, world-shaping cards, repeated routes, and risk-driven growth. Stardew Valley supplies the reference for an elevated pixel-art perspective and readable lived-in spaces. The proposed game needs its own characters, setting, terminology, cards, assets, dialogue, music, and visual identity.

This design is based on the decisions in this conversation. It does not import either reference game's full rules. Technical feasibility, balance, and production scope still need validation through the connected playable slice.
