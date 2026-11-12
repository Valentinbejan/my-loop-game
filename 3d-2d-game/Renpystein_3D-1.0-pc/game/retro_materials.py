"""Deterministic architectural finishes, independent of sector colors."""
from collections import deque

WALL_VARIANTS=('lab-armor','lab-service','reactor-ribs','reactor-conduits',
               'cargo-bracing','cargo-lockers','maintenance-vents','maintenance-hatch')
FLOOR_VARIANTS=('lab-tiles','lab-walkway','reactor-grating','reactor-channel',
                'cargo-traction','cargo-plates','maintenance-grid','maintenance-cover')
SECTOR_FAMILY={'ARRIVAL':2,'REACTOR':1,'LABORATORY':0,'EXTRACTION':3}


def room_materials(definition):
    """Extend saved room identities onto adjacent walls without consuming RNG."""
    world=definition.world;width=len(world)
    names={sector['id']:sector['name'] for sector in definition.sectors}
    seed=int(definition.seed);deck=getattr(definition,'area_id',0)
    styles={}
    for room in definition.rooms:
        family=SECTOR_FAMILY.get(names.get(room['sector']),3)
        if deck:family=(family+deck+room['id'])%4
        variant=(seed+room['id']*3+definition.index*5+deck)%2
        styles[room['id']]=family*2+variant
    materials=[[-1]*len(row) for row in world];queue=deque()
    for x,row in enumerate(definition.room_ids):
        for y,room in enumerate(row):
            if room in styles:materials[x][y]=styles[room];queue.append((x,y))
    # Stable queue ordering resolves walls shared by two rooms consistently.
    while queue:
        x,y=queue.popleft()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<width and 0<=ny<len(world[nx]) and materials[nx][ny]<0:
                materials[nx][ny]=materials[x][y];queue.append((nx,ny))
    return materials


def material_at(x,y,materials):
    x=max(0,min(len(materials)-1,int(x)))
    y=max(0,min(len(materials[x])-1,int(y)))
    return max(0,min(7,materials[x][y]))
