"""Three extra prop/fixture colorways in each of the eight room families."""
# Original room color remains option zero. These options add colors to existing art.
COLORWAYS = (
    (("teal","279eac"),("turquoise","45d8c2"),("aqua","81dcf0")),
    (("navy","3c5793"),("cobalt","416be2"),("ice","87c7f5")),
    (("lime","aacb45"),("olive","859448"),("emerald","37b779")),
    (("gold","e8bc50"),("copper","cf875d"),("bronze","ad9857")),
    (("scarlet","de5546"),("crimson","ae3f62"),("coral","ec937a")),
    (("indigo","6865bd"),("lavender","b2a3df"),("orchid","c78fd3")),
    (("ivory","dad3b2"),("slate","879aa6"),("sand","c5ae88")),
    (("rose","d583a5"),("magenta","ca62b7"),("peach","e4b09d")),
)


def colorway_slot(number,x,y,level=0):
    # Integer tile coordinates keep the color fixed while the camera moves.
    return (int(x)*7+int(y)*11+number*3+level)%4


def colorway_name(theme,slot):
    return COLORWAYS[theme][slot-1][0] if slot else None


def colorway_palette(hex_color):
    tint=tuple(int(hex_color[i:i+2],16) for i in (0,2,4))
    dark=(11,16,33)
    light=(228,243,238)
    def mix(a,b,weight):
        return "{:02x}{:02x}{:02x}".format(*(round(x*(1-weight)+y*weight) for x,y in zip(a,b)))
    return ("0b1021",mix(dark,tint,.18),mix(dark,tint,.36),mix(dark,tint,.65),
            hex_color,mix(tint,light,.32),mix(tint,light,.66),"e4f3ee")
