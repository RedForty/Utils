# ============================================================================ #
# My collection of graph editor tools ======================================== #

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
CHANNELBOX = mel.eval('$cbtemp=$gChannelBoxName')
BACKGROUND_COLOR = (0x32A14B)
FONT_COLOR = 'white'
FONT = 'Roboto'

START_FRAME = cmds.playbackOptions(q=True, minTime=True)
END_FRAME = cmds.playbackOptions(q=True, maxTime=True)
NON_CYCLING_CURVES = []
TOLERANCE = 0.0000000001

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
# Thank you Freya Holmer | Neat Corp
# https://youtu.be/NzjF1pdlK7Y

def lerp(a, b, t):
    return ((1.0 - t) * a + b * t)

def inv_lerp(a, b, v):
    return ((v - a) / (b - a))

def remap(iMin, iMax, oMin, oMax, v):
    t = inv_lerp(iMin, iMax, v)
    return lerp(oMin, oMax, t)


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

# @restore_ge_selection # Broken in 2018
@undo        
def do_ge_isolate():
    # GE isolating acts differently. There is a job number for it so just toggle it.
    gUnisolateJobNum = mel.eval('global int $gUnisolateJobNum; $isotemp=$gUnisolateJobNum;')
    # gUnisolateJobNum = mel.eval('$isotemp=$gUnisolateJobNum;')
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
    if not current_channels: print("Only works on selected keys/curves"); return
    keys_selected = Vividict()
    for channel in current_channels:
        keys = cmds.keyframe(channel, q=True, selected=True, indexValue=True)
        for key in keys:
            tangent_type = cmds.keyTangent(channel, index=(float(key),), q=True, itt=True, ott=True)
            keys_selected[channel][float(key)]['tangent_types']   = tangent_type
            keys_selected[channel][float(key)]['tangent_angles']  = cmds.keyTangent(channel, index=(float(key),), q=True, inAngle=True, outAngle=True)
            keys_selected[channel][float(key)]['tangent_weights'] = cmds.keyTangent(channel, index=(float(key),), q=True, inWeight=True, outWeight=True)
            keys_selected[channel][float(key)]['lock']            = cmds.keyTangent(channel, index=(float(key),), q=True, lock=True)
    
            cmds.keyTangent(channel, index=(float(key),), itt=IN_TANGENT_TYPES[IN_TANGENT_TYPES.index(tangent_type[0])-1], ott=OUT_TANGENT_TYPES[OUT_TANGENT_TYPES.index(tangent_type[-1])-1]) # This breaks in 2020
            # cmds.keyTangent(itt=IN_TANGENT_TYPES[IN_TANGENT_TYPES.index(tangent_type[0])-1], ott=OUT_TANGENT_TYPES[OUT_TANGENT_TYPES.index(tangent_type[-1])-1])
    
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
    if not current_channels: print("Only works on selected keys/curves"); return
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
# Toggle selected channels in the GE

def toggle_channels(channels):
    '''
    You could pass a list such as ['tx', 'ty', 'tz']
    Or a boolean of False to deselect the channels
    '''
    if channels == False:
        cmds.channelBox(CHANNELBOX, edit=True, select=False, update=True)
        mel.eval('syncChannelBoxFcurveEd') # For 2018
        return
    if not isinstance(channels, list): channels = [channels]
    valid_channels = [c for c in channels if c in VALID_ATTRS]
    nodes = cmds.ls(selection=True)
    channels_to_select = ['{}.{}'.format(n, c) for c in valid_channels for n in nodes]
    cmds.channelBox(CHANNELBOX, edit=True, select=channels_to_select, update=True)
    mel.eval('syncChannelBoxFcurveEd') # For 2018




# --------------------------------------------------------------------------- #
# Crop selected curves to frame range, cutting/pasting from outside to inside
def crop_cycle():
    global NON_CYCLING_CURVES
    NON_CYCLING_CURVES  = []
    global START_FRAME
    START_FRAME = cmds.playbackOptions(q=True, minTime=True)
    global END_FRAME
    END_FRAME = cmds.playbackOptions(q=True, maxTime=True)
    
    ctrls = cmds.ls(sl=True)
    if not ctrls:
        print("No controls selected!")
        return

    curves_to_process = []
    for ctrl in ctrls:
        curves = []
        curves = cmds.keyframe(ctrl, selected=True, q=True, name=True) or []
        curves_to_process.extend(curves)

    if not curves_to_process:
        print("No curves selected!")
        return

    for curve in curves_to_process:
        _normalize_cycle(curve)

    if NON_CYCLING_CURVES:
        cmds.warning("Non cycling curves detected!")
        print(NON_CYCLING_CURVES)
        result = cmds.confirmDialog( title='Warning', message='Select non-cycling controls?', button=['Yes','No'], defaultButton='Yes', cancelButton='No', dismissString='No' )
        if result == 'Yes':
            cmds.select(NON_CYCLING_CURVES)
    else:
        print("Success probably!")

# --------------------------------------------------------------------------- #
# The process that does the work
def _normalize_cycle(curve):
    # prime the pump
    global NON_CYCLING_CURVES

    keys = cmds.keyframe(curve, q=True)
    last_key = keys[-1]
    first_key = keys[0]

    if first_key >= START_FRAME and last_key > END_FRAME:
        # Normalize post-end-frame
        cmds.setKeyframe(curve, time=(END_FRAME,), insert=True)
        
        # Save tangent info
        tangent_data = _save_tangent_data(curve, last_key)
        # Apply tangent info
        cmds.keyTangent(curve, e=True, time=(first_key,), lock=False)
        cmds.keyTangent(curve, e=True, time=(first_key,), ott='fixed')
        cmds.keyTangent(curve, e=True, time=(first_key,), itt='fixed')
        cmds.keyTangent(curve, e=True, time=(first_key,), inAngle=tangent_data[curve, last_key]['in_angle'][0])
        if tangent_data[curve, last_key]['weighted'][0]:
            cmds.keyTangent(curve, e=True, time=(first_key,), inWeight=tangent_data[curve, last_key]['in_weight'][0])
        
        # Save tangent info
        tangent_data = _save_tangent_data(curve, first_key)
        # Apply tangent info
        cmds.keyTangent(curve, e=True, time=(last_key,), lock=False)
        cmds.keyTangent(curve, e=True, time=(last_key,), ott='fixed')
        cmds.keyTangent(curve, e=True, time=(last_key,), itt='fixed')
        cmds.keyTangent(curve, e=True, time=(last_key,), outAngle=tangent_data[curve, first_key]['out_angle'][0])
        if tangent_data[curve, first_key]['weighted'][0]:
            cmds.keyTangent(curve, e=True, time=(last_key,), outWeight=tangent_data[curve, first_key]['out_weight'][0])

        cmds.copyKey(curve, time=(END_FRAME, last_key))
        cmds.pasteKey(curve, time=(START_FRAME,), option="merge")
        cmds.cutKey(curve, time=(last_key, END_FRAME+1))

    elif first_key < START_FRAME and last_key <= END_FRAME:
        # Normalize pre-start-frame
        cmds.copyKey(curve, time=(last_key,))
        cmds.pasteKey(curve, time=(first_key,), option="merge")
        cmds.setKeyframe(curve, time=(START_FRAME,), insert=True)
        cmds.copyKey(curve, time=(first_key, START_FRAME))
        cmds.pasteKey(curve, time=(last_key,), option="merge")
        cmds.cutKey(curve, time=(first_key, START_FRAME-1))

    elif first_key < START_FRAME and last_key > END_FRAME:
        # Assume the cycle is already good and just trim the outside edges
        cmds.setKeyframe(curve, time=(START_FRAME,), insert=True)
        cmds.setKeyframe(curve, time=(END_FRAME,), insert=True)
        cmds.keyTangent(curve, e=True, time=(END_FRAME,), itt="fixed", ott="fixed")
        cmds.keyTangent(curve, e=True, time=(START_FRAME,), itt="fixed", ott="fixed")
        cmds.cutKey(curve, time=(first_key, START_FRAME-1))
        cmds.cutKey(curve, time=(END_FRAME+1, last_key))
    elif first_key == START_FRAME and last_key == END_FRAME:
        # Curve is already the proper length and within the bounds
        pass
    else:
        NON_CYCLING_CURVES.append(curve)
        print("%s not a valid curve." % curve)

    # Then check the curve and add it to the list if it doesn't cycle
    value_start = cmds.keyframe(curve, q=True, time=(START_FRAME,), valueChange=True)
    value_end = cmds.keyframe(curve, q=True, time=(END_FRAME,), valueChange=True)
    
    if abs(value_start[0] - value_end[0]) > TOLERANCE: # Because of floating point numbers
        NON_CYCLING_CURVES.append(curve)

def _save_tangent_data(curve, time):
    weighted = cmds.keyTangent(curve, q=True, time=(time,), weightedTangents=True)
    if weighted:
        out_weight = cmds.keyTangent(curve, q=True, time=(time,), outWeight=True)
        in_weight = cmds.keyTangent(curve, q=True, time=(time,), inWeight=True)
    out_angle = cmds.keyTangent(curve, q=True, time=(time,), outAngle=True)
    in_angle = cmds.keyTangent(curve, q=True, time=(time,), inAngle=True)
    tangent_data = {}
    tangent_data[curve, time] = { "weighted" : weighted
                                , "out_angle" : out_angle
                                , "in_angle" : in_angle
                                , "out_weight" : out_weight
                                , "in_weight" : in_weight
                                }
    return tangent_data

# --------------------------------------------------------------------------- #
# Based on ack_SliceCurves
@undo
def slice_curves():
    sel = cmds.ls(sl=1)
    if not sel: return None

    objects_to_skip = []
    # Does the object have a key on it to begin with?
    for obj in sel:
        shape_keyables = []
        shapes = cmds.listRelatives(obj, shapes=True)
        for shape in shapes:
            # shape = 'ARCT_WelderBot_01_rig:backFoot_01FK_L_CTRLShape1'
            keyCountShape = cmds.keyframe(shape, q=True, kc=True, shape=True)
            found = cmds.listAnimatable(shape) or []
            if found and not keyCountShape:
                shape_keyables.append(shape)

        keyCountCtrl = cmds.keyframe(obj, q=True, kc=True, shape=False)
        if shape_keyables:
            keyCountShape = cmds.keyframe(shape_keyables, q=True, kc=True, shape=True)
            if keyCountCtrl == 0 and keyCountShape > 0: # Keys on the shape node but not on the ctrl
                cmds.setKeyframe(obj, breakdown=False, hierarchy='none', controlPoints=False, shape=False)
                objects_to_skip.append(obj)
            if keyCountCtrl == 0 and keyCountShape == 0:
                cmds.setKeyframe(obj, breakdown=False, hierarchy='none', controlPoints=False, shape=True)
                objects_to_skip.append(obj)
            if keyCountCtrl > 0 and keyCountShape == 0:
                for shape in shape_keyables:
                    cmds.setKeyframe(shape, breakdown=False, hierarchy='none', controlPoints=False, shape=True)
        else:
            keyCountCtrl = cmds.keyframe(obj, q=True, kc=True, shape=False)
            if not keyCountCtrl:
                cmds.setKeyframe(obj, breakdown=False, hierarchy='none', controlPoints=False, shape=False)


    # Get selected curves in GE
    selectedCurves = cmds.keyframe(selected=True, q=True, name=True) or [] # return curves of selected keys
    if selectedCurves:
        cmds.setKeyframe(selectedCurves, insert=True)
        return True

    # Get selection from GE_outliner
    # ge_outliner_selection = mel.eval("string $temp[] = `selectionConnection -q -object graphEditor1FromOutliner`;")
    # if ge_outliner_selection:
    #     cmds.setKeyframe(ge_outliner_selection, insert=True)
    #     return True

    # Get selection from channelbox
    channelbox_selection = []
    cb_attr_main, cb_attr_shapes = _get_selected_channels()
    if cb_attr_main:
        for obj in sel:
            for attr in cb_attr_main:
                if cmds.objExists(obj + "." + attr):
                    channelbox_selection.append(obj + "." + attr)
    if cb_attr_shapes:
        for obj in sel:
            shape_nodes = cmds.listRelatives(obj, shapes=True)
            for shape_node in shape_nodes:
                for attr in cb_attr_shapes:
                    if cmds.objExists(shape_node + "." + attr):
                        channelbox_selection.append(shape_node + "." + attr)

    if channelbox_selection:
        for attr in channelbox_selection:
            if cmds.keyframe(attr, q=True, kc=True):
                cmds.setKeyframe(channelbox_selection, insert=True)
            else:
                cmds.setKeyframe(channelbox_selection)
        return True

    # Ok, maybe no selection. Just insert all the ones we didn't initially do a setkey
    for obj in sel:
        if obj not in objects_to_skip:
            cmds.setKeyframe(obj, insert=True, shape=True)
    '''
    # We need a way of accounting for MMB drag set-key override. Comparing these two values will do it.
    # Refer to Guppy canInsert() for more into
    oldValue = cmds.keyframe(obj + '.tx', query=1, eval=1)
    # # GetAttr returns a single value if only one.  Otherwise, a list of
    # # tuples ex: [(0, 0, 0)]
    newValue = cmds.getAttr(obj + '.tx')
    '''

def _get_selected_channels():

    attrs_main = cmds.channelBox(CHANNELBOX, q=True, sma=True) or []
    attrs_shape = cmds.channelBox(CHANNELBOX, q=True, ssa=True) or []
    return attrs_main, attrs_shape



# EoF
