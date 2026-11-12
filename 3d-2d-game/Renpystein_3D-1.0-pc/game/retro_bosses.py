"""Seeded final arenas and three telegraphed robot boss behaviors."""
import math

BOSS_SPECS = {
    'boss_siege':dict(label='ATLAS / SIEGE ENGINE',health=900,speed=.55,damage=14,
        reach=12.,windup=1.05,interval=2.3,awareness=20.,radius=.40,projectile=True),
    'boss_reactor':dict(label='NOVA / REACTOR WARDEN',health=780,speed=.85,damage=6,
        reach=13.,windup=.95,interval=1.8,awareness=20.,radius=.38,projectile=True),
    'boss_blade':dict(label='RAZOR / BLADE COMMANDER',health=720,speed=1.35,damage=18,
        reach=5.,windup=.9,interval=1.9,awareness=20.,radius=.36),
}
BOSS_KINDS=tuple(BOSS_SPECS)
ARENA_NAMES=('REACTOR CHAMBER','SIEGE FOUNDRY','COMMAND VAULT')

def install_boss_arena(level,rng,reserved):
    """Use the final extraction room, preserving the validated room/corridor graph."""
    if level.index!=2:return level
    ex,ey=level.exits[0][:2];rid=level.room_ids[int(ex)][int(ey)]
    room=next(r for r in level.rooms if r['id']==rid)
    a,b,c,d=room['rect'];layout=rng.randrange(3);kind=rng.choice(BOSS_KINDS)
    used={(int(x),int(y)) for x,y,*_ in level.props+level.enemies+level.weapon_pickups+level.exits}
    protected=set(level.protected_cells)
    cells=[(x,y) for x in range(a+1,c-1) for y in range(b+1,d-1)
           if level.room_ids[x][y]==rid and (x,y) not in used|protected]
    rng.shuffle(cells)
    def put(collection,code,preferred=None,cover=False):
        candidates=[p for p in cells if not cover or p not in reserved]
        if not candidates:raise ValueError('Boss arena has insufficient clear space')
        if preferred is not None:candidates.sort(key=lambda p:(p[0]-preferred[0])**2+(p[1]-preferred[1])**2)
        x,y=candidates[0];cells.remove((x,y));used.add((x,y))
        collection.append((x+.5,y+.5,code));return x+.5,y+.5
    # Different cover arrangements stay off pre-existing routes and lift spaces.
    layouts=(((a+2,b+2),(c-3,d-3)),((a+2,d-3),(c-3,b+2)),((a+2,(b+d)//2),(c-3,(b+d)//2)))
    for point in layouts[layout]:put(level.props,2,point,True)
    boss=put(level.enemies,kind,(c-3,d-3))
    for point in ((a+2,b+2),(c-3,b+2)):put(level.props,1,point,True)
    for _ in range(2):put(level.props,4)
    for _ in range(3):put(level.weapon_pickups,'plasma_rifle')
    put(level.weapon_pickups,'plasma_launcher')
    level.boss=dict(kind=kind,room=rid,rect=room['rect'],spawn=boss,layout=layout,
                    arena=ARENA_NAMES[layout],exit=level.exits[0][:2])
    level.encounters.append(dict(room=rid,sector=room['sector'],enemies=[len(level.enemies)-1]))
    return level

def active_boss(session):
    return next((e for e in session.enemies if e.kind in BOSS_SPECS and e.alive),None)

def boss_blocks_exit(definition,session):
    missing_key=bool(getattr(definition,'boss_access',None) and 'boss_access' not in getattr(session,'boss_keys',()))
    return missing_key or bool(getattr(definition,'boss',None) and active_boss(session) is not None)

def shoot_boss(session,enemy,px,py):
    """Slow visible ordnance; telegraphed fan/radial patterns leave dodge gaps."""
    angle=math.atan2(py-enemy.y,px-enemy.x)
    enraged=enemy.damage_stage==2
    if enemy.kind=='boss_siege':
        pattern=[(angle+offset,i*.16,'heavy_orb') for i,offset in enumerate((-.16,0,.16))]
        if enraged:pattern.append((angle,.65,'heavy_orb'))
    else:
        count=10 if enraged else 8
        # Rotate the radial wave each attack, plus one aimed bolt.
        phase=angle+getattr(enemy,'volley',0)*.23
        pattern=[(phase+math.tau*i/count,0,'plasma_bolt') for i in range(count)]
        pattern.append((angle,.28,'turret_bolt'))
    enemy.volley=getattr(enemy,'volley',0)+1
    z=session.heights.floor_at(enemy.x,enemy.y)+.5
    slope=(session.heights.floor_at(px,py)+.5-z)/max(.1,math.hypot(px-enemy.x,py-enemy.y))
    for angle,delay,kind in pattern:
        session.enemy_shots.append((session.time+delay,enemy,kind,math.cos(angle),math.sin(angle),slope))

def tick_blade(session,enemy,dt,px,py):
    """Lock the dash direction during a long warning, then lunge without steering."""
    if not enemy.alive:return
    enemy.alerted=enemy.alerted or (math.hypot(enemy.x-px,enemy.y-py)<enemy.spec['awareness'] and session.line_of_sight(enemy.x,enemy.y,px,py))
    if enemy.state=='attack':
        elapsed=session.time-enemy.state_since
        if elapsed<enemy.spec['windup']:return
        if not hasattr(enemy,'dash_vector'):
            angle=math.atan2(py-enemy.y,px-enemy.x)
            enemy.dash_vector=(math.cos(angle),math.sin(angle));enemy.dash_hit=False
        if elapsed<enemy.spec['windup']+.52:
            dx,dy=enemy.dash_vector;floor=session.heights.floor_at(enemy.x,enemy.y)
            nx,ny=enemy.x+dx*5.2*dt,enemy.y+dy*5.2*dt
            # Respect geometry and solid cover; the lunge never crosses a wall.
            if session.can_occupy(nx,ny,enemy.spec['radius'],enemy,None,floor):enemy.x,enemy.y=nx,ny
            if not enemy.dash_hit and math.hypot(enemy.x-px,enemy.y-py)<.85 and session.line_of_sight(enemy.x,enemy.y,px,py):
                session.health=max(0,session.health-enemy.spec['damage']);session.damage_until=session.time+.2;enemy.dash_hit=True
            ally=session.companion
            if not enemy.dash_hit and ally is not None and ally.alive and math.hypot(enemy.x-ally.x,enemy.y-ally.y)<.8:
                session.hurt_companion(enemy.spec['damage']);enemy.dash_hit=True
            return
        del enemy.dash_vector
        enemy.change_state('idle',session.time)
        return
    # The ordinary movement code handles pursuit; this hook owns only the dash.
    if enemy.alerted and session.time>=enemy.next_attack and math.hypot(enemy.x-px,enemy.y-py)<=5 and session.line_of_sight(enemy.x,enemy.y,px,py):
        enemy.change_state('attack',session.time);enemy.next_attack=session.time+3.1
        angle=math.atan2(py-enemy.y,px-enemy.x);enemy.dash_vector=(math.cos(angle),math.sin(angle));enemy.dash_hit=False
        return
    return False
