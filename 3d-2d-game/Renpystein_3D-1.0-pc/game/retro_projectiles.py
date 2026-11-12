"""Visible projectiles with swept collisions, wall occlusion and timed impacts."""
import math

ALLY_PROJECTILE_SPEC=dict(speed=5.0,radius=.07,size=.18,damage=18,splash=0,ttl=4)
PROJECTILE_SPECS = {
    "plasma_bolt": dict(speed=3.6, radius=.08, size=.19, damage=6, splash=0, ttl=5),
    "energy_sphere": dict(speed=5.5, radius=.13, size=.30, damage=60, splash=1.45, ttl=4),
    "heavy_orb": dict(speed=2.8, radius=.15, size=.34, damage=14, splash=.85, ttl=5),
    "turret_bolt": dict(speed=4.2, radius=.07, size=.17, damage=5, splash=0, ttl=5),
}
EFFECT_SPECS = {"impact": (.24,.30,4), "explosion": (.42,.85,6), "blade_arc": (.18,.6,4), "muzzle_flash": (.12,.30,4)}
EFFECT_SPECS.update(barrel_explosion=(1.05,5.2,10),barrel_shockwave=(.55,10.5,6))


def effect_frame_path(kind,frame):
    folder='barrels_v39' if kind.startswith('barrel_') else 'v13'
    return 'images/projectiles/{}/{}_{:02d}.png'.format(folder,kind,frame)

class Projectile:
    def __init__(self,x,y,dx,dy,kind,owner,now,z=.5,slope=0):
        self.x,self.y,self.dx,self.dy=x,y,dx,dy
        self.kind,self.owner,self.born=kind,owner,now
        self.spec=ALLY_PROJECTILE_SPEC if kind=='ally_bolt' else PROJECTILE_SPECS[kind]
        self.z,self.slope=z,slope

    def image_path(self,now):
        if self.kind=='ally_bolt':return 'images/allies/v21/ally_bolt_{:02d}.png'.format(int((now-self.born)*12)%4)
        return "images/projectiles/v13/{}_{:02d}.png".format(self.kind,int((now-self.born)*12)%4)

class Impact:
    def __init__(self,x,y,kind,now,z=.5):
        self.x,self.y,self.kind,self.born=x,y,kind,now
        self.z=z

    def image_path(self,now):
        duration,_,count=EFFECT_SPECS[self.kind]
        frame=min(count-1,int((now-self.born)/duration*count))
        return effect_frame_path(self.kind,frame)

def circle_entry(x,y,dx,dy,cx,cy,radius,reach):
    vx,vy=cx-x,cy-y
    along=vx*dx+vy*dy
    cross=vx*vx+vy*vy-along*along
    if cross>radius*radius:return None
    half=math.sqrt(max(0,radius*radius-cross))
    if along+half<0:return None
    entry=max(0,along-half)
    return entry if entry<=reach else None

def launch(session,x,y,dx,dy,kind,owner,z=None,slope=0):
    length=math.hypot(dx,dy)
    if length<1e-9:return
    dx,dy=dx/length,dy/length
    if z is None:z=session.heights.floor_at(x,y)+.5
    session.projectiles.append(Projectile(x,y,dx,dy,kind,owner,session.time,z,slope))

def cylinder_entry(p,cx,cy,floor,radius,reach):
    vx,vy=cx-p.x,cy-p.y;along=vx*p.dx+vy*p.dy
    cross=vx*vx+vy*vy-along*along
    if cross>radius*radius:return None
    half=math.sqrt(max(0,radius*radius-cross))
    begin,end=max(0,along-half),min(reach,along+half)
    low,high=floor-p.spec['radius'],floor+1+p.spec['radius']
    if abs(p.slope)<1e-9:
        if not low<=p.z<=high:return None
    else:
        a,b=(low-p.z)/p.slope,(high-p.z)/p.slope
        begin=max(begin,min(a,b));end=min(end,max(a,b))
    return begin if begin<=end else None

def enemy_shoot(session,enemy,px,py):
    from retro_bosses import BOSS_SPECS,shoot_boss
    if enemy.kind in BOSS_SPECS:return shoot_boss(session,enemy,px,py)
    kind={"drone":"plasma_bolt","heavy":"heavy_orb","turret":"turret_bolt"}[enemy.kind]
    angle=math.atan2(py-enemy.y,px-enemy.x)
    count=3 if enemy.kind=="turret" else 1
    source_z=session.heights.floor_at(enemy.x,enemy.y)+.5
    slope=(session.heights.floor_at(px,py)+.5-source_z)/max(.1,math.hypot(px-enemy.x,py-enemy.y))
    for i in range(count):
        a=angle+(i-1)*.045 if count==3 else angle
        session.enemy_shots.append((session.time+i*.12,enemy,kind,math.cos(a),math.sin(a),slope))

def impact(session,projectile,x,y,px,py,target):
    spec=projectile.spec
    z=projectile.z+projectile.slope*math.hypot(x-projectile.x,y-projectile.y)
    session.effects.append(Impact(x,y,"explosion" if spec["splash"] else "impact",session.time,z))
    if projectile.owner in ('player','ally'):
        victims=[e for e in session.enemies if e.alive and
                 (e is target or (spec["splash"] and math.hypot(e.x-x,e.y-y)<=spec["splash"] and
                                  abs(session.heights.floor_at(e.x,e.y)+.5-z)<=spec['splash'] and
                                  session.line_of_sight(x,y,e.x,e.y,z)))]
        for enemy in victims:
            distance=math.hypot(enemy.x-x,enemy.y-y)
            factor=1 if enemy is target else max(.3,1-distance/spec["splash"])
            session.hurt_enemy(enemy,max(1,round(spec["damage"]*factor)))
    elif target=="player" or (spec["splash"] and math.hypot(px-x,py-y)<=spec["splash"] and
                             abs(session.player_floor+.5-z)<=spec['splash'] and session.line_of_sight(x,y,px,py,z)):
        factor=1 if target=="player" else max(.3,1-math.hypot(px-x,py-y)/spec["splash"])
        session.health=max(0,session.health-max(1,round(spec["damage"]*factor)))
        session.damage_until=session.time+.18
    ally=session.companion
    if projectile.owner=='enemy' and ally is not None and ally.alive:
        if target is ally or (spec['splash'] and math.hypot(ally.x-x,ally.y-y)<=spec['splash'] and session.line_of_sight(x,y,ally.x,ally.y,z)):
            session.hurt_companion(spec['damage'])

def advance_projectiles(session,dt,px,py):
    pending=[]
    for shot in session.enemy_shots:
        due,enemy,kind,dx,dy=shot[:5]
        if not enemy.alive:continue
        if due>session.time+1e-9:pending.append(shot);continue
        offset=enemy.spec["radius"]+.04
        z=session.heights.floor_at(enemy.x,enemy.y)+.5
        distance=max(.1,math.hypot(px-enemy.x,py-enemy.y))
        slope=shot[5] if len(shot)>5 else (session.player_floor+.5-z)/distance
        launch(session,enemy.x+dx*offset,enemy.y+dy*offset,dx,dy,kind,"enemy",z+slope*offset,slope)
        session.effects.append(Impact(enemy.x+dx*offset,enemy.y+dy*offset,"muzzle_flash",session.time,z))
    session.enemy_shots=pending
    active=[]
    for p in session.projectiles:
        length=p.spec["speed"]*dt
        wall=session.obstruction_distance(p.x,p.y,p.dx,p.dy,length,p.z,p.slope)
        candidates=[]
        from retro_barrels import ray_barrel,detonate_barrel
        barrel=ray_barrel(session,p.x,p.y,p.dx,p.dy,length,p.z,p.slope,p.spec['radius'],limit=wall)
        if barrel is not None:candidates.append(barrel)
        if p.owner in ('player','ally'):
            for enemy in session.enemies:
                if not enemy.alive:continue
                entry=cylinder_entry(p,enemy.x,enemy.y,session.heights.floor_at(enemy.x,enemy.y),enemy.spec["radius"]+p.spec["radius"],length)
                if entry is not None:candidates.append((entry,enemy))
        else:
            entry=cylinder_entry(p,px,py,session.player_floor,.18+p.spec["radius"],length)
            if entry is not None:candidates.append((entry,"player"))
            ally=session.companion
            if ally is not None and ally.alive:
                entry=cylinder_entry(p,ally.x,ally.y,session.heights.floor_at(ally.x,ally.y),.23+p.spec['radius'],length)
                if entry is not None:candidates.append((entry,ally))
        target=min(candidates,key=lambda pair:pair[0]) if candidates else None
        wall_hit=wall<length-1e-8 or not session.cell_open(int(p.x+p.dx*length),int(p.y+p.dy*length))
        if target and (not wall_hit or target[0]<=wall+1e-7):
            x,y=p.x+p.dx*target[0],p.y+p.dy*target[0]
            if barrel is not None and target[1] is barrel[1]:detonate_barrel(session,barrel[1])
            else:impact(session,p,x,y,px,py,target[1])
        elif wall_hit:
            distance=max(0,wall-.035)
            impact(session,p,p.x+p.dx*distance,p.y+p.dy*distance,px,py,None)
        elif session.time-p.born>p.spec["ttl"]:
            session.effects.append(Impact(p.x,p.y,"impact",session.time,p.z))
        else:
            p.x+=p.dx*length;p.y+=p.dy*length;p.z+=p.slope*length;active.append(p)
    session.projectiles=active
    session.effects=[e for e in session.effects if session.time-e.born<EFFECT_SPECS[e.kind][0]]

def render_entries(session):
    entries=[(p.x,p.y,p.image_path(session.time),p.spec["size"],p.z-.5) for p in session.projectiles]
    entries.extend((e.x,e.y,e.image_path(session.time),EFFECT_SPECS[e.kind][1],e.z-.5) for e in session.effects)
    return entries
