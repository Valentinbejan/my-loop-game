"""Small, wall-occluded survey radius for the persistent automap."""
import math

SURVEY_RADIUS=6.


def visible_cell(world,px,py,tx,ty):
    """Grid ray to a cell centre; solid corners do not reveal diagonal rooms."""
    x,y=math.floor(px),math.floor(py)
    dx,dy=tx+.5-px,ty+.5-py
    sx,sy=(1 if dx>=0 else -1),(1 if dy>=0 else -1)
    stepx=abs(1/dx) if abs(dx)>1e-10 else math.inf
    stepy=abs(1/dy) if abs(dy)>1e-10 else math.inf
    nextx=(x+1-px if sx>0 else px-x)*stepx
    nexty=(y+1-py if sy>0 else py-y)*stepy
    def wall(a,b):return not (0<=a<len(world) and 0<=b<len(world[a])) or bool(world[a][b])
    for _ in range(abs(tx-x)+abs(ty-y)+2):
        if (x,y)==(tx,ty):return True
        if wall(x,y):return False
        if abs(nextx-nexty)<1e-9:
            if wall(x+sx,y) or wall(x,y+sy):return False
            x+=sx;y+=sy;nextx+=stepx;nexty+=stepy
        elif nextx<nexty:x+=sx;nextx+=stepx
        else:y+=sy;nexty+=stepy
    return False


def reveal_cells(world,px,py,explored,radius=SURVEY_RADIUS):
    """Accumulate only nearby open cells visible through the current deck's walls."""
    added=set()
    for x in range(max(0,math.floor(px-radius)),min(len(world),math.floor(px+radius)+1)):
        for y in range(max(0,math.floor(py-radius)),min(len(world[x]),math.floor(py+radius)+1)):
            if world[x][y] or (x,y) in explored:continue
            if (x+.5-px)**2+(y+.5-py)**2>radius*radius:continue
            if visible_cell(world,px,py,x,y):added.add((x,y))
    explored.update(added)
    return added
