"""Seeded, saveable sci-fi missions. No Ren'Py, graphics or global RNG dependency."""
import hashlib
import json
import math
import random
from collections import deque
from retro_heights import HeightSectors,STEP_HEIGHT
from retro_lifts import Lift
from retro_building import install_cabin
from retro_combat import CombatSession,ENEMIES,WEAPONS,BLOCKING_PROPS

GENERATOR_VERSION=7
DEFAULT_RULES=dict(sizes=(56,64,72),rooms=(12,15,18),enemies=(20,28,36),
                   ammo_caches=(3,5,7),bonus_healing=(4,5,6),attempts=12)
SECTOR_NAMES=('ARRIVAL','REACTOR','LABORATORY','EXTRACTION')

class LevelDefinition:
    def __init__(self,**values):self.__dict__.update(values)
    def fingerprint(self):
        data=(self.world,self.floors,self.spawn,self.exits,
              [a.fingerprint() for a in getattr(self,'stacked_areas',[])])
        return hashlib.sha256(json.dumps(data,separators=(',',':')).encode()).hexdigest()
    def build_heights(self):
        h=HeightSectors(self.world,ceiling=2.)
        h.floors=[list(row) for row in self.floors]
        h.ceilings=[list(row) for row in self.ceilings]
        h.themes=self.themes;h.generated=True
        from retro_materials import room_materials
        h.materials=room_materials(self)
        h.lifts=[]
        for spec in self.lifts:
            if 'target_area' in spec:
                from retro_stacked import AreaLift
                lift=AreaLift(h,spec)
            else:lift=Lift(h,spec['rect'],spec['low'],spec['high'])
            lift.landings=spec['landings']
            h.lifts.append(lift)
        h.active=True;h.version+=1
        return h

class GeneratedRun:
    def __init__(self,seed,levels):
        self.seed=seed;self.version=GENERATOR_VERSION;self.levels=levels;self.results={};self.floor_states={}
    def fingerprint(self):return ':'.join(level.fingerprint() for level in self.levels)

def _point(rect):return ((rect[0]+rect[2])//2,(rect[1]+rect[3])//2)

def _layout(seed,index,rules):
    rng=random.Random(seed);n=rules['sizes'][index]
    world=[[1]*n for _ in range(n)];floors=[[0.]*n for _ in range(n)]
    ceilings=[[2.]*n for _ in range(n)];room_ids=[[-1]*n for _ in range(n)]
    cx=n//2+rng.randint(-2,2);cy=n//2+rng.randint(-2,2)
    boxes=((0,0,cx,cy),(cx,0,n,cy),(cx,cy,n,n),(0,cy,cx,n))
    first=rng.randrange(4);direction=rng.choice((-1,1));order=[(first+direction*i)%4 for i in range(4)]
    colors=rng.sample(range(8),4)
    sectors=[dict(id=s,rect=boxes[s],theme=colors[s],name=SECTOR_NAMES[order.index(s)]) for s in range(4)]
    sector_ids=[[0]*n for _ in range(n)];themes=[[0]*n for _ in range(n)]
    for sector in sectors:
        a,b,c,d=sector['rect']
        for x in range(a,c):
            for y in range(b,d):sector_ids[x][y]=sector['id'];themes[x][y]=sector['theme']
    rooms=[];reserved=set();corridors=set()
    def carve(rect,room=False,sector=None,height=0.):
        a,b,c,d=rect
        rid=len(rooms) if room else -1
        for x in range(a,c):
            for y in range(b,d):
                world[x][y]=0;floors[x][y]=height
                if room:room_ids[x][y]=rid
        if room:rooms.append(dict(id=rid,rect=rect,sector=sector,centre=_point(rect)))
        return rid
    def corridor(start,end,sector,flip=None):
        a,b,c,d=boxes[sector]
        x,y=start;ex,ey=end
        axes=(0,1) if (rng.randrange(2) if flip is None else flip) else (1,0)
        points=[(x,y)]
        for axis in axes:
            while (x!=ex if axis==0 else y!=ey):
                if axis==0:x+=1 if ex>x else -1
                else:y+=1 if ey>y else -1
                points.append((x,y))
        for x,y in points:
            for xx,yy in ((x,y),(x+1,y),(x,y+1),(x+1,y+1)):
                if a+1<=xx<c-1 and b+1<=yy<d-1:
                    world[xx][yy]=0;corridors.add((xx,yy))

    # The 16x16 module has ground circulation, six broad up-steps,
    # four down-steps, and a two-stop 2x2 lift alongside the upper room.
    vertical=order[rng.choice((1,2))];a,b,c,d=boxes[vertical]
    ox=a+(c-a-16)//2;oy=b+(d-b-16)//2
    turn=rng.randrange(4);mirror=bool(rng.randrange(2))
    def cell(u,v):
        if mirror:u=15-u
        for _ in range(turn):u,v=15-v,u
        return ox+u,oy+v
    def point(u,v):
        x,y=cell(int(u),int(v));return x+.5,y+.5
    for u in range(1,15):
        for v in range(1,15):
            x,y=cell(u,v);world[x][y]=0
    for rect,height in (((1,2,6,9),.75),((9,1,15,6),0.),((9,10,15,15),-.5)):
        rid=len(rooms);native=[]
        for u in range(rect[0],rect[2]):
            for v in range(rect[1],rect[3]):
                x,y=cell(u,v);floors[x][y]=height;room_ids[x][y]=rid;native.append((x,y))
        xs,ys=zip(*native);centre=cell(*_point(rect))
        rooms.append(dict(id=rid,rect=(min(xs),min(ys),max(xs)+1,max(ys)+1),sector=vertical,centre=centre))
    for u,z in ((6,.625),(7,.5),(8,.375),(9,.25),(10,.125),(11,0.)):
        for v in (3,4):x,y=cell(u,v);floors[x][y]=z;reserved.add((x,y))
    for v,z in ((7,-.125),(8,-.25),(9,-.375)):
        for u in (10,11):x,y=cell(u,v);floors[x][y]=z;reserved.add((x,y))
    lift_cells=[cell(u,v) for u in (6,7) for v in (6,7)]
    xs,ys=zip(*lift_cells)
    high=(*point(5.5,6.5),.75);low=(*point(8.5,6.5),0.)
    lifts=[dict(rect=(min(xs),min(ys),max(xs)+1,max(ys)+1),low=0.,high=.75,landings=(high,low))]
    for x,y in lift_cells:floors[x][y]=0.;reserved.add((x,y))
    for x,y,z in (high,low):reserved.add((int(x),int(y)))
    # Keep all stair approaches, shaft perimeter, and boarding space clear.
    reserved={p for x,y in reserved for p in ((x,y),(x-1,y),(x+1,y),(x,y-1),(x,y+1))}
    vertical_reserved=set(reserved)

    counts={s:1 for s in range(4) if s!=vertical}
    remaining=rules['rooms'][index]-3-len(counts)
    for i in range(remaining):counts[[s for s in order if s!=vertical][i%3]]+=1
    for s,count in counts.items():
        a,b,c,d=boxes[s]
        columns=math.ceil(math.sqrt(count));rows=math.ceil(count/columns)
        sx=(c-a-4)//columns;sy=(d-b-4)//rows
        slots=[(x,y) for x in range(columns) for y in range(rows)]
        rng.shuffle(slots)
        for gx,gy in slots[:count]:
            left=a+2+gx*sx;top=b+2+gy*sy
            w=rng.randint(min(7,sx-1),min(11,sx-1));h=rng.randint(min(7,sy-1),min(11,sy-1))
            left+=rng.randrange(sx-w);top+=rng.randrange(sy-h)
            carve((left,top,left+w,top+h),True,s)
    hubs={}
    for s in range(4):
        group=[r for r in rooms if r['sector']==s]
        hub=rooms[1]['centre'] if s==vertical else group[0]['centre'];hubs[s]=hub
        for r in group:
            if s!=vertical:corridor(hub,r['centre'],s)
        if s!=vertical and len(group)>1:
            corridor(group[-1]['centre'],group[0]['centre'],s,0)
            corridor(group[-1]['centre'],group[0]['centre'],s,1)
    portals=[]
    for sa,sb in zip(order,order[1:]):
        ra,rb=boxes[sa],boxes[sb]
        if ra[2]==rb[0] or rb[2]==ra[0]:
            boundary=max(ra[0],rb[0]);y=rng.randint(max(ra[1],rb[1])+3,min(ra[3],rb[3])-4)
            pa=(boundary-2,y) if ra[0]<rb[0] else (boundary+1,y)
            pb=(boundary+1,y) if ra[0]<rb[0] else (boundary-2,y)
            opening=[(x,yy) for x in range(boundary-2,boundary+2) for yy in (y,y+1)]
        else:
            boundary=max(ra[1],rb[1]);x=rng.randint(max(ra[0],rb[0])+3,min(ra[2],rb[2])-4)
            pa=(x,boundary-2) if ra[1]<rb[1] else (x,boundary+1)
            pb=(x,boundary+1) if ra[1]<rb[1] else (x,boundary-2)
            opening=[(xx,y) for xx in (x,x+1) for y in range(boundary-2,boundary+2)]
        corridor(hubs[sa],pa,sa);corridor(hubs[sb],pb,sb)
        for x,y in opening:world[x][y]=0;corridors.add((x,y))
        portals.append((sa,sb))
    # Corridors do not alter height data; the prevalidated module remains intact.
    start_room=max((r for r in rooms if r['sector']==order[0]),key=lambda r:sum((p-q)**2 for p,q in zip(r['centre'],hubs[order[1]])))
    end_room=max((r for r in rooms if r['sector']==order[-1]),key=lambda r:sum((p-q)**2 for p,q in zip(r['centre'],start_room['centre'])))
    spawn=tuple(v+.5 for v in start_room['centre'])
    exit_pos=tuple(v+.5 for v in end_room['centre'])
    building_elevators=[];building_reserved=set()
    for room,target,shaft in ((start_room,index-1,index-1),(end_room,index+1,index)):
        if not 0<=target<3:continue
        spec,clear=install_cabin(world,floors,ceilings,room,corridors,target,shaft,rng)
        building_elevators.append(spec);building_reserved|=clear
        if room is start_room:spawn=spec['lobby']
        else:exit_pos=spec['lobby']
    vertical_reserved|=building_reserved
    occupied={tuple(map(int,spawn)),tuple(map(int,exit_pos))};reserved|=corridors|occupied
    props=[];enemies=[];pickups=[]
    h=HeightSectors(world,ceiling=2);h.floors=floors
    scratch=CombatSession(world,[],[],heights=h)
    def place(room,avoid_reserved=False):
        a,b,c,d=room['rect'];candidates=[(x,y) for x in range(a+1,c-1) for y in range(b+1,d-1)
            if room_ids[x][y]==room['id'] and (x,y) not in occupied and (x,y) not in vertical_reserved and (not avoid_reserved or (x,y) not in reserved)]
        rng.shuffle(candidates)
        for x,y in candidates:
            if any((x-xx)**2+(y-yy)**2<2 for xx,yy in occupied):continue
            if scratch.can_occupy(x+.5,y+.5,.35,from_floor=floors[x][y]):
                occupied.add((x,y));return x+.5,y+.5
        raise ValueError('No clear placement in room '+str(room['id']))
    # Starting supplies never depend on what the player brought from the last map.
    pickups.append((*place(start_room),'plasma_rifle'))
    pickups.append((*place(start_room),'pulse_pistol'))
    for s in order:
        room=rng.choice([r for r in rooms if r['sector']==s])
        props.append((*place(room),4))
    for room in rooms:props.append((*place(room),5))
    unlocks=(('scattergun','plasma_axe'),('plasma_launcher','energy_blade'),('scattergun','plasma_launcher'))[index]
    optional_rooms=[r for r in rooms if r['id'] not in (start_room['id'],end_room['id']) and
                    (r['centre']!=hubs[r['sector']] or r['sector']==vertical)]
    for name in unlocks:
        room=rng.choice(optional_rooms);pickups.append((*place(room),name))
    pickups.append((*place(end_room),'pulse_pistol'))
    # More exploration needs resupply along the optional routes too. Reuse
    # accepted animated gun pickups as ammunition caches, with no new assets.
    supply_rooms=[r for r in rooms if r['sector']!=vertical and r['id']!=start_room['id']]
    rng.shuffle(supply_rooms)
    for i in range(rules.get('ammo_caches',(0,0,0))[index]):
        room=supply_rooms[i%len(supply_rooms)]
        pickups.append((*place(room),'plasma_rifle' if i%2==0 else 'pulse_pistol'))
    for i in range(rules.get('bonus_healing',(0,0,0))[index]):
        room=supply_rooms[(i+1)%len(supply_rooms)]
        props.append((*place(room),4))
    eligible=[r for r in rooms if r['id'] not in (start_room['id'],end_room['id'])]
    kinds=(('sentry','drone','crawler'),('sentry','drone','crawler','heavy','turret'),('heavy','turret','drone','sentry','crawler'))[index]
    room_counts={r['id']:0 for r in rooms}
    for i in range(rules['enemies'][index]):
        module_count=sum(room_counts[r['id']] for r in rooms if r['sector']==vertical)
        choices=[r for r in eligible if room_counts[r['id']]<3 and (r['sector']!=vertical or module_count<3)]
        rng.shuffle(choices);placed=False
        for room in choices:
            try:x,y=place(room)
            except ValueError:continue
            if math.hypot(x-spawn[0],y-spawn[1])<6:
                occupied.remove((int(x),int(y)));continue
            if scratch.line_of_sight(x,y,*spawn):
                occupied.remove((int(x),int(y)));continue
            enemies.append((x,y,kinds[i%len(kinds)]));room_counts[room['id']]+=1;placed=True;break
        if not placed:raise ValueError('No fair enemy placement')
    # Original blocking designs live against room edges, away from every route.
    for s in order:
        for kind in (1,rng.choice((2,3,6))):
            group=[r for r in rooms if r['sector']==s];rng.shuffle(group)
            for room in group:
                try:p=place(room,True)
                except ValueError:continue
                props.append((*p,kind));scratch.props=props;break
    if index==2:props.append((*exit_pos,7))
    for room in rooms:
        try:props.append((*place(room,True),0))
        except ValueError:pass
    for x in range(n):
        for y in range(n):
            if world[x][y]:world[x][y]=1+(sector_ids[x][y]*2+index+rng.randrange(2))%8
    encounters=[dict(room=room['id'],sector=room['sector'],
                     enemies=[i for i,e in enumerate(enemies) if room_ids[int(e[0])][int(e[1])]==room['id']])
                for room in rooms if room_counts[room['id']] and room['sector']!=vertical]
    encounters.append(dict(room=None,sector=vertical,
        enemies=[i for i,e in enumerate(enemies) if sector_ids[int(e[0])][int(e[1])]==vertical]))
    level=LevelDefinition(seed=seed,index=index,version=GENERATOR_VERSION,world=world,floors=floors,
        ceilings=ceilings,rooms=rooms,room_ids=room_ids,sectors=sectors,sector_ids=sector_ids,themes=themes,
        spawn=spawn,facing=math.atan2(hubs[order[0]][1]+.5-spawn[1],hubs[order[0]][0]+.5-spawn[0]),
        exits=[(*exit_pos,index+1 if index<2 else 'complete')],props=props,enemies=enemies,
        weapon_pickups=pickups,lifts=lifts,building_elevators=building_elevators,sector_order=order,portals=portals,fallback=False,
        encounters=encounters,vertical_sector=vertical,
        protected_cells=sorted(vertical_reserved|{tuple(map(int,spawn)),tuple(map(int,exit_pos))}),
        optional_rooms=[r['id'] for r in optional_rooms])
    from retro_bosses import install_boss_arena
    install_boss_arena(level,rng,reserved)
    from retro_stacked import install_stacked_area
    install_stacked_area(level,cell)
    from retro_boss_access import install_boss_access
    return install_boss_access(level,rng)

def validate_level(level):
    """Validate both parked lift states, using runtime collision and sight rules."""
    errors=[];checks={}
    def require(condition,reason):
        if not condition and reason not in errors:errors.append(reason)
    n=len(level.world)
    require(n>0 and all(len(row)==n for row in level.world),'map must be rectangular')
    for field in ('floors','ceilings','room_ids','sector_ids','themes'):
        grid=getattr(level,field,())
        require(len(grid)==n and all(len(row)==n for row in grid),'invalid '+field+' grid')
    if errors:return dict(valid=False,errors=errors,checks=checks)
    require(all(level.world[x][y] for x in range(n) for y in range(n) if x in (0,n-1) or y in (0,n-1)),'open outer boundary')
    require(len(level.sectors)==4 and len({s['theme'] for s in level.sectors})==4,'four distinct sector palettes required')
    require(len(level.lifts)==1,'exactly one lift required')
    require(any(f>.5 for row in level.floors for f in row) and any(f<0 for row in level.floors for f in row),'upper and lower areas required')
    require(all(p[2] in range(8) for p in level.props),'rejected prop design')
    require(all(e[2] in ENEMIES for e in level.enemies),'unknown enemy type')
    require(all(p[2] in WEAPONS for p in level.weapon_pickups),'unknown weapon type')
    require(all(0<=x<n and 0<=y<n for x,y,*_ in level.props+level.enemies+level.weapon_pickups+level.exits+[level.spawn]),'placement outside map')
    require(all(math.isfinite(level.floors[x][y]) and math.isfinite(level.ceilings[x][y]) and
                level.ceilings[x][y]-level.floors[x][y]>=.8
                for x in range(n) for y in range(n) if not level.world[x][y]),'insufficient floor headroom')
    sector_themes={s['id']:s['theme'] for s in level.sectors}
    require(all(level.sector_ids[x][y] in sector_themes and
                level.themes[x][y]==sector_themes.get(level.sector_ids[x][y]) and 0<=level.themes[x][y]<8
                for x in range(n) for y in range(n)),'inconsistent sector colors')
    protected=set(getattr(level,'protected_cells',()))
    require(all((int(x),int(y)) not in protected for x,y,kind in level.props if kind!=7) and
            all((int(x),int(y)) not in protected for x,y,_ in level.enemies+level.weapon_pickups),
            'placement blocks protected spawn/stair/lift space')
    if errors:return dict(valid=False,errors=errors,checks=checks)
    try:h=level.build_heights()
    except (ValueError,IndexError):return dict(valid=False,errors=['invalid lift shaft or headroom'],checks=checks)
    session=CombatSession(level.world,level.props,[],heights=h)
    spawn=tuple(map(int,level.spawn))
    # All props use cell centres. For radius < .5, adjacent cell-centre moves
    # sweep only their two cells. Validate centres with the real collider, then
    # require the stricter, reversible ECHO stair limit for every graph edge.
    require(all(abs(p[0]%1-.5)<1e-8 and abs(p[1]%1-.5)<1e-8 for p in level.props),'props must use validated cell centres')
    for stop in ('low','high'):
        for lift in h.lifts:lift.apply(h,getattr(lift,stop))
        unavailable={p for lift in h.lifts if hasattr(lift,'parked') and abs(lift.height-lift.parked)>.01 for p in lift.cells}
        nodes={(x,y) for x in range(n) for y in range(n) if not level.world[x][y] and (x,y) not in unavailable
               and session.can_occupy(x+.5,y+.5,.23,from_floor=h.floor_at(x,y))}
        reached={spawn} if spawn in nodes else set();queue=deque(reached)
        while queue:
            x,y=queue.popleft();f=h.floor_at(x,y)
            for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if (xx,yy) in nodes and (xx,yy) not in reached and abs(h.floor_at(xx,yy)-f)<=STEP_HEIGHT+1e-8:
                    reached.add((xx,yy));queue.append((xx,yy))
        require(len(reached)==len(nodes) and bool(reached),'unreachable or stranded floor at lift '+stop)
        for room in level.rooms:
            require(any(level.room_ids[x][y]==room['id'] for x,y in reached),'unreachable room '+str(room['id']))
        for x,y,*_ in level.exits+level.weapon_pickups+[p for p in level.props if p[2] in (4,5,7)]:
            require((int(x),int(y)) in reached,'unreachable pickup/exit')
        for x,y,kind in level.enemies:
            require(session.can_occupy(x,y,ENEMIES[kind]['radius'],from_floor=h.floor_at(x,y)),'enemy overlaps solid geometry')
            candidates=((xx,yy) for xx,yy in reached if .6<=math.hypot(xx+.5-x,yy+.5-y)<=4)
            require(any(session.line_of_sight(xx+.5,yy+.5,x,y) for xx,yy in candidates),'enemy has no reachable fighting position')
        for lift in h.lifts:
            for x,y,z in lift.landings:
                require((int(x),int(y)) in reached and abs(h.floor_at(x,y)-z)<1e-8,'invalid lift landing')
                require(lift.distance(x,y)<=1.5,'landing cannot call lift')
        for spec in getattr(level,'building_elevators',[]):
            a,b,c,d=spec['rect']
            require(c-a==2 and d-b==2,'building lift must hold player and ECHO')
            require(all((x,y) in reached and abs(h.floor_at(x,y))<1e-8
                        for x in range(a,c) for y in range(b,d)),'unreachable building lift cabin')
            require(session.can_occupy(*spec['lobby'],.23,from_floor=0.),'blocked building lift lobby')
            require(all(level.world[x][y] for x,y in spec['walls']),'building lift missing side wall')
        checks[stop+'_reachable_cells']=len(reached)
    require(any(p[2]=='plasma_rifle' and level.sector_ids[int(p[0])][int(p[1])]==level.sector_ids[spawn[0]][spawn[1]] for p in level.weapon_pickups),'missing safe early rifle')
    require(all(any(p[2]==4 and level.sector_ids[int(p[0])][int(p[1])]==s['id'] for p in level.props) for s in level.sectors),'missing sector healing')
    if getattr(level,'version',0)>=5:
        require(any(p[2]==1 for p in level.props),'missing explosive barrels')
    hp=sum(ENEMIES[e[2]]['health'] for e in level.enemies)
    ammo=sum(WEAPONS[p[2]]['damage']*WEAPONS[p[2]]['capacity']*2 for p in level.weapon_pickups)
    require(ammo>=hp*1.5,'insufficient independent ammunition budget')
    counts={r['id']:0 for r in level.rooms}
    for x,y,kind in level.enemies:
        rid=level.room_ids[int(x)][int(y)];counts[rid]=counts.get(rid,0)+1
        require(math.hypot(x-level.spawn[0],y-level.spawn[1])>=6,'enemy too close to spawn')
        require(not session.line_of_sight(x,y,*level.spawn),'enemy can fire into spawn')
    require(max(counts.values())<=3,'encounter exceeds three enemies')
    encounter_indices=[i for encounter in level.encounters for i in encounter['enemies']]
    require(sorted(encounter_indices)==list(range(len(level.enemies))) and
            all(len(e['enemies'])<=3 for e in level.encounters),'invalid encounter groups')
    require(sum(level.sector_ids[int(x)][int(y)]==level.vertical_sector for x,y,kind in level.enemies)<=3,
            'vertical module encounter exceeds three enemies')
    require(level.index>0 or all(e[2] not in ('heavy','turret') for e in level.enemies),'heavy encounter before level two')
    if hasattr(level,'building_elevators'):
        expected={i for i in (level.index-1,level.index+1) if 0<=i<3}
        require({s['target'] for s in level.building_elevators}==expected,'building lift floor links are invalid')
        require(all(s['shaft']==min(level.index,s['target']) for s in level.building_elevators),'building lift shaft mismatch')
    if getattr(level,'version',0)>=6:
        from retro_bosses import BOSS_SPECS
        bosses=[e for e in level.enemies if e[2] in BOSS_SPECS]
        require(len(bosses)==(1 if level.index==2 else 0),'final floor must contain exactly one boss')
        if level.index==2:
            boss=getattr(level,'boss',{})
            require(bool(boss) and bosses and bosses[0][2]==boss.get('kind'),'invalid boss metadata')
            if boss and bosses:
                require(level.room_ids[int(bosses[0][0])][int(bosses[0][1])]==boss['room'],'boss outside arena')
                require(level.room_ids[int(level.exits[0][0])][int(level.exits[0][1])]==boss['room'],'exit outside boss arena')
                require(boss.get('layout') in range(3),'invalid boss arena layout')
    checks.update(enemy_health=hp,ammunition_damage=ammo,rooms=len(level.rooms),sectors=4)
    from retro_boss_access import validate_boss_access
    errors.extend(validate_boss_access(level))
    from retro_stacked import validate_stacked_area
    errors.extend(validate_stacked_area(level))
    checks['stacked_areas']=len(getattr(level,'stacked_areas',[]))
    return dict(valid=not errors,errors=errors,checks=checks)

def generate_level(seed,index,rules=None):
    config=dict(DEFAULT_RULES);config.update(rules or {})
    for attempt in range(config['attempts']):
        try:level=_layout(seed+attempt*1000003,index,config)
        except ValueError:continue
        report=validate_level(level)
        if report['valid']:level.validation=report;level.requested_seed=seed;return level
    # Safe fallback removes other optional solid fixtures from a bounded bank
    # of asymmetric candidates, retaining the validated barrel minimum and all
    # enemies, supplies and objectives.
    for fallback_seed in range(256):
        try:level=_layout(918273+index*10000+fallback_seed,index,config)
        except ValueError:continue
        level.props=[p for p in level.props if p[2] not in BLOCKING_PROPS or p[2]==1]
        report=validate_level(level)
        if report['valid']:
            level=_orient_level(level,seed%8)
            level.fallback=True;level.requested_seed=seed;level.validation=validate_level(level)
            if level.validation['valid']:return level
    raise ValueError('No valid level; generation rules need repair')

def generate_run(seed,rules=None):
    rng=random.Random(seed)
    return GeneratedRun(seed,[generate_level(rng.getrandbits(63),i,rules) for i in range(3)])

def _orient_level(level,orientation):
    """D4 variants preserve the proven fallback's geometry and every placement."""
    import copy
    out=copy.deepcopy(level);n=len(level.world);turn=orientation%4;mirror=orientation>=4
    def cell(x,y):
        if mirror:x=n-1-x
        for _ in range(turn):x,y=n-1-y,x
        return x,y
    def point(x,y):
        if mirror:x=n-x
        for _ in range(turn):x,y=n-y,x
        return x,y
    def rect(box):
        x0,y0,x1,y1=box;pts=[cell(x,y) for x in (x0,x1-1) for y in (y0,y1-1)]
        xs,ys=zip(*pts);return min(xs),min(ys),max(xs)+1,max(ys)+1
    for field in ('world','floors','ceilings','room_ids','sector_ids','themes'):
        original=getattr(level,field);grid=[[None]*n for _ in range(n)]
        for x in range(n):
            for y in range(n):xx,yy=cell(x,y);grid[xx][yy]=original[x][y]
        setattr(out,field,grid)
    out.protected_cells=sorted(cell(x,y) for x,y in level.protected_cells)
    for field in ('rooms','sectors'):
        for item in getattr(out,field):
            item['rect']=rect(item['rect'])
            if 'centre' in item:item['centre']=cell(*item['centre'])
    if getattr(out,'boss',None):
        out.boss['rect']=rect(out.boss['rect'])
        out.boss['spawn']=point(*out.boss['spawn'])
        out.boss['exit']=point(*out.boss['exit'])
    if getattr(out,'boss_access',None):
        out.boss_access['key']=point(*out.boss_access['key'])
        out.boss_access['gates']=sorted(cell(x,y) for x,y in out.boss_access['gates'])
    out.spawn=point(*level.spawn)
    for field in ('exits','props','enemies','weapon_pickups'):
        setattr(out,field,[(*point(x,y),*rest) for x,y,*rest in getattr(level,field)])
    for spec in out.lifts:
        spec['rect']=rect(spec['rect']);spec['landings']=tuple((*point(x,y),z) for x,y,z in spec['landings'])
        if 'normal' in spec:
            dx,dy=spec['normal']
            if mirror:dx=-dx
            for _ in range(turn):dx,dy=-dy,dx
            spec['normal']=(dx,dy)
    for spec in getattr(out,'building_elevators',[]):
        spec['rect']=rect(spec['rect']);spec['lobby']=point(*spec['lobby'])
        for field in ('walls','protected'):spec[field]=sorted(cell(x,y) for x,y in spec[field])
        dx,dy=spec['normal']
        if mirror:dx=-dx
        for _ in range(turn):dx,dy=-dy,dx
        spec['normal']=(dx,dy)
    dx,dy=math.cos(level.facing),math.sin(level.facing)
    if mirror:dx=-dx
    for _ in range(turn):dx,dy=-dy,dx
    out.facing=math.atan2(dy,dx)
    out.stacked_areas=[_orient_level(area,orientation) for area in getattr(level,'stacked_areas',[])]
    return out

def fresh_run(seed,previous_fingerprint=None,rules=None):
    """Prevent an immediate structural repeat, including the fallback path."""
    previous=set(previous_fingerprint.split(':')) if previous_fingerprint else set()
    for offset in range(8):
        run=generate_run(seed+offset,rules)
        if all(level.fingerprint() not in previous for level in run.levels):return run
    for index,level in enumerate(run.levels):
        if level.fingerprint() not in previous:continue
        for orientation in range(1,8):
            candidate=_orient_level(level,orientation)
            if candidate.fingerprint() not in previous and validate_level(candidate)['valid']:
                run.levels[index]=candidate;break
        else:raise ValueError('Repeated fallback layout')
    return run

def level_progress(definition,session,visited_rooms):
    totals=dict(rooms=len(definition.rooms),kills=len(definition.enemies),
                data=sum(p[2]==5 for p in definition.props),gear=len(definition.weapon_pickups))
    done=dict(rooms=len(visited_rooms),kills=session.kills,data=session.treasure,
              gear=totals['gear']-len(session.weapon_pickups))
    # The active session carries data-only snapshots of the other local decks.
    root=getattr(session,'floor_definition',definition)
    definitions=[root]+list(getattr(root,'stacked_areas',[]))
    if len(definitions)>1:
        states=getattr(session,'area_states',{})
        current=getattr(definition,'area_id',0)
        totals=dict(rooms=0,kills=0,data=0,gear=0);done=dict(totals)
        for area in definitions:
            subtotal=dict(rooms=len(area.rooms),kills=len(area.enemies),data=sum(p[2]==5 for p in area.props),gear=len(area.weapon_pickups))
            saved=states.get(area.area_id)
            active=session if area.area_id==current else (saved['session'] if saved else None)
            visited=visited_rooms if area.area_id==current else (saved['visited_rooms'] if saved else ())
            subdone=dict(rooms=len(visited),kills=active.kills if active else 0,data=active.treasure if active else 0,
                         gear=subtotal['gear']-len(active.weapon_pickups) if active else 0)
            for key in totals:totals[key]+=subtotal[key];done[key]+=subdone[key]
    total=sum(totals.values());count=sum(done.values())
    return dict(done=done,totals=totals,percent=int(100*count/max(1,total)),full_clear=done==totals)
