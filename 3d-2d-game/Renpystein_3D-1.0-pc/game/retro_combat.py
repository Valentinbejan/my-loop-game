"""Deterministic combat rules for the local retro sci-fi Ren'Py minigame.

This module has no Ren'Py dependency so collisions, aim, ammunition and AI can
be checked without opening a window. Coordinates follow the existing maps.
"""
import math
from collections import deque
from retro_projectiles import launch, enemy_shoot, advance_projectiles, Impact
from retro_weapon_pickups import WeaponPickup
from retro_heights import HeightSectors, STEP_HEIGHT, BODY_HEIGHT

BLOCKING_PROPS = {1, 2, 3, 6}
WEAPONS = {
    "baton": dict(label="Stun baton", damage=40, reach=1.7, interval=0.34,
                  capacity=0, reserve=0, reload=0.0, fire_duration=0.25),
    "pulse_pistol": dict(label="Pulse pistol", damage=26, reach=14.0, interval=0.28,
                         capacity=12, reserve=60, reload=1.1, fire_duration=0.225),
    "plasma_rifle": dict(label="Plasma rifle", damage=19, reach=18.0, interval=0.12,
                         capacity=24, reserve=96, reload=1.4, fire_duration=0.12),
    "scattergun": dict(label="Scattergun",damage=10,reach=10,interval=.65,
                      capacity=6,reserve=30,reload=1.55,fire_duration=.30,pellets=7,spread=.06),
    "plasma_launcher": dict(label="Plasma launcher",damage=60,reach=20,interval=.85,
                           capacity=4,reserve=20,reload=1.75,fire_duration=.35,projectile="energy_sphere"),
    "energy_blade": dict(label="Energy blade",damage=45,reach=1.85,interval=.40,
                         capacity=0,reserve=0,reload=0,fire_duration=.30,arc=.52),
    "plasma_axe": dict(label="Plasma axe",damage=75,reach=2.0,interval=.65,
                       capacity=0,reserve=0,reload=0,fire_duration=.42,arc=.66),
}
WEAPON_ORDER=tuple(WEAPONS)
ENEMIES = {
    "sentry": dict(health=65, speed=0.8, damage=8, reach=6.0, windup=0.38,
                   interval=1.4, awareness=11.0, radius=0.28),
    "drone": dict(health=40, speed=1.25, damage=6, reach=4.5, windup=0.30,
                  interval=1.0, awareness=10.0, radius=0.25,projectile=True),
    "crawler": dict(health=35,speed=1.6,damage=8,reach=.9,windup=.22,
                    interval=.75,awareness=10,radius=.25),
    "heavy": dict(health=150,speed=.5,damage=14,reach=8,windup=.8,
                  interval=2.0,awareness=13,radius=.35,projectile=True),
    "turret": dict(health=80,speed=0,damage=5,reach=9,windup=.5,
                   interval=1.6,awareness=12,radius=.3,projectile=True),
}
from retro_bosses import BOSS_SPECS
ENEMIES.update(BOSS_SPECS)
ANIMATION_COUNTS = dict(idle=4, walk=6, attack=4, hit=3, death=6)
ENEMY_FRAME_DURATIONS = dict(idle=0.18, walk=0.10, hit=0.08, death=0.12)


class WeaponState:
    def __init__(self, name):
        self.name = name
        self.spec = WEAPONS[name]
        self.ammo = self.spec["capacity"]
        self.reserve = self.spec["reserve"]
        self.last_fire = -100.0
        self.next_fire = 0.0
        self.reload_started = None

    def reload(self, now):
        if (not self.spec["capacity"] or self.reload_started is not None
                or self.ammo >= self.spec["capacity"] or not self.reserve):
            return False
        self.reload_started = now
        return True

    def update(self, now):
        if self.reload_started is not None and now >= self.reload_started + self.spec["reload"]:
            amount = min(self.spec["capacity"] - self.ammo, self.reserve)
            self.ammo += amount
            self.reserve -= amount
            self.reload_started = None

    def pose(self, now):
        if self.reload_started is not None:
            elapsed = (now - self.reload_started) / self.spec["reload"]
            return "reload", min(5, max(0, int(elapsed * 6)))
        elapsed = now - self.last_fire
        if elapsed < self.spec["fire_duration"]:
            return "fire", min(4, max(0, int(elapsed / self.spec["fire_duration"] * 5)))
        return "idle", int(now * 3) % 2


class Enemy:
    def __init__(self, x, y, kind):
        if kind not in ENEMIES:
            raise ValueError("Unknown enemy type: " + str(kind))
        self.x, self.y, self.kind = float(x), float(y), kind
        self.spec = ENEMIES[kind]
        self.health = self.spec["health"]
        self.state = "idle"
        self.state_since = 0.0
        self.next_attack = 0.65
        self.attack_applied = False
        self.alerted = False
        self.path = []
        self.path_refresh = 0.0

    @property
    def alive(self):
        return self.health > 0

    @property
    def damage_stage(self):
        ratio = self.health / self.spec["health"]
        return 2 if ratio <= 0.30 else (1 if ratio <= 0.75 else 0)

    def change_state(self, state, now):
        if self.state != state:
            self.state, self.state_since = state, now

    def image_key(self, now):
        count = ANIMATION_COUNTS[self.state]
        elapsed = max(0, now - self.state_since)
        if self.state in ("death", "hit"):
            frame = min(count - 1, int(elapsed / ENEMY_FRAME_DURATIONS[self.state]))
        elif self.state == "attack":
            frame = min(count - 1, int(elapsed / ((self.spec["windup"] + 0.18) / count)))
        else:
            frame = int(elapsed / ENEMY_FRAME_DURATIONS[self.state]) % count
        return "{}_{}_{}_{:02d}".format(self.kind, self.damage_stage, self.state, frame)


class CombatSession:
    def __init__(self, world, props, enemy_spawns, health=100,weapon_pickups=(),owned_weapons=None,weapon_ammo=None,heights=None):
        self.world = world
        self.heights=heights or HeightSectors(world)
        self.player_floor=0.
        self.companion=None
        self.props = list(props)
        self.enemies = [Enemy(*spawn) for spawn in enemy_spawns]
        self.health = max(0, min(100, health))
        self.time = 0.0
        self.accumulator = 0.0
        self.weapons = {name: WeaponState(name) for name in WEAPONS}
        self.owned_weapons=set(WEAPONS if owned_weapons is None else owned_weapons)&set(WEAPONS)
        if not self.owned_weapons:self.owned_weapons.add("baton")
        self.weapon_name = "pulse_pistol" if "pulse_pistol" in self.owned_weapons else next(name for name in WEAPON_ORDER if name in self.owned_weapons)
        for name,values in (weapon_ammo or {}).items():
            if name in self.weapons:
                weapon=self.weapons[name]
                weapon.ammo=max(0,min(weapon.spec["capacity"],values.get("ammo",weapon.ammo)))
                weapon.reserve=max(0,min(999,values.get("reserve",weapon.reserve)))
        self.weapon_pickups=[WeaponPickup(*p) for p in weapon_pickups if p[2] in WEAPONS]
        self.boss_keys=set();self.boss_access=None
        self.notice_kind=None
        self.notice_until=0
        self.kills = 0
        self.treasure = 0
        self.damage_until = 0.0
        self.hit_until = 0.0
        self.projectiles=[]
        self.effects=[]
        self.enemy_shots=[]
        self.pending_swings=[]

    @property
    def dead(self):
        return self.health <= 0

    def __setstate__(self,state):
        self.__dict__.update(state)
        if not hasattr(self,'heights'):self.heights=HeightSectors(self.world)
        if not hasattr(self,'player_floor'):self.player_floor=0.
        if not hasattr(self,'companion'):self.companion=None
        if not hasattr(self,'boss_keys'):self.boss_keys=set()
        if not hasattr(self,'boss_access'):self.boss_access=None

    def hurt_companion(self,amount):
        from retro_companion import hurt_companion
        hurt_companion(self,amount)

    @property
    def weapon(self):
        return self.weapons[self.weapon_name]

    def switch_weapon(self, name):
        if name not in self.weapons or self.dead:
            return False
        if name not in self.owned_weapons:
            self.notice_kind="locked";self.notice_until=self.time+1.25
            return False
        if name != self.weapon_name:
            self.weapon.reload_started = None
            self.pending_swings=[]
            self.weapon_name = name
        return True

    def collect_weapon(self,pickup):
        if self.dead or pickup not in self.weapon_pickups:return False
        new=pickup.name not in self.owned_weapons
        self.owned_weapons.add(pickup.name)
        weapon=self.weapons[pickup.name]
        if new:
            self.switch_weapon(pickup.name)
            self.notice_kind="acquired"
        else:
            if weapon.spec["capacity"]:
                weapon.ammo=weapon.spec["capacity"]
                weapon.reserve=min(999,weapon.reserve+weapon.spec["capacity"]*2)
                weapon.reload_started=None
                self.notice_kind="refilled"
            else:self.notice_kind="acquired"
        self.notice_until=self.time+1.6
        self.weapon_pickups.remove(pickup)
        return True

    def equipment_snapshot(self):
        owned=[name for name in WEAPON_ORDER if name in self.owned_weapons]
        ammo={name:{"ammo":self.weapons[name].ammo,"reserve":self.weapons[name].reserve} for name in owned}
        return owned,ammo

    def collect_prop(self, prop):
        """Consume useful nearby pickups once; leave unused medicine in place."""
        if self.dead or prop not in self.props:
            return False
        kind = prop[2]
        if kind == 4:
            if self.health >= 100:
                return False
            self.health = 100
        elif kind == 5:
            self.treasure += 1
        else:
            return False
        self.props.remove(prop)
        return True

    def cell_open(self, x, y):
        return 0 <= x < len(self.world) and 0 <= y < len(self.world[x]) and self.world[x][y] == 0

    def can_occupy(self, x, y, radius=0.18, ignore=None, player=None,from_floor=None,from_pos=None,allow_drop=False):
        floor=self.heights.floor_at(x,y)
        source_pos=from_pos or ((ignore.x,ignore.y) if ignore is not None else None)
        source_lift=self.heights.lift_at(*source_pos) if source_pos else None
        target_lift=self.heights.lift_at(x,y)
        if source_lift and source_lift.moving:return False
        if target_lift and target_lift.moving:return False
        if allow_drop and from_floor is not None and floor<from_floor-STEP_HEIGHT and self.heights.bounds(x,y)[1]<from_floor+BODY_HEIGHT:
            return False
        for cx in range(math.floor(x - radius), math.floor(x + radius) + 1):
            for cy in range(math.floor(y - radius), math.floor(y + radius) + 1):
                solid=not self.cell_open(cx,cy)
                height_block=from_floor is not None and not self.heights.traversable(cx,cy,from_floor,allow_drop)
                # Bots cannot drop. Check their whole circle against the new
                # floor too: entering a step diagonally must not leave a foot
                # over a lower side edge and trap the actor on the next tick.
                if from_floor is not None and not allow_drop:
                    height_block=height_block or not self.heights.traversable(cx,cy,floor)
                if height_block and not solid and allow_drop and source_pos and floor<=from_floor+STEP_HEIGHT:
                    f,c,_=self.heights.bounds(cx,cy)
                    if f>from_floor+STEP_HEIGHT and c-f>=BODY_HEIGHT:
                        # Once over a ledge, its rim must not trap the player's
                        # collision circle while they move away from it.
                        ox,oy=source_pos
                        old=(ox-max(cx,min(ox,cx+1)))**2+(oy-max(cy,min(oy,cy+1)))**2
                        new=(x-max(cx,min(x,cx+1)))**2+(y-max(cy,min(y,cy+1)))**2
                        if old<radius**2 and new>=old-1e-12:height_block=False
                if solid or height_block:
                    nx, ny = max(cx, min(x, cx + 1)), max(cy, min(y, cy + 1))
                    if (x - nx) ** 2 + (y - ny) ** 2 < radius ** 2:
                        return False
        for sx, sy, kind in self.props:
            if kind in BLOCKING_PROPS and abs(self.heights.floor_at(sx,sy)-floor)<BODY_HEIGHT and (sx-x)**2 + (sy-y)**2 < (0.35+radius)**2:
                return False
        for enemy in self.enemies:
            if enemy is not ignore and enemy.alive and abs(self.heights.floor_at(enemy.x,enemy.y)-floor)<BODY_HEIGHT:
                if (enemy.x-x)**2+(enemy.y-y)**2 < (enemy.spec["radius"]+radius)**2:
                    return False
        if player and abs(self.heights.floor_at(*player)-floor)<BODY_HEIGHT and (player[0]-x)**2 + (player[1]-y)**2 < (0.18+radius)**2:
            return False
        return True

    def obstruction_distance(self, x, y, dx, dy, reach,z=None,slope=0):
        if z is not None:
            limit=self.heights.ray_limit(x,y,dx,dy,reach,z,slope)
            for px,py,kind in self.props:
                if kind not in BLOCKING_PROPS:continue
                vx,vy=px-x,py-y;along=vx*dx+vy*dy
                cross=vx*vx+vy*vy-along*along
                if along>=0 and cross<=.35**2:
                    entry=max(0,along-math.sqrt(max(0,.35**2-cross)))
                    f=self.heights.floor_at(px,py)
                    if f<=z+slope*entry<=f+1:limit=min(limit,entry)
            return limit
        # DDA hits walls exactly, including corners and ragged map boundaries.
        cx, cy = math.floor(x), math.floor(y)
        if not self.cell_open(cx, cy):
            return 0.0
        tx = abs(1 / dx) if abs(dx) > 1e-9 else math.inf
        ty = abs(1 / dy) if abs(dy) > 1e-9 else math.inf
        sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
        nx = (cx + 1 - x if sx > 0 else x - cx) * tx
        ny = (cy + 1 - y if sy > 0 else y - cy) * ty
        limit = reach
        for _ in range(512):
            if nx < ny:
                distance = nx
                nx += tx
                cx += sx
            elif ny < nx:
                distance = ny
                ny += ty
                cy += sy
            else:
                distance = nx
                # A diagonal ray cannot leak between two touching walls.
                if not self.cell_open(cx + sx, cy) or not self.cell_open(cx, cy + sy):
                    limit = min(limit, distance)
                    break
                nx += tx
                ny += ty
                cx += sx
                cy += sy
            if distance > reach:
                break
            if not self.cell_open(cx, cy):
                limit = min(limit, distance)
                break
        for px, py, kind in self.props:
            if kind not in BLOCKING_PROPS:
                continue
            vx, vy = px-x, py-y
            along = vx*dx + vy*dy
            perpendicular = vx*vx+vy*vy-along*along
            if along >= 0 and perpendicular <= 0.35**2:
                distance = along-math.sqrt(max(0, 0.35**2-perpendicular))
                if distance<0 and vx*vx+vy*vy<=0.35**2:
                    distance=0
                if distance >= 0:
                    limit = min(limit, distance)
        return limit

    def line_of_sight(self, x, y, target_x, target_y,z=None,target_z=None):
        vx, vy = target_x-x, target_y-y
        distance = math.hypot(vx, vy)
        if z is None:z=self.heights.floor_at(x,y)+.5
        if target_z is None:target_z=self.heights.floor_at(target_x,target_y)+.5
        return distance < 1e-8 or self.obstruction_distance(
            x, y, vx/distance, vy/distance, distance,z,(target_z-z)/distance) >= distance - 1e-5

    def aim_slope(self,x,y,dx,dy,reach):
        z=self.heights.floor_at(x,y)+.5
        choices=[]
        for enemy in self.enemies:
            if not enemy.alive:continue
            vx,vy=enemy.x-x,enemy.y-y;along=vx*dx+vy*dy
            if 0<along<=reach and abs(vx*dy-vy*dx)<=enemy.spec['radius']+.08:
                target_z=self.heights.floor_at(enemy.x,enemy.y)+.5
                slope=(target_z-z)/along
                if self.obstruction_distance(x,y,dx,dy,along,z,slope)>=along-1e-5:
                    choices.append((along,slope))
        # The camera has no manual vertical aim: exposed barrels on galleries
        # need the same height-aware aim assistance as enemies.
        from retro_barrels import ray_barrel
        for prop in self.props:
            if prop[2]!=1:continue
            vx,vy=prop[0]-x,prop[1]-y;along=vx*dx+vy*dy
            if 0<along<=reach and abs(vx*dy-vy*dx)<=.35:
                slope=(self.heights.floor_at(prop[0],prop[1])+.45-z)/along
                hit=ray_barrel(self,x,y,dx,dy,reach,z,slope)
                if hit is not None and hit[1] is prop:choices.append((along,slope))
        return min(choices)[1] if choices else 0.

    def fire(self, x, y, dx, dy):
        weapon = self.weapon
        if self.dead or weapon.reload_started is not None or self.time + 1e-8 < weapon.next_fire:
            return False
        if weapon.spec["capacity"] and weapon.ammo == 0:
            weapon.reload(self.time)
            return False
        weapon.last_fire = self.time
        weapon.next_fire = self.time + weapon.spec["interval"]
        if weapon.spec["capacity"]:
            weapon.ammo -= 1
        norm = math.hypot(dx, dy)
        if norm<1e-9:
            return True
        dx, dy = dx/norm, dy/norm
        for enemy in self.enemies:
            if enemy.alive and math.hypot(enemy.x-x,enemy.y-y)<9:enemy.alerted=True
        if weapon.spec.get("projectile"):
            slope=self.aim_slope(x,y,dx,dy,weapon.spec['reach'])
            launch(self,x,y,dx,dy,weapon.spec["projectile"],"player",self.heights.floor_at(x,y)+.5,slope)
        elif weapon.spec.get("arc"):
            self.pending_swings.append((self.time+weapon.spec["fire_duration"]*.42,weapon.name,dx,dy))
        else:
            angle=math.atan2(dy,dx)
            count=weapon.spec.get("pellets",1)
            for i in range(count):
                a=angle+(i-(count-1)/2)*weapon.spec.get("spread",0)
                self.shoot_ray(x,y,math.cos(a),math.sin(a),weapon.spec)
        return True

    def shoot_ray(self,x,y,dx,dy,spec):
        z=self.heights.floor_at(x,y)+.5
        slope=self.aim_slope(x,y,dx,dy,spec['reach'])
        limit = self.obstruction_distance(x, y, dx, dy, spec["reach"],z,slope)
        candidates = []
        for enemy in self.enemies:
            if not enemy.alive:
                continue
            if not spec['capacity'] and abs(self.heights.floor_at(enemy.x,enemy.y)-self.heights.floor_at(x,y))>=.55:continue
            vx, vy = enemy.x-x, enemy.y-y
            along = vx*dx+vy*dy
            cross = abs(vx*dy-vy*dx)
            radius = enemy.spec["radius"]
            if along > 0 and cross <= radius:
                entry = along-math.sqrt(max(0, radius*radius-cross*cross))
                f=self.heights.floor_at(enemy.x,enemy.y)
                if entry <= limit and entry <= spec["reach"] and f-.05<=z+slope*entry<=f+1:
                    candidates.append((entry, enemy))
            if math.hypot(vx,vy) < 9:
                enemy.alerted = True
        if candidates:
            target_entry,target=min(candidates,key=lambda item:item[0])
        else:target_entry,target=math.inf,None
        if spec.get('capacity',0)>0:
            from retro_barrels import ray_barrel,detonate_barrel
            barrel=ray_barrel(self,x,y,dx,dy,spec['reach'],z,slope,limit=limit)
            if barrel is not None and barrel[0]<=target_entry:
                detonate_barrel(self,barrel[1]);return
        if target is not None:self.hurt_enemy(target,spec['damage'])

    def advance_swings(self,px,py):
        pending=[]
        for due,name,dx,dy in self.pending_swings:
            if due>self.time+1e-9:pending.append((due,name,dx,dy));continue
            spec=WEAPONS[name]
            self.effects.append(Impact(px+dx*.65,py+dy*.65,"blade_arc",self.time,self.heights.floor_at(px,py)+.5))
            for enemy in self.enemies:
                if not enemy.alive:continue
                vx,vy=enemy.x-px,enemy.y-py
                distance=math.hypot(vx,vy)
                angle=abs(math.atan2(vx*dy-vy*dx,vx*dx+vy*dy))
                if distance<=spec["reach"]+enemy.spec["radius"] and angle<=spec["arc"] and abs(self.heights.floor_at(px,py)-self.heights.floor_at(enemy.x,enemy.y))<.55 and self.line_of_sight(px,py,enemy.x,enemy.y):
                    self.hurt_enemy(enemy,spec["damage"])
        self.pending_swings=pending

    def hurt_enemy(self, enemy, amount):
        if not enemy.alive:
            return
        enemy.health = max(0, enemy.health - amount)
        self.hit_until = self.time + 0.12
        enemy.alerted = True
        if enemy.kind in BOSS_SPECS and enemy.alive:
            # Damage changes the armor stage but cannot cancel every windup
            # with a rapid-fire rifle, permanently preventing boss attacks.
            if enemy.state not in ('attack','hit'):
                enemy.change_state('hit',self.time)
            return
        enemy.attack_applied = False
        self.enemy_shots=[shot for shot in self.enemy_shots if shot[1] is not enemy]
        enemy.change_state("hit" if enemy.alive else "death", self.time)
        # A fresh hit restarts the visible impact and recovery even during recoil.
        enemy.state_since = self.time
        if not enemy.alive:
            self.kills += 1

    def reload(self):
        return False if self.dead else self.weapon.reload(self.time)

    def find_path(self, start, target):
        start, target = (int(start[0]), int(start[1])), (int(target[0]), int(target[1]))
        queue, previous = deque([start]), {start:None}
        blocked = {(int(x),int(y)) for x,y,kind in self.props if kind in BLOCKING_PROPS}
        while queue:
            cell = queue.popleft()
            if cell == target:
                path = []
                while previous[cell] is not None:
                    path.append((cell[0]+0.5,cell[1]+0.5))
                    cell = previous[cell]
                return list(reversed(path))
            for vx,vy in ((-1,0),(1,0),(0,-1),(0,1)):
                next_cell = (cell[0]+vx, cell[1]+vy)
                if next_cell not in previous and next_cell not in blocked and self.heights.traversable(*next_cell,self.heights.floor_at(*cell)):
                    previous[next_cell] = cell
                    queue.append(next_cell)
        return []

    def tick_enemy(self, enemy, dt, px, py):
        if not enemy.alive:
            return
        if enemy.kind=='boss_blade':
            from retro_bosses import tick_blade
            if tick_blade(self,enemy,dt,px,py) is not False:return
        actual_player=(px,py)
        ally=self.companion
        # Sleeping rooms do not cast long sight rays across the entire floor.
        # Alerted enemies retain their existing pursuit and combat behavior.
        if not enemy.alerted and math.hypot(px-enemy.x,py-enemy.y)>enemy.spec['awareness'] and (
                ally is None or not ally.alive or math.hypot(ally.x-enemy.x,ally.y-enemy.y)>enemy.spec['awareness']):
            enemy.change_state('idle',self.time)
            return
        target_ally=ally is not None and ally.alive and math.hypot(ally.x-enemy.x,ally.y-enemy.y)<math.hypot(px-enemy.x,py-enemy.y)*.85 and self.line_of_sight(enemy.x,enemy.y,ally.x,ally.y)
        if target_ally:px,py=ally.x,ally.y
        elapsed = self.time - enemy.state_since
        if enemy.state == "hit" and elapsed < ANIMATION_COUNTS["hit"] * ENEMY_FRAME_DURATIONS["hit"]:
            return
        distance = math.hypot(px-enemy.x,py-enemy.y)
        visible = self.line_of_sight(enemy.x,enemy.y,px,py)
        attack_visible=visible and (enemy.kind!='crawler' or abs(self.heights.floor_at(enemy.x,enemy.y)-self.heights.floor_at(px,py))<.55)
        enemy.alerted = enemy.alerted or (visible and distance < enemy.spec["awareness"])
        if enemy.state == "attack":
            if elapsed >= enemy.spec["windup"] and not enemy.attack_applied:
                enemy.attack_applied = True
                if attack_visible and distance <= enemy.spec["reach"]:
                    if enemy.spec.get("projectile"):
                        enemy_shoot(self,enemy,px,py)
                    elif enemy.kind!='crawler' or abs(self.heights.floor_at(enemy.x,enemy.y)-self.heights.floor_at(px,py))<.55:
                        if target_ally:self.hurt_companion(enemy.spec['damage'])
                        else:
                            self.health = max(0, self.health-enemy.spec["damage"])
                            self.damage_until = self.time + 0.18
            if elapsed < enemy.spec["windup"] + 0.18:
                return
            enemy.change_state("idle", self.time)
        if not enemy.alerted:
            enemy.change_state("idle", self.time)
            return
        if attack_visible and distance <= enemy.spec["reach"]:
            if self.time >= enemy.next_attack:
                enemy.change_state("attack", self.time)
                enemy.attack_applied = False
                enemy.next_attack = self.time + enemy.spec["windup"] + enemy.spec["interval"]
            else:
                enemy.change_state("idle", self.time)
            return
        if enemy.spec["speed"]<=0:
            enemy.change_state("idle",self.time)
            return
        # An unobstructed chase already uses the target directly. Avoid a
        # whole-floor path search whose result would immediately be discarded.
        direct=visible and self.heights.walk_line(enemy.x,enemy.y,px,py)
        if not direct and self.time >= enemy.path_refresh:
            enemy.path = self.find_path((enemy.x,enemy.y),(px,py))
            enemy.path_refresh = self.time + 0.6
        # A visible player on a balcony can still be unreachable directly.
        target_x, target_y = (px,py) if direct else (enemy.path[0] if enemy.path else (enemy.x,enemy.y))
        if enemy.path and math.hypot(target_x-enemy.x,target_y-enemy.y) < 0.12:
            enemy.path.pop(0)
            if not direct and enemy.path:
                target_x,target_y = enemy.path[0]
        vx,vy=target_x-enemy.x,target_y-enemy.y
        length=math.hypot(vx,vy)
        moved=False
        if length > 0.01:
            distance=min(length,enemy.spec["speed"]*dt)
            nx,ny=enemy.x+vx/length*distance,enemy.y+vy/length*distance
            source=self.heights.floor_at(enemy.x,enemy.y)
            if self.can_occupy(nx,ny,enemy.spec["radius"],enemy,actual_player,source):
                enemy.x,enemy.y=nx,ny
                moved=True
            elif self.can_occupy(nx,enemy.y,enemy.spec["radius"],enemy,actual_player,source):
                enemy.x=nx
                moved=True
            elif self.can_occupy(enemy.x,ny,enemy.spec["radius"],enemy,actual_player,source):
                enemy.y=ny
                moved=True
        enemy.change_state("walk" if moved else "idle", self.time)

    def advance(self, elapsed, px, py, paused=False,view=None):
        self.player_floor=self.heights.floor_at(px,py)
        if paused or self.dead:
            return
        # Discard long gaps from menus/window suspension, and use fixed physics steps.
        self.accumulator += max(0,min(0.12,elapsed))
        step=1/60
        while self.accumulator + 1e-9 >= step and not self.dead:
            self.accumulator -= step
            self.time += step
            for weapon in self.weapons.values():
                weapon.update(self.time)
            if self.companion is not None:
                from retro_companion import tick_companion
                tick_companion(self,step,px,py,view)
            self.advance_swings(px,py)
            for enemy in self.enemies:
                self.tick_enemy(enemy,step,px,py)
                if self.dead:
                    break
            if not self.dead:advance_projectiles(self,step,px,py)

