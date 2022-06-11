# For matrix utilities

from maya import cmds, mel
import maya.OpenMaya as om
import maya.api.OpenMaya as mapi
import math

# setMatrixKeyframe uses this
from klugTools import animLayer_utils as au

# GLOBALS
gMainProgressBar = mel.eval('string $tmpString = $gMainProgressBar');
TIMELINE = mel.eval('string $tmpString=$gPlayBackSlider')


# Helper dict will create a new key if it doesn't already exist
class Vividict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


class ProgressBar():
    def __init__ (self, message, amount, title="Progress..."):    
        self.message          = message
        self.amount           = amount
        self.title            = title
        self.progressbar      = self.makeProgressBarWindow()
        self.increment()

    def makeProgressBarWindow(self):    
        self.window = cmds.progressWindow(title=self.title, status=self.message, maxValue=self.amount, isInterruptable=True)

    def kill(self):
        cmds.progressWindow(endProgress=1)

    def increment(self):
        cmds.progressWindow(self.window, edit=True, step=1)

    def checkAbort(self):
        if cmds.progressWindow(self.window, query=True, isCancelled=True):
            return True
        else:
            return False

def constructMatrix(translate=om.MVector(0,0,0), rotate=om.MEulerRotation(0,0,0,0), scale=om.MVector(1,1,1)):
    '''
    Create API matrix from translate, rotate and scale
    '''
    if isinstance(translate, (list, tuple)):
        translate = om.MVector(translate[0], translate[1], translate[2])
    if isinstance(rotate, (list, tuple)):
        rotate = om.MEulerRotation(rotate[0], rotate[1], rotate[2])
    if isinstance(scale, (list, tuple)):
        scale = om.MVector(scale[0], scale[1], scale[2])
    
    t_matrix = om.MTransformationMatrix()
    r_matrix = om.MTransformationMatrix(rotate.asMatrix())
    s_matrix = om.MTransformationMatrix()
    
    # Translate
    t_matrix.setTranslation( translate, om.MSpace.kTransform ) 
      
    # Scale
    s = [scale.x,scale.y,scale.z]
    scaleDoubleArray = om.MScriptUtil()
    scaleDoubleArray.createFromList( s, 3 )
    scaleDoubleArrayPtr = scaleDoubleArray.asDoublePtr() 
    s_matrix.setScale(scaleDoubleArrayPtr, om.MSpace.kTransform)
       
    return s_matrix.asMatrix() * r_matrix.asMatrix() * t_matrix.asMatrix()


def APIMatrix(mlist): # where mlist is a list of floats
    matrix = om.MMatrix()
    om.MScriptUtil.createMatrixFromList(mlist, matrix)
    return matrix


def getMObject(nodeName):
    list = om.MSelectionList()
    meshes = cmds.ls(nodeName)
    obj = om.MObject()  
     
    if len(meshes) == 1:
        list.add  ( nodeName )  
        list.getDependNode ( 0, obj )    
        return obj


def getTranslate(mMatrix): 
    if isinstance(mMatrix, list):
        mMatrix = APIMatrix(mMatrix)    
    tMatrix = om.MTransformationMatrix (mMatrix)
    return tMatrix.getTranslation(om.MSpace.kTransform) 


def getRotate(mMatrix, rot_order=0, asDegrees=False, asRadians=False):
    
    if isinstance(mMatrix, list):
        mMatrix = APIMatrix(mMatrix)

    # Convert to MTransformationMatrix to extract rotations:
    mTransformMtx = om.MTransformationMatrix(mMatrix)
    
    # Get an MEulerRotation object
    eulerRot = mTransformMtx.eulerRotation() # MEulerRotation
    # Update rotate order to match original object, since the orig MMatrix has
    # no knoweldge of it:
    eulerRot.reorderIt(rot_order)
    
    if asDegrees:
        return [math.degrees(x) for x in (eulerRot.x, eulerRot.y, eulerRot.z)]
    elif asRadians:
        return [eulerRot.x, eulerRot.y, eulerRot.z]
    else:
        return eulerRot


def inverseMatrix(mMatrix): 
    if isinstance(mMatrix, list):
        mMatrix = APIMatrix(mMatrix)
    
    iMatrix = om.MTransformationMatrix(mMatrix)
    return iMatrix.asMatrixInverse() 


def getParentInverseMatrixAtTime(node, time = None): 
    if time:
        return cmds.getAttr(node + '.parentInverseMatrix', time=time)
    else:
        return cmds.getAttr(node + '.parentInverseMatrix')


def listMatrix(matrix):
    mList = []
    for i in range(4):
        for j in range(4):
            mList.append(matrix(i,j))    
    return mList


def getMatrixAtTime(node, time = None):
    if not time:
        time = cmds.currentTime(q=True)
    # Do Translate
    matrix       = cmds.getAttr(node + '.parentMatrix', time=time) # NOT the world!
    rotate_pivot = cmds.getAttr(node + '.rotatePivot' , time=time)[0] # A tuple in a list
    translate    = cmds.getAttr(node + '.translate'   , time=time)[0] # A tuple in a list
    rp_translate = cmds.getAttr(node + '.rotatePivotTranslate', time=time)[0] # A tuple in a list
    
    # We're doing it this way because worldmatrix doesn't take into account frozen trasnforms
    # or moved pivots.
    
    # Doing the math manually like this is faster than using API calls (like mvector and mmatrix)
    # Could do the math manually: http://discourse.techart.online/t/maya-get-world-space-rotatepivot-at-a-specified-time/4559/2
    offset_pivot = [x + y + z for x,y,z in zip(rotate_pivot, rp_translate, translate)]
    offset = [matrix[0]*offset_pivot[0] + matrix[4]*offset_pivot[1] + matrix[8]*offset_pivot[2]  + matrix[12],
              matrix[1]*offset_pivot[0] + matrix[5]*offset_pivot[1] + matrix[9]*offset_pivot[2]  + matrix[13],
              matrix[2]*offset_pivot[0] + matrix[6]*offset_pivot[1] + matrix[10]*offset_pivot[2] + matrix[14]]

    # Rotation
    world_matrix = cmds.getAttr(node + '.worldMatrix', time=time)
    rot_order = cmds.getAttr(node + '.rotateOrder', time=time)
    angles = getRotate(APIMatrix(world_matrix), rot_order)
    
    scale = getScale(APIMatrix(world_matrix))

    return constructMatrix(offset, angles, scale)


def getScale( matrix ): 
    '''
    Returns the scale component of a given matrix

    :param MMatrix matrix: MMatrix from which to extract the scale component
    :returns: MVector object containg the scale component.
    :rtype: MVector
    '''  
    matrixT = om.MTransformationMatrix ( matrix )
    
    util = om.MScriptUtil()
    util.createFromDouble(0.0, 0.0, 0.0)
    ptr = util.asDoublePtr()
    
    matrixT.getScale( ptr, om.MSpace.kTransform ) 
    
    outVec = om.MVector() 

    outVec.x = util.getDoubleArrayItem(ptr, 0)
    outVec.y = util.getDoubleArrayItem(ptr, 1)
    outVec.z = util.getDoubleArrayItem(ptr, 2) 
    
    return outVec


def printMatrix(matrix, comment='', format='trs'): 
    '''
    Prints the components (TRS) of a matrix the script editor output                                               

    :param MMatrix matrix: Matrix to be printed                                                                   
    :param str comment: comment or headline of the printed matrix, ie 'myWorldMatrix'                             
    :rtype: str
    ''' 

    t = getTranslate ( matrix )
    r = getRotate ( matrix )
    s = getScale ( matrix )
    
    print('printMatrix: ', comment)
    
    if format == 'trs': 
        print('t ', (round ( t.x, 3 )), '\t\t',  (round ( t.y, 3 )), '\t\t', (round ( t.z, 3 )))
        print('r ', (round ( math.degrees( r.x ), 2 )), '\t\t', (round ( math.degrees( r.y ), 2 )), '\t\t', (round ( math.degrees( r.z ), 2 )) )
        print('s ', (round ( s.x, 3 )), '\t\t\t', (round ( s.y, 3 )), '\t\t\t', (round ( s.z, 3 )) )
    if format == 'matrix':
        print(round ( matrix(0,0), 3 ),'\t', round ( matrix(0,1), 3 ),'\t', round ( matrix(0,2), 3 ),'\t', round ( matrix(0,3), 3 ))
        print(round ( matrix(1,0), 3 ),'\t', round ( matrix(1,1), 3 ),'\t', round ( matrix(1,2), 3 ),'\t', round ( matrix(1,3), 3 ))
        print(round ( matrix(2,0), 3 ),'\t', round ( matrix(2,1), 3 ),'\t', round ( matrix(2,2), 3 ),'\t', round ( matrix(2,3), 3 ))
        print(round ( matrix(3,0), 3 ),'\t', round ( matrix(3,1), 3 ),'\t', round ( matrix(3,2), 3 ),'\t', round ( matrix(3,3), 3 ))


def setMatrixKeyframe(node, matrix, time = None, writeToAnimLayers=True):
    if isinstance(matrix, list):
        matrix = APIMatrix(matrix)

    if not time:
        time = cmds.currentTime(q=True)
    
    rot_order = cmds.getAttr(node + '.rotateOrder')
    
    translate = getTranslate(matrix)
    rotate    = getRotate   (matrix, rot_order)
    scale     = getScale    (matrix)
    
    transform_data = Vividict()
    transform_data['translateX'] = translate.x
    transform_data['translateY'] = translate.y
    transform_data['translateZ'] = translate.z
    
    transform_data['rotateX'] = math.degrees(rotate.x)
    transform_data['rotateY'] = math.degrees(rotate.y)
    transform_data['rotateZ'] = math.degrees(rotate.z)
    
    transform_data['scaleX'] = scale.x
    transform_data['scaleY'] = scale.y
    transform_data['scaleZ'] = scale.z
    
    animLayerData = Vividict()
    if writeToAnimLayers:
        # Even if we want to, we must check to see if we can.
        root_layer = cmds.animLayer(query=True, root=True)
        if root_layer:
            # Each attribute could be assigned to its own layer. Complexity, yay!
            animLayerData = au.getAnimLayerAuthoringDict(node)
    
    for attr, layer in transform_data.items():
        if animLayerData:
            cmds.setKeyframe(node, at=attr, value=transform_data[attr], time=time, animLayer=animLayerData[attr])
        else:
            # Ignore animLayers and either write to BaseAnimation or None.
            cmds.setKeyframe(node, at=attr, value=transform_data[attr], time=time)

def get_timeline_selection():
    if cmds.timeControl(TIMELINE, q=True, rangeVisible=True):
        return cmds.timeControl(TIMELINE, q=True, rangeArray=True)
    else: 
        return []

def get_timeline_range():
    start_frame = cmds.playbackOptions(q=True, minTime=True)
    end_frame = cmds.playbackOptions(q=True, maxTime=True)
    return [start_frame, end_frame]

def get_work_time(node=None):
    
    keyframes = []
    
    timeline_selection = get_timeline_selection() # Selection takes priority
    if timeline_selection:
        timeline_selection = [x * 1.0 for x in range(int(min(timeline_selection)), int(max(timeline_selection))+1)]
    
    if node:
        keyframes = cmds.keyframe(node, q=True) or []
        keyframes = list(set(keyframes)) # All the keys

    time_range = get_timeline_range()
    start      = min(time_range + keyframes)
    end        = max(time_range + keyframes)
    keyframes = [x * 1.0 for x in range(int(start), int(end)+1)]
        
    if timeline_selection:
        new_keyframes = []
        for key in keyframes:
            if key in timeline_selection:
                new_keyframes.append(key)
        keyframes = new_keyframes # Crop to selection    
    
    return keyframes


def get_offset_matrix(target, node):
    node_m    = getMatrixAtTime(node)
    target_m  = getMatrixAtTime(target)

    offset_cache_m = target_m * inverseMatrix(node_m) # The cached position
    
    return offset_cache_m

if __name__ == "__main__":
    # cmds.getAttr('pCube7.tmrp') # maya wtf
    
    # import imp
    # imp.reload(au)

    node   = 'pCube1'
    target = 'locator1'
    loc    = 'pSphere1'
    
    offset_cache_m = get_offset_matrix(target, node)
    
    amount = get_work_time()
    progressBar = ProgressBar('Baking keys...', len(amount))

    for time in amount:
        # Progress bar
        if progressBar.checkAbort():
            break
        
        # cmds.currentTime(key) # NO! We do NOT need to march the timeline!
        node_m = getMatrixAtTime(node, time)
        offset_loc_m = APIMatrix(getParentInverseMatrixAtTime(loc, time)) # To cancel out the locator's parent anim
        
        # The offset
        # Into the space of the node anim
        # Into the space of the cancelled-out-locator-parent anim
        offset_m = offset_cache_m * node_m * offset_loc_m  # <---- The order MATTERS here
        setMatrixKeyframe(loc, offset_m, time)
        
        # This is the brute force authoring of the transformation. Which solves anim layers, too.
        # Trying to avoid xform because xform cannot do time. :(
        # mList = listMatrix(offset_m)
        # cmds.xform(loc, ws=True, a=True, m=mList)
        
        progressBar.increment()

    progressBar.kill()
    
    cmds.dgdirty(a=True) # Refresh scene at end

