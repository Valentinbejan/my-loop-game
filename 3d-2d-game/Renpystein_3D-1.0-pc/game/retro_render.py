"""Pixel-buffer raycaster: one world texture per frame, nearest-neighbor only."""
import math
import pygame
import renpy
from retro_environment import (wall_path_at,surface_ids,SURFACE_ATLAS,SURFACE_ATLAS_WIDTH,
                               SURFACE_ATLAS_HEIGHT,SURFACE_ATLAS_COLUMNS,FLOOR_COUNT)

_SURFACES = {}
_COLUMNS = {}
_SCALED = {}
_DEPTH_SCALED = {}

def surface(path):
    if path not in _SURFACES:
        _SURFACES[path] = renpy.display.im.load_surface(path)
    return _SURFACES[path]

class PixelRaycaster:
    def __init__(self, world, width=480, height=270, level=0,heights=None):
        self.world, self.width, self.height = world, width, height
        self.level = level
        self.world_size = (len(world), max(map(len,world)))
        self.plane_pixels = None
        self.depth_surface = None
        self._depth_planes = None
        self.focus_depth = 4.0
        self.heights=heights
        self._height_surface=None

    def __getstate__(self):
        state=self.__dict__.copy()
        # GPU depth surfaces are temporary and are rebuilt after loading a save.
        state["depth_surface"]=None
        state["_depth_planes"]=None
        state["_height_surface"]=None
        state.pop('_wall_atlas',None)
        state.pop('_wall_indices',None)
        state.pop('_sector_cells',None)
        state.pop('_sector_version',None)
        return state

    def __setstate__(self,state):
        self.__dict__.update(state)
        self.depth_surface=None
        self._depth_planes=None
        self.focus_depth=state.get("focus_depth",4.0)

    def software_planes(self, player):
        """Nearest-neighbor perspective fallback for the software renderer."""
        if self.plane_pixels is None or len(self.plane_pixels)!=SURFACE_ATLAS_WIDTH*SURFACE_ATLAS_HEIGHT:
            image = surface(SURFACE_ATLAS)
            self.plane_pixels = [tuple(image.get_at((x,y))) for y in range(SURFACE_ATLAS_HEIGHT) for x in range(SURFACE_ATLAS_WIDTH)]
        atlas = self.plane_pixels
        width, height = self.width//2, self.height//2
        small = pygame.Surface((width,height),pygame.SRCALPHA)
        for y in range(height):
            offset = y+.5-height*.5
            if abs(offset) < .5:
                small.fill((11,16,33,255),(0,y,width,1))
                continue
            distance = height*.5*player.projection_scale/abs(offset)
            for x in range(width):
                camera = 2*(x+.5)/width-1
                wx = player.x+(player.dirx+player.planex*camera)*distance
                wy = player.y+(player.diry+player.planey*camera)*distance
                cell_x, cell_y = math.floor(wx), math.floor(wy)
                floor_id, ceiling_id = surface_ids(cell_x,cell_y,*self.world_size,self.level,getattr(self.heights,'themes',None),getattr(self.heights,'materials',None))
                tile = floor_id if offset>0 else ceiling_id+FLOOR_COUNT
                tx = (tile%SURFACE_ATLAS_COLUMNS)*64+min(63,int((wx-cell_x)*64))
                ty = (tile//SURFACE_ATLAS_COLUMNS)*64+min(63,int((wy-cell_y)*64))
                small.set_at((x,y),atlas[ty*SURFACE_ATLAS_WIDTH+tx])
        return pygame.transform.scale(small,(self.width,self.height))

    def frame(self, player, sprites, transparent=False, depth=False,gpu_world=False):
        if getattr(self,'heights',None) is not None and (self.heights.active or gpu_world):
            from retro_sector_render import render_sector_frame
            return render_sector_frame(self,player,sprites,transparent,depth,gpu_world)
        projection_height = self.height * player.projection_scale
        if len(_COLUMNS) > 4096:
            _COLUMNS.clear()
        if len(_SCALED) > 256:
            _SCALED.clear()
        if len(_DEPTH_SCALED) > 256:
            _DEPTH_SCALED.clear()
        if depth:
            if self._depth_planes is None or getattr(self,"_depth_projection",None)!=projection_height:
                self._depth_projection=projection_height
                self._depth_planes = pygame.Surface((self.width,self.height),pygame.SRCALPHA)
                for y in range(self.height):
                    distance=projection_height*.5/max(.5,abs(y+.5-self.height*.5))
                    value=max(1,min(255,round(distance*255/24)))
                    self._depth_planes.fill((value,value,value,255),(0,y,self.width,1))
            self.depth_surface=self._depth_planes.copy()
        canvas = (pygame.Surface((self.width,self.height),pygame.SRCALPHA)
                  if transparent else self.software_planes(player))
        zbuffer = []
        world = self.world
        px,py = player.x,player.y
        for x in range(self.width):
            camera = 2*x/self.width-1
            rx = player.dirx+player.planex*camera
            ry = player.diry+player.planey*camera
            rx = rx if abs(rx)>1e-9 else 1e-9
            ry = ry if abs(ry)>1e-9 else 1e-9
            mx,my = int(px),int(py)
            sx,sy = (-1 if rx<0 else 1),(-1 if ry<0 else 1)
            dx,dy = abs(1/rx),abs(1/ry)
            nx = (px-mx if sx<0 else mx+1-px)*dx
            ny = (py-my if sy<0 else my+1-py)*dy
            wall = 1
            for _ in range(512):
                if nx < ny:
                    distance=nx;nx+=dx;mx+=sx;side=0
                else:
                    distance=ny;ny+=dy;my+=sy;side=1
                if mx<0 or mx>=len(world) or my<0 or my>=len(world[mx]):
                    break
                if world[mx][my]:
                    wall=world[mx][my]
                    break
            distance=max(0.001,distance)
            zbuffer.append(distance)
            height=max(1,min(4096,int(projection_height/distance)))
            top=self.height//2-height//2
            wx=(py+distance*ry) if side==0 else (px+distance*rx)
            u=max(0,min(63,int((wx-math.floor(wx))*64)))
            if (side==0 and rx>0) or (side==1 and ry<0):
                u=63-u
            path=wall_path_at(wall,mx,my,*self.world_size,self.level,getattr(self.heights,'themes',None),getattr(self.heights,'materials',None))
            key=(path,u,height)
            column=_COLUMNS.get(key)
            if column is None:
                tex=surface(path)
                column=pygame.transform.scale(tex.subsurface((u,0,1,64)),(1,height))
                _COLUMNS[key]=column
            canvas.blit(column,(x,top))
            if depth:
                value=max(1,min(255,round(distance*255/24)))
                self.depth_surface.fill((value,value,value,255),(x,top,1,height))
        for entry in sorted(sprites,key=lambda s:-((s[0]-px)**2+(s[1]-py)**2)):
            x,y,path=entry[:3]
            world_size=entry[3] if len(entry)>3 else 1
            elevation=entry[4] if len(entry)>4 else 0
            vx,vy=x-px,y-py
            det=1/(player.planex*player.diry-player.dirx*player.planey)
            tx=det*(player.diry*vx-player.dirx*vy)
            ty=det*(-player.planey*vx+player.planex*vy)
            if ty<=0.001:
                continue
            size=max(1,min(1024,int(projection_height/ty*world_size)))
            center=int(self.width/2*(1+tx/ty))
            left,top=center-size//2,self.height//2-size//2-int(projection_height*elevation/ty)
            start,end=max(0,left),min(self.width,left+size)
            visible_top=max(0,-top)
            visible_bottom=min(size,self.height-top)
            if visible_bottom<=visible_top or start>=end:
                continue
            key=(path,size)
            art=_SCALED.get(key)
            if art is None:
                art=pygame.transform.scale(surface(path),(size,size))
                _SCALED[key]=art
            depth_art=None
            if depth:
                value=max(1,min(255,round(ty*255/24)))
                depth_key=(path,size,value)
                depth_art=_DEPTH_SCALED.get(depth_key)
                if depth_art is None:
                    depth_art=art.copy()
                    depth_art.fill((0,0,0,255),special_flags=pygame.BLEND_RGBA_MULT)
                    depth_art.fill((value,value,value,0),special_flags=pygame.BLEND_RGBA_ADD)
                    _DEPTH_SCALED[depth_key]=depth_art
            run=None
            for stripe in range(start,end+1):
                visible=stripe<end and ty<zbuffer[stripe]
                if visible and run is None:
                    run=stripe
                elif not visible and run is not None:
                    canvas.blit(art,(run,max(0,top)),(
                        run-left,visible_top,stripe-run,visible_bottom-visible_top))
                    if depth:
                        self.depth_surface.blit(depth_art,(run,max(0,top)),(
                            run-left,visible_top,stripe-run,visible_bottom-visible_top))
                    run=None
        if depth:
            self.focus_depth=self.depth_surface.get_at((self.width//2,self.height//2))[0]*24/255
        return canvas

