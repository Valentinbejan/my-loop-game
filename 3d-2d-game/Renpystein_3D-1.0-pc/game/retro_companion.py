"""A friendly humanoid robot: follows stairs, supports fire, and self-repairs."""
import math
from retro_projectiles import launch,Impact

def create_companion(session,x,y):
    from retro_combat import Enemy
    floor=session.heights.floor_at(x,y)
    for dx,dy in ((.9,.9),(-.9,.9),(.9,-.9),(-.9,-.9),(1.4,0),(-1.4,0)):
        if session.can_occupy(x+dx,y+dy,.23,from_floor=floor):
            ally=Enemy(x+dx,y+dy,'sentry')
            ally.name='ECHO';ally.friendly=True
            ally.spec=dict(ally.spec,health=120,radius=.23,speed=5.2,windup=.16)
            ally.health=120;ally.last_damage=-100.;ally.disabled_until=0.
            ally.next_attack=.4;ally.repair_fraction=0.
            return ally
    return None

def companion_image(ally,now):
    return 'images/allies/armed_v39/'+ally.image_key(now).replace('sentry_','echo_',1)+'.png'

def hurt_companion(session,amount):
    ally=session.companion
    if ally is None or not ally.alive:return
    ally.health=max(0,ally.health-amount);ally.last_damage=session.time
    ally.change_state('hit' if ally.alive else 'death',session.time)
    ally.state_since=session.time
    if not ally.alive:ally.disabled_until=session.time+6

def companion_visible(session,view,x,y):
    """Conservative view test covering the body edges and overhead team marker."""
    if view is None:return True
    dx,dy=x-view.x,y-view.y
    forward=dx*view.dirx+dy*view.diry
    side=dx*view.diry-dy*view.dirx
    # Include the full billboard and a small margin around the camera edges.
    if forward<-.75 or abs(side)>max(0.,forward)*(view.plane_length+.08)+.75:return False
    floor,ceiling,_=session.heights.bounds(x,y)
    for offset in (0.,-.45,.45):
        sx,sy=x-view.diry*offset,y+view.dirx*offset
        for height in (.2,.6,1.12):
            vx,vy=sx-view.x,sy-view.y;distance=math.hypot(vx,vy)
            target_z=min(ceiling-.02,floor+height)
            # Sprite props have transparent gaps; only solid sector geometry can hide her.
            if distance<1e-8 or session.heights.ray_limit(view.x,view.y,vx/distance,vy/distance,
                    distance,view.view_z,(target_z-view.view_z)/distance)>=distance-1e-5:
                return True
    return False

def recover_companion(session,ally,px,py,view,goal,boarding):
    """Recover a separated or stuck helper, without visible disappearance/arrival."""
    now=session.time;distance=math.hypot(goal[0]-ally.x,goal[1]-ally.y)
    best=getattr(ally,'follow_best_distance',distance)
    progress=getattr(ally,'follow_progress_at',now)
    settled=distance<=(.3 if boarding else 1.8)
    same_floor=abs(session.heights.floor_at(ally.x,ally.y)-session.heights.floor_at(px,py))<=.19
    if distance<best-.2 or (settled and same_floor):best=distance;progress=now
    elif distance>best+2:best=distance
    ally.follow_best_distance=best;ally.follow_progress_at=progress
    if distance>8:
        if getattr(ally,'separated_since',None) is None:ally.separated_since=now
    else:ally.separated_since=None
    far=ally.separated_since is not None and now-ally.separated_since>=2
    stuck=(distance>2 or not same_floor) and now-progress>=3
    lift=getattr(session,'building_lift',None) or session.heights.lift_at(px,py)
    late=boarding and lift.waiting_for_companion(px,py,ally) and lift.elapsed>=1.5
    if not (far or stuck or late) or view is None:return False
    if now<getattr(ally,'recall_cooldown',0) or now<getattr(ally,'recall_check_at',0):return False
    ally.recall_check_at=now+.15
    riding=session.heights.lift_at(ally.x,ally.y)
    if (riding and riding.moving) or companion_visible(session,view,ally.x,ally.y):return False
    if boarding:
        x0,y0,x1,y1=lift.rect
        candidates=[lift.boarding_spot(px,py)]+[(x,y) for x in (x0+.45,x1-.45) for y in (y0+.45,y1-.45)]
    else:
        facing=math.atan2(view.diry,view.dirx)
        candidates=[(px+math.cos(facing+angle)*radius,py+math.sin(facing+angle)*radius)
                    for radius in (1.25,1.65,2.1) for angle in (math.pi,math.pi-.45,math.pi+.45,math.pi-.9,math.pi+.9)]
    floor=session.heights.floor_at(px,py)
    for x,y in candidates:
        if boarding and not lift.contains(x,y):continue
        if not session.can_occupy(x,y,ally.spec['radius'],ignore=ally,player=(px,py),from_floor=floor):continue
        # Keep the arrival near the player's accessible floor, with no wall between them.
        if not session.heights.walk_line(px,py,x,y) or not session.line_of_sight(px,py,x,y):continue
        if companion_visible(session,view,x,y):continue
        ally.x,ally.y=x,y;ally.path=[];ally.path_refresh=now
        ally.change_state('idle',now);ally.next_attack=max(ally.next_attack,now+.15)
        ally.follow_best_distance=math.hypot(goal[0]-x,goal[1]-y)
        ally.follow_progress_at=now;ally.separated_since=None;ally.recall_cooldown=now+5
        ally.recall_count=getattr(ally,'recall_count',0)+1
        return True
    return False

def tick_companion(session,dt,px,py,view=None):
    ally=session.companion
    if ally is None:return
    if not ally.alive:
        if session.time>=ally.disabled_until:
            ally.health=60;ally.change_state('idle',session.time)
        else:return
    if session.time-ally.last_damage>5 and ally.health<ally.spec['health']:
        ally.repair_fraction+=dt*8
        if ally.repair_fraction>=1:
            amount=int(ally.repair_fraction);ally.repair_fraction-=amount
            ally.health=min(120,ally.health+amount)
    if ally.state=='hit' and session.time-ally.state_since<.24:return
    player_lift=getattr(session,'building_lift',None) or session.heights.lift_at(px,py)
    boarding=player_lift is not None and player_lift.state=='boarding' and not player_lift.called
    goal_x,goal_y=player_lift.boarding_spot(px,py) if boarding else (px,py)
    recover_companion(session,ally,px,py,view,(goal_x,goal_y),boarding)
    targets=[e for e in session.enemies if e.alive and math.hypot(e.x-ally.x,e.y-ally.y)<=11
             and session.line_of_sight(ally.x,ally.y,e.x,e.y)]
    if targets and session.time>=ally.next_attack:
        target=min(targets,key=lambda e:(e.x-px)**2+(e.y-py)**2)
        dx,dy=target.x-ally.x,target.y-ally.y;distance=max(.01,math.hypot(dx,dy))
        dx,dy=dx/distance,dy/distance
        z=session.heights.floor_at(ally.x,ally.y)+.5
        slope=(session.heights.floor_at(target.x,target.y)+.5-z)/distance
        launch(session,ally.x,ally.y,dx,dy,'ally_bolt','ally',z,slope)
        session.effects.append(Impact(ally.x+dx*.25,ally.y+dy*.25,'muzzle_flash',session.time,z))
        ally.change_state('attack',session.time);ally.state_since=session.time
        ally.next_attack=session.time+.6;target.alerted=True
    attacking=ally.state=='attack' and session.time-ally.state_since<.34
    distance=math.hypot(goal_x-ally.x,goal_y-ally.y)
    ally_lift=session.heights.lift_at(ally.x,ally.y)
    riding=ally_lift is not None and ally_lift.moving
    moved=False
    if distance>(.2 if boarding else 1.6) and not riding:
        direct=session.heights.walk_line(ally.x,ally.y,goal_x,goal_y) and session.line_of_sight(ally.x,ally.y,goal_x,goal_y)
        if not direct and session.time>=ally.path_refresh:
            ally.path=session.find_path((ally.x,ally.y),(goal_x,goal_y));ally.path_refresh=session.time+.3
        if direct:tx,ty=goal_x,goal_y
        else:
            while ally.path and math.hypot(ally.path[0][0]-ally.x,ally.path[0][1]-ally.y)<.13:ally.path.pop(0)
            tx,ty=ally.path[0] if ally.path else (ally.x,ally.y)
        vx,vy=tx-ally.x,ty-ally.y;length=math.hypot(vx,vy)
        if length>.01:
            speed=8.0 if distance>4 else ally.spec['speed']
            step=min(length,speed*dt);nx,ny=ally.x+vx/length*step,ally.y+vy/length*step
            floor=session.heights.floor_at(ally.x,ally.y)
            for xx,yy in ((nx,ny),(nx,ally.y),(ally.x,ny)):
                if session.can_occupy(xx,yy,.23,ignore=ally,player=(px,py),from_floor=floor):
                    moved=xx!=ally.x or yy!=ally.y;ally.x,ally.y=xx,yy;break
    if not attacking:ally.change_state('walk' if moved else 'idle',session.time)
