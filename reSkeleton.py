import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.cmds as cmds
import maya.mel as mel
from functools import partial


# Private Methods ------------------------------------------------------------ #
def _getNextParentInList( infNames, joint=""):
    nextJoint = joint
    while (True):
        parent = cmds.listRelatives(nextJoint, parent=True)
        if not parent:
            nextJoint = 'origin'
            break
        nextJoint = parent[0]
        if cmds.nodeType(parent) == 'joint':
            if parent[0] in infNames:
                break
    return nextJoint

def _getGenerationInList( infNames, joint = ""):
    nextJoint = joint
    gen = 0
    while (True):
        parent = cmds.listRelatives(nextJoint, parent=True)
        if not parent:
            break
        if cmds.nodeType(parent) == 'joint':
            if parent[0] in infNames:
                gen += 1
        nextJoint = parent[0]
    return gen

def _getHierarchyRootJoint( joint="" ):   
    # Search through the rootJoint's top most joint parent node
    rootJoint = joint
    while (True):
        parent = cmds.listRelatives( rootJoint, parent=True, type='joint' )
        if not parent:
            break;
        rootJoint = parent[0]
    return rootJoint 

def _getClusterName(node):
    # get the MFnSkinCluster for clusterName
    selList = OpenMaya.MSelectionList()
    selList.add(node)
    clusterNode = OpenMaya.MObject()
    selList.getDependNode(0, clusterNode)
    skinFn = OpenMayaAnim.MFnSkinCluster(clusterNode)
    return skinFn
    
def _infIDsDict(infDags, skin):
    # create a dictionary whose key is the MPlug indice id and 
    # whose value is the influence list id
    infIds = {}
    infs = []
    boneNamesIDs = {}
    for x in xrange(infDags.length()):
        infPath = infDags[x].fullPathName()
        infId = int(skin.indexForInfluenceObject(infDags[x]))
        infIds[infId] = x
        infs.append(infPath)
        boneNamesIDs[x] = infPath.rpartition('|')[-1]
    return infIds, infs, boneNamesIDs

def _normWeights(clusterName, shapeName):
    # normalize needs turned off for the prune to work
    skinNorm = cmds.getAttr('%s.normalizeWeights' % clusterName)
    if skinNorm != 0:
        cmds.setAttr('%s.normalizeWeights' % clusterName, 0)
    cmds.skinPercent(clusterName, shapeName, nrm=False, prw=100)
    # restore normalize setting
    if skinNorm != 0:
        cmds.setAttr('%s.normalizeWeights' % clusterName, skinNorm)


# Globals -------------------------------------------------------------------- #
global meshes
global origin
global mesh_skins_dict
global bones_list


# Public Methods ------------------------------------------------------------- #
def start():
    global meshes
    global origin
    global mesh_skins_dict
    global bones_list

    # Manually select some meshes
    meshes = cmds.ls(sl=1)
    # Feed it to the machine...
    mSel_skin_clusters  = api.MSelectionList()
    mesh_skins_dict     = {}
    skins_bones_dict    = {}
    bones_set           = set()
    skin_clusters       = cmds.ls(':*', exactType = 'skinCluster')
    for skin_cluster in skin_clusters:
        mSel_skin_clusters.add(skin_cluster)

    for i in xrange(mSel_skin_clusters.length()):
        depend_node = mSel_skin_clusters.getDependNode(i)
        skin_cluster_node = apiAnim.MFnSkinCluster(depend_node)
        all_skinned_meshes = skin_cluster_node.getOutputaddEventCallbackGeometry()
        for skinned_mesh in all_skinned_meshes:
            obj_dag_node = api.MDagPath.getAPathTo(skinned_mesh).transform()
            obj_dag_node = api.MDagPath.getAPathTo(obj_dag_node).partialPathName()
            if obj_dag_node in meshes:
                mesh_skins_dict[obj_dag_node] = skin_cluster_node.name()   
                infDags = skin_cluster_node.influenceObjects()
                infNames = [x.fullPathName().rpartition('|')[-1] for x in infDags]
                skins_bones_dict[skin_cluster_node.name()] = infNames
                bones_set |= set(infNames)
    bones_list = list(bones_set)            

    bones_parents = {}
    bonesGen = {}
    for inf in bones_list:
        # currentInf = inf.fullPathName().rpartition('|')[-1]
        parent = _getNextParentInList(bones_list, inf)
        gen = _getGenerationInList(bones_list, inf)
        bones_parents[inf] = parent
        bonesGen[inf] = gen

    # Set the stage
    cmds.select(clear=True)
    origin = 'origin'
    if not cmds.objExists(origin):
        origin = cmds.joint(name=origin)
    else:
        return

    for bone in bones_list:
        cmds.select(bone)
        boneLO = cmds.joint(name = bone + '_LO')
        cmds.parent(boneLO, origin)
        cmds.select(clear=True)

    transforms = cmds.listRelatives(origin)
    for transform in transforms:
        cmds.setAttr(transform + '.scale', 1, 1, 1)

    # sel = cmds.ls(sl=1)
    boneLOs = cmds.listRelatives(origin, allDescendents=True, type='joint')
    for bone in boneLOs:
        if cmds.nodeType(bone) == 'joint':
            parent = cmds.listRelatives(bone, parent=True)
            if parent[0] == origin:
                continue
            cmds.parent(bone, origin)
            cmds.delete(parent)
    # Make sure there aren't any transform groups mixed into the skeleton!!!

    # Restore the hierarchy
    for bone, parent in bones_parents.items():
        boneLO = bone + '_LO'
        parentLO = parent + '_LO'
        try:
            cmds.parent(boneLO, parentLO)
        except:
            pass


def end():
    global meshes
    global origin
    global mesh_skins_dict
    global bones_list

    # Then attach skins, fix, etc
    cmds.select(clear=True)
    meshes_LO_GRP = 'meshes_LO'
    if not cmds.objExists(meshes_LO_GRP):
        meshes_LO_GRP = cmds.group(name=meshes_LO_GRP, empty=True)

    # Dupe and clean all meshes
    kwargs = { # Settings for the skin bind
        'toSelectedBones': False,
        'bindMethod': 0,
        'skinMethod': 0,
        'normalizeWeights': 1,
        'maximumInfluences': 5,
    }
    meshes_LO = []
    for mesh in meshes:
        mesh_LO = cmds.duplicate(mesh, name=mesh + '_LO')[0]
        cmds.parent(mesh_LO, meshes_LO_GRP)
        for attr in cmds.listAttr(mesh_LO, locked = True) or []:
            cmds.setAttr(mesh_LO + "." + attr, lock = False)    
        # Delete those pesky unconnected Orig nodes
        hero_shape = cmds.listRelatives(\
            mesh_LO,
            shapes = True,
            noIntermediate = True)[0]
        mesh_LO_shapes = cmds.listRelatives(\
            mesh_LO,
            shapes = True,
            noIntermediate = False)
        for shape in mesh_LO_shapes:
            if not shape == hero_shape:
                cmds.delete(shape)
        
        # bones = skins_bones_dict[mesh_skins_dict[mesh]]
        # bones.append(origin)
        skin_LO = cmds.skinCluster(origin, mesh_LO, **kwargs)[0]

        skinFn = _getClusterName(mesh_skins_dict[mesh])
        newSkinFn = _getClusterName(skin_LO)

        # get the MDagPath for all influence
        infDags = OpenMaya.MDagPathArray()
        skinFn.influenceObjects(infDags)

        newInfDags = OpenMaya.MDagPathArray()
        newSkinFn.influenceObjects(newInfDags)

        infIds, infs, boneNamesIDs = _infIDsDict(infDags, skinFn)
        newinfIds, newInfs, newBoneNamesIDs = _infIDsDict(newInfDags, newSkinFn)

        # get the MPlug for the weightList and weights attributes
        wlPlug = skinFn.findPlug('weightList')
        wPlug = skinFn.findPlug('weights')
        wlAttr = wlPlug.attribute()
        wAttr = wPlug.attribute()
        wInfIds = OpenMaya.MIntArray()

        # the weights are stored in dictionary, the key is the vertId, 
        # the value is another dictionary whose key is the influence id and 
        # value is the weight for that influence
        weights = {}
        for vId in xrange(wlPlug.numElements()):
            vWeights = {}
            # tell the weights attribute which vertex id it represents
            wPlug.selectAncestorLogicalIndex(vId, wlAttr)
            
            # get the indice of all non-zero weights for this vert
            wPlug.getExistingArrayAttributeIndices(wInfIds)

            # create a copy of the current wPlug
            infPlug = OpenMaya.MPlug(wPlug)
            for infId in wInfIds:
                # tell the infPlug it represents the current influence id
                infPlug.selectAncestorLogicalIndex(infId, wAttr)
                
                # add this influence and its weight to this verts weights
                try:
                    vWeights[infIds[infId]] = infPlug.asDouble()
                except KeyError:
                    # assumes a removed influence
                    pass
            weights[vId] = vWeights


        # The following removes all weighting so only non-zero weights need applied:
        # unlock influences used by skincluster
        # for inf in infs:
        #     cmds.setAttr('%s.liw' % inf)
        for inf in newInfs:
            cmds.setAttr('%s.liw' % inf)

        _normWeights(skin_LO, mesh_LO) # Fix normalization before applying weights!

        # Now to set the weights using the weights variable you would use something like this:
        for vertId, weightData in weights.items():
            wlAttr = '%s.weightList[%s]' % (skin_LO, vertId)
            for infId, infValue in weightData.items():
                bone = boneNamesIDs[infId]
                newID = newBoneNamesIDs.keys()[newBoneNamesIDs.values().index(bone + '_LO')]
                wAttr = '.weights[%s]' % newID
                # if not cmds.skinPercent(newClusterName, newShapeName + '.vtx[%d]' % vertId, transform=bone + '_LO', q=True) == 0:
                cmds.setAttr(wlAttr + wAttr, infValue)
                #print cmds.skinPercent(newClusterName, newShapeName + '.vtx[%d]' % vertId, transform=bone + '_LO', q=True)

    # Parent Constrain new Skeleton with Original (based on names)
    for bone in bones_list:
        cmds.parentConstraint(bone, bone + '_LO', mo=False)


def createHierarchyFromSelected():
    # Helper script to parent chains (like Michelle's skirt)
    sel = cmds.ls(sl=1)
    for each in sel:
        if not each == sel[-1]:
            cmds.parent(each, sel[sel.index(each)+1])

