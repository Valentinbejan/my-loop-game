"""Animated world weapon pickups, kept separate from the eight original props."""
from retro_environment import THEMES

class WeaponPickup:
    def __init__(self,x,y,name):
        self.x,self.y,self.name=float(x),float(y),name
        self.appearance_theme=0

    def image_path(self,now):
        return "images/weapon_pickups/krea3/{}/{}_idle_{:02d}.png".format(
            THEMES[self.appearance_theme],self.name,int(now/.18)%4)

def render_pickups(session):
    return [(p.x,p.y,p.image_path(session.time),.55,session.heights.floor_at(p.x,p.y)-.225) for p in session.weapon_pickups]
