from maya import cmds, mel
from functools import wraps

# Decorators ========================================================= #

def viewport_off(func):
    """
    Decorator - turn off Maya display while func is running. if func fails, the error will be raised after.
    """
    @wraps(func)
    def wrap( *args, **kwargs ):

        parallel = False
        if 'parallel' in cmds.evaluationManager(q=True, mode=True):
            cmds.evaluationManager(mode='off')
            parallel = True
            print "Turning off Parallel evaluation..."
        # Turn $gMainPane Off:
        mel.eval("paneLayout -e -manage false $gMainPane")
        cmds.refresh(suspend=True)
        # Hide the timeslider
        mel.eval("setTimeSliderVisible 0;")


        # Decorator will try/except running the function.
        # But it will always turn on the viewport at the end.
        # In case the function failed, it will prevent leaving maya viewport off.
        try:
            return func( *args, **kwargs )
        except Exception:
            raise # will raise original error
        finally:
            cmds.refresh(suspend=False)
            mel.eval("setTimeSliderVisible 1;")
            if parallel:
                cmds.evaluationManager(mode='parallel')
                print "Turning on Parallel evaluation..."
            mel.eval("paneLayout -e -manage true $gMainPane")
            cmds.refresh()

    return wrap


@viewport_off
def run(nodes_to_bake, start_frame=None, end_frame=None, sample = 1):
    '''
    nodes: list
    start_frame: int
    end_frame: int
    '''
    if not start_frame:
        start_frame = cmds.playbackOptions(q=True, ast=True)
    if not end_frame:
        end_frame = cmds.playbackOptions(q=True, aet=True)
    try:
        cmds.bakeResults(
            nodes_to_bake,
            simulation = True,
            time = (start_frame, end_frame),
            sampleBy = sample,
            oversamplingRate = 1,
            disableImplicitControl = True,
            preserveOutsideKeys = True,
            at = ("tx", "ty", "tz", "rx", "ry", "rz", "blendParent1"),
            sparseAnimCurveBake = False,
            removeBakedAttributeFromLayer = False,
            removeBakedAnimFromLayer = False,
            bakeOnOverrideLayer = False,
            minimizeRotation = True,
            controlPoints = False,
            shape = True
            )
        return True
    except:
        return False


# Developer section ================================================== #
if __name__ == '__main__':
    selection = cmds.ls(sl=1)
    if selection:
        start_frame = cmds.playbackOptions(q=True, ast=True)
        end_frame = cmds.playbackOptions(q=True, aet=True)
        run(selection, start_frame, end_frame)
        try:
            for sel in selection:
                cmds.delete(sel, constraints=True)
        except:
            pass
