"""A two-stop moving floor that carries riders and waits for a companion."""
import math

SIGNAL_IMAGES=tuple('images/lift_signals/v23/lift_beacon_signal_{:02d}.png'.format(i) for i in range(2))

def lift_light_phase(now):
    # A restrained alternating signal; the gameplay clock freezes it during pause.
    return int(max(0.,now)/.65)%2

def lift_signal_entries(sectors,now):
    entries=[]
    for lift in getattr(sectors,'lifts',[]):
        x0,y0,x1,y1=lift.rect
        # Fixed posts on the gallery and ground landing, independent of deck height.
        for x,y,floor in getattr(lift,'landings',((x0-.45,y0+.25,lift.high),(x1+.45,y0+.25,lift.low))):
            if sectors.bounds(math.floor(x),math.floor(y))[2]:continue
            entries.append((x,y,SIGNAL_IMAGES[lift_light_phase(now)],.95,floor-.025))
    return entries

class Lift:
    def __init__(self,sectors,rect,low=0.,high=.75):
        self.rect=rect
        self.low,self.high=low,high
        self.height=low;self.target=low;self.start=low
        self.state='idle';self.elapsed=0.;self.duration=2.4
        self.called=False
        x0,y0,x1,y1=rect
        self.cells=[(x,y) for x in range(x0,x1) for y in range(y0,y1)]
        for x,y in self.cells:
            f,c,wall=sectors.bounds(x,y)
            if wall or high+.8>c:raise ValueError('Lift needs an open shaft with headroom')
        self.apply(sectors,low)

    @property
    def moving(self):return self.state=='moving'

    @property
    def centre(self):
        x0,y0,x1,y1=self.rect
        return (x0+x1)/2,(y0+y1)/2

    def contains(self,x,y):
        x0,y0,x1,y1=self.rect
        return x0<=x<x1 and y0<=y<y1

    def boarding_spot(self,x,y):
        x0,y0,x1,y1=self.rect;cx,cy=self.centre
        return (x1-.45 if x<cx else x0+.45,
                y1-.45 if y<cy else y0+.45)

    def waiting_for_companion(self,x,y,ally):
        if self.called or ally is None or not ally.alive:return False
        spot=self.boarding_spot(x,y)
        return not self.contains(ally.x,ally.y) or math.hypot(ally.x-spot[0],ally.y-spot[1])>.45

    def distance(self,x,y):
        x0,y0,x1,y1=self.rect
        return math.hypot(max(x0-x,0,x-x1),max(y0-y,0,y-y1))

    def apply(self,sectors,height):
        changed=abs(self.height-height)>1e-9
        self.height=height
        for x,y in self.cells:
            changed=changed or sectors.floors[x][y]!=height
            sectors.floors[x][y]=height
        if changed:sectors.version=getattr(sectors,'version',0)+1

    def request(self,x,y,floor):
        if self.state!='idle' or self.distance(x,y)>1.5:return False
        aboard=self.contains(x,y)
        target=(self.high if self.height<(self.low+self.high)/2 else self.low) if aboard else min((self.low,self.high),key=lambda h:abs(h-floor))
        if abs(target-self.height)<1e-8:return False
        self.start=self.height;self.target=target
        self.called=not aboard;self.state='boarding';self.elapsed=0.
        return True

    def update(self,sectors,dt,player,ally):
        if self.state=='idle':return
        self.elapsed+=max(0.,dt)
        if self.state=='boarding':
            if not self.called and not self.contains(player.x,player.y):
                self.state='idle';return
            waiting=self.waiting_for_companion(player.x,player.y,ally)
            minimum=.3 if self.called else .6
            # A healthy partner rides with the player. Never abandon her on a timer.
            if self.elapsed<minimum or waiting:return
            self.state='moving';self.elapsed=0.
        fraction=min(1.,self.elapsed/self.duration)
        eased=fraction*fraction*(3-2*fraction)
        self.apply(sectors,self.start+(self.target-self.start)*eased)
        if fraction>=1:
            self.apply(sectors,self.target);self.state='idle';self.elapsed=0.

def install_gallery_lift(sectors):
    if getattr(sectors,'gallery_lift_installed',False):return
    if not hasattr(sectors,'lifts'):sectors.lifts=[]
    sectors.lifts.append(Lift(sectors,(8,14,10,16)))
    sectors.gallery_lift_installed=True
    sectors.active=True;sectors.version=getattr(sectors,'version',0)+1
