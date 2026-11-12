"""Cached native elevator doors, animated without fractional texture scaling."""
import pygame
from retro_environment import THEMES

_PANELS={}


def door_frame(lift,now):
    # Freeze travel detail while paused: callers supply the simulation clock.
    return int(max(0.,now)/.10)%8 if lift.state in ('travel','moving') else 0


def lift_panel(theme,frame):
    key=(int(theme)%8,int(frame)%8)
    if key not in _PANELS:
        from retro_render import surface
        tile=surface('images/environment/surfaces_v42/{}/lift-door-{:02d}.png'.format(THEMES[key[0]],key[1]))
        panel=pygame.Surface((240,210),pygame.SRCALPHA)
        # One complete panel per leaf, enlarged by an exact integer factor.
        panel.fill((32,45,61,255))
        panel.blit(pygame.transform.scale(tile,(192,192)),(24,9))
        panel.fill((101,121,138,255),(5,4,230,2))
        panel.fill((61,78,96,255),(5,204,230,2))
        # Structural rails at the exposed door edges.
        panel.fill((11,16,33,255),(0,0,5,210))
        panel.fill((11,16,33,255),(235,0,5,210))
        panel.fill((231,160,75,255),(2,4,2,202))
        panel.fill((231,160,75,255),(236,4,2,202))
        _PANELS[key]=(panel,pygame.transform.flip(panel,True,False))
    return _PANELS[key]
