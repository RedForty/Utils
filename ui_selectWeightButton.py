# Adds a button to the animLayer tab to select layer weight curves
# ============================================================================ #
'''
- How to install -
Place in your ~/maya/scripts folder

- How to use -
Run this PYTHON code in your userSetup.py file or shelf button:

from maya import cmds
import ui_selectWeightButton
cmds.evalDeferred('ui_selectWeightButton.createSelectWeightButton()')
'''
# ============================================================================ #
# Imports -------------------------------------------------------------------- #

from maya import cmds, mel

# Really hoping this doesn't change between maya versions. Works in 2018.
PARENT_LAYOUT = 'ChannelBoxLayerEditor|MainChannelsLayersLayout|ChannelsLayersPaneLayout|LayerEditorForm|DisplayLayerUITabLayout|AnimLayerTab|formLayout3'
ANIMLAYER_TAB = 'AnimLayerTab'
SELECT_ICON   = 'unstackedCurves.png' # Maya built-in

SELECT_BUTTON = 'AnimLayerTabSelectWeightsButton'
WEIGHT_BUTTON = 'AnimLayerTabWeightButton'
ANIMLAYER_TAB_EDITOR  = 'AnimLayerTabanimLayerEditor'
GRAPH_EDITOR_LIST     = 'graphEditorList'
GRAPH_EDITOR_OUTLINER = 'graphEditor1FromOutliner'

# Private -------------------------------------------------------------------- #

def _getSelectedAnimLayers():
    '''
    Return the names of the layers which are selected
    '''
    # Whoa, turns out there is a maya built-in!
    layers = mel.eval('getSelectedAnimLayer {}'.format(ANIMLAYER_TAB))
    if 'BaseAnimation' in layers: layers.remove('BaseAnimation') # Ignore Base only
    if layers:
        return layers

    layers = cmds.treeView(ANIMLAYER_TAB_EDITOR, q=True, children=True) or []
    if 'BaseAnimation' in layers: layers.remove('BaseAnimation')
    return layers

def _select_layers(layers):
    if layers:
        selected_layers = mel.eval('getSelectedAnimLayer {}'.format(ANIMLAYER_TAB))
        if 'BaseAnimation' in selected_layers:
            cmds.animLayer('BaseAnimation', e=True, selected=False)
        all_layers = cmds.treeView(ANIMLAYER_TAB_EDITOR, q=True, children=True) or []
        if 'BaseAnimation' in all_layers: all_layers.remove('BaseAnimation')
        if all_layers:
            for layer in all_layers:
                if layer not in layers:
                    cmds.animLayer(layer, e=True, selected=False)
        for layer in layers:
            cmds.animLayer(layer, e=True, selected=True)

def _update_GE_Outliner(*args):
    outliner_contents = cmds.selectionConnection('graphEditorList', q=True, object=True) or []
    for obj in outliner_contents:
        cmds.selectionConnection('graphEditor1FromOutliner', e=True, object=obj)

def _selectWeightCurves(*args, **kwargs):

    curves_to_select = []
    layers = []

    selected_layers = _getSelectedAnimLayers()
    for layer in selected_layers:
        if cmds.nodeType(layer) == 'animLayer':
            try:
                # plug = cmds.listConnections(layer + '.weight', plugs=True)[0]
                curve = cmds.listConnections(layer + '.weight')[0] or []
                curves_to_select.append(curve)
                layers.append(layer)
            except:
                # print("{} has no weight curve".format(layer))
                continue

    cmds.select(clear=True)
    _select_layers(layers)

    cmds.evalDeferred("cmds.select({})".format(curves_to_select))
    cmds.evalDeferred("ui_selectWeightButton._update_GE_Outliner()")


# Public --------------------------------------------------------------------- #

def createSelectWeightButton():
    global SELECT_BUTTON
    if not cmds.iconTextButton(SELECT_BUTTON, q=True, exists=True):
        SELECT_BUTTON = cmds.iconTextButton( SELECT_BUTTON
                                           , height=24
                                           , width=24
                                           , parent=PARENT_LAYOUT
                                           , image=SELECT_ICON
                                           , command=_selectWeightCurves)
    # Move it to bottom right of the parent formLayout
    cmds.formLayout(PARENT_LAYOUT, e=True, attachForm=(SELECT_BUTTON, "right", 2))
    cmds.formLayout(PARENT_LAYOUT, e=True, attachNone=(SELECT_BUTTON, "left"))
    cmds.formLayout(PARENT_LAYOUT, e=True, attachNone=(SELECT_BUTTON, "top"))
    cmds.formLayout(PARENT_LAYOUT, e=True, attachForm=(SELECT_BUTTON, "bottom", 2))
    # Move the key button
    cmds.formLayout(PARENT_LAYOUT, e=True, attachControl=(PARENT_LAYOUT + "|" + WEIGHT_BUTTON, "right", 2, SELECT_BUTTON))

def deleteSelectWeightButton():        
    # Delete it
    global SELECT_BUTTON
    if not cmds.iconTextButton(SELECT_BUTTON, q=True, exists=True):
        return
    
    cmds.deleteUI(SELECT_BUTTON)
    
    # Move the key button back to its original position
    cmds.formLayout(PARENT_LAYOUT, e=True, attachForm=(PARENT_LAYOUT + "|" + WEIGHT_BUTTON, "right", 2))
    
    SELECT_BUTTON = None


# Developer section ---------------------------------------------------------- #
if __name__ == '__main__':
    createSelectWeightButton()
    # deleteSelectWeightButton()
