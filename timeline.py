# ============================================================================ #
# Timeline tools

from maya import cmds, mel

# ============================================================================ #
# Flexible Globals

timeline_control = mel.eval('$tmpVar=$gPlayBackSlider')
start_time       = None
end_time         = None
min_time         = None
max_time         = None
increment        = 1
bounds           = True

audio_scrub      = True
audio            = True

# ============================================================================ #

def toggle_audio():
    sound_enabled = cmds.timeControl(timeline_control, q=True, displaySound=True)
    cmds.timeControl(timeline_control, e=True, displaySound=not sound_enabled)
    if sound_enabled == True:
        cmds.evalDeferred('print "Sound disabled"')
    else:
        cmds.evalDeferred('print "Sound enabled"')

def toggle_audio_scrub():
    global audio_scrub
    audio_scrub = not audio_scrub

def toggle_bounds():
    global bounds
    bounds = not bounds

def set_increment(new_increment = 1):
    global increment
    increment = new_increment

def updateVars():
    global start_time, end_time, min_time, max_time
    start_time = cmds.playbackOptions(animationStartTime=1,q=1)
    end_time   = cmds.playbackOptions(animationEndTime=1,q=1)
    min_time   = cmds.playbackOptions(minTime=1,q=1)
    max_time   = cmds.playbackOptions(maxTime=1,q=1)

# ---------------------------------------------------------------------------- #

def set_in():
    updateVars()
    cmds.playbackOptions(min = start_time \
        if cmds.currentTime(q=1) == min_time \
        else cmds.currentTime(q=1))

def set_out():
    updateVars()
    cmds.playbackOptions(max = end_time \
        if cmds.currentTime(q=1) == max_time \
        else cmds.currentTime(q=1))

def set_in_and_out():
    updateVars()
    if cmds.timeControl(timeline_control, q=True, rangeVisible=True):
        range_array = cmds.timeControl(timeline_control, q=True, rangeArray=True)
        cmds.playbackOptions(maxTime=range_array[0], minTime=range_array[-1])
    # Not convinced this behavior should be here
    # else: 
    #     cmds.playbackOptions(maxTime=min_time, minTime=max_time)

# ---------------------------------------------------------------------------- #

def next_frame():
    updateVars()
    cmds.undoInfo(swf=False)
    frame = cmds.currentTime(q=True) + increment
    cmds.currentTime(min_time if bounds and frame > max_time else frame)
    cmds.undoInfo(swf=True)

def previous_frame():
    updateVars()
    cmds.undoInfo(swf=False)
    frame = cmds.currentTime(q=True) - increment
    cmds.currentTime(max_time if bounds and frame < min_time else frame)
    cmds.undoInfo(swf=True)

def next_key():
    updateVars()
    cmds.undoInfo(swf=False)
    frame = cmds.findKeyframe(timeSlider=True, which="next")
    # Returns current frame if it can't find a key
    if frame == cmds.currentTime(q=True):
        cmds.currentTime(max_time, e=1) # Just go to the end
    else:
        cmds.currentTime(frame, e=1)
    cmds.undoInfo(swf=True)

def previous_key():
    updateVars()
    cmds.undoInfo(swf=False)
    frame = cmds.findKeyframe(timeSlider=True, which="previous")
    # Returns current frame if it can't find a key
    if frame == cmds.currentTime(q=True):
        cmds.currentTime(min_time, e=1) # Go to the beginning
    else:
        cmds.currentTime(frame, e=1)
    cmds.undoInfo(swf=True)
