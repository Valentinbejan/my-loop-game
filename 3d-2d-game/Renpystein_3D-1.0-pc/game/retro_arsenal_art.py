"""Native asset paths and stable palette selection for the expanded arsenal."""
from retro_environment import THEMES
from retro_bosses import BOSS_KINDS
BOSS_ART_READY=BOSS_KINDS
BOSS_STANDINS={'boss_siege':'heavy','boss_reactor':'drone','boss_blade':'sentry'}
NEW_WEAPONS=("scattergun","plasma_launcher","energy_blade","plasma_axe")
NEW_ENEMIES=("crawler","heavy","turret")
KREA_ENEMIES=("sentry","drone","crawler","heavy","turret")
KREA_WEAPONS=("baton","pulse_pistol","plasma_rifle","scattergun","plasma_launcher","energy_blade","plasma_axe")
MELEE_WEAPONS=("baton","energy_blade","plasma_axe")

def weapon_path(name,state,frame,theme=0):
    stem="{}_{}_{:02d}.png".format(name,state,frame)
    if name in KREA_WEAPONS:
        return "images/weapons/krea3/{}/{}".format(THEMES[theme],stem)
    return "images/weapons/v13/{}/{}".format(THEMES[theme],stem) if name in NEW_WEAPONS else "images/weapons/v9/"+stem

def enemy_frame_path(kind,stage,state,frame,theme=0):
    key="{}_{}_{}_{:02d}".format(kind,stage,state,frame)
    if kind in BOSS_KINDS:
        if kind in BOSS_ART_READY:return "images/enemies/bosses_v40/{}.png".format(key)
        return enemy_frame_path(BOSS_STANDINS[kind],stage,state,frame,theme)
    if kind in KREA_ENEMIES:
        return "images/enemies/krea3/{}/{}.png".format(THEMES[theme],key)
    if kind in NEW_ENEMIES:
        return "images/enemies/v13/{}/{}.png".format(THEMES[theme],key)
    return "images/enemies/v6/"+key+".png"

def enemy_path(enemy,now):
    key=enemy.image_key(now)
    if enemy.kind in BOSS_KINDS:
        state,frame=key.rsplit('_',2)[-2:]
        return enemy_frame_path(enemy.kind,enemy.damage_stage,state,int(frame),getattr(enemy,'appearance_theme',0))
    if enemy.kind in KREA_ENEMIES:
        return "images/enemies/krea3/{}/{}.png".format(THEMES[getattr(enemy,"appearance_theme",0)],key)
    if enemy.kind in NEW_ENEMIES:
        return "images/enemies/v13/{}/{}.png".format(THEMES[getattr(enemy,"appearance_theme",0)],key)
    return "images/enemies/v6/"+key+".png"
