"""Aligned, persistent room-over-room decks served by the local freight lift.

Only the occupied deck is rendered. The shaft gate conceals the deck change;
world XY coordinates and absolute elevation remain aligned throughout the ride.
"""
import copy
import math
from collections import deque
from retro_lifts import Lift


class AreaLift(Lift):
    def __init__(self,sectors,spec):
        super().__init__(sectors,spec['rect'],spec['low'],spec['high'])
        self.spec=spec;self.target_area=spec['target_area'];self.parked=spec['parked']
        self.landings=spec['landings'];self.close_time=.4;self.open_time=.4
        self.apply(sectors,self.parked);self.target=self.parked

    @property
    def locked(self):return self.state in ('closing','moving','arrived','opening')

    @property
    def door_fraction(self):
        if self.state=='closing':return min(1.,self.elapsed/self.close_time)
        if self.state=='opening':return max(0.,1-self.elapsed/self.open_time)
        return 1. if self.state in ('moving','arrived') else 0.

    def boarding_spot(self,x,y):
        cx,cy=self.centre;nx,ny=self.spec['normal'];sx,sy=-ny,nx
        side=1 if (x-cx)*sx+(y-cy)*sy<=0 else -1
        return cx+sx*.55*side,cy+sy*.55*side

    def request(self,x,y,floor):
        # Each deck keeps the shared lift parked at its own landing when active.
        # Boarding is explicit, so pressing F outside cannot send an empty lift.
        if self.state!='idle' or not self.contains(x,y):return False
        self.start=self.height;self.target=self.high if self.parked==self.low else self.low
        self.called=False;self.elapsed=0.;self.state='boarding';return True

    def update(self,sectors,dt,player,ally):
        if self.state in ('idle','arrived'):return False
        self.elapsed+=max(0.,dt)
        if self.state=='boarding':
            if not self.contains(player.x,player.y):self.state='idle';self.elapsed=0.;return False
            if self.elapsed<.6 or self.waiting_for_companion(player.x,player.y,ally):return False
            self.state='closing';self.elapsed=0.
        elif self.state=='closing' and self.elapsed>=self.close_time:
            self.state='moving';self.elapsed=0.
        elif self.state=='moving':
            fraction=min(1.,self.elapsed/self.duration);eased=fraction*fraction*(3-2*fraction)
            previous=self.height;self.apply(sectors,self.start+(self.target-self.start)*eased)
            player.floor_z=self.height;player.view_z+=self.height-previous
            if fraction>=1:
                self.state='arrived';self.elapsed=0.;return True
        elif self.state=='opening' and self.elapsed>=self.open_time:
            self.state='idle';self.elapsed=0.
        return False


def install_stacked_area(level,cell):
    """Three upper rooms occupy the same XY footprint as the existing atrium."""
    from retro_generation import LevelDefinition
    n=len(level.world);sector=level.vertical_sector
    shaft=level.lifts[0];rect=shaft['rect']
    # Enclose the existing deck on three sides, opening east in module space.
    walls=[cell(u,v) for u,v in [(5,6),(5,7),(6,5),(7,5),(6,8),(7,8)]]
    for x,y in walls:level.world[x][y]=8;level.ceilings[x][y]=5.
    for x in range(rect[0],rect[2]):
        for y in range(rect[1],rect[3]):level.ceilings[x][y]=5.
    a,b=cell(7,6);c,d=cell(8,6);normal=(c-a,d-b)
    low=(*shaft['landings'][1][:2],0.)
    shaft.update(high=3.,landings=(low,),parked=0.,target_area=1,normal=normal)
    level.area_id=0;level.area_name='MAIN DECK'
    world=[[1]*n for _ in range(n)];floors=[[3.]*n for _ in range(n)]
    ceilings=[[5.]*n for _ in range(n)];ids=[[-1]*n for _ in range(n)]
    rooms=[]
    for rid,box in enumerate(((9,1,15,6),(9,9,15,15),(1,2,6,13))):
        pts=[]
        for u in range(box[0],box[2]):
            for v in range(box[1],box[3]):
                x,y=cell(u,v);world[x][y]=0;ids[x][y]=rid;pts.append((x,y))
        xs,ys=zip(*pts);cx,cy=cell((box[0]+box[2])//2,(box[1]+box[3])//2)
        rooms.append(dict(id=rid,rect=(min(xs),min(ys),max(xs)+1,max(ys)+1),centre=(cx,cy),sector=sector))
    # Two-wide circulation loops around the closed shaft to the west room.
    for u in range(1,15):
        for v in range(1,15):
            if u in (8,9) or v in (1,2,12,13):world[cell(u,v)[0]][cell(u,v)[1]]=0
    for x in range(rect[0],rect[2]):
        for y in range(rect[1],rect[3]):world[x][y]=0
    upper_spec=copy.deepcopy(shaft)
    upper_spec.update(parked=3.,target_area=0,landings=((*low[:2],3.),))
    # Main-deck stairs underneath are ordinary upper-room space. Protect the
    # upper shaft/landing itself rather than inheriting unrelated lower routes.
    protected={cell(u,v) for u in range(5,10) for v in range(5,9)}
    props=[];enemies=[];pickups=[]
    # Deliberately simple, spaced encounters; the landing and circulation stay safe.
    for rid,coords in enumerate(((12,3),(12,12),(3,7))):
        x,y=cell(*coords);kind=('sentry','drone','crawler')[rid]
        enemies.append((x+.5,y+.5,kind))
    for u,v,kind in ((13,4,5),(13,13,5),(2,10,5),(10,2,4),(2,4,0),(10,4,1),(10,11,1),(4,5,1)):
        x,y=cell(u,v);props.append((x+.5,y+.5,kind))
    for u,v,kind in ((10,13,'plasma_rifle'),(2,11,'scattergun')):
        x,y=cell(u,v);pickups.append((x+.5,y+.5,kind))
    # Match the sector palette underneath, with contrasting enemies and pickups
    # supplied by the existing runtime appearance rules.
    top=LevelDefinition(seed=level.seed,index=level.index,version=4,world=world,floors=floors,
        ceilings=ceilings,rooms=rooms,room_ids=ids,sectors=copy.deepcopy(level.sectors),
        sector_ids=copy.deepcopy(level.sector_ids),themes=copy.deepcopy(level.themes),
        spawn=low[:2],facing=math.atan2(normal[1],normal[0]),exits=[],props=props,enemies=enemies,
        weapon_pickups=pickups,lifts=[upper_spec],building_elevators=[],area_id=1,
        area_name='UPPER WORKS',protected_cells=sorted(protected),stacked_areas=[],
        vertical_sector=sector,encounters=[dict(room=i,sector=sector,enemies=[i]) for i in range(3)])
    top.sector_order=list(level.sector_order)
    level.stacked_areas=[top]
    return level


def validate_stacked_area(level):
    """Check absolute overlap, reciprocal shaft, reversible clearance and loot."""
    from retro_combat import CombatSession,ENEMIES,WEAPONS,BLOCKING_PROPS
    errors=[];areas=getattr(level,'stacked_areas',[])
    if not areas:
        return ['linked lift has no upper deck'] if any('target_area' in s for s in level.lifts) else errors
    if len(areas)!=1:return ['one upper deck required']
    top=areas[0];base=level.lifts[0];other=top.lifts[0]
    if base['rect']!=other['rect'] or base['target_area']!=1 or other['target_area']!=0:
        errors.append('stacked lift links or XY alignment are invalid')
    if base['low']!=0 or base['high']!=3 or other['low']!=0 or other['high']!=3:
        errors.append('stacked lift height mismatch')
    if base['parked']!=0 or other['parked']!=3:errors.append('invalid deck landing elevation')
    try:h=top.build_heights()
    except (ValueError,IndexError):return errors+['invalid upper lift shaft or headroom']
    session=CombatSession(top.world,top.props,[],heights=h)
    floor_nodes={(x,y) for x in range(len(top.world)) for y in range(len(top.world[x])) if not top.world[x][y]}
    # A solid prop's occupied cell is not playable floor. Validate the remaining
    # routes with the real companion clearance, without requiring its explosion.
    nodes={(x,y) for x,y in floor_nodes if session.can_occupy(x+.5,y+.5,.23,from_floor=3.)}
    start=tuple(map(int,top.spawn));seen={start};queue=deque(seen)
    while queue:
        x,y=queue.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if (xx,yy) in nodes and (xx,yy) not in seen and h.walk_line(x+.5,y+.5,xx+.5,yy+.5):
                seen.add((xx,yy));queue.append((xx,yy))
    if seen!=nodes:errors.append('unreachable or stranded upper deck area')
    if not all(h.traversable(x,y,3.) for x,y in floor_nodes):errors.append('upper deck clearance failed')
    if not all(h.floor_at(x,y)>=level.ceilings[x][y] for x,y in nodes if not level.world[x][y] and not h.lift_at(x,y)):
        errors.append('upper rooms intersect lower ceiling')
    overlap=sum(not level.world[x][y] for x,y in nodes if not h.lift_at(x,y))
    if overlap<40:errors.append('upper deck does not overlap lower playable rooms')
    for x,y,z in other['landings']:
        if (int(x),int(y)) not in seen or abs(h.floor_at(x,y)-z)>.001 or h.lifts[0].distance(x,y)>1.5:
            errors.append('invalid upper lift landing')
    protected=set(top.protected_cells)
    if any((int(x),int(y)) in protected for x,y,_ in top.props+top.enemies+top.weapon_pickups):errors.append('upper placement blocks protected lift space')
    for x,y,kind in top.enemies:
        if (int(x),int(y)) not in seen or not session.can_occupy(x,y,ENEMIES[kind]['radius'],from_floor=3.):errors.append('invalid upper enemy position')
        if not any(.6<=math.hypot(xx+.5-x,yy+.5-y)<=4 and session.line_of_sight(xx+.5,yy+.5,x,y) for xx,yy in seen):errors.append('upper enemy has no reachable fighting position')
    loot=[p for p in top.props if p[2] not in BLOCKING_PROPS]+top.weapon_pickups
    if any((int(x),int(y)) not in seen for x,y,_ in loot):errors.append('unreachable upper loot')
    if sum(WEAPONS[p[2]]['damage']*WEAPONS[p[2]]['capacity']*2 for p in top.weapon_pickups)<1.5*sum(ENEMIES[e[2]]['health'] for e in top.enemies):errors.append('insufficient upper ammunition')
    return errors
