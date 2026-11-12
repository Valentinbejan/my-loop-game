"""Mouse/touch hold regions in the minigame's native 1920x1080 coordinates."""
# IDs and semantic actions keep the input rules independently testable.
REGIONS=(
 ('forward_left',(24,508,116,88),'move',('forward','left')),
 ('forward',(148,508,116,88),'move',('forward',)),
 ('forward_right',(272,508,116,88),'move',('forward','right')),
 ('left',(24,604,116,88),'move',('left',)),
 ('run',(148,604,116,88),'move',('forward','sprint')),
 ('right',(272,604,116,88),'move',('right',)),
 ('strafe_left',(24,700,116,88),'move',('strafe_left',)),
 ('back',(148,700,116,88),'move',('back',)),
 ('strafe_right',(272,700,116,88),'move',('strafe_right',)),
 ('weapon',(1410,540,280,88),'weapon',()),
 ('reload',(1410,644,280,88),'reload',()),
 ('fire',(1710,600,186,188),'fire',()),
)
LABELS=('L+GO','GO','R+GO','TURN L','RUN','TURN R','STEP L','BACK','STEP R','WEAPON','RELOAD','FIRE')
def region_at(x,y):
    return next((r for r in REGIONS if r[1][0]<=x<r[1][0]+r[1][2] and r[1][1]<=y<r[1][1]+r[1][3]),None)
