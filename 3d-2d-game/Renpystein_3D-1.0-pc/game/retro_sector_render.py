"""Height-sector column portals with per-row occlusion and native texels."""
import math
import pygame
from retro_environment import (wall_path_at,surface_ids,theme_at,SURFACE_ATLAS_LOD,SURFACE_ATLAS_HEIGHT,
                               SURFACE_ATLAS_COLUMNS,FLOOR_COUNT,FLOOR_VARIANT_COUNT)

def height_surface(renderer):
    cached=getattr(renderer,'_height_surface',None)
    if cached is not None and getattr(renderer,'_height_version',-1)==getattr(renderer.heights,'version',0):return cached
    sectors=renderer.heights
    data=pygame.Surface((sectors.width,sectors.height),pygame.SRCALPHA)
    for x in range(sectors.width):
        for y in range(sectors.height):
            f,c,wall=sectors.bounds(x,y)
            packed=(f+2)*32;coarse=math.floor(packed)
            lift=sectors.lift_at(x,y)
            flag=255 if wall else (64+round((packed-coarse)*63) if lift else 0)
            data.set_at((x,y),(coarse,round((c+2)*32),flag,255))
    renderer._height_surface=data
    renderer._height_version=getattr(sectors,'version',0)
    return data

def wall_textures(renderer):
    """Pack existing native wall texels once for the sector GPU renderer."""
    from retro_render import surface
    if getattr(renderer,'_wall_atlas',None) is not None:return renderer._wall_atlas,renderer._wall_indices
    sectors=renderer.heights;paths={};tiles=[]
    # Opaque second lookup plane stores floor identity. Alpha must stay 255:
    # Ren'Py's premultiplication would otherwise corrupt the wall-index bytes.
    data=pygame.Surface((sectors.width,sectors.height*2),pygame.SRCALPHA)
    for x in range(sectors.width):
        for y in range(sectors.height):
            wall=renderer.world[x][y] if y<len(renderer.world[x]) else 1
            pair=[]
            for number in (wall or 1,2):
                path=wall_path_at(number,x,y,*renderer.world_size,renderer.level,getattr(sectors,'themes',None),getattr(sectors,'materials',None))
                if path not in paths:paths[path]=len(tiles);tiles.append(path)
                pair.append(paths[path])
            lift=sectors.lift_at(x,y);edges=0
            if lift:
                for bit,dx,dy in ((1,-1,0),(2,1,0),(4,0,-1),(8,0,1)):
                    if sectors.lift_at(x+dx,y+dy) is not lift:edges+=bit
            theme=theme_at(x,y,*renderer.world_size,renderer.level,getattr(sectors,'themes',None))
            data.set_at((x,y),(pair[0],pair[1],theme*16+edges,255))
            floor_id,_=surface_ids(x,y,*renderer.world_size,renderer.level,getattr(sectors,'themes',None),getattr(sectors,'materials',None))
            data.set_at((x,y+sectors.height),(floor_id,0,0,255))
    assert len(tiles)<=256,'Sector wall atlas exceeded one byte of tile indices'
    atlas=pygame.Surface((512,((len(tiles)+7)//8)*64),pygame.SRCALPHA)
    for i,path in enumerate(tiles):atlas.blit(surface(path),((i%8)*64,(i//8)*64))
    renderer._wall_atlas=atlas;renderer._wall_indices=data
    return atlas,data

def render_sector_frame(renderer,player,sprites,transparent,depth,gpu_world=False):
    from retro_render import surface,_COLUMNS,_SCALED,_DEPTH_SCALED
    w,h=renderer.width,renderer.height
    sectors=renderer.heights
    eye=player.view_z;projection=h*player.projection_scale
    canvas=pygame.Surface((w,h),pygame.SRCALPHA)
    if not transparent:canvas.fill((11,16,33,255))
    if depth:
        if gpu_world:renderer.focus_depth=24.
        renderer.depth_surface=pygame.Surface((w,h),pygame.SRCALPHA)
        renderer.depth_surface.fill((255,255,255,0 if gpu_world else 255))
    clips=[]
    rays=[]
    # Snapshot once per geometry revision, rather than decoding each cell for
    # every ray. Lift travel increments the version and rebuilds these tuples.
    if getattr(renderer,'_sector_version',-1)!=getattr(sectors,'version',0) or not hasattr(renderer,'_sector_cells'):
        renderer._sector_cells=[[(sectors.floors[x][y],sectors.ceilings[x][y],bool(wall))
                                for y,wall in enumerate(row)] for x,row in enumerate(sectors.world)]
        renderer._sector_version=getattr(sectors,'version',0)
    cells=renderer._sector_cells;world_width=len(cells)
    active_columns=None
    if gpu_world:
        # GPU handles the scenery. Trace only rays used to occlude an on-screen
        # sprite, plus the centre ray needed for depth-of-field focus.
        active_columns=[False]*w;active_columns[w//2]=True
        det=1/(player.planex*player.diry-player.dirx*player.planey)
        for entry in sprites:
            vx,vy=entry[0]-player.x,entry[1]-player.y
            tx=det*(player.diry*vx-player.dirx*vy);ty=det*(-player.planey*vx+player.planex*vy)
            if ty<=.001:continue
            scale=entry[3] if len(entry)>3 else 1
            elevation=entry[4] if len(entry)>4 else sectors.floor_at(entry[0],entry[1])
            size=max(1,min(1024,int(projection/ty*scale)))
            top=round(h*.5-(.5+elevation-eye)*projection/ty-size*.5)
            if top+size<=0 or top>=h:continue
            left=int(w*.5*(1+tx/ty))-size//2
            for column in range(max(0,left),min(w,left+size)):active_columns[column]=True
    templates={}
    atlas=surface(SURFACE_ATLAS_LOD) if not transparent else None

    def screen(z,d):return h*.5+(eye-z)*projection/max(.001,d)
    def depth_template(z):
        if z not in templates:
            col=pygame.Surface((1,h),pygame.SRCALPHA)
            for y in range(h):
                slope=(h*.5-(y+.5))/projection
                distance=(z-eye)/slope if abs(slope)>1e-9 else 64
                value=max(1,min(255,round(distance*255/24)))
                col.set_at((0,y),(value,value,value,255))
            templates[z]=col
        return templates[z]

    def plane_span(x,start,end,z,rx,ry,is_floor):
        start,end=max(0,start),min(h,end)
        if start>=end:return
        if depth and gpu_world and x==w//2 and start<=h//2<end:
            slope=(h*.5-(h//2+.5))/projection
            renderer.focus_depth=min(24.,max(1/255*24,(z-eye)/slope))
        if depth and not gpu_world:renderer.depth_surface.blit(depth_template(z),(x,start),(0,start,1,end-start))
        if not transparent:
            for y in range(start,end):
                slope=(h*.5-(y+.5))/projection
                if abs(slope)<1e-9:continue
                d=(z-eye)/slope
                wx,wy=player.x+rx*d,player.y+ry*d
                cx,cy=math.floor(wx),math.floor(wy)
                fi,ci=surface_ids(cx,cy,*renderer.world_size,renderer.level,getattr(sectors,'themes',None),getattr(sectors,'materials',None))
                lift=sectors.lift_at(wx,wy) if is_floor else None
                if lift:fi=fi//FLOOR_VARIANT_COUNT*FLOOR_VARIANT_COUNT+1
                tile=fi if is_floor else ci+FLOOR_COUNT
                footprint=max(d*player.plane_length*2/w,d*d/(projection*max(.0625,abs(z-eye))))*64
                lod=min(4,max(0,int(math.log2(max(1,footprint)))))
                u=(tile%SURFACE_ATLAS_COLUMNS)*64+min(63,int((wx-cx)*64))
                v=(tile//SURFACE_ATLAS_COLUMNS)*64+min(63,int((wy-cy)*64))+lod*SURFACE_ATLAS_HEIGHT
                color=atlas.get_at((u,v))
                if lift:
                    x0,y0,x1,y1=lift.rect
                    tx,ty=int(wx*64),int(wy*64)
                    edge_x=min(tx-x0*64,x1*64-1-tx);edge_y=min(ty-y0*64,y1*64-1-ty)
                    edge=min(edge_x,edge_y)
                    if edge<3:
                        color=(231,160,75,255) if (int(wx*16)+int(wy*16))%2==0 else (11,16,33,255)
                    elif edge<7:
                        along=wy if edge_x<edge_y else wx
                        if int(along*64)%16<7:
                            active=int(along*4)%2==getattr(renderer,'lift_light_phase',0)
                            color=(175,244,222,255) if active else (18,103,107,255)
                canvas.set_at((x,y),color)

    def wall_span(x,hi,lo,d,side,rx,ry,cx,cy,number,top,bottom):
        if hi<=lo:return
        origin=screen(hi,d)
        start=max(top,0,math.floor(origin));end=min(bottom,h,math.ceil(screen(lo,d)))
        if start>=end:return
        if gpu_world:
            if depth and x==w//2 and start<=h//2<end:renderer.focus_depth=min(24.,max(1/255*24,d))
            return
        hit=(player.y+ry*d) if side==0 else (player.x+rx*d)
        u=max(0,min(63,int((hit-math.floor(hit))*64)))
        if (side==0 and rx>0) or (side==1 and ry<0):u=63-u
        path=wall_path_at(number,cx,cy,*renderer.world_size,renderer.level,getattr(sectors,'themes',None),getattr(sectors,'materials',None))
        unit=max(1,min(4096,round(projection/max(.001,d))))
        key=(path,u,unit)
        col=_COLUMNS.get(key)
        if col is None:
            col=pygame.transform.scale(surface(path).subsurface((u,0,1,64)),(1,unit));_COLUMNS[key]=col
        phase=round(((1-hi%1)%1)*unit+start-origin)%unit
        y=start
        while y<end:
            amount=min(end-y,unit-phase)
            canvas.blit(col,(x,y),(0,phase,1,amount));y+=amount;phase=0
        if depth:
            value=max(1,min(255,round(d*255/24)))
            renderer.depth_surface.fill((value,value,value,255),(x,start,1,end-start))

    for x in range(w):
        camera=2*(x+.5)/w-1
        rx,ry=player.dirx+player.planex*camera,player.diry+player.planey*camera
        rays.append((rx,ry))
        if active_columns is not None and not active_columns[x]:
            clips.append([]);continue
        top,bottom=0,h
        cx,cy=math.floor(player.x),math.floor(player.y)
        f,c,_=cells[cx][cy]
        windows=[(0.,top,bottom,f,c)]
        delta_x=abs(1/rx) if abs(rx)>1e-9 else math.inf
        delta_y=abs(1/ry) if abs(ry)>1e-9 else math.inf
        step_x=1 if rx>=0 else -1;step_y=1 if ry>=0 else -1
        edge_x=(cx+1-player.x if step_x>0 else player.x-cx)*delta_x
        edge_y=(cy+1-player.y if step_y>0 else player.y-cy)*delta_y
        near=0.
        for _ in range(128):
            side=0 if edge_x<edge_y else 1
            far=min(edge_x,edge_y,64.)
            nx,ny=(cx+step_x,cy) if side==0 else (cx,cy+step_y)
            nf,nc,wall=cells[nx][ny] if 0<=nx<world_width and 0<=ny<len(cells[nx]) else (0.,1.,True)
            # Identical adjacent planes form one span. Texture variants are
            # still sampled per cell by the GPU or software plane sampler.
            if not wall and nf==f and nc==c and far<64:
                cx,cy=nx,ny
                if side==0:edge_x+=delta_x
                else:edge_y+=delta_y
                continue
            if f<eye:
                yfar=math.ceil(screen(f,far))
                plane_span(x,max(top,yfar),min(bottom,math.ceil(screen(f,near))),f,rx,ry,True)
                bottom=min(bottom,yfar)
            if c>eye:
                yfar=math.floor(screen(c,far))
                plane_span(x,max(top,math.floor(screen(c,near))),min(bottom,yfar+1),c,rx,ry,False)
                top=max(top,yfar+1)
            if wall:
                number=renderer.world[nx][ny] if 0<=nx<len(renderer.world) and 0<=ny<len(renderer.world[nx]) else 1
                wall_span(x,c,f,far,side,rx,ry,nx,ny,number or 1,top,bottom)
                windows.append((far,0,0,nf,nc));break
            wall_span(x,max(f,nf),min(f,nf),far,side,rx,ry,nx,ny,2,top,bottom)
            wall_span(x,max(c,nc),min(c,nc),far,side,rx,ry,nx,ny,2,top,bottom)
            top=max(top,math.floor(screen(min(c,nc),far))+1)
            bottom=min(bottom,math.ceil(screen(max(f,nf),far)))
            windows.append((far,top,bottom,nf,nc))
            if top>=bottom or far>=64:break
            near=far;cx,cy=nx,ny;f,c=nf,nc
            if side==0:edge_x+=delta_x
            else:edge_y+=delta_y
        clips.append(windows)

    for entry in sorted(sprites,key=lambda s:-((s[0]-player.x)**2+(s[1]-player.y)**2)):
        sx,sy,path=entry[:3];scale=entry[3] if len(entry)>3 else 1
        elevation=entry[4] if len(entry)>4 else sectors.floor_at(sx,sy)
        vx,vy=sx-player.x,sy-player.y
        det=1/(player.planex*player.diry-player.dirx*player.planey)
        tx=det*(player.diry*vx-player.dirx*vy)
        ty=det*(-player.planey*vx+player.planex*vy)
        if ty<=.001:continue
        size=max(1,min(1024,int(projection/ty*scale)))
        center=int(w*.5*(1+tx/ty));left=center-size//2
        top=round(h*.5-(.5+elevation-eye)*projection/ty-size*.5)
        # Off-screen props/bots still participate in simulation, but allocating
        # their enlarged color/depth sprites wastes memory and causes stalls
        # while turning near them. Cull before loading or scaling any artwork.
        if left>=w or left+size<=0 or top>=h or top+size<=0:continue
        key=(path,size);art=_SCALED.get(key)
        if art is None:art=pygame.transform.scale(surface(path),(size,size));_SCALED[key]=art
        depth_art=None
        if depth:
            value=max(1,min(255,round(ty*255/24)));key=(path,size,value)
            depth_art=_DEPTH_SCALED.get(key)
            if depth_art is None:
                depth_art=art.copy();depth_art.fill((0,0,0,255),special_flags=pygame.BLEND_RGBA_MULT)
                depth_art.fill((value,value,value,0),special_flags=pygame.BLEND_RGBA_ADD);_DEPTH_SCALED[key]=depth_art
        for stripe in range(max(0,left),min(w,left+size)):
            a,b=0,h
            enter=0.;floor_z=ceil_z=None
            for distance,lo,hi,fz,cz in clips[stripe]:
                if distance>=ty:break
                a,b=lo,hi;enter=distance;floor_z,ceil_z=fz,cz
            # Reproduce the clipping at the last crossed grid edge inside a
            # merged span, including effects/sprites which cross its planes.
            rx,ry=rays[stripe]
            cell_x=math.floor(player.x+rx*(ty-1e-7));cell_y=math.floor(player.y+ry*(ty-1e-7))
            last_x=(cell_x+(1 if rx<0 else 0)-player.x)/rx if abs(rx)>1e-9 else -math.inf
            last_y=(cell_y+(1 if ry<0 else 0)-player.y)/ry if abs(ry)>1e-9 else -math.inf
            last=max(last_x,last_y)
            if last>enter+1e-7 and floor_z is not None:
                a=max(a,math.floor(screen(ceil_z,last))+1)
                b=min(b,math.ceil(screen(floor_z,last)))
            start,end=max(0,a,top),min(h,b,top+size)
            if start>=end:continue
            rect=(stripe-left,start-top,1,end-start)
            canvas.blit(art,(stripe,start),rect)
            if depth:renderer.depth_surface.blit(depth_art,(stripe,start),rect)
    if depth:
        focus_pixel=renderer.depth_surface.get_at((w//2,h//2))
        if not gpu_world or focus_pixel[3]:renderer.focus_depth=focus_pixel[0]*24/255
    if len(_COLUMNS)>4096:_COLUMNS.clear()
    if len(_SCALED)>256:_SCALED.clear()
    if len(_DEPTH_SCALED)>256:_DEPTH_SCALED.clear()
    return canvas
