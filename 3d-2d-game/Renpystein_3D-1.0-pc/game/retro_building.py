"""Full building floors joined by enclosed elevators; no graphics dependency."""
import copy
import math

def install_cabin(world,floors,ceilings,room,corridors,target,shaft,rng):
    """Fit a two-person cabin into a closed room corner, opening into its lobby."""
    a,b,c,d=room['rect']
    def point(u,v,turn):
        return ((a+u,b+v),(c-1-v,b+u),(c-1-u,d-1-v),(a+v,d-1-u))[turn]
    choices=[]
    for turn in range(4):
        shell={point(-1,v,turn) for v in range(-1,3)}|{point(u,-1,turn) for u in range(-1,3)}
        # The two outer room walls already enclose the back and left side.
        if any(not (0<=x<len(world) and 0<=y<len(world)) or not world[x][y] for x,y in shell):continue
        walls={point(2,v,turn) for v in range(3)}
        score=sum(p in corridors for p in walls)
        choices.append((score,rng.random(),turn,walls))
    if not choices:raise ValueError('No closed room corner for building elevator')
    _,_,turn,walls=min(choices)
    for x,y in walls:world[x][y]=8
    protected={point(u,v,turn) for u in range(2) for v in range(5)}
    for x,y in protected:
        if world[x][y]:raise ValueError('Elevator lobby crosses a wall')
        floors[x][y]=0.;ceilings[x][y]=2.
    cells=[point(u,v,turn) for u in range(2) for v in range(2)]
    xs,ys=zip(*cells);rect=(min(xs),min(ys),max(xs)+1,max(ys)+1)
    centre=((rect[0]+rect[2])/2,(rect[1]+rect[3])/2)
    x,y=point(0,0,turn);xx,yy=point(0,1,turn);normal=(xx-x,yy-y)
    lobby=(centre[0]+normal[0]*2.5,centre[1]+normal[1]*2.5)
    return dict(rect=rect,normal=normal,lobby=lobby,target=target,shaft=shaft,room=room['id'],
                protected=sorted(protected),walls=sorted(walls)),protected

class BuildingLift:
    def __init__(self,spec):
        self.spec=spec;self.rect=spec['rect'];self.target_floor=spec['target'];self.shaft=spec['shaft']
        self.state='idle';self.elapsed=0.;self.called=False
        self.close_time=.5;self.travel_time=2.2;self.open_time=.5

    @property
    def centre(self):
        a,b,c,d=self.rect;return (a+c)/2,(b+d)/2

    @property
    def locked(self):return self.state in ('closing','travel','opening','arrived')

    @property
    def moving(self):return self.state=='travel'

    @property
    def door_fraction(self):
        if self.state=='closing':return min(1.,self.elapsed/self.close_time)
        if self.state=='opening':return max(0.,1-self.elapsed/self.open_time)
        return 1. if self.state in ('travel','arrived') else 0.

    def contains(self,x,y):
        a,b,c,d=self.rect;return a<=x<c and b<=y<d

    def distance(self,x,y):
        a,b,c,d=self.rect;return math.hypot(max(a-x,0,x-c),max(b-y,0,y-d))

    def boarding_spot(self,x,y):
        cx,cy=self.centre;nx,ny=self.spec['normal'];sx,sy=-ny,nx
        side=1 if (x-cx)*sx+(y-cy)*sy<=0 else -1
        return cx+sx*.55*side,cy+sy*.55*side

    def waiting_for_companion(self,x,y,ally):
        if ally is None or not ally.alive:return False
        spot=self.boarding_spot(x,y)
        return not self.contains(ally.x,ally.y) or math.hypot(ally.x-spot[0],ally.y-spot[1])>.4

    def request(self,x,y):
        if self.state!='idle' or not self.contains(x,y):return False
        self.state='boarding';self.elapsed=0.;return True

    def update(self,dt,player,ally):
        if self.state in ('idle','arrived'):return False
        self.elapsed+=max(0.,dt)
        if self.state=='boarding':
            if not self.contains(player.x,player.y):self.state='idle';self.elapsed=0.;return False
            if self.elapsed<.6 or self.waiting_for_companion(player.x,player.y,ally):return False
            self.state='closing';self.elapsed=0.
        elif self.state=='closing' and self.elapsed>=self.close_time:self.state='travel';self.elapsed=0.
        elif self.state=='travel' and self.elapsed>=self.travel_time:
            self.state='arrived';self.elapsed=0.;return True
        elif self.state=='opening' and self.elapsed>=self.open_time:self.state='idle';self.elapsed=0.
        return False

def capture_traveler(session):
    return dict(time=session.time,health=session.health,owned=set(session.owned_weapons),
                weapons=copy.deepcopy(session.weapons),weapon_name=session.weapon_name,
                companion=copy.deepcopy(session.companion),boss_keys=set(getattr(session,'boss_keys',())))

def apply_traveler(session,traveler):
    """Keep equipment and ECHO timers continuous across independent floor clocks."""
    delta=session.time-traveler['time']
    session.health=traveler['health'];session.owned_weapons=set(traveler['owned'])
    session.weapons=copy.deepcopy(traveler['weapons']);session.weapon_name=traveler['weapon_name']
    session.boss_keys=set(traveler.get('boss_keys',()))
    from retro_boss_access import apply_access
    apply_access(session)
    for weapon in session.weapons.values():
        for field in ('last_fire','next_fire','reload_started'):
            value=getattr(weapon,field)
            if value is not None:setattr(weapon,field,value+delta)
    session.companion=copy.deepcopy(traveler['companion'])
    ally=session.companion
    if ally is not None:
        for field in ('state_since','next_attack','last_damage','disabled_until'):
            if hasattr(ally,field):setattr(ally,field,getattr(ally,field)+delta)
        ally.path=[];ally.path_refresh=session.time;ally.follow_progress_at=session.time
        ally.recall_cooldown=session.time+1.;ally.separated_since=None
    session.accumulator=0.;session.damage_until=0.;session.hit_until=0.
    session.notice_kind=None;session.notice_until=0.;session.building_lift=None

def floor_snapshot(arena):
    """Keep gameplay data only; inactive floors retain no renderer or GPU textures."""
    return dict(session=arena.session,visited_rooms=set(arena.visited_rooms))

def building_progress(run):
    reports=[]
    for index,level in enumerate(run.levels):
        if index in run.results:
            reports.append(run.results[index]);continue
        definitions=[level]+list(getattr(level,'stacked_areas',[]))
        totals=dict(rooms=sum(len(d.rooms) for d in definitions),
            kills=sum(len(d.enemies) for d in definitions),
            data=sum(sum(p[2]==5 for p in d.props) for d in definitions),
            gear=sum(len(d.weapon_pickups) for d in definitions))
        reports.append(dict(totals=totals,done={key:0 for key in totals}))
    totals={key:sum(r['totals'][key] for r in reports) for key in ('rooms','kills','data','gear')}
    done={key:sum(r['done'][key] for r in reports) for key in totals}
    return dict(totals=totals,done=done,percent=int(100*sum(done.values())/max(1,sum(totals.values()))),
                full_clear=len(run.results)==len(run.levels) and totals==done)
