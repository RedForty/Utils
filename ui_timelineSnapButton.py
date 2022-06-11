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
cmds.evalDeferred('ui_timelineSnapButton.create_timelineSnapButton()')

'''
# ==================================================================== #


from maya import cmds, mel



SNAP_BUTTON  = 'toggleTimelineSnap'
SLIDER       = mel.eval('$tempSlider = $gPlayBackSlider')
# Really hoping this doesn't change between maya versions. Works in 2018.
RANGE_SLIDER = 'RangeSlider|MainPlaybackRangeLayout|formLayout9|formLayout14'

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

def create_timelineSnapButton():
    global SNAP_BUTTON
    if not cmds.symbolCheckBox(SNAP_BUTTON, q=True, exists=True):
        SNAP_BUTTON = cmds.symbolCheckBox(SNAP_BUTTON, height=24, width=24, parent=RANGE_SLIDER, image='snapTime.png', onCommand=timelineSnapOff, offCommand=timelineSnapOn, highlightColor=[0.8, 0.8, 0.2])

def delete_timelineSnapButton():        
    # Delete it
    if cmds.symbolCheckBox(SNAP_BUTTON, q=True, exists=True):
        cmds.deleteUI(SNAP_BUTTON)

if __name__ == '__main__':
    create_timelineSnapButton()

