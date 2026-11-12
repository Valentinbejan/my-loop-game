"""Shared color zones for walls, planes, fixtures, and pickups."""
import math
from retro_colorways import colorway_name, colorway_slot
from retro_materials import WALL_VARIANTS,material_at

THEMES = ("cyan", "blue", "green", "amber", "red", "violet", "white", "pink")
PALETTES = (
    ("0b1021", "102f3e", "165064", "207d90", "36b5c7", "5be3e0", "aff4de", "e4f3ee"),
    ("0b1021", "172844", "213f75", "345caa", "547fe1", "78acff", "c2d8ff", "e4f3ee"),
    ("0b1021", "18332a", "275a38", "398748", "60b85d", "9de879", "d2f6b0", "e4f3ee"),
    ("0b1021", "3d2920", "70432a", "a66b34", "d99b48", "ffcb66", "ffe7aa", "e4f3ee"),
    ("0b1021", "3d1b2a", "722d3d", "aa4251", "df656b", "ff9391", "ffd0ba", "e4f3ee"),
    ("0b1021", "302042", "523463", "80519d", "ab77d4", "d0a0f5", "ebcdfc", "e4f3ee"),
    ("0b1021", "303640", "505c6b", "7a8792", "aebbbf", "d4dccc", "f4ead3", "e4f3ee"),
    ("0b1021", "3b2039", "6b355d", "a85085", "d97bac", "f6acd1", "ffdaeb", "e4f3ee"),
)
WALL_COUNT = 32
FLOOR_VARIANT_COUNT = 10
FLOOR_COUNT = 80
CEILING_COUNT = 64
CEILING_VARIANTS=('smooth-panel','ribbed-panel','strip-light','vent-grille',
                  'cable-channel','crossbeam','service-hatch','cooling-fan')
SURFACE_ART_VERSION=42
SURFACE_ATLAS='images/environment/surfaces_v42/surface_atlas.png'
SURFACE_ATLAS_LOD='images/environment/surfaces_v42/surface_atlas_lod.png'
SURFACE_ATLAS_WIDTH=1024
SURFACE_ATLAS_HEIGHT=576
SURFACE_ATLAS_COLUMNS=16
PROP_SCALES=(.65,.8,1.,1.,.6,.6,1.,.8)
SECONDARY_ACCENTS=('e7a04b','e7a04b','64c9c0','67bcd0','69cbd2','65d1b0','c78c58','6dd4c1')


def environment_palette(theme):
    """Steel architecture, a sector accent, a secondary accent and warm lamps."""
    p=PALETTES[theme]
    return ('0b1021','202d3d','3d4e60','65798a','a8bdc4','e4f3ee',
            p[2],p[4],p[5],SECONDARY_ACCENTS[theme],'e7a04b','ffe4ae')


def prop_render_profile(number,floor=0.,ceiling=1.):
    """Anchor opaque pixels to the floor/ceiling, including scaled billboards.

    Billboard elevation positions the centre at elevation + .5, regardless of
    scale. The native masters have two transparent pixels below their feet
    (or above the lamp mount); compensate both that padding and the centre.
    """
    size=PROP_SCALES[number]
    centre_correction=(size-1.)*.5
    padding=size*2./64.
    offset=(ceiling-floor-size+centre_correction+padding if number==0
            else centre_correction-padding)
    return size,offset


def theme_at(x, y, width, height, level=0,themes=None):
    if themes is not None:
        cx=max(0,min(len(themes)-1,math.floor(x)))
        cy=max(0,min(len(themes[cx])-1,math.floor(y)))
        return themes[cx][cy]
    column = max(0, min(3, int(x * 4 / width)))
    row = max(0, min(1, int(y * 2 / height)))
    return (column + 4 * row + 3 * level) % 8


def ceiling_variant(x,y,level=0,theme=0):
    """Quiet panel fields with coherent light, cable and structural lanes.

    Keep the small integer rules identical to ceiling_variant in the GPU shader.
    Coordinates and level metadata determine the result; no render-time RNG.
    """
    x,y=math.floor(x),math.floor(y)
    zone=(x//4*3+y//4*5+theme*7+level*11)%8
    lx,ly=x%4,y%4
    if lx==0 and ly==0:return 5
    if ly==1 and lx in (1,2) and zone%3==0:return 2
    if lx==3 and zone in (1,4,6):return 4
    if lx==2 and ly==2:return (3,6,7)[zone%3]
    return 1 if zone in (2,5) else 0


def surface_ids(x, y, width, height, level=0,themes=None,materials=None):
    theme = theme_at(x, y, width, height, level,themes)
    variant=2+material_at(x,y,materials) if materials is not None else (int(x)+int(y))%2
    return theme * FLOOR_VARIANT_COUNT + variant, theme * 8 + ceiling_variant(x,y,level,theme)


def decorate_world(world, level=0,themes=None):
    width, height = len(world), max(map(len, world))
    result, retained = [], set()
    for x, row in enumerate(world):
        decorated = []
        for y, wall in enumerate(row):
            if not wall:
                decorated.append(0)
            elif wall not in retained:
                # Keep one fixture of every original wall design in each level.
                retained.add(wall)
                decorated.append(wall)
            else:
                theme = theme_at(x, y, width, height, level,themes)
                style = (wall - 1 + x // 4 + y // 4) % 3
                decorated.append(9 + theme * 3 + style)
        result.append(decorated)
    return result


def wall_path(number, theme=None, colorway=0):
    if number <= 8 and theme is not None:
        name=colorway_name(theme,colorway) if colorway else 'original'
        return 'images/environment/surfaces_v42/fixtures/{}/{}/wall_{:03d}.png'.format(THEMES[theme],name,number)
    return "images/walls/wall_{:03d}.{}".format(number, "webp" if number <= 8 else "png")


def wall_path_at(number, x, y, width, height, level=0,themes=None,materials=None):
    if number==33:return 'images/keys/boss_v43/gate-wall.png'
    if number>8 and materials is not None:
        return 'images/environment/surfaces_v42/{}/{}.png'.format(
            THEMES[theme_at(x,y,width,height,level,themes)],WALL_VARIANTS[material_at(x,y,materials)])
    return wall_path(number, theme_at(x, y, width, height, level,themes),
                     colorway_slot(number,x,y,level) if number<=8 else 0)


def prop_path(number, x, y, width, height, level=0, now=0, colorway=None,themes=None):
    if number not in range(8):
        raise ValueError("Unknown original prop: {}".format(number))
    # Use the containing floor tile, including half-cell zone boundaries.
    theme = theme_at(math.floor(x), math.floor(y), width, height, level,themes)
    if themes is not None and number==7:theme=(theme+4)%len(THEMES)
    slot=colorway_slot(number,math.floor(x),math.floor(y),level) if colorway is None else colorway
    name=colorway_name(theme,slot) if slot else 'original'
    frame=int(max(0.,now)/.18)%4
    folder='themed_v42' if number in (0,1,2,3,6) else 'krea3_front'
    return "images/props/{}/{}/{}/prop_{:03d}_idle_{:02d}.png".format(folder,THEMES[theme],name,number,frame)
