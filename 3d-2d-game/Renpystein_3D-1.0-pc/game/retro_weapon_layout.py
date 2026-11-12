"""Keep each weapon's grip visible and its sleeve ends concealed by the HUD."""
FRAME_SIZE = 96
CORE_LEFT = 16
CORE_SIZE = 64
HUD_HEIGHT = 240

# Integer zoom preserves square pixels. The anchor is the native row at the HUD
# in the raised pose; per-weapon values account for different wrist positions.
PROFILES = {
    "pulse_pistol": (6, 240, 58, 48),
    "plasma_rifle": (6, 260, 54, 48),
    "scattergun": (6, 260, 58, 48),
    "plasma_launcher": (6, 120, 54, 48),
    "baton": (5, -224, 60, 32),
    "energy_blade": (5, -216, 62, 32),
    "plasma_axe": (5, -224, 60, 32),
}

def weapon_zoom(name):
    return PROFILES[name][0]

def weapon_visible_row(name, zoom, rest):
    _, _, anchor, drop = PROFILES[name]
    return anchor - drop * max(0.0, min(1.0, rest)) / zoom

def weapon_position(width,height,zoom,name,rest):
    rest=max(0.0,min(1.0,rest))
    _,offset,anchor,drop=PROFILES[name]
    x=(width-CORE_SIZE*zoom)/2+offset-CORE_LEFT*zoom
    y=height-HUD_HEIGHT-anchor*zoom+drop*rest
    return round(x),round(y)
