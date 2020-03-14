# =========================================================================== #
# My collection of graph editor tools
from maya import cmds, mel
from functools import wraps

# ============================================================================ #
# Data handlers ============================================================== #

class Vividict(dict):
    """A dictionary that adds a key if it does not exist."""
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

# ============================================================================ #
# Globals ==================================================================== #

ANIM_CURVE_EDITOR = 'graphEditor1GraphEd'
CHANNELBOX = mel.eval('$temp=$gChannelBoxName')
BACKGROUND_COLOR = (0x32A14B)
FONT_COLOR = 'white'
FONT = 'Roboto'

IN_TANGENT_TYPES  = [ "spline"
                    , "linear"
                    , "fast"
                    , "slow"
                    , "flat"
                    , "stepnext"
                    , "fixed"
                    , "clamped"
                    , "plateau"
                    , "auto"
                    ]

OUT_TANGENT_TYPES = [ "spline"
                    , "linear"
                    , "fast"
                    , "slow"
                    , "flat"
                    , "step"
                    , "fixed"
                    , "clamped"
                    , "plateau"
                    , "auto"
                    ]

VALID_ATTRS       = [ 'translateX'
                    , 'translateY'
                    , 'translateZ'
                    , 'rotateX'
                    , 'rotateY'
                    , 'rotateZ'
                    , 'scaleX'
                    , 'scaleY'
                    , 'scaleZ'
                    , 'tx'
                    , 'ty'
                    , 'tz'
                    , 'rx'
                    , 'ry'
                    , 'rz'
                    , 'sx'
                    , 'sy'
                    , 'sz'
                    ]

SELECTED_KEYS = Vividict()
from maya import cmds, mel

# ============================================================================ #
# Wrappers =================================================================== #

def undo(func):
    '''
    Decorator - open/close undo chunk
    '''
    @wraps(func)
    def wrap(*args, **kwargs):
        cmds.undoInfo(openChunk = True)
        try:
            return func(*args, **kwargs)
        except Exception:
            raise # will raise original error
        finally:
            cmds.undoInfo(closeChunk = True)

    return wrap


# ---------------------------------------------------------------------------- #
# Helper function to restore GE key selection when using the other methods

def restore_ge_selection(func):
    '''
    Decorator - restore ge key selection
    '''
    @wraps(func)
    def wrap(*args, **kwargs):
        # Capture GE selection
        selection_data = {}
        selected_curve_names = cmds.keyframe(q=True, selected=True, name=True) or []
        for curve_name in selected_curve_names:
            keys = cmds.keyframe(curve_name, q=True, selected=True, indexValue=True)
            selection_data[curve_name] = [int(x) for x in keys]
        
        try: # Do the original function
            return func(*args, **kwargs)
        except Exception:
            raise # will raise original error

        finally:
            # This one assumes the selection changed because of the function.
            cmds.selectKey(clear=True)
            # Restore selection
            for curve, keys in selection_data.items():
                for k in keys:
                    cmds.selectKey(curve, add=True, index=(k,))
    return wrap


# ---------------------------------------------------------------------------- #
# Launch the GE - depends on maya version

def launch_graphEditor():
    mel.eval("GraphEditor;")


# ---------------------------------------------------------------------------- #
# Isolate Select

def flexible_isolate_select():
    '''
    Works on both the graph editor and viewport. Use this hotkey instead
    of the standard 'shift-i'.
    '''
    currentPanel  = cmds.getPanel(withFocus=True)
    model_panels  = cmds.getPanel(type='modelPanel')
    graph_editors = cmds.getPanel(scriptType='graphEditor')
    
    if currentPanel in model_panels:
        do_viewport_isolate(currentPanel)
    elif currentPanel in graph_editors:
        do_ge_isolate()        

def do_viewport_isolate(currentPanel):
    if cmds.ls(sl=1) == []:
            # Nothing selected? Un-isolate
            cmds.isolateSelect(currentPanel, state=False)
            cmds.isolateSelect(currentPanel, update=True)
    else:
        # Else isolate
        cmds.isolateSelect(currentPanel, state=True)
        cmds.isolateSelect(currentPanel, addSelected=True)
        cmds.isolateSelect(currentPanel, update=True)

@undo        
@restore_ge_selection
def do_ge_isolate():
    # GE isolating acts differently. There is a job number for it so just toggle it.
    gUnisolateJobNum = mel.eval('global int $gUnisolateJobNum; $temp=$gUnisolateJobNum;')
    if int(gUnisolateJobNum) > 0:
        mel.eval('isolateAnimCurve false graphEditor1FromOutliner graphEditor1GraphEd;')
    else:
        mel.eval('isolateAnimCurve true graphEditor1FromOutliner graphEditor1GraphEd;')

@undo
@restore_ge_selection
def filter_curve():
    # Do filter
    mel.eval('filterCurve')


# ---------------------------------------------------------------------------- #
# Swap keys
@undo
def reverse_keys_horizontal():
    if cmds.scaleKey(attribute=True): # Is a key/curve selected?
        keys = cmds.keyframe(query=True, selected=True, timeChange=True) or []
        curve_names = cmds.keyframe(query=True, selected=True, name=True) or []
    else:
        keys = cmds.keyframe(query=True, timeChange=True) or []
        curve_names = cmds.keyframe(query=True, name=True) or []

    first_key = min(keys)
    last_key = max(keys)
    mid_pivot = (first_key + last_key) / 2
    for curve in curve_names:
        cmds.scaleKey(curve, time=(first_key, last_key), timeScale=-1.0, timePivot=mid_pivot)

    do_snap_keys(first_key, last_key)

@restore_ge_selection
def do_snap_keys(first_key, last_key):
    cmds.selectKey(clear=True) # Must clear the selection to use the -time flag
    cmds.snapKey(time=(first_key, last_key), timeMultiple=1)


# ---------------------------------------------------------------------------- #
# Tangent control

def tangent_spline():
    cmds.keyTangent(inTangentType='spline', outTangentType='spline')
def tangent_linear():
    cmds.keyTangent(inTangentType='linear', outTangentType='linear')
def tangent_flat():
    cmds.keyTangent(inTangentType='flat', outTangentType='flat')
def tangent_auto():
    cmds.keyTangent(inTangentType='auto', outTangentType='auto')
def tangent_stepped():
    cmds.keyTangent(inTangentType='stepnext', outTangentType='step')
# = # 
def tangent_free():
    cmds.keyTangent(weightLock=False)
def tangent_lock():
    cmds.keyTangent(weightLock=True)
# = # 
def tangent_PRESS():
    ''' 
    #  Used to fix a bug in maya, but no longer needed from 2018 onward
    crvs = cmds.keyframe(q=True, sl=True, name=True)
    for crv in crvs:
        times = cmds.keyframe(crv, q=True, sl=True)
        for time in times:
            cmds.keyTangent(crv, time=(time,), e=True, inTangentType="fixed")
            cmds.keyTangent(crv, time=(time,), e=True, outTangentType="fixed")
    '''
    cmds.keyTangent(weightLock=False)
    cmds.keyTangent(lock=False)
def tangent_RELEASE():
    cmds.keyTangent(lock=True)


# ---------------------------------------------------------------------------- #
# Visibilities

def infinity_visibility():
    cmds.animCurveEditor(ANIM_CURVE_EDITOR, e=True, displayInfinities='tgl')

def buffer_curve_visibility():
    cmds.animCurveEditor(ANIM_CURVE_EDITOR, e=True, showBufferCurves='tgl')


# ---------------------------------------------------------------------------- #
# Misc functions

def frame_current_time():
    cmds.animCurveEditor(ANIM_CURVE_EDITOR, e=True, lookAt='currentTime')

def set_time_to_selected():
    current_frames = cmds.keyframe(q=True, selected=True) or []
    if current_frames:
        start_selection_frame = min(current_frames)
        # Use this line to go to the middle
        # middle_frame = (current_frames[0] + current_frames[-1]) / 2
        cmds.currentTime(start_selection_frame)
        cmds.animCurveEditor(ANIM_CURVE_EDITOR, e=True, lookAt='selected')
    else:
        frame_current_time()

def infinity_cycle():
    infinities = ["constant", "linear", "cycle"]
    selected_infinity = cmds.setInfinity(q=1, preInfinite=1, postInfinite=1)[0]
    cmds.setInfinity(preInfinite=infinities[infinities.index(selected_infinity)-1])
    cmds.setInfinity(postInfinite=infinities[infinities.index(selected_infinity)-1])
    message = infinities[infinities.index(selected_infinity)-1]
    status_message = '<div style="color:{2}; font-family:{1}">{0}  </div>'\
               .format( message
                      , FONT
                      , FONT_COLOR
                      )
    cmds.inViewMessage( statusMessage=status_message
                      , fade=True
                      , backColor=BACKGROUND_COLOR
                      , fadeStayTime=600
                      , fadeInTime=0
                      , fadeOutTime=200
                      , position="topCenter"
                      )

def buffer_curve_snapshot():
    cmds.bufferCurve(animation='keys', overwrite=True)

def buffer_curve_swap():
    cmds.bufferCurve(animation='keys', swap=True)

def toggle_normalized():
    normalized_state = cmds.animCurveEditor( ANIM_CURVE_EDITOR
                                           , query=True
                                           , displayNormalized=True
                                           )
    cmds.animCurveEditor( ANIM_CURVE_EDITOR
                        , edit=True
                        , displayNormalized=not(normalized_state)
                        )


# ---------------------------------------------------------------------------- #
# Weight current tangent handle to 0.0 

@undo
def scale_tangent_to_value(value):
    current_channels = cmds.keyframe(q=True, selected=True, name=True)
    if not current_channels: print "Only works on selected keys/curves"; return
    keys_selected = Vividict()
    for channel in current_channels:
        keys = cmds.keyframe(channel, q=True, selected=True, indexValue=True)
        for key in keys:
            tangent_type = cmds.keyTangent(channel, index=(float(key),), q=True, itt=True, ott=True)
            keys_selected[channel][float(key)]['tangent_types']   = tangent_type
            keys_selected[channel][float(key)]['tangent_angles']  = cmds.keyTangent(channel, index=(float(key),), q=True, inAngle=True, outAngle=True)
            keys_selected[channel][float(key)]['tangent_weights'] = cmds.keyTangent(channel, index=(float(key),), q=True, inWeight=True, outWeight=True)
            keys_selected[channel][float(key)]['lock']            = cmds.keyTangent(channel, index=(float(key),), q=True, lock=True)
    
            cmds.keyTangent(itt=IN_TANGENT_TYPES[IN_TANGENT_TYPES.index(tangent_type[0])-1], ott=OUT_TANGENT_TYPES[OUT_TANGENT_TYPES.index(tangent_type[-1])-1])
    
    keys_modified = Vividict()
    for channel in current_channels:
        keys = cmds.keyframe(channel, q=True, selected=True, indexValue=True)
        for key in keys:
            keys_modified[channel][float(key)]['tangent_types'] = cmds.keyTangent(channel, index=(float(key),), q=True, itt=True, ott=True)

    for channel, keys in keys_modified.items():
        for key in keys:
            cmds.keyTangent(channel, index=(key ,), lock=False)
            if keys_modified[channel][key]['tangent_types'][0] != keys_selected[channel][key]['tangent_types'][0]:
                cmds.keyTangent(channel, index=(key ,), itt=keys_selected[channel][key]['tangent_types'][0])
                cmds.keyTangent(channel, index=(key ,), inAngle=keys_selected[channel][key]['tangent_angles'][0])
                cmds.keyTangent(channel, index=(key ,), inWeight=keys_selected[channel][key]['tangent_weights'][0])
                cmds.keyTangent(channel, index=(key ,), inWeight=value)
            if keys_modified[channel][key]['tangent_types'][-1] != keys_selected[channel][key]['tangent_types'][-1]:
                cmds.keyTangent(channel, index=(key ,), ott=keys_selected[channel][key]['tangent_types'][-1])
                cmds.keyTangent(channel, index=(key ,), outAngle=keys_selected[channel][key]['tangent_angles'][-1])
                cmds.keyTangent(channel, index=(key ,), outWeight=keys_selected[channel][key]['tangent_weights'][-1])
                cmds.keyTangent(channel, index=(key ,), outWeight=value)
            cmds.keyTangent(channel, index=(key ,), lock=keys_selected[channel][key]['lock'][0])


# ---------------------------------------------------------------------------- #
# Angle current tangent handle to a value

def map_from_to(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)
    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def get_anim_data():
    global SELECTED_KEYS
    keys_selected = Vividict()

    current_channels = cmds.keyframe(q=True, selected=True, name=True) or []
    if not current_channels: print "Only works on selected keys/curves"; return
    for channel in current_channels:
        keys = cmds.keyframe(channel, q=True, selected=True, indexValue=True)
        for key in keys:
            key = float(key)
            tangent_types = cmds.keyTangent(channel, index=(key,), q=True, inTangentType=True, outTangentType=True)
            keys_selected[channel][key]['tangent_types']    = tangent_types
            keys_selected[channel][key]['tangent_angles']   = cmds.keyTangent(channel, index=(key,), q=True, inAngle=True, outAngle=True)
            keys_selected[channel][key]['tangent_weights']  = cmds.keyTangent(channel, index=(key,), q=True, inWeight=True, outWeight=True)
            keys_selected[channel][key]['tangent_selected'] = [0, 0]
            keys_selected[channel][key]['lock']             = cmds.keyTangent(channel, index=(key,), q=True, lock=True)

            current_value = cmds.keyframe(channel, index=(key,), q=True, valueChange=True)
            next_value = cmds.keyframe(channel, index=(key+1,), q=True, valueChange=True) # TODO - Will break at the end. No more last key.
            if next_value >= current_value:
                keys_selected[channel][key]['tangent_direction_up'] = True
            else:
                keys_selected[channel][key]['tangent_direction_up'] = False
            
            in_tangent_index  = IN_TANGENT_TYPES.index(tangent_types[0])
            out_tangent_index = OUT_TANGENT_TYPES.index(tangent_types[-1])
            cmds.keyTangent( channel
                           , index=(key,)
                           , inTangentType=IN_TANGENT_TYPES[in_tangent_index-1]
                           , outTangentType=OUT_TANGENT_TYPES[out_tangent_index-1]
                           )
            modified_tangent_types = cmds.keyTangent(channel, index=(key,), q=True, inTangentType=True, outTangentType=True)
            
            if modified_tangent_types[0] != keys_selected[channel][key]['tangent_types'][0]:
                keys_selected[channel][key]['tangent_selected'][0] = 1
            if modified_tangent_types[-1] != keys_selected[channel][key]['tangent_types'][-1]:
                keys_selected[channel][key]['tangent_selected'][-1] = 1

            cmds.keyTangent(channel, index=(key,), lock=False)
            if keys_selected[channel][key]['tangent_selected'][0]:
                cmds.keyTangent(channel, index=(key,), inTangentType=keys_selected[channel][key]['tangent_types'][0])
                cmds.keyTangent(channel, index=(key,), inWeight=keys_selected[channel][key]['tangent_weights'][0])
                cmds.keyTangent(channel, index=(key,), inAngle=keys_selected[channel][key]['tangent_angles'][0])
            if keys_selected[channel][key]['tangent_selected'][-1]:
                cmds.keyTangent(channel, index=(key,), outTangentType=keys_selected[channel][key]['tangent_types'][-1])
                cmds.keyTangent(channel, index=(key,), outWeight=keys_selected[channel][key]['tangent_weights'][-1])
                cmds.keyTangent(channel, index=(key,), outAngle=keys_selected[channel][key]['tangent_angles'][-1])
            cmds.keyTangent(channel, index=(key,), lock=keys_selected[channel][key]['lock'][0])

    SELECTED_KEYS = keys_selected

def angle_tangent_to_value(value):
    for channel, keys in keys_selected.items():
        for key in keys:
            in_angle, out_angle = keys_selected[channel][key]['tangent_angles']
            if keys_selected[channel][float(key)]['tangent_direction_up'] == True:
                new_value = map_from_to(value, 0.0, 90.0, in_angle, 90.0)
            elif keys_selected[channel][float(key)]['tangent_direction_up'] == False:
                new_value = map_from_to(value, 0.0, 90.0, in_angle, -90.0)
            cmds.keyTangent(channel, index=(key,), inAngle=new_value, outAngle=new_value)

'''
get_anim_data()
cmds.window()
cmds.columnLayout(adjustableColumn=True)
cmds.floatSlider(min=-90, max=90, value=0, step=1, width=500, dragCommand=angle_tangent_to_value)
cmds.showWindow()
'''


# ---------------------------------------------------------------------------- #
# Angle current tangent handle to a value

def toggle_channels(channels):
    '''
    You could pass a list such as ['tx', 'ty', 'tz']
    Or a boolean of False to deselect the channels
    '''
    if channels == False:
        cmds.channelBox(CHANNELBOX, edit=True, select=False, update=True)
        return
    if not isinstance(channels, list): channels = [channels]
    valid_channels = [c for c in channels if c in VALID_ATTRS]
    nodes = cmds.ls(selection=True)
    channels_to_select = ['{}.{}'.format(n, c) for c in valid_channels for n in nodes]
    cmds.channelBox(CHANNELBOX, edit=True, select=channels_to_select, update=True)







# EoF