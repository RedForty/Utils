# ============================================================================ #
# Imports ==================================================================== #

from maya import cmds, mel
from functools import wraps


# ============================================================================ #
# Globals ==================================================================== #

in_tangent_types  = [ "spline"
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

out_tangent_types = [ "spline"
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


# ============================================================================ #
# Wrapper ==================================================================== #

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


# ============================================================================ #
# Data handlers ============================================================== #

class Vividict(dict):
    """A dictionary that adds a key if it does not exist."""
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


# ============================================================================ #
# Weight current tangent handle to 0.0 ======================================= #

@undo
def to_value(value):
    current_channels = cmds.keyframe(q=True, selected=True, name=True)
    if not current_channels: print "Only works on selected keys/curves"; return
    keys_selected = Vividict()
    for channel in current_channels:
        keys = cmds.keyframe(channel, q=True, selected=True, indexValue=True)
        for key in keys:
            tangent_type = cmds.keyTangent(channel, index=(float(key),), q=True, itt=True, ott=True)
            keys_selected[channel][float(key)]['tangent_types'] = tangent_type
            keys_selected[channel][float(key)]['tangent_angles'] = cmds.keyTangent(channel, index=(float(key),), q=True, inAngle=True, outAngle=True)
            keys_selected[channel][float(key)]['tangent_weights'] = cmds.keyTangent(channel, index=(float(key),), q=True, inWeight=True, outWeight=True)
            keys_selected[channel][float(key)]['lock'] = cmds.keyTangent(channel, index=(float(key),), q=True, lock=True)
    
            cmds.keyTangent(itt=in_tangent_types[in_tangent_types.index(tangent_type[0])-1], ott=out_tangent_types[out_tangent_types.index(tangent_type[-1])-1])
    
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

