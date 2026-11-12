"""Destructible energy drums. Their chain blasts only apply enemy damage."""
import math
from collections import deque
from types import SimpleNamespace

BARREL_KIND=1
BLAST_RADIUS=5.5
BLAST_DAMAGE=220


def ray_barrel(session,x,y,dx,dy,reach,z,slope=0.,padding=0.,limit=None):
    """Nearest exposed barrel hit by a ray or swept projectile, before cover."""
    from retro_projectiles import cylinder_entry
    barrels=[p for p in session.props if p[2]==BARREL_KIND]
    if not barrels:return None
    if limit is None:limit=session.obstruction_distance(x,y,dx,dy,reach,z,slope)
    ray=SimpleNamespace(x=x,y=y,dx=dx,dy=dy,z=z,slope=slope,spec={'radius':padding})
    choices=[]
    for prop in barrels:
        px,py,kind=prop
        if kind!=BARREL_KIND:continue
        entry=cylinder_entry(ray,px,py,session.heights.floor_at(px,py),.35+padding,reach)
        if entry is not None and entry<=limit+1e-7:choices.append((entry,prop))
    return min(choices,key=lambda p:p[0]) if choices else None


def blast_clear(session,x,y,z,tx,ty,tz):
    """Walls, height sectors and solid fixtures block blasts; drums can chain."""
    from retro_combat import BLOCKING_PROPS
    from retro_projectiles import cylinder_entry
    distance=math.hypot(tx-x,ty-y)
    if distance<1e-8:return True
    dx,dy=(tx-x)/distance,(ty-y)/distance;slope=(tz-z)/distance
    if session.heights.ray_limit(x,y,dx,dy,distance,z,slope)<distance-1e-5:return False
    ray=SimpleNamespace(x=x,y=y,dx=dx,dy=dy,z=z,slope=slope,spec={'radius':0.})
    for px,py,kind in session.props:
        if kind not in BLOCKING_PROPS or kind==BARREL_KIND:continue
        entry=cylinder_entry(ray,px,py,session.heights.floor_at(px,py),.35,distance)
        if entry is not None and entry<distance-1e-5:return False
    return True


def detonate_barrel(session,prop):
    """Remove each drum before its blast; a bounded queue prevents recursion.

    Only hurt_enemy is called: neither the player nor the companion can receive
    damage from this feature, regardless of who fired the triggering shot.
    Existing props/session snapshots preserve destruction across saves/floors.
    """
    from retro_projectiles import Impact
    if prop not in session.props or prop[2]!=BARREL_KIND:return False
    queue=deque([prop]);scheduled={tuple(prop)}
    while queue:
        barrel=queue.popleft()
        if barrel not in session.props:continue
        x,y,_=barrel;z=session.heights.floor_at(x,y)+.4
        session.props.remove(barrel)
        session.barrels_detonated=getattr(session,'barrels_detonated',0)+1
        session.effects.append(Impact(x,y,'barrel_explosion',session.time,z+.65))
        session.effects.append(Impact(x,y,'barrel_shockwave',session.time,z))
        for enemy in session.enemies:
            if not enemy.alive or getattr(enemy,'friendly',False):continue
            ez=session.heights.floor_at(enemy.x,enemy.y)+.5
            distance=math.sqrt((enemy.x-x)**2+(enemy.y-y)**2+(ez-z)**2)
            if distance<=BLAST_RADIUS and blast_clear(session,x,y,z,enemy.x,enemy.y,ez):
                damage=max(1,round(BLAST_DAMAGE*max(.25,1-distance/BLAST_RADIUS)))
                session.hurt_enemy(enemy,damage)
        for other in tuple(session.props):
            if other[2]!=BARREL_KIND or tuple(other) in scheduled:continue
            ox,oy,_=other;oz=session.heights.floor_at(ox,oy)+.4
            if math.sqrt((ox-x)**2+(oy-y)**2+(oz-z)**2)<=BLAST_RADIUS and blast_clear(session,x,y,z,ox,oy,oz):
                scheduled.add(tuple(other));queue.append(other)
    return True
