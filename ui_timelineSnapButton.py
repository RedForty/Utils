# ==================================================================== #
'''
- Subframe Scrubber -
Creates a button next to the rangeslider that lets you toggle
timeline snapping

- How to install -
Place in your ~/maya/scripts folder

- How to use -
Run this PYTHON code in your userSetup.py file or shelf button:

from maya import cmds
import ui_timelineSnapButton
cmds.evalDeferred('ui_timelineSnapButton.createTimelineSnapButton()')

'''
# ==================================================================== #


from maya import cmds, mel

SNAP_BUTTON   = 'toggleTimelineSnap'
# Really hoping this doesn't change between maya versions. Works in 2018.
# RANGE_SLIDER = 'RangeSlider|MainPlaybackRangeLayout|formLayout9|formLayout15'

# Yep, they changed it. 2022 uses this now, but I need to mess with the layout further
RANGE_SLIDER = 'TimeSlider|MainTimeSliderLayout|formLayout8'


'''
# Not using this one
def _toggleTimelineSnap(*args, **kwargs):
    from maya import mel
    mel.eval("timeControl -e -snap (!`timeControl -q -snap $gPlayBackSlider`) $gPlayBackSlider;")
'''

# Using these instead. Simpler to manage button state.
def timelineSnapOn(*args, **kwargs):
    from maya import mel
    slider = mel.eval('$tempSlider = $gPlayBackSlider')
    cmds.timeControl(slider, e=True, snap=True)

def timelineSnapOff(*args, **kwargs):
    from maya import mel
    slider = mel.eval('$tempSlider = $gPlayBackSlider')
    cmds.timeControl(slider, e=True, snap=False)

def createTimelineSnapButton():
    global SNAP_BUTTON
    if not cmds.symbolCheckBox(SNAP_BUTTON, q=True, exists=True):
        lastControl = cmds.formLayout(RANGE_SLIDER, q=True, childArray=True)[-1]
        SNAP_BUTTON = cmds.symbolCheckBox(SNAP_BUTTON, height=24, width=24, parent=RANGE_SLIDER, image='snapTime.png', onCommand=timelineSnapOff, offCommand=timelineSnapOn, highlightColor=[0.8, 0.8, 0.2])
        # New ui changes because maya
        cmds.formLayout(RANGE_SLIDER, e=True, attachForm=[SNAP_BUTTON, 'right', 0])
        cmds.formLayout(RANGE_SLIDER, e=True, attachForm=[SNAP_BUTTON, 'top', 3])
        cmds.formLayout(RANGE_SLIDER, e=True, attachNone=[SNAP_BUTTON, 'left'])
        cmds.formLayout(RANGE_SLIDER, e=True, attachNone=[SNAP_BUTTON, 'bottom'])
        cmds.formLayout(RANGE_SLIDER, e=True, attachControl=[lastControl, 'right', 6, SNAP_BUTTON])

def deleteTimelineSnapButton():
    # Delete it
    if cmds.symbolCheckBox(SNAP_BUTTON, q=True, exists=True):
        cmds.deleteUI(SNAP_BUTTON)
        lastControl = cmds.formLayout(RANGE_SLIDER, q=True, childArray=True)[-1]
        cmds.formLayout(RANGE_SLIDER, e=True, attachForm=[lastControl, 'right', 0])

if __name__ == '__main__':
    createTimelineSnapButton()
    # deleteTimelineSnapButton() # The killcode in case you need it
