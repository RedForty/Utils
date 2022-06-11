# =========================================================================== #
# Isolate select in the GE and viewport
from maya import cmds, mel

def run():
    currentPanel  = cmds.getPanel(withFocus=True)
    model_panels  = cmds.getPanel(type='modelPanel')
    graph_editors = cmds.getPanel(scriptType='graphEditor')
    
    if currentPanel in model_panels:
        if cmds.ls(sl=1) == []:
            # Nothing selected? Un-isolate
            cmds.isolateSelect(currentPanel, state=False)
            cmds.isolateSelect(currentPanel, update=True)
        else:
            # Else isolate
            cmds.isolateSelect(currentPanel, state=True)
            cmds.isolateSelect(currentPanel, addSelected=True)
            cmds.isolateSelect(currentPanel, update=True)

    elif currentPanel in graph_editors:
        # Capture GE selection
        selection_data = {}
        selected_curve_names = cmds.keyframe(q=True, selected=True, name=True) or []
        for curve_name in selected_curve_names:
            keys = cmds.keyframe(curve_name, q=True, selected=True, indexValue=True)
            selection_data[curve_name] = [int(x) for x in keys]
        
        # GE isolating acts differently. There is a job number for it so just toggle it.
        gUnisolateJobNum = mel.eval('global int $gUnisolateJobNum; $temp=$gUnisolateJobNum;')
        if int(gUnisolateJobNum) > 0:
            mel.eval('isolateAnimCurve false graphEditor1FromOutliner graphEditor1GraphEd;')
        else:
            mel.eval('isolateAnimCurve true graphEditor1FromOutliner graphEditor1GraphEd;')
            
        # Restore selection
        cmds.selectKey(clear=True)
        for curve, keys in selection_data.items():
            for k in keys:
                cmds.selectKey(curve, add=True, index=(k,))

# EoF