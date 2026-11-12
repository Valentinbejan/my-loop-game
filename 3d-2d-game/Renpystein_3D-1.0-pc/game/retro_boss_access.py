"""Final-floor gold key, validated placement and real locked-room geometry."""
import math
from collections import deque
from retro_heights import STEP_HEIGHT

GATE_WALL=33
KEY_ID='boss_access'


def reachable_cells(definition,closed=True,stop=None,origin=None):
    from retro_combat import CombatSession
    world=[list(row) for row in definition.world]
    spec=getattr(definition,'boss_access',None)
    if closed and spec:
        for x,y in spec['gates']:world[x][y]=GATE_WALL
    h=definition.build_heights();h.world=world
    for lift in h.lifts:
        if stop is not None:lift.apply(h,getattr(lift,stop))
    session=CombatSession(world,definition.props,[],heights=h)
    nodes={(x,y) for x,row in enumerate(world) for y,wall in enumerate(row)
           if not wall and session.can_occupy(x+.5,y+.5,.23,from_floor=h.floor_at(x,y))}
    start=tuple(map(int,origin or definition.spawn))
    distance={start:0} if start in nodes else {};queue=deque(distance)
    while queue:
        x,y=queue.popleft();floor=h.floor_at(x,y)
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if (nx,ny) in nodes and (nx,ny) not in distance and abs(h.floor_at(nx,ny)-floor)<=STEP_HEIGHT+1e-8:
                distance[nx,ny]=distance[x,y]+1;queue.append((nx,ny))
    return distance


def install_boss_access(definition,rng):
    if definition.index!=2:return definition
    boss=definition.boss;rid=boss['room'];world=definition.world
    used={(int(x),int(y)) for x,y,*_ in definition.props+definition.enemies+definition.weapon_pickups+definition.exits+[definition.spawn]}
    protected=set(definition.protected_cells);gates=set()
    # Seal every open room boundary; no assumption that an arena has one door.
    for x,row in enumerate(world):
        for y,wall in enumerate(row):
            if wall or definition.room_ids[x][y]!=rid:continue
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if not (0<=nx<len(world) and 0<=ny<len(world[nx])) or world[nx][ny] or definition.room_ids[nx][ny]==rid:continue
                choices=[p for p in ((nx,ny),(x,y)) if p not in used|protected]
                if not choices:raise ValueError('Boss entrance overlaps a protected placement')
                gates.add(choices[0])
    if not gates:raise ValueError('Boss room has no usable entrance')
    definition.boss_access=dict(gates=sorted(gates),room=rid)
    reached=reachable_cells(definition)
    start_room=definition.room_ids[int(definition.spawn[0])][int(definition.spawn[1])]
    candidates=[p for p in reached if p not in used|protected|gates and definition.room_ids[p[0]][p[1]]>=0
                and definition.room_ids[p[0]][p[1]] not in (rid,start_room)]
    if not candidates:raise ValueError('No reachable key room outside the locked arena')
    a,b,c,d=boss['rect'];centre=((a+c)/2,(b+d)/2)
    distances=reachable_cells(definition,False,origin=centre)
    candidates.sort(key=lambda p:(-distances.get(p,0),p[0],p[1]))
    # Favor the far side by walking distance, then vary the exact clear tile.
    far=distances.get(candidates[0],0)
    choices=[p for p in candidates if distances.get(p,0)>=far*.9]
    x,y=rng.choice(choices)
    definition.boss_access.update(key=(x+.5,y+.5),distance_from_boss=distances.get((x,y),0))
    return definition


def validate_boss_access(definition):
    if getattr(definition,'version',0)<7 or definition.index!=2:return []
    spec=getattr(definition,'boss_access',None)
    if not spec or not spec.get('gates') or 'key' not in spec:return ['missing final-floor boss key or gate']
    n=len(definition.world);key=tuple(map(int,spec['key']));errors=[]
    placements={(int(x),int(y)) for x,y,*_ in definition.props+definition.enemies+definition.weapon_pickups+definition.exits+[definition.spawn]}
    gates=set(map(tuple,spec['gates']))
    if any(not (0<=x<n and 0<=y<len(definition.world[x])) for x,y in gates|{key}):return ['boss access placement outside map']
    if any(definition.world[x][y] for x,y in gates|{key}):errors.append('boss access overlaps solid geometry')
    if (gates|{key})&(placements|set(definition.protected_cells)):errors.append('boss access overlaps a protected placement')
    if definition.room_ids[key[0]][key[1]]==spec['room']:errors.append('boss key placed inside locked room')
    for stop in ('low','high'):
        reached=reachable_cells(definition,True,stop)
        if key not in reached:errors.append('boss key unreachable before unlock at '+stop)
        if any(definition.room_ids[x][y]==spec['room'] for x,y in reached):errors.append('boss room bypasses key gate at '+stop)
    return errors


def configure_access(session,definition,keys=None):
    session.boss_access=getattr(definition,'boss_access',None) if definition is not None else None
    session.boss_keys=set(keys or ())
    apply_access(session)


def apply_access(session):
    spec=getattr(session,'boss_access',None)
    if not spec:return
    value=0 if KEY_ID in getattr(session,'boss_keys',()) else GATE_WALL
    changed=False
    for x,y in spec['gates']:
        if session.world[x][y]!=value:session.world[x][y]=value;changed=True
    if changed:session.heights.version=getattr(session.heights,'version',0)+1


def collect_key(session,x,y):
    spec=getattr(session,'boss_access',None)
    if not spec or session.dead or KEY_ID in getattr(session,'boss_keys',()):return False
    kx,ky=spec['key']
    if math.hypot(kx-x,ky-y)>=.6 or abs(session.heights.floor_at(kx,ky)-session.heights.floor_at(x,y))>STEP_HEIGHT:return False
    if not session.line_of_sight(x,y,kx,ky):return False
    session.boss_keys.add(KEY_ID);apply_access(session)
    session.notice_kind='boss_key';session.notice_until=session.time+2.5
    return True


def render_key(session):
    spec=getattr(session,'boss_access',None)
    if not spec or KEY_ID in getattr(session,'boss_keys',()):return []
    x,y=spec['key'];frame=int(session.time/.12)%8
    return [(x,y,'images/keys/boss_v43/key-idle-{:02d}.png'.format(frame),.6,session.heights.floor_at(x,y)-.2)]
