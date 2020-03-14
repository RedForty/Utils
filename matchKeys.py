from maya import cmds
import maya.api.OpenMaya as mapi

def matchKeys(pivot=None):
    # Feed it a string
    # 'first' to pivot first key 
    # 'last' to pivot from last
    # hur dur
    if not pivot:
        pivot = 'first'
    if not pivot == 'first':
        if not pivot == 'last':
            mapi.MGlobal.displayError(\
                'Check the spelling of your matchKeys call. '\
                'It should either be calling "first" or "last"')
            return None

    selectedAttrs = cmds.keyframe(q=True, sl=True, shape=True, name=True)
    if not selectedAttrs:
        shownCurves = cmds.animCurveEditor('graphEditor1GraphEd', q=True, cs=True)
        selectedAttrs = shownCurves

    for attr in selectedAttrs:
        firstKey = 0
        lastKey = cmds.keyframe(attr, q=True, keyframeCount=True) -1 # count starts at 0

        if pivot == 'first':
            pivotKey = 0 # indexth key, not frame
            targetKey = lastKey
        elif pivot == 'last':
            pivotKey = lastKey
            targetKey = firstKey

        keyValue = cmds.keyframe(attr, q=True, index=(pivotKey, ), valueChange=True)

        itt = cmds.keyTangent(attr, index=(pivotKey, ), q=True, inTangentType=True)
        ott = cmds.keyTangent(attr, index=(pivotKey, ), q=True, outTangentType=True)
        ia = cmds.keyTangent(attr, index=(pivotKey, ), q=True, inAngle=True)    
        oa = cmds.keyTangent(attr, index=(pivotKey, ), q=True, outAngle=True)
        
        cmds.keyframe(attr, edit=True, index=(targetKey, ), valueChange=keyValue[0])

        isWeighted = cmds.keyTangent(attr, index=(pivotKey, ), q=True, weightedTangents=True)
        if isWeighted:
            iw = cmds.keyTangent(attr, index=(pivotKey, ), q=True, inWeight=True)
            ow = cmds.keyTangent(attr, index=(pivotKey, ), q=True, outWeight=True)
            cmds.keyTangent(attr, index=(targetKey, ), edit=True, itt=itt[0], ott=ott[0], ia=ia[0], oa=oa[0], iw=iw[0], ow=ow[0])
        else:
            cmds.keyTangent(attr, index=(targetKey, ), edit=True, itt=itt[0], ott=ott[0], ia=ia[0], oa=oa[0])

