"""Single floor/ceiling per cell, walkable stairs and height-aware ray traversal."""
import math

STEP_HEIGHT=.19
BODY_HEIGHT=.8
EYE_HEIGHT=.5

class HeightSectors:
    def __init__(self,world,floor=0.0,ceiling=1.0):
        self.world=world
        self.width=len(world);self.height=max(map(len,world))
        self.floors=[[float(floor) for _ in row] for row in world]
        self.ceilings=[[float(ceiling) for _ in row] for row in world]
        self.active=floor!=0 or ceiling!=1
        self.lifts=[];self.version=0

    def bounds(self,x,y):
        x,y=math.floor(x),math.floor(y)
        if not (0<=x<self.width and 0<=y<len(self.world[x])):
            return 0.,1.,True
        return self.floors[x][y],self.ceilings[x][y],bool(self.world[x][y])

    def floor_at(self,x,y):return self.bounds(x,y)[0]

    def set_cell(self,x,y,floor,ceiling=None):
        if 0<=x<self.width and 0<=y<len(self.world[x]):
            self.floors[x][y]=floor
            if ceiling is not None:self.ceilings[x][y]=ceiling
            self.active=True
            self.version=getattr(self,'version',0)+1

    def lift_at(self,x,y):
        return next((lift for lift in getattr(self,'lifts',[]) if lift.contains(x,y)),None)

    def nearby_lift(self,x,y):
        choices=[lift for lift in getattr(self,'lifts',[]) if lift.distance(x,y)<=1.5]
        return min(choices,key=lambda lift:lift.distance(x,y)) if choices else None

    def update_lifts(self,dt,player,ally=None):
        previous=self.floor_at(player.x,player.y)
        rider=self.lift_at(player.x,player.y)
        for lift in getattr(self,'lifts',[]):
            if not hasattr(lift,'target_area'):lift.update(self,dt,player,ally)
        if rider is not None:
            delta=self.floor_at(player.x,player.y)-previous
            player.floor_z=self.floor_at(player.x,player.y)
            player.view_z+=delta

    def reset_lifts(self):
        for lift in getattr(self,'lifts',[]):
            parked=getattr(lift,'parked',lift.low)
            lift.apply(self,parked);lift.state='idle';lift.elapsed=0.;lift.target=parked

    def traversable(self,x,y,source_floor,allow_drop=False):
        f,c,wall=self.bounds(x,y)
        lift=self.lift_at(x,y)
        difference=f-source_floor
        return not wall and not (lift and lift.moving) and c-f>=BODY_HEIGHT and difference<=STEP_HEIGHT+1e-8 and (allow_drop or difference>=-STEP_HEIGHT-1e-8)

    def walk_line(self,px,py,tx,ty):
        dx,dy=tx-px,ty-py;distance=math.hypot(dx,dy)
        if distance<1e-8:return True
        for x,y,near,far,side,nx,ny in self.segments(px,py,dx/distance,dy/distance,distance):
            if far>=distance-1e-8:return True
            if not self.traversable(nx,ny,self.floor_at(x,y)):return False
        return False

    def segments(self,px,py,dx,dy,reach=64):
        """Yield cell intervals and the boundary crossed at their far end."""
        x,y=math.floor(px),math.floor(py)
        sx,sy=(1 if dx>=0 else -1),(1 if dy>=0 else -1)
        tx=abs(1/dx) if abs(dx)>1e-9 else math.inf
        ty=abs(1/dy) if abs(dy)>1e-9 else math.inf
        nx=(x+1-px if sx>0 else px-x)*tx
        ny=(y+1-py if sy>0 else py-y)*ty
        near=0.
        for _ in range(128):
            side=0 if nx<ny else 1
            far=min(nx,ny,reach)
            xx,yy=(x+sx,y) if side==0 else (x,y+sy)
            yield x,y,near,far,side,xx,yy
            if far>=reach:return
            if side==0:nx+=tx
            else:ny+=ty
            x,y=xx,yy;near=far
            if self.bounds(x,y)[2]:return

    def ray_limit(self,px,py,dx,dy,reach,z,slope=0):
        if self.bounds(px,py)[2]:return 0.
        for x,y,near,far,side,xx,yy in self.segments(px,py,dx,dy,reach):
            f,c,_=self.bounds(x,y)
            start_z=z+slope*(near+1e-7)
            if start_z<f-1e-7 or start_z>c+1e-7:return near
            if slope<0:
                hit=(f-z)/slope
                if near+1e-7<hit<far:return hit
            elif slope>0:
                hit=(c-z)/slope
                if near+1e-7<hit<far:return hit
            nf,nc,wall=self.bounds(xx,yy)
            end_z=z+slope*far
            # Prevent a ray leaking through a solid diagonal corner.
            atx,aty=px+dx*far,py+dy*far
            corner=abs(atx-round(atx))<1e-7 and abs(aty-round(aty))<1e-7
            if corner:
                ox,oy=(x,y+(1 if dy>=0 else -1)) if side==0 else (x+(1 if dx>=0 else -1),y)
                of,oc,ow=self.bounds(ox,oy)
                if ow or end_z<of or end_z>oc:return min(reach,far)
            if wall or end_z<nf-1e-7 or end_z>nc+1e-7:return min(reach,far)
        return reach

def build_level_heights(world,level):
    h=HeightSectors(world,ceiling=2.0 if level==0 else 1.0)
    if level!=0:return h
    # The first spawn faces these broad stairs. Eight-cell upper gallery gives
    # a view back across the lower atrium without rooms stacked at one XY cell.
    for x in range(3,8):
        for y in range(8,16):h.set_cell(x,y,.75)
    for x,z in ((12,.125),(11,.25),(10,.375),(9,.5),(8,.625)):
        for y in range(10,13):h.set_cell(x,y,z)
    # A lower service bay and a separate staircase along its north approach.
    for x in range(18,24):
        for y in range(14,21):h.set_cell(x,y,-.5)
    for y,z in ((11,-.125),(12,-.25),(13,-.375)):
        for x in range(19,22):h.set_cell(x,y,z)
    from retro_lifts import install_gallery_lift
    install_gallery_lift(h)
    return h
